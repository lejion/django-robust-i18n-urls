import urllib.parse
from django.conf import settings
from django.core.urlresolvers import get_resolver, NoReverseMatch, resolve, Resolver404
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from .utils import try_url_for_language, translate_url


class RobustI18nLocaleMiddleware(object):
    """
    If `response.status_code == 404` this middleware makes sure to
    check request.path resolution in contex of all languages present
    in `settings.Languages`. If resolution succeeds a proper page will
    be returned instead. If resolution fails nothing happens.
    """

    def process_response(self, request, response):
        """
        If request status code is other than 404, just return provided response.
        If request status code is 404:
          - if request.path can be resolved in context of a language from
            `settings.Languages`, call `handle_successful_match` and return it's
            result
          - if request.path cannot be resolved in context of a language from
            `settings.Languages` return provided response.
        """
        if response.status_code == 404:
            all_languages = [i[0] for i in settings.LANGUAGES]
            resolver = get_resolver(None)
            for language in all_languages:
                match = try_url_for_language(request.path, language, resolver)
                if match is not None:
                    return self.handle_successful_match(request, match[0], match[1], match[2],
                                                        match.url_name, match.namespaces)
            return response
        else:
            return response

    def handle_successful_match(self, request, view, args, kwargs, url_name, namespaces):
        """
        Use found namespace and url name to reverse and redirect to proper page,
        if that fails use view function to render the correct view or redirect
        """

        try:
            return self.redirect_by_reverse(request, namespaces, url_name, *args, **kwargs)
        except (NoReverseMatch, IndexError):
            pass

        try:
            return self.render_by_function(request, view, *args, **kwargs)
        except Exception:
            return HttpResponseNotFound

    def redirect_by_reverse(self, request, namespaces, url_name, *args, **kwargs):
        parsed = urllib.parse.urlsplit(request.get_full_path())
        url = reverse('%s:%s' % (namespaces[0], url_name), args=args, kwargs=kwargs)
        full_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, url, parsed.query, parsed.fragment))
        return redirect(full_url)

    def render_by_function(self, request, view, args, kwargs):
        new_response = view(request, *args, **kwargs)
        if hasattr(new_response, 'render') and callable(new_response.render):
            new_response = new_response.render()
        return new_response


4

'''
Created on 13 lut 2014

@author: karol
'''
import urllib.parse

from contextlib import contextmanager

from django.core.urlresolvers import Resolver404, resolve, reverse, NoReverseMatch
from django.utils import translation
from django.utils.translation import get_language, override


@contextmanager
def locale_context(locale):
    """
    Calls given block of code between calls to `transaction,activate(locale)` and
    `transaction.deactivate()`.
    """
    original_locale = translation.get_language()
    translation.activate(locale)
    yield
    translation.activate(original_locale)


def try_url_for_language(path, language, resolver):
    """
    Tries to resolve given path forcing `transaction.get_language()` to be 
    given language. If url resoution succeeds returns a ResolverMatch, if
    not returns None.
    """
    with locale_context(language):
        try:
            return resolver.resolve(path)
        except Resolver404:
            return None


def translate_url(url, lang_code):
    """
    Given a URL (absolute or relative), try to get its translated version in
    the `lang_code` language (either by i18n_patterns or by translated regex).
    Return the original URL if no translated version is found.
    """
    parsed = urllib.parse.urlsplit(url)
    try:
        match = resolve(parsed.path)
    except Resolver404:
        pass
    else:
        to_be_reversed = "%s:%s" % (match.namespace, match.url_name) if match.namespace else match.url_name
        with override(lang_code):
            try:
                url = reverse(to_be_reversed, args=match.args, kwargs=match.kwargs)
            except NoReverseMatch:
                pass
            else:
                url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, url, parsed.query, parsed.fragment))
    return url

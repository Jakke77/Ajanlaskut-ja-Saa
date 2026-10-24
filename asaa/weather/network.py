"""Verified HTTPS for public weather APIs, including embedded Windows Python."""
from functools import lru_cache
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import urlopen as standard_urlopen
from ..platform_support import IS_WINDOWS

NETWORK_REVISION = 1


@lru_cache(maxsize=1)
def https_context():
    context = ssl.create_default_context()
    if IS_WINDOWS:
        # Windows Python enumerates installed roots, but cannot fetch missing
        # roots/intermediates like a browser. Retain OS trust and add Mozilla's
        # public roots shipped with the application. Verification stays enabled.
        import certifi
        context.load_verify_locations(cafile=certifi.where())
    return context


def urlopen(request, timeout=15):
    return standard_urlopen(request, timeout=timeout, context=https_context())


def network_error(error, service):
    if isinstance(error, HTTPError):
        return f'{service}: palvelin vastasi HTTP {error.code}'
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, ssl.SSLCertVerificationError):
        return f'{service}: HTTPS-varmenteen tarkistus epäonnistui'
    if isinstance(reason, ssl.SSLError):
        return f'{service}: suojattu HTTPS-yhteys epäonnistui'
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return f'{service}: yhteys aikakatkaistiin'
    if isinstance(reason, socket.gaierror):
        return f'{service}: palvelimen osoitetta ei voitu selvittää'
    if isinstance(error, (ValueError, KeyError, TypeError, SyntaxError)):
        return f'{service}: ennusteen tietoja ei voitu lukea'
    return f'{service}: verkkoyhteys epäonnistui'


def backoff_current(state):
    """Retry legacy connection failures once after the HTTPS fix.

    Healthy cache expiry and explicit server throttling remain in force. New
    failures keep their ordinary retry delay; an update does not erase data.
    """
    return (not state.get('error') or state.get('network_revision') == NETWORK_REVISION
            or state.get('http_status') in (429, 503)
            or any(code in state.get('error', '') for code in ('HTTP 429', 'HTTP 503')))

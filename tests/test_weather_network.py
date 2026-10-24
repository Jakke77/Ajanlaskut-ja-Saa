"""Public CA trust, useful errors and recovery from legacy negative caches."""
from datetime import timedelta
import io
import json
from pathlib import Path
import socket
import ssl
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from asaa.weather import network
from asaa.weather.forecast import ForecastCache, atomic_write
from asaa.weather.providers import SiteCache, Place
from tests.test_forecast import NOW, Response, payload
from tests.test_providers import foreca_body, row


class NetworkTests(unittest.TestCase):
    def tearDown(self): network.https_context.cache_clear()

    def test_windows_bundle_supplies_trust_when_system_store_is_empty(self):
        try:
            import certifi
        except ImportError:
            if sys.platform == 'win32': raise
            self.skipTest('Windows dependency certifi is not installed')
        empty = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(empty.cert_store_stats()['x509_ca'], 0)
        network.https_context.cache_clear()
        with patch.object(network, 'IS_WINDOWS', True), \
                patch.object(network.ssl, 'create_default_context', return_value=empty):
            context = network.https_context()
        self.assertGreater(context.cert_store_stats()['x509_ca'], 100)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_https_opener_passes_a_verified_context_and_timeout(self):
        network.https_context.cache_clear()
        with patch.object(network, 'standard_urlopen', return_value='response') as opener:
            self.assertEqual(network.urlopen('https://opendata.fmi.fi/wfs', timeout=7), 'response')
            self.assertEqual(opener.call_args.kwargs['timeout'], 7)
            context = opener.call_args.kwargs['context']
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_tls_dns_http_and_timeout_errors_are_distinguishable(self):
        cases = [(URLError(ssl.SSLCertVerificationError(1, 'verify failed')), 'HTTPS-varmenteen'),
                 (URLError(ssl.SSLError(1, 'handshake failed')), 'HTTPS-yhteys'),
                 (URLError(socket.gaierror(-2, 'name resolution')), 'osoitetta'),
                 (URLError(TimeoutError('timeout')), 'aikakatkaistiin'),
                 (HTTPError('https://api.met.no/', 403, 'Forbidden', {}, io.BytesIO()), 'HTTP 403')]
        for error, expected in cases:
            self.assertIn(expected, network.network_error(error, 'Yr'))

    def test_new_tls_failure_is_saved_with_cause_and_still_backs_off(self):
        with tempfile.TemporaryDirectory() as folder:
            opener = Mock(side_effect=URLError(ssl.SSLCertVerificationError(1, 'verify failed')))
            cache = SiteCache('fmi', Place(), Path(folder), opener)
            for now in (NOW, NOW + timedelta(minutes=1)):
                with self.assertRaisesRegex(ValueError, 'HTTPS-varmenteen'): cache.fetch(now)
            self.assertEqual(opener.call_count, 1)
            self.assertIsNone(cache.cached(NOW))

    def test_yr_retries_legacy_network_failure_after_update(self):
        with tempfile.TemporaryDirectory() as folder:
            opener = Mock(return_value=Response(payload()))
            cache = ForecastCache(Path(folder), opener)
            atomic_write(cache.path, json.dumps(dict(url=cache.url, error='Sääpalveluun ei saada yhteyttä',
                next_request=(NOW + timedelta(minutes=15)).isoformat())))
            self.assertEqual(len(cache.fetch(NOW).hours), 24)
            self.assertEqual(opener.call_count, 1)

    def test_site_retries_legacy_failure_without_deleting_cached_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            response = Mock(); response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False); response.headers = {}; response.url = 'https://www.foreca.fi/'
            response.read.return_value = foreca_body([row(), row(hour='06.00')]).encode('utf-8')
            opener = Mock(return_value=response)
            cache = SiteCache('foreca', Place(), Path(folder), opener)
            atomic_write(cache.path, json.dumps(dict(provider='foreca', location=Place().key,
                error='FORECA: ennustetta ei voitu hakea', next_request=(NOW + timedelta(minutes=30)).isoformat())))
            self.assertTrue(cache.fetch(NOW).hours)
            self.assertEqual(opener.call_count, 1)

    def test_legacy_explicit_throttling_and_healthy_cache_still_back_off(self):
        self.assertTrue(network.backoff_current({'error': 'Palvelu (HTTP 429)'}))
        self.assertTrue(network.backoff_current({'error': 'Palvelu (HTTP 503)'}))
        self.assertTrue(network.backoff_current({'error': ''}))
        with tempfile.TemporaryDirectory() as folder:
            opener = Mock()
            cache = ForecastCache(Path(folder), opener)
            atomic_write(cache.path, json.dumps(dict(url=cache.url, error='Palvelu (HTTP 429)',
                next_request=(NOW + timedelta(hours=1)).isoformat())))
            with self.assertRaisesRegex(ValueError, 'HTTP 429'): cache.fetch(NOW)
            opener.assert_not_called()


if __name__ == '__main__': unittest.main()

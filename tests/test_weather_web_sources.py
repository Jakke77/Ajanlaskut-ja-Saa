"""Public source selection never turns cached URLs into arbitrary navigation."""
import unittest
from urllib.parse import parse_qs, urlsplit

from asaa.weather.providers import Place
from asaa.weather.web_sources import (
    FMI_RADAR_URL, FORECA_RADAR_URL, foreca_map_url, forecast_url, map_url, source_url,
)


class WeatherWebSourcesTests(unittest.TestCase):
    def setUp(self):
        self.oulu = Place('Oulu', 65.0701, 25.5071)
        self.helsinki = Place('Helsinki', 60.1699, 24.9384)

    def test_windy_forecast_uses_actual_place_and_only_forecast_embed(self):
        parsed = urlsplit(forecast_url(self.oulu))
        self.assertEqual((parsed.scheme, parsed.netloc, parsed.path),
                         ('https', 'embed.windy.com', '/embed.html'))
        params = parse_qs(parsed.query)
        self.assertEqual(params, {
            'type': ['forecast'], 'location': ['coordinates'], 'detail': ['true'],
            'detailLat': ['65.0701'], 'detailLon': ['25.5071'],
            'metricTemp': ['°C'], 'metricRain': ['mm'], 'metricWind': ['m/s'],
        })

    def test_original_windy_map_camera_and_selected_layer_remain(self):
        oulu = parse_qs(urlsplit(map_url(self.oulu, 9, 'temp')).query)
        self.assertEqual((oulu['lat'], oulu['lon']), (['65.03'], ['25.4']))
        self.assertEqual(oulu['type'], ['map'])
        helsinki = parse_qs(urlsplit(map_url(self.helsinki, 7, 'rain')).query)
        self.assertEqual((helsinki['lat'], helsinki['lon']), (['60.1699'], ['24.9384']))
        self.assertEqual((helsinki['zoom'], helsinki['overlay']), (['7'], ['rain']))

    def test_foreca_uses_selected_coordinates_even_if_cached_city_differs(self):
        for resolved in ('https://www.foreca.fi/Finland/Oulu',
                         'https://foreca.fi/Finland/Oulu/',
                         'https://www.foreca.fi/Finland/Oulu/tuntiennuste?hours=12#forecast'):
            with self.subTest(resolved=resolved):
                parsed = urlsplit(foreca_map_url(resolved, place=self.helsinki, zoom=7))
                self.assertEqual((parsed.scheme, parsed.netloc, parsed.path),
                                 ('https', 'www.foreca.fi', '/tutka'))
                self.assertEqual(parse_qs(parsed.query),
                                 {'lt':['60.1699'], 'ln':['24.9384'],
                                  'z':['7'], 'l':['tutkaennuste']})

    def test_foreca_without_place_uses_current_renderer_not_older_city_page(self):
        self.assertEqual(foreca_map_url('https://www.foreca.fi/Finland/%C3%84k%C3%A4slompolo'),
                         FORECA_RADAR_URL)

    def test_foreca_zoom_is_the_supported_integer_range(self):
        for zoom in (0, 21, 9.5, '9', True):
            with self.subTest(zoom=zoom), self.assertRaises(ValueError):
                foreca_map_url(place=self.oulu, zoom=zoom)

    def test_missing_or_unsafe_foreca_cache_uses_national_official_page(self):
        for resolved in ('', None, {}, 'https://www.foreca.fi/sadetutka',
                         'http://www.foreca.fi/Finland/Oulu',
                         'https://www.foreca.fi.evil.test/Finland/Oulu',
                         'https://user@www.foreca.fi/Finland/Oulu',
                         'https://www.foreca.fi@evil.test/Finland/Oulu',
                         'https://www.foreca.fi:443/Finland/Oulu',
                         'file:///Finland/Oulu', '//www.foreca.fi/Finland/Oulu',
                         'https://www.foreca.fi/Finland/../Oulu',
                         'https://www.foreca.fi/Finland/%2F%2Fevil.test',
                         'https://www.foreca.fi/Finland/%252F%252Fevil.test',
                         'https://www.foreca.fi/Finland/%FF',
                         '\nhttps://www.foreca.fi/Finland/Oulu', 'x' * 2001):
            with self.subTest(resolved=resolved):
                self.assertEqual(foreca_map_url(resolved), FORECA_RADAR_URL)

    def test_fmi_is_the_national_rain_page_without_fabricated_location_query(self):
        self.assertEqual(source_url('fmi', 'map', self.oulu), FMI_RADAR_URL)
        self.assertEqual(source_url('fmi', 'map', self.helsinki), FMI_RADAR_URL)

    def test_source_router_separates_windy_graph_from_native_providers(self):
        self.assertEqual(source_url('windy', 'graph', self.oulu), forecast_url(self.oulu))
        self.assertEqual(source_url('windy', 'map', self.helsinki, 7, 'rain'),
                         map_url(self.helsinki, 7, 'rain'))
        self.assertEqual(source_url('foreca', 'map', self.oulu,
                                    foreca_url='https://www.foreca.fi/Finland/Oulu'),
                         foreca_map_url(place=self.oulu))
        for provider, mode in (('yr', 'map'), ('foreca', 'graph'), ('fmi', 'graph'),
                               ('windy', 'unknown'), ('unknown', 'map')):
            with self.subTest(provider=provider, mode=mode), self.assertRaises(ValueError):
                source_url(provider, mode, self.oulu)


if __name__ == '__main__':
    unittest.main()

"""Official weather pages; no copied tiles or alternate forecast attribution."""
from __future__ import annotations

import re
from urllib.parse import quote, unquote, urlencode, urlsplit


FORECA_RADAR_URL = 'https://www.foreca.fi/sadetutka'
FMI_RADAR_URL = 'https://www.ilmatieteenlaitos.fi/sadekartta'


def map_url(place, zoom=9, layer='temp'):
    """Keep the existing Windy map and its Oulu/Hailuoto camera position."""
    lat, lon = ((65.03, 25.40) if place.key == '65.0701,25.5071'
                else (place.latitude, place.longitude))
    return 'https://embed.windy.com/embed.html?' + urlencode(dict(
        type='map', location='coordinates', lat=lat, lon=lon, zoom=zoom,
        overlay=layer, level='surface', product='ecmwf', metricTemp='°C',
        metricWind='m/s', metricRain='mm', marker='false'))


def forecast_url(place):
    """Windy's public, map-free hourly forecast, using the actual place."""
    return 'https://embed.windy.com/embed.html?' + urlencode(dict(
        type='forecast', location='coordinates', detail='true',
        detailLat=place.latitude, detailLon=place.longitude,
        metricTemp='°C', metricRain='mm', metricWind='m/s'))


def foreca_map_url(resolved_url=''):
    """Use a validated city resolved by Foreca, otherwise its national radar.

    The cached source URL is user-writable. Never navigate to its arbitrary
    host, retain a query/fragment or guess a city from the user-facing name.
    """
    if (not isinstance(resolved_url, str) or len(resolved_url) > 2000
            or any(ord(char) <= 32 for char in resolved_url)):
        return FORECA_RADAR_URL
    try:
        parsed = urlsplit(resolved_url)
        if (parsed.scheme != 'https'
                or parsed.netloc.lower() not in ('www.foreca.fi', 'foreca.fi')):
            return FORECA_RADAR_URL
        parts = parsed.path.strip('/').split('/')
        if len(parts) < 2:
            return FORECA_RADAR_URL
        country, city = (unquote(part, errors='strict') for part in parts[:2])
        if not all(re.fullmatch(r'[\w-]+', part) for part in (country, city)):
            return FORECA_RADAR_URL
        return ('https://www.foreca.fi/' + quote(country, safe='-_') + '/'
                + quote(city, safe='-_') + '/kartta-v2')
    except (ValueError, UnicodeError):
        return FORECA_RADAR_URL


def source_url(provider, mode, place, zoom=9, layer='temp', foreca_url=''):
    """Select only the supported official web views, not native graph sources."""
    if provider == 'windy':
        if mode == 'map':
            return map_url(place, zoom, layer)
        if mode == 'graph':
            return forecast_url(place)
    elif mode == 'map':
        if provider == 'foreca':
            return foreca_map_url(foreca_url)
        if provider == 'fmi':
            return FMI_RADAR_URL
    raise ValueError('Tälle sääpalvelulle ei ole tätä verkkonäkymää')

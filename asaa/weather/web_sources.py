"""Official weather pages; no copied tiles or alternate forecast attribution."""
from __future__ import annotations

from urllib.parse import urlencode


FORECA_RADAR_URL = 'https://www.foreca.fi/tutka'
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


def foreca_map_url(resolved_url='', *, place=None, zoom=9):
    """Use Foreca's current radar and its own coordinate/layer parameters.

    Older city pages can omit the site's fullscreen control. The current
    /tutka renderer supports it and reads lt/ln/z/l directly. Cached forecast
    URLs are deliberately not navigation inputs, including their queries.
    """
    if place is None:
        return FORECA_RADAR_URL
    if type(zoom) is not int or not 1 <= zoom <= 20:
        raise ValueError('Virheellinen Forecan kartan zoom')
    return FORECA_RADAR_URL + '?' + urlencode(dict(
        lt=place.latitude, ln=place.longitude, z=zoom, l='tutkaennuste'))


def source_url(provider, mode, place, zoom=9, layer='temp', foreca_url=''):
    """Select only the supported official web views, not native graph sources."""
    if provider == 'windy':
        if mode == 'map':
            return map_url(place, zoom, layer)
        if mode == 'graph':
            return forecast_url(place)
    elif mode == 'map':
        if provider == 'foreca':
            return foreca_map_url(foreca_url, place=place, zoom=zoom)
        if provider == 'fmi':
            return FMI_RADAR_URL
    raise ValueError('Tälle sääpalvelulle ei ole tätä verkkonäkymää')

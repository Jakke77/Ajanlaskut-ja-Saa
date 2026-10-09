"""Independent forecast sources, fixed UTC slots and common comparison scales."""
from __future__ import annotations
import ast
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
import fcntl
from functools import partial
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
from .forecast import (Forecast, ForecastCache, Hour, LOCATION, TZ, UTC, URL,
                      USER_AGENT, atomic_write, cache_directory, instant, number)

PROVIDERS = ('yr', 'foreca', 'fmi')
NAMES = {'yr': 'YR · MET NORWAY', 'foreca': 'FORECA', 'fmi': 'ILMATIETEEN LAITOS'}

@dataclass(frozen=True)
class Place:
    name: str = LOCATION
    latitude: float = 65.0701
    longitude: float = 25.5071
    timezone: str = 'Europe/Helsinki'

    def __post_init__(self):
        if not -90 <= number(self.latitude) <= 90 or not -180 <= number(self.longitude) <= 180:
            raise ValueError('Virheellinen sijainti')
        ZoneInfo(self.timezone)
        if not self.name.strip() or len(self.name) > 180:
            raise ValueError('Virheellinen paikan nimi')

    @property
    def key(self):
        return f'{self.latitude:.4f},{self.longitude:.4f}'


def read_place(settings):
    try:
        return Place(**json.loads(settings.value('place', '{}')))
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError):
        return Place()


def slots(now=None, count=12):
    start = (now or datetime.now(UTC)).astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    return tuple(start + timedelta(hours=i) for i in range(count))


def aligned(forecast, times):
    by_time = {h.time.astimezone(UTC): h for h in forecast.hours} if forecast else {}
    return tuple(by_time.get(t) for t in times)


@dataclass(frozen=True)
class Scales:
    temperature: tuple[float, float]
    wind: float
    rain: float


def common_scales(forecasts, times):
    hours = [h for f in forecasts if f for h in aligned(f, times) if h]
    temps = [h.temperature for h in hours] or [0]
    lo = math.floor((min(temps) - 1) / 2) * 2
    hi = max(lo + 4, math.ceil((max(temps) + 1) / 2) * 2)
    wind = max([h.gust or h.wind for h in hours] + [h.wind for h in hours] + [2])
    rain = max([h.rain or 0 for h in hours] + [.5])
    return Scales((lo, hi), math.ceil((wind + 1) / 2) * 2, math.ceil(rain * 2) / 2)


def foreca_symbol(code):
    if not re.fullmatch('[dn][0-6][0-4][0-2]', code):
        return 'unknown'
    cloud, rate, kind = map(int, code[1:])
    name = {0:'clearsky', 1:'fair', 2:'partlycloudy', 3:'partlycloudy',
            4:'cloudy', 5:'fair', 6:'fog'}[cloud]
    if rate:
        name = ('partlycloudy' if cloud < 4 else 'cloudy') + ('rain','sleet','snow')[kind]
        if rate == 4:
            name += 'thunder'
    return name + ('_night' if code[0] == 'n' else '_day')


def fmi_symbol(value):
    value = int(number(value))
    if value in (1,2,3):
        return {1:'clearsky',2:'partlycloudy',3:'cloudy'}[value]
    if value in (91,92):
        return 'fog'
    if value in (61,62,63,64):
        return 'cloudyrainthunder'
    if value // 10 in (2,3):
        return 'cloudyrain'
    if value // 10 in (4,5):
        return 'cloudysnow'
    if value // 10 in (7,8):
        return 'cloudysleet'
    return 'unknown'


def forecast_from_rows(rows, fetched, now=None, error=''):
    now = now or datetime.now(UTC)
    hours = tuple(h for h in rows if h.time.astimezone(UTC) + timedelta(hours=1) > now)
    if not hours:
        raise ValueError('Ennusteessa ei ole ajantasaisia tuntitietoja')
    return Forecast(hours, fetched, fetched, error)


def parse_foreca(body, fetched, now=None, error='', zone=TZ):
    # Read scalar literals only; never run scripts received from a web page.
    match = re.search(r'\bdata_1h:\s*(\[.*?\])', body, re.S)
    stamp = re.search(r'\bvar\s+page_settings\s*=\s*\{(.*?)\};', body, re.S)
    if not match or not stamp:
        raise ValueError('Forecan tuntiennusteen rakenne muuttui')
    epoch = re.search(r'\bt\s*:\s*(\d{9,12})', stamp[1])
    if not epoch:
        raise ValueError('Forecan aikaleima puuttuu')
    reference = datetime.fromtimestamp(int(epoch[1]), zone)
    literal = re.sub(r'([,{]\s*)([A-Za-z_][A-Za-z_0-9]*)(\s*:)', r"\1'\2'\3", match[1])
    rows = ast.literal_eval(literal)
    if not isinstance(rows, list) or len(rows) > 240:
        raise ValueError('Virheellinen Foreca-vastaus')
    values = {}
    previous = None
    for row in rows:
        day, month = [int(x) for x in row['dt'].strip('.').split('.')]
        hh, minute = [int(x) for x in row['hi'].split('.')]
        candidates = []
        for year in (reference.year - 1, reference.year, reference.year + 1):
            try:
                local = datetime(year, month, day, hh, minute, tzinfo=zone)
                for fold in (0,1):
                    candidate = local.replace(fold=fold).astimezone(UTC)
                    if candidate.astimezone(zone).replace(tzinfo=None) == local.replace(tzinfo=None):
                        candidates.append(candidate)
            except ValueError:
                continue
        if previous:
            candidates = [x for x in candidates if x > previous]
        if not candidates:
            raise ValueError('Forecan kellonajat ovat virheellisiä')
        t = min(candidates, key=lambda x: abs((x - (previous + timedelta(hours=1) if previous else reference)).total_seconds()))
        if abs((t - reference).total_seconds()) > 21 * 86400:
            raise ValueError('Forecan ennustepäivä on virheellinen')
        values[t] = row
        previous = t
    hours = []
    for t, row in sorted(values.items()):
        # r belongs to the hour ending at t. Display all rain at interval START.
        following = values.get(t + timedelta(hours=1), {})
        rain = following.get('r')
        hours.append(Hour(t, number(row['t']), max(0,number(rain)) if rain is not None else None,
                          max(0,number(row['ws'])), max(0,number(row['wg'])) if row.get('wg') is not None else None,
                          number(row['wd']) % 360, foreca_symbol(str(row['s'])),
                          number(row['tf']) if row.get('tf') is not None else None))
    return forecast_from_rows(hours, fetched, now, error)


def parse_fmi(body, fetched, now=None, error=''):
    root = ET.fromstring(body)
    data = {}
    for item in root.iter():
        if item.tag.rsplit('}',1)[-1] != 'BsWfsElement':
            continue
        fields = {e.tag.rsplit('}',1)[-1]: e.text for e in item}
        try:
            time = instant(fields['Time']).astimezone(UTC)
            data.setdefault(time,{})[fields['ParameterName']] = number(fields['ParameterValue'])
        except (KeyError, TypeError, ValueError):
            continue
    hours = []
    for t, row in sorted(data.items()):
        try:
            rain = data.get(t + timedelta(hours=1), {}).get('Precipitation1h')
            hours.append(Hour(t, row['Temperature'], max(0,rain) if rain is not None else None,
                              max(0,row['WindSpeedMS']), row.get('HourlyMaximumGust'),
                              row['WindDirection'] % 360, fmi_symbol(row.get('WeatherSymbol3',0))))
        except KeyError:
            continue
    return forecast_from_rows(hours, fetched, now, error)


def search_places(query, opener=urlopen):
    query = query.strip()
    if len(query) < 2:
        raise ValueError('Kirjoita vähintään kaksi merkkiä')
    url = 'https://geocoding-api.open-meteo.com/v1/search?' + urlencode(
        dict(name=query, count=10, language='fi'))
    with opener(Request(url, headers={'User-Agent':USER_AGENT}), timeout=15) as response:
        result = json.loads(response.read(500_001))
    places = []
    for row in result.get('results', []):
        names = list(dict.fromkeys(x for x in (row.get('name'), row.get('admin2'), row.get('country')) if x))
        try:
            places.append(Place(', '.join(names), row['latitude'], row['longitude'], row.get('timezone','Europe/Helsinki')))
        except (KeyError,ValueError,TypeError):
            continue
    return places


class SiteCache:
    """Bounded raw response cache with one request per 30 min and offline fallback."""
    def __init__(self, provider, place, directory=None, opener=urlopen):
        self.provider, self.place, self.opener = provider, place, opener
        self.directory = directory if directory is not None else cache_directory()
        key = hashlib.sha256(place.key.encode()).hexdigest()[:16]
        self.path = self.directory / f'{provider}-{key}.json'
        self.parser = partial(parse_foreca,zone=ZoneInfo(place.timezone)) if provider == 'foreca' else parse_fmi

    def read(self):
        try:
            state = json.loads(self.path.read_text())
            return state if state.get('location') == self.place.key and state.get('provider') == self.provider else {}
        except (OSError,ValueError,AttributeError):
            return {}

    def cached(self, now=None):
        state = self.read()
        try:
            return self.parser(state['body'], instant(state['fetched']), now, state.get('error',''))
        except (KeyError,ValueError,TypeError,SyntaxError,ET.ParseError,AttributeError,OverflowError,IndexError):
            return None

    def request(self, now):
        if self.provider == 'foreca':
            # This is the website's observed "use my location" form, not a private API.
            return Request('https://www.foreca.fi/search', data=urlencode(dict(q='',do_search=1,
                geolocation_lat=self.place.latitude, geolocation_lon=self.place.longitude)).encode(),
                headers={'User-Agent':USER_AGENT, 'Accept-Encoding':'gzip'})
        start = now.astimezone(UTC).replace(minute=0,second=0,microsecond=0)
        return Request('https://opendata.fmi.fi/wfs?' + urlencode(dict(service='WFS',version='2.0.0',
            request='GetFeature', storedquery_id='fmi::forecast::edited::weather::scandinavia::point::simple',
            latlon=self.place.key, starttime=start.isoformat(), endtime=(start+timedelta(hours=25)).isoformat(),
            timestep=60, parameters='Temperature,WindSpeedMS,WindDirection,HourlyMaximumGust,Precipitation1h,WeatherSymbol3')),
            headers={'User-Agent':USER_AGENT,'Accept-Encoding':'gzip'})

    def fetch(self, now=None):
        now = now or datetime.now(UTC)
        self.directory.mkdir(parents=True,exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            state = self.read()
            try:
                due = instant(state.get('next_request',''))
            except ValueError:
                due = now
            if now < due:
                cached = self.cached(now)
                if cached:
                    return cached
                raise ValueError(state.get('error') or 'Odotetaan sääpalvelun päivitystä')
            try:
                with self.opener(self.request(now),timeout=15) as response:
                    body = response.read(2_000_001)
                    if len(body) > 2_000_000:
                        raise ValueError('Liian suuri vastaus')
                    if response.headers.get('Content-Encoding') == 'gzip':
                        body = gzip.decompress(body)
                    if len(body) > 4_000_000:
                        raise ValueError('Liian suuri vastaus')
                    body = body.decode('utf-8')
                    result = self.parser(body,now,now)
                    # Cache only forecast literals, not tracking scripts or public map keys.
                    if self.provider == 'foreca':
                        array = re.search(r'\bdata_1h:\s*(\[.*?\])',body,re.S)[1]
                        info = re.search(r'\bvar\s+page_settings\s*=\s*\{(.*?)\};',body,re.S)[1]
                        epoch = re.search(r'\bt\s*:\s*(\d{9,12})',info)[1]
                        name = re.search(r'\bname\s*:\s*("[^"]*"|\x27[^\x27]*\x27)',info)
                        resolved = ast.literal_eval(name[1]) if name else ''
                        state['resolved_name'] = resolved
                        state['source_url'] = response.url
                        body = f'var page_settings = {{t:{epoch}}}; data_1h: {array}'
                state.update(body=body,fetched=now.isoformat(),error='',next_request=(now+timedelta(minutes=30)).isoformat())
            except (OSError,ValueError,KeyError,TypeError,SyntaxError,ET.ParseError,AttributeError,OverflowError,IndexError) as exc:
                delay = 30*60
                if isinstance(exc,HTTPError):
                    try: delay = max(delay,int(exc.headers.get('Retry-After','0')))
                    except ValueError: pass
                    exc.close()
                state.update(error=f'{NAMES[self.provider]}: ennustetta ei voitu hakea',next_request=(now+timedelta(seconds=delay)).isoformat())
                result = None
            state.update(location=self.place.key,provider=self.provider)
            atomic_write(self.path,json.dumps(state,ensure_ascii=False)+'\n')
            result = result or self.cached(now)
            if not result:
                raise ValueError(state['error'])
            return result


def provider_caches(place, directory=None):
    key = hashlib.sha256(place.key.encode()).hexdigest()[:16]
    met = ForecastCache(directory,url='https://api.met.no/weatherapi/locationforecast/2.0/complete?' +
        urlencode(dict(lat=f'{place.latitude:.4f}',lon=f'{place.longitude:.4f}')),
        filename='forecast.json' if place.key == Place().key else f'yr-{key}.json')
    return {'yr':met, 'foreca':SiteCache('foreca',place,directory), 'fmi':SiteCache('fmi',place,directory)}

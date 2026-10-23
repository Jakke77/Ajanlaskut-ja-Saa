"""Local, offline Sun/Moon almanac using the bundled, unmodified PyMeeus.

Positions use TT; rotation, civil-day bounds and returned instants use UTC.
Rise/set is the upper limb on a level sea horizon with standard refraction.
Times are estimates: terrain and the actual atmosphere are not modelled.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

try:
    from pymeeus.Epoch import Epoch
except ModuleNotFoundError as error:
    if error.name != 'pymeeus':
        raise
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor'))
    from pymeeus.Epoch import Epoch
from pymeeus.Moon import Moon
from pymeeus.Sun import Sun
from pymeeus.Coordinates import true_obliquity, nutation_longitude

UTC = timezone.utc
JD_UNIX = 2440587.5
MIN_YEAR, MAX_YEAR = 1900, 2100
PHASE_NAMES = {'new': 'Uusikuu', 'first': 'Ensimmäinen neljännes',
               'full': 'Täysikuu', 'last': 'Viimeinen neljännes'}


def check_day(day):
    if not MIN_YEAR <= day.year <= MAX_YEAR:
        raise ValueError('Tähtitieteellinen laskenta on saatavilla vuosille 1900–2100.')


def _epochs(jd):
    ut = Epoch(float(jd))
    year, month, _ = ut.get_date()
    return ut, Epoch(jd + Epoch.tt2ut(year, month) / 86400)


def _from_tt(epoch):
    year, month, _ = epoch.get_date()
    return datetime.fromtimestamp((float(epoch) - JD_UNIX) * 86400
                                  - Epoch.tt2ut(year, month), UTC)


def julian_day(moment):
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError('Aikaleima tarvitsee aikavyöhykkeen.')
    return moment.timestamp() / 86400 + JD_UNIX


@dataclass(frozen=True)
class MoonInfo:
    name: str
    illumination: float
    angle: float
    age: float

    @property
    def label(self):
        return f'{self.name} · {self.illumination:.0%}'


@lru_cache(maxsize=4096)
def _moon_minute(minute):
    moment = datetime.fromtimestamp(minute * 60, UTC)
    check_day(moment.date())
    _, tt = _epochs(julian_day(moment))
    lunar_lon = Moon.apparent_ecliptical_pos(tt)[0]
    solar_lon = Sun.apparent_longitude_coarse(tt)[0]
    angle = (float(lunar_lon) - float(solar_lon)) % 360
    illumination = min(1.0, max(0.0, Moon.illuminated_fraction_disk(tt)))
    if angle < 6 or angle >= 354:
        name = PHASE_NAMES['new']
    elif abs(angle - 90) <= 6:
        name = PHASE_NAMES['first']
    elif abs(angle - 180) <= 6:
        name = PHASE_NAMES['full']
    elif abs(angle - 270) <= 6:
        name = PHASE_NAMES['last']
    elif angle < 90:
        name = 'Kasvava sirppi'
    elif angle < 180:
        name = 'Kasvava kuu'
    elif angle < 270:
        name = 'Vähenevä kuu'
    else:
        name = 'Vähenevä sirppi'
    candidates = [_from_tt(Moon.moon_phase(tt + offset, 'new')) for offset in (-32, -16, 0)]
    previous = max(candidate for candidate in candidates if candidate <= moment)
    return MoonInfo(name, illumination, angle, (moment - previous).total_seconds() / 86400)


def moon_at(moment):
    julian_day(moment)  # Reject naive datetimes rather than using host time.
    return _moon_minute(math.floor(moment.timestamp() / 60))


@lru_cache(maxsize=2048)
def moon_on(day, zone='Europe/Helsinki'):
    """A selected date's phase is evaluated at local noon in every calendar."""
    check_day(day)
    return moon_at(datetime.combine(day, time(12), ZoneInfo(zone)))


def phase_label(day, zone='Europe/Helsinki'):
    try:
        return moon_on(day, zone).label
    except ValueError as error:
        return str(error)


@lru_cache(maxsize=512)
def phase_events(day):
    """Nearby true phase instants, sorted and deduplicated (UTC)."""
    check_day(day)
    _, tt = _epochs(julian_day(datetime.combine(day, time(12), UTC)))
    events = {}
    for target, title in PHASE_NAMES.items():
        # Spacing shorter than a lunation matters: PyMeeus' year-based phase
        # seed can select the following event even when the previous is nearer.
        for offset in range(-35, 71, 14):
            moment = _from_tt(Moon.moon_phase(tt + offset, target))
            events[(target, moment.date())] = (moment, title)
    return tuple(sorted(events.values()))


@dataclass(frozen=True)
class Horizon:
    rises: tuple
    sets: tuple
    segments: tuple
    duration: float
    state: str


@dataclass(frozen=True)
class SolarDay:
    day: date
    zone: str
    start: datetime
    end: datetime
    sun: Horizon
    civil: Horizon
    nautical: Horizon
    astronomical: Horizon


def _bounds(day, zone):
    tz = ZoneInfo(zone)
    start = datetime.combine(day, time(), tz).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time(), tz).astimezone(UTC)
    if end <= start:
        raise ValueError('Tämä paikallinen päivämäärä puuttuu aikavyöhykkeeltä.')
    return start, end


@lru_cache(maxsize=32768)
def _position_hour(body, hour):
    _, tt = _epochs(hour / 24 + JD_UNIX)
    if body == 'sun':
        ra, dec, distance = Sun.apparent_rightascension_declination_coarse(tt)
    else:
        ra, dec, distance, _ = Moon.apparent_equatorial_pos(tt)
    equation = float(nutation_longitude(tt)) * math.cos(true_obliquity(tt).rad())
    return float(ra), float(dec), distance, equation


def _altitude(body, stamp, latitude, longitude):
    # Hourly interpolation of slow orbital coordinates avoids repeating the
    # entire ephemeris for each one-second root step. Earth rotation uses the
    # actual UT instant, not the rounded hour. RA interpolation wraps at 360°.
    hour = math.floor(stamp / 3600)
    fraction = stamp / 3600 - hour
    a, b = _position_hour(body, hour), _position_hour(body, hour + 1)
    ra = a[0] + ((b[0] - a[0] + 180) % 360 - 180) * fraction
    dec, distance, equation = (a[i] + (b[i] - a[i]) * fraction for i in (1, 2, 3))
    jd = stamp / 86400 + JD_UNIX
    t = (jd - 2451545.0) / 36525
    sidereal = (280.46061837 + 360.98564736629 * (jd - 2451545.0)
                + 0.000387933 * t*t - t*t*t / 38710000 + equation)
    hour_angle = math.radians((sidereal + longitude - ra) % 360)
    phi, delta = math.radians(latitude), math.radians(dec)
    if body == 'moon':
        # Subtract the geodetic observer from the geocentric lunar vector.
        u = math.atan2(0.99664719 * math.sin(phi), math.cos(phi))
        x = distance * math.cos(delta) * math.cos(hour_angle) - 6378.137 * math.cos(u)
        y = -distance * math.cos(delta) * math.sin(hour_angle)
        z = distance * math.sin(delta) - 6378.137 * 0.99664719 * math.sin(u)
        up = x * math.cos(phi) + z * math.sin(phi)
        north = -x * math.sin(phi) + z * math.cos(phi)
        altitude = math.degrees(math.atan2(up, math.hypot(north, y)))
        return altitude + 0.5667 + math.degrees(math.asin(1737.4 / distance))
    return math.degrees(math.asin(max(-1, min(1, math.sin(phi) * math.sin(delta)
                        + math.cos(phi) * math.cos(delta) * math.cos(hour_angle)))))


def _samples(function, start, end):
    count = math.ceil((end - start) / 300)
    samples = [(start + (end - start) * i / count, None) for i in range(count + 1)]
    samples = [(stamp, function(stamp)) for stamp, _ in samples]
    # Refine both extrema so a short polar rise/set is not lost between samples.
    extra = []
    for i in range(1, len(samples) - 1):
        left, center, right = samples[i-1][1], samples[i][1], samples[i+1][1]
        if (center > left and center > right) or (center < left and center < right):
            sign = 1 if center > left else -1
            a, b = samples[i-1][0], samples[i+1][0]
            for _ in range(24):
                c, d = a + (b-a)/3, b - (b-a)/3
                if sign * function(c) > sign * function(d):
                    b = d
                else:
                    a = c
            stamp = (a+b)/2
            extra.append((stamp, function(stamp)))
    return sorted(samples + extra)


def _horizon(samples, function, threshold, start, end, zone):
    events = []
    for (a, va), (b, vb) in zip(samples, samples[1:]):
        rising = va <= threshold < vb
        setting = va > threshold >= vb
        if not (rising or setting):
            continue
        lo, hi = a, b
        for _ in range(16):
            mid = (lo + hi) / 2
            if (function(mid) > threshold) == rising:
                hi = mid
            else:
                lo = mid
        stamp = (lo + hi) / 2
        if start <= stamp < end:
            events.append((stamp, rising))
    above = samples[0][1] > threshold
    segment_start, segments = start, []
    for stamp, rising in events:
        if above:
            segments.append((segment_start, stamp))
        above, segment_start = rising, stamp
    if above:
        segments.append((segment_start, end))
    tz = ZoneInfo(zone)
    local = lambda stamp: datetime.fromtimestamp(stamp, tz)
    return Horizon(tuple(local(stamp) for stamp, rising in events if rising),
                   tuple(local(stamp) for stamp, rising in events if not rising),
                   tuple((local(a), local(b)) for a, b in segments),
                   sum(b-a for a, b in segments),
                   'crosses' if events else 'always_above' if above else 'always_below')


def _validate(day, latitude, longitude, zone):
    check_day(day)
    if not (math.isfinite(latitude) and -90 <= latitude <= 90
            and math.isfinite(longitude) and -180 <= longitude <= 180):
        raise ValueError('Virheelliset koordinaatit.')
    return _bounds(day, zone)


@lru_cache(maxsize=1024)
def solar_day(day, latitude, longitude, zone):
    start, end = _validate(day, latitude, longitude, zone)
    function = lambda stamp: _altitude('sun', stamp, latitude, longitude)
    a, b = start.timestamp(), end.timestamp()
    samples = _samples(function, a, b)
    horizons = [_horizon(samples, function, threshold, a, b, zone)
                for threshold in (-0.8333, -6, -12, -18)]
    return SolarDay(day, zone, start, end, *horizons)


@lru_cache(maxsize=512)
def lunar_day(day, latitude, longitude, zone):
    start, end = _validate(day, latitude, longitude, zone)
    function = lambda stamp: _altitude('moon', stamp, latitude, longitude)
    a, b = start.timestamp(), end.timestamp()
    return _horizon(_samples(function, a, b), function, 0, a, b, zone)


def duration_label(seconds):
    minutes = round(seconds / 60)
    return f'{minutes // 60} h {minutes % 60:02d} min'


def event_label(events, missing):
    return ' / '.join(clock_label(moment) for moment in events) if events else missing


def clock_label(moment):
    rounded = datetime.fromtimestamp(math.floor((moment.timestamp()+30)/60)*60, moment.tzinfo)
    return rounded.strftime('%H:%M') + (rounded.strftime(' (%d.%m.)') if rounded.date()!=moment.date() else '')

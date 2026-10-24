"""Seven real stars of Otava above Oulu, calculated locally without a network.

J2000 FK5 positions, visual magnitudes and proper motions are from Yale Bright
Star Catalogue, fifth edition (Hoffleit & Warren, CDS V/50), HR 4301, 4295,
4554, 4660, 4905, 5054 and 5191.  Catalogue and column definitions:
https://cdsarc.cds.unistra.fr/ftp/V/50/ReadMe

Bundled PyMeeus applies equatorial precession and proper motion.  Rotation uses
Greenwich *mean* sidereal time with UTC as the UT1 approximation.  Geometric
altitude/azimuth omit refraction, nutation and annual aberration; this is an
orientation illustration, not an instrument pointing or visibility prediction.

The compact image is a stereographic view centred on the north celestial pole,
with a fixed 50-degree field radius.  x is right/east when facing north; y is
screen-down, so the direction toward the zenith is up.  The pole stays at (0,0)
and the frame is never rotated, stretched or refitted to the current stars.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from functools import lru_cache
import math

from .astronomy import Epoch, check_day, julian_day
from pymeeus.Angle import Angle
from pymeeus.Coordinates import precession_equatorial

OULU_LATITUDE = 65.0121
OULU_LONGITUDE = 25.4651
FIELD_RADIUS = 50.0
PROJECTION_SCALE = math.tan(math.radians(FIELD_RADIUS / 2))


@dataclass(frozen=True)
class Star:
    name: str
    ra: float  # J2000 degrees
    dec: float  # J2000 degrees
    magnitude: float
    pm_ra: float = 0.0  # catalogue mu_alpha*cos(delta), arcseconds/year
    pm_dec: float = 0.0  # arcseconds/year


STARS = (
    Star('Dubhe', 165.93208333333334, 61.75083333333333, 1.79, -.119, -.067),
    Star('Merak', 165.4604166666667, 56.3825, 2.37, .082, .034),
    Star('Phecda', 178.4575, 53.69472222222222, 2.44, .095, .012),
    Star('Megrez', 183.85666666666668, 57.0325, 3.31, .104, .009),
    Star('Alioth', 193.50708333333336, 55.959722222222226, 1.77, .112, -.006),
    Star('Mizar', 200.98125, 54.92527777777777, 2.27, .122, -.020),
    Star('Alkaid', 206.885, 49.31333333333333, 1.86, -.122, -.011),
)
LINKS = ((0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (4, 5), (5, 6))


@dataclass(frozen=True)
class StarPosition:
    name: str
    altitude: float  # degrees above geometric horizon
    azimuth: float  # degrees clockwise from true north, east=90
    x: float  # normalized screen coordinates: fixed NCP centre, radius one=50deg
    y: float
    magnitude: float


@lru_cache(maxsize=512)
def _equatorial(day_ordinal):
    """Day-level precession is ample for a minute-of-arc sky illustration."""
    day = date.fromordinal(day_ordinal)
    target = Epoch(julian_day(datetime.combine(day, time(12), timezone.utc)))
    result = []
    for star in STARS:
        # BSC mu_alpha is projected motion; PyMeeus expects d(alpha)/dt.
        pm_ra = star.pm_ra / (3600 * math.cos(math.radians(star.dec)))
        ra, dec = precession_equatorial(
            Epoch(2451545.0), target, Angle(star.ra), Angle(star.dec),
            pm_ra, star.pm_dec / 3600)
        result.append((float(ra), float(dec)))
    return tuple(result)


def sky_at(moment):
    """Return Otava's seven geometric positions at an aware instant, 1900–2100.

    Oulu's fixed location is intentional: the user's weather location and the
    operating system's timezone do not move this symbolic sky calendar.
    """
    jd = julian_day(moment)  # Explicitly reject naive host-local timestamps.
    utc = moment.astimezone(timezone.utc)
    check_day(utc.date())
    sidereal = (Epoch(jd).mean_sidereal_time() * 360 + OULU_LONGITUDE) % 360
    latitude = math.radians(OULU_LATITUDE)
    result = []
    for star, (ra, dec) in zip(STARS, _equatorial(utc.date().toordinal())):
        hour = math.radians(sidereal - ra)
        declination = math.radians(dec)
        east = -math.cos(declination) * math.sin(hour)
        north = (math.sin(declination) * math.cos(latitude)
                 - math.cos(declination) * math.cos(hour) * math.sin(latitude))
        up = (math.sin(declination) * math.sin(latitude)
              + math.cos(declination) * math.cos(hour) * math.cos(latitude))
        altitude = math.degrees(math.asin(max(-1, min(1, up))))
        azimuth = math.degrees(math.atan2(east, north)) % 360
        denominator = (1 + math.sin(declination)) * PROJECTION_SCALE
        x = east / denominator
        y = -math.cos(declination) * math.cos(hour) / denominator
        result.append(StarPosition(star.name, altitude, azimuth, x, y, star.magnitude))
    return tuple(result)

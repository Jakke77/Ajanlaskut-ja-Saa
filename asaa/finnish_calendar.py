"""An explicitly modern interpretation of the linked Finnish folk calendar.

Katajala describes lunar months and Vaahtokuu after February, but gives no
intercalation algorithm. OUR rule: Joulukuu contains the winter solstice;
between consecutive such months there are 12 or 13 lunations. In a 13-month
year Vaahtokuu follows Helmikuu. A month begins on the Helsinki civil date of
the calculated astronomical new moon, rather than a first-crescent sighting.
This is not presented as a uniquely reconstructed historical calendar.
"""
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from zoneinfo import ZoneInfo

from .astronomy import Epoch, Moon, Sun, _from_tt, check_day
from .namedays import names_at

SOURCE = 'https://www.katajala.net/viikinkiaika/ajanlasku/suomalainen_kalenteri.html'
ZONE = ZoneInfo('Europe/Helsinki')
MONTHS = ('Tammikuu', 'Helmikuu', 'Vaahtokuu', 'Maaliskuu', 'Huhtikuu',
          'Toukokuu', 'Kesäkuu', 'Heinäkuu', 'Elokuu', 'Syyskuu', 'Lokakuu',
          'Marraskuu', 'Joulukuu')
# Original short summaries of the linked source, not reproduced page content.
DESCRIPTIONS = (
    'Talven keskus: tammi viittaa napaan tai akseliin.',
    'Suojasään jälkeen puiden oksille jäätyvät jäähelmet.',
    'Ylimääräinen kuukausi helmikuun ja maaliskuun välissä.',
    'Lumen alta näkyviin tuleva maa.',
    'Huhta ja kaskipuiden kaataminen.',
    'Kevään toukotyöt ja kylvö.',
    'Kesantopellon kyntö; vanha yhteys maataloustöihin.',
    'Heinänteko ja niitto.',
    'Elonkorjuu ja valmistuva sato.',
    'Syksyn alkaminen.',
    'Lokainen vuodenaika; myös lika- ja ruojakuu.',
    'Marras viittaa kuolemaan ja luonnon talvilepoon.',
    'Keskitalven juhla; myös talvikuu.',
)


@dataclass(frozen=True)
class FolkMonth:
    year: int
    month: int
    start: date
    end: date
    intercalary_year: bool

    @property
    def length(self):
        return (self.end - self.start).days


@dataclass(frozen=True)
class FolkDate:
    period: FolkMonth
    day: int

    @property
    def label(self):
        return f'{self.day}. {MONTHS[self.period.month]} · kierto {self.period.year}–{self.period.year+1}'

    @property
    def names(self):
        return names_at('finnish', self.period.month, self.day - 1)


@lru_cache(maxsize=256)
def _winter_new_moon(year):
    solstice = Sun.get_equinox_solstice(year, target='winter')
    candidates = [Moon.moon_phase(solstice + offset, 'new') for offset in (-32, -16, 0)]
    return max((epoch for epoch in candidates if float(epoch) <= float(solstice)), key=float)


@lru_cache(maxsize=256)
def year_months(year):
    start, end = _winter_new_moon(year), _winter_new_moon(year + 1)
    starts = [start]
    for n in range(1, 14):
        current = Moon.moon_phase(start + n * 29.53058886, 'new')
        if float(current) >= float(end) - 1e-7:
            break
        starts.append(current)
    if len(starts) not in (12, 13):
        raise ValueError('Kuuvuoden pituutta ei voitu laskea.')
    leap = len(starts) == 13
    indices = [12, 0, 1] + ([2] if leap else []) + list(range(3, 12))
    days = [_from_tt(epoch).astimezone(ZONE).date() for epoch in starts + [end]]
    months = tuple(FolkMonth(year, index, a, b, leap)
                   for index, a, b in zip(indices, days, days[1:]))
    if any(month.length not in (29, 30) for month in months):
        raise ValueError('Kuukauden pituutta ei voitu laskea.')
    return months


@lru_cache(maxsize=2048)
def convert(civil):
    check_day(civil)
    year = civil.year
    if civil < _from_tt(_winter_new_moon(year)).astimezone(ZONE).date():
        year -= 1
    for month in year_months(year):
        if month.start <= civil < month.end:
            return FolkDate(month, (civil - month.start).days + 1)
    raise ValueError('Päivää ei löytynyt kuuvuodesta.')

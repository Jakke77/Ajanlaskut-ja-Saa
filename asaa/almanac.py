"""Real, optional parallel dates; never change the fictional 510-day calendar.

Conversions use convertdate at civil noon, not local religious sunset boundaries.
The Islamic date is tabular, not an observed or Umm al-Qura calendar. Persian
equinox calculations are deliberately restricted to modern supported years.
"""
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
import sys

try:
    import convertdate
except ModuleNotFoundError as error:
    if error.name not in ('convertdate', 'pymeeus'): raise
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor'))
    import convertdate

from convertdate import islamic, hebrew, persian, julian, coptic, indian_civil

# The astronomical equinox is identical for every day in one Gregorian year.
# Memoize that expensive library function without altering its calculation.
persian.equinox_jd = lru_cache(maxsize=512)(persian.equinox_jd)

@dataclass(frozen=True)
class CalendarSpec:
    title: str
    kind: str
    module: object
    description: str

SPECS = {
    'islamic': CalendarSpec('Islamilainen · taulukollinen', 'Kuukalenteri', islamic,
                           'Laskennallinen hijri; ei havaittuun kuunsirppiin perustuva päiväys.'),
    'hebrew': CalendarSpec('Heprealainen', 'Kuu–aurinkokalenteri', hebrew,
                          'Kiinteä heprealainen kalenteri, mukaan lukien karkauskuukaudet.'),
    'persian': CalendarSpec('Persialainen · Solar Hijri', 'Aurinkokalenteri', persian,
                           'Kevätpäiväntasaukseen perustuva laskenta Teheranin meridiaanilla.'),
    'julian': CalendarSpec('Juliaaninen', 'Aurinkokalenteri', julian,
                          'Juliaaninen karkausvuosisääntö; ei kiinteää 13 päivän vähennystä.'),
    'indian': CalendarSpec('Intian kansallinen · Saka', 'Aurinkokalenteri', indian_civil,
                          'Intian kansallinen siviilikalenteri, ei hindulainen kuukalenteri.'),
    'coptic': CalendarSpec('Koptilainen', 'Aurinkokalenteri', coptic,
                          '12 kuukautta ja vuoden lyhyt 13. kuukausi.'),
}

@dataclass(frozen=True)
class ParallelDate:
    key: str
    year: int | None
    month: int | None
    day: int | None
    label: str
    available: bool = True

@lru_cache(maxsize=4096)
def convert(key, civil):
    spec = SPECS[key]
    if key == 'persian' and not 1900 <= civil.year <= 2100:
        return ParallelDate(key, None, None, None, 'Saatavilla vuosille 1900–2100', False)
    try:
        year, month, day = map(int, spec.module.from_gregorian(civil.year, civil.month, civil.day))
        if hasattr(spec.module, 'MONTHS'):
            month_name = spec.module.MONTHS[month-1]
            if key == 'hebrew' and month == 12 and hebrew.leap(year): month_name = 'Adar I'
            if key == 'hebrew' and month == 13: month_name = 'Adar II'
        else:
            month_name = ('tammikuu','helmikuu','maaliskuu','huhtikuu','toukokuu','kesäkuu',
                          'heinäkuu','elokuu','syyskuu','lokakuu','marraskuu','joulukuu')[month-1]
        return ParallelDate(key, year, month, day, f'{day}. {month_name} · vuosi {year}')
    except (ValueError, OverflowError):
        return ParallelDate(key, None, None, None, 'Päiväys ei ole saatavilla tällä alueella', False)

def visible(options, system):
    return options['calendar_extras_visible'] and (options['calendar_extras_scope'] == 'all' or system == 'star')

def lines(options, system, civil):
    if not visible(options, system): return []
    return [f'{SPECS[key].title} · {SPECS[key].kind}\n{convert(key, civil).label}' for key in options['calendar_extras']]

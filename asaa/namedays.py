"""Original fictional names, fixed in a versioned data file rather than random."""
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
import json
from pathlib import Path

from .models import shadow


@dataclass(frozen=True)
class NamePair:
    male: str
    female: str

    @property
    def label(self):
        return f'Mies: {self.male} · Nainen: {self.female}'


@lru_cache(maxsize=1)
def catalog():
    path = Path(__file__).resolve().parents[1] / 'assets/calendar-names.json'
    data = json.loads(path.read_text())
    if data['schema'] != 1:
        raise ValueError('Tuntematon nimikalenterin versio.')
    return {key: tuple(NamePair(*pair) for pair in pairs)
            for key, pairs in data['calendars'].items()}


def names_at(system, month, day):
    count = 17 if system == 'star' else 13
    if (system not in catalog() or type(month) is not int or type(day) is not int
            or not 0 <= month < count or not 0 <= day < 30):
        raise ValueError('Virheellinen nimikalenterin päivä.')
    return catalog()[system][month * 30 + day]


def cycle_position(system, civil, star_epoch=date(2026, 7, 1)):
    """Project a birthday into the fixed cycle, including dates before epoch.

    This is a name lookup only. The application's historical date conversion
    still starts at year one and calendar notes keep their original civil key.
    """
    if system not in ('shadow', 'star'):
        raise ValueError('Tuntematon nimikierto.')
    epoch = shadow.EPOCH if system == 'shadow' else star_epoch
    count = 390 if system == 'shadow' else 510
    offset = (civil.toordinal() - epoch.toordinal()) % count
    return divmod(offset, 30)


def names_for_day(system, civil, star_epoch=date(2026, 7, 1)):
    return names_at(system, *cycle_position(system, civil, star_epoch))

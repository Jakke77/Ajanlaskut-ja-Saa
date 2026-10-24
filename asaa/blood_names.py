"""Permanent, authored blood/life-science names for Veri Aika's 777 days.

The versioned list contains fictional male/female name pairs inspired by
circulation, blood components and living cells.  It is an application name
calendar, not an official name-day register.  Birthdays before the epoch use
the same repeating cycle without changing their civil dates or notes.
"""
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
import json
from pathlib import Path
from urllib.parse import urlsplit

from .blood_time import DAYS_PER_YEAR, EPOCH_DATE
from .namedays import NamePair

DATA_PATH = Path(__file__).resolve().parents[1] / 'assets/blood-names.json'
MEANINGS_PATH = DATA_PATH.with_name('blood-name-meanings.json')
INVENTED_LEGEND = '** tämän keksin :)'


@dataclass(frozen=True)
class NameSource:
    """A reference for the factual background, not proof of a name's origin."""
    title: str
    url: str


@dataclass(frozen=True)
class NameMeaning:
    """Permanent authored interpretation kept distinct from cited background."""
    name: str
    day_of_year: int
    gender: str
    meaning: str
    invented: bool
    background: str
    sources: tuple[NameSource, ...]

    @property
    def label(self):
        """Plain text: retain the user's literal marker, including in exports."""
        return self.meaning + (' **' if self.invented else '')


@lru_cache(maxsize=1)
def catalog():
    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or data.get('schema') != 1
            or data.get('calendar') != 'blood' or data.get('year_days') != DAYS_PER_YEAR
            or not isinstance(data.get('pairs'), list)
            or len(data['pairs']) != DAYS_PER_YEAR):
        raise ValueError('Veri Ajan nimiluettelo ei ole tuettua muotoa.')
    seen_male, seen_female = set(), set()
    pairs = []
    for entry in data['pairs']:
        if (not isinstance(entry, list) or len(entry) != 2
                or any(not isinstance(name, str) or not 2 <= len(name) <= 40
                       or not name.isalpha() or name != name.capitalize()
                       for name in entry)):
            raise ValueError('Veri Ajan nimiparissa on virhe.')
        male, female = entry
        if male in seen_male or female in seen_female:
            raise ValueError('Veri Ajan nimiluettelossa on toistuva nimi.')
        seen_male.add(male)
        seen_female.add(female)
        pairs.append(NamePair(male, female))
    return tuple(pairs)


def names_at(day_of_year):
    """Return the fixed pair for a one-based day in 1..777."""
    if type(day_of_year) is not int or not 1 <= day_of_year <= DAYS_PER_YEAR:
        raise ValueError('Veri Ajan vuoden päivän pitää olla 1–777.')
    return catalog()[day_of_year - 1]


def names_for_day(civil):
    """Project a selected civil birthday into the repeating name cycle."""
    if not isinstance(civil, date) or isinstance(civil, datetime):
        raise TypeError('Nimihaku tarvitsee päivämäärän.')
    return names_at((civil - EPOCH_DATE).days % DAYS_PER_YEAR + 1)


@lru_cache(maxsize=1)
def meanings():
    """Read the complete, versioned book without deriving origins from spelling.

    Sources document the separate word/science background.  ``invented`` says
    whether the name's personal meaning is an authored interpretation; a
    biological word appearing nearby never turns that interpretation into a
    historical etymology.  Existing names and their day assignments are fixed.
    """
    data = json.loads(MEANINGS_PATH.read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or data.get('schema') != 1
            or data.get('calendar') != 'blood'
            or data.get('year_days') != DAYS_PER_YEAR
            or data.get('legend') != INVENTED_LEGEND
            or not isinstance(data.get('sources'), dict)
            or not isinstance(data.get('families'), dict)
            or not isinstance(data.get('entries'), list)
            or len(data['entries']) != DAYS_PER_YEAR * 2):
        raise ValueError('Veri Ajan nimiselitykset eivät ole tuettua muotoa.')

    sources = {}
    for key, record in data['sources'].items():
        if (not isinstance(key, str) or not key
                or not isinstance(record, dict)
                or not _nonempty_text(record.get('title'))
                or not isinstance(record.get('url'), str)):
            raise ValueError('Veri Ajan nimiselityksen lähteessä on virhe.')
        url = urlsplit(record['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Veri Ajan nimiselityksen lähdeosoite ei ole kelvollinen.')
        sources[key] = NameSource(record['title'], record['url'])

    families = {}
    for key, record in data['families'].items():
        if (not isinstance(key, str) or not key
                or not isinstance(record, dict)
                or not _nonempty_text(record.get('background'))
                or not isinstance(record.get('source_ids'), list)
                or not record['source_ids']
                or any(not isinstance(source, str) or source not in sources
                       for source in record['source_ids'])):
            raise ValueError('Veri Ajan nimiselityksen sanataustassa on virhe.')
        families[key] = (record['background'],
                         tuple(sources[source] for source in record['source_ids']))

    expected = [(name, day, gender)
                for day, pair in enumerate(catalog(), 1)
                for name, gender in ((pair.male, 'male'), (pair.female, 'female'))]
    result = []
    for record, (name, day, gender) in zip(data['entries'], expected):
        if (not isinstance(record, dict)
                or record.get('name') != name
                or type(record.get('day_of_year')) is not int
                or record['day_of_year'] != day
                or record.get('gender') != gender
                or not isinstance(record.get('family'), str)
                or record.get('family') not in families
                or not _nonempty_text(record.get('meaning'))
                or '**' in record['meaning']
                or type(record.get('invented')) is not bool):
            raise ValueError('Veri Ajan nimiselitys ei vastaa pysyvää nimikalenteria.')
        background, references = families[record['family']]
        result.append(NameMeaning(name, day, gender, record['meaning'],
                                  record['invented'], background, references))
    return tuple(result)


def _nonempty_text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 4000


def meaning_for_name(name):
    """Look up an exact registered spelling; never guess a meaning by prefix."""
    if not isinstance(name, str):
        raise TypeError('Nimiselityksen haku tarvitsee nimen tekstinä.')
    try:
        return next(record for record in meanings() if record.name == name)
    except StopIteration:
        raise ValueError('Nimeä ei ole Veri Ajan nimikalenterissa.') from None


def meaning_pair_at(day_of_year):
    """Two interpretations for the same fixed, one-based calendar day."""
    names_at(day_of_year)
    offset = (day_of_year - 1) * 2
    return meanings()[offset:offset + 2]

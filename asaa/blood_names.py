"""Permanent, authored blood/life-science names for Veri Aika's 777 days.

The versioned list contains fictional male/female name pairs inspired by
circulation, blood components and living cells.  It is an application name
calendar, not an official name-day register.  Birthdays before the epoch use
the same repeating cycle without changing their civil dates or notes.
"""
from datetime import date, datetime
from functools import lru_cache
import json
from pathlib import Path

from .blood_time import DAYS_PER_YEAR, EPOCH_DATE
from .namedays import NamePair

DATA_PATH = Path(__file__).resolve().parents[1] / 'assets/blood-names.json'


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

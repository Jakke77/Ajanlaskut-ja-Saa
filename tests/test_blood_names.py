"""Permanent 777-day name registry: authored data, birth dates and year rollover."""
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from asaa import blood_names as names, blood_time as blood
from asaa.namedays import NamePair


class BloodNameTests(unittest.TestCase):
    def test_every_year_day_has_two_distinct_unique_readable_names(self):
        pairs = names.catalog()
        self.assertIsInstance(pairs, tuple)
        self.assertEqual(len(pairs), 777)
        male = {pair.male for pair in pairs}
        female = {pair.female for pair in pairs}
        self.assertEqual((len(male), len(female)), (777, 777))
        self.assertFalse(male & female)
        for pair in pairs:
            self.assertIsInstance(pair, NamePair)
            for name in (pair.male, pair.female):
                self.assertTrue(name.isalpha(), name)
                self.assertEqual(name, name.capitalize())
                self.assertGreaterEqual(len(name), 4)
                self.assertLessEqual(len(name), 14)

    def test_fixed_registry_anchors_preserve_authored_day_assignments(self):
        for day, expected in [(1, ('Rubino', 'Rubina')), (2, ('Hemero', 'Hemera')),
            (3, ('Sereno', 'Serena')), (4, ('Veno', 'Vena')),
            (5, ('Fibriano', 'Fibria')), (111, ('Systolis', 'Systolisa')),
            (222, ('Ydinel', 'Ydinela')), (333, ('Hemerevi', 'Hemerenia')),
            (444, ('Lymfis', 'Lymfisa')), (555, ('Globurio', 'Globuria')),
            (666, ('Valterio', 'Valteria')), (777, ('Oksan', 'Oksanna'))]:
            with self.subTest(day=day):
                self.assertEqual(names.names_at(day), NamePair(*expected))

    def test_every_pair_returns_on_the_same_day_of_each_authored_year(self):
        for offset in range(777):
            day = blood.EPOCH_DATE + timedelta(days=offset)
            expected = names.names_at(offset + 1)
            self.assertEqual(names.names_for_day(day), expected)
            for years in (1, 3):
                self.assertEqual(names.names_for_day(day + timedelta(days=777 * years)), expected)
            self.assertEqual(blood.from_date(day).names, expected)

    def test_birthdays_before_epoch_continue_the_cycle_without_changing_the_date(self):
        for birthday in (date(1900, 1, 1), date(1985, 2, 14), date(2000, 2, 29)):
            with self.subTest(birthday=birthday):
                original = birthday
                item = blood.from_date(birthday)
                self.assertIn('ennen Veri Ajan alkua', item.label)
                self.assertEqual(item.names, names.names_for_day(birthday))
                self.assertEqual(names.names_for_day(birthday),
                    names.names_for_day(birthday + timedelta(days=777)))
                self.assertEqual(item.civil, original)
        self.assertEqual(names.names_for_day(blood.EPOCH_DATE - timedelta(days=1)),
                         names.names_at(777))

    def test_lookup_accepts_civil_dates_and_rejects_ambiguous_day_numbers(self):
        for value in (0, -1, 778, True, 1.0, '1', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                names.names_at(value)
        for value in (datetime(2026, 6, 26), '2026-06-26', 1, None):
            with self.subTest(value=value), self.assertRaises(TypeError):
                names.names_for_day(value)

    def test_source_describes_the_calendar_and_scientific_name_inspirations(self):
        payload = json.loads(names.DATA_PATH.read_text(encoding='utf-8'))
        self.assertEqual((payload['schema'], payload['calendar'], payload['year_days']),
                         (1, 'blood', 777))
        self.assertIn('eivät virallisia nimipäiviä', payload['description'])
        self.assertEqual(len(payload['inspirations']), 37)
        self.assertTrue(all(record['stem'] and record['meaning']
                            for record in payload['inspirations']))

    def test_truncated_or_duplicate_registry_is_rejected_instead_of_reassigning_days(self):
        original = json.loads(names.DATA_PATH.read_text(encoding='utf-8'))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'names.json'
            for broken in ('truncated', 'duplicate'):
                payload = json.loads(json.dumps(original))
                if broken == 'truncated':
                    payload['pairs'].pop()
                else:
                    payload['pairs'][776] = payload['pairs'][0]
                path.write_text(json.dumps(payload), encoding='utf-8')
                names.catalog.cache_clear()
                try:
                    with patch.object(names, 'DATA_PATH', path), self.assertRaises(ValueError):
                        names.catalog()
                finally:
                    names.catalog.cache_clear()
        self.assertEqual(len(names.catalog()), 777)


if __name__ == '__main__':
    unittest.main()

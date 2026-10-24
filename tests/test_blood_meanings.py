"""A permanent namebook separates authored meanings from referenced facts."""
from dataclasses import FrozenInstanceError
from datetime import date
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from asaa import blood_names as names, blood_time


class BloodMeaningTests(unittest.TestCase):
    def test_book_covers_every_existing_name_once_in_its_original_day_order(self):
        expected = [(day, gender, name)
                    for day, pair in enumerate(names.catalog(), 1)
                    for gender, name in (('male', pair.male), ('female', pair.female))]
        records = names.meanings()
        self.assertIsInstance(records, tuple)
        self.assertEqual(len(records), 1554)
        self.assertEqual([(item.day_of_year, item.gender, item.name) for item in records], expected)
        self.assertEqual(len({item.name for item in records}), 1554)
        self.assertEqual(len({item.meaning for item in records}), 1554)
        # Name meanings must never silently reassign the previous release's names.
        self.assertEqual(hashlib.sha256(names.DATA_PATH.read_bytes()).hexdigest(),
                         '5c0ffe55edaf3a1848e9fbfd48fec6f135c8890bd521a695e9508d52554986bd')

    def test_authored_meanings_keep_the_exact_plain_text_marker(self):
        self.assertEqual(names.INVENTED_LEGEND, '** tämän keksin :)')
        for item in names.meanings():
            with self.subTest(name=item.name):
                self.assertTrue(item.invented)
                self.assertNotIn('**', item.meaning)
                self.assertEqual(item.label, item.meaning + ' **')
                self.assertGreater(len(item.meaning), 70)
                self.assertLess(len(item.meaning), 350)
                self.assertNotEqual(item.meaning, item.background)

    def test_anchored_interpretations_remain_personal_and_distinct(self):
        rubino = names.meaning_for_name('Rubino')
        rubina = names.meaning_for_name('Rubina')
        self.assertTrue(rubino.meaning.startswith('Rubiininpunaisen elinvoiman kantaja.'))
        self.assertTrue(rubina.meaning.startswith('Rubiininpunaisen elinvoiman vaalija.'))
        self.assertIn('verenvirran', names.meaning_for_name('Virrio').meaning)
        self.assertIn('elämänketjun', names.meaning_for_name('Tetrio').meaning)
        self.assertTrue(names.meaning_for_name('Fibriano').meaning.startswith(
            'Eheyttävän punaisen verkon kulkija.'))
        self.assertTrue(names.meaning_for_name('Fibria').meaning.startswith(
            'Eheyttävän punaisen verkon opastaja.'))

    def test_background_references_are_separate_and_immutable(self):
        source_urls = set()
        for item in names.meanings():
            self.assertIsInstance(item.sources, tuple)
            self.assertTrue(item.background)
            self.assertTrue(item.sources)
            self.assertIs(names.meaning_for_name(item.name), item)
            for source in item.sources:
                self.assertTrue(source.title)
                self.assertEqual(urlsplit(source.url).scheme, 'https')
                self.assertTrue(urlsplit(source.url).hostname)
                source_urls.add(source.url)
        self.assertEqual(len(source_urls), 18)
        item = names.meaning_for_name('Hemera')
        self.assertIn('ei näiden kokonaisten nimien todistettu historiallinen alkuperä',
                      item.background)
        self.assertIn('sovelluksen oma mielikuva', names.meaning_for_name('Serena').background)
        self.assertIn('mielikuvituksellisena yhteytenä',
                      names.meaning_for_name('Valterio').background)
        with self.assertRaises(FrozenInstanceError):
            item.meaning = 'muuttunut'
        with self.assertRaises(FrozenInstanceError):
            item.sources[0].url = 'https://example.com/'

    def test_calendar_pair_lookup_retains_date_cycle_and_genders(self):
        for day in (1, 2, 333, 666, 777):
            pair = names.names_at(day)
            first, second = names.meaning_pair_at(day)
            self.assertEqual((first.name, second.name), (pair.male, pair.female))
            self.assertEqual((first.day_of_year, second.day_of_year), (day, day))
            self.assertEqual((first.gender, second.gender), ('male', 'female'))
        birthday = date(1985, 2, 14)
        day = blood_time.from_date(birthday).day_of_year
        pair = names.names_for_day(birthday)
        self.assertEqual(tuple(item.name for item in names.meaning_pair_at(day)),
                         (pair.male, pair.female))

    def test_unknown_names_and_ambiguous_days_do_not_guess_an_explanation(self):
        for value in ('', 'rubino', 'Rubino ', 'Rubin', 'Tuntematon'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                names.meaning_for_name(value)
        for value in (None, 1, True, ['Rubino']):
            with self.subTest(value=value), self.assertRaises(TypeError):
                names.meaning_for_name(value)
        for value in (0, 778, -1, True, '1', 1.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                names.meaning_pair_at(value)

    def test_damaged_or_misattributed_book_is_rejected(self):
        original = json.loads(names.MEANINGS_PATH.read_text(encoding='utf-8'))
        mutations = {
            'missing entry': lambda data: data['entries'].pop(),
            'duplicate name': lambda data: data['entries'][1].update(name='Rubino'),
            'wrong day': lambda data: data['entries'][0].update(day_of_year=2),
            'wrong gender': lambda data: data['entries'][0].update(gender='female'),
            'missing background': lambda data: data['families']['Rubin'].update(background=''),
            'missing source': lambda data: data['families']['Rubin'].update(source_ids=[]),
            'unknown source': lambda data: data['families']['Rubin'].update(source_ids=['missing']),
            'unsafe source URL': lambda data: data['sources']['ruby'].update(url='javascript:alert(1)'),
            'missing marker truth value': lambda data: data['entries'][0].update(invented='yes'),
            'marker in meaning': lambda data: data['entries'][0].update(meaning='Punainen valo **'),
            'wrong legend': lambda data: data.update(legend='keksitty'),
            'invalid family': lambda data: data['entries'][0].update(family=[]),
        }
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'meanings.json'
            for title, mutate in mutations.items():
                with self.subTest(title=title):
                    payload = json.loads(json.dumps(original))
                    mutate(payload)
                    path.write_text(json.dumps(payload), encoding='utf-8')
                    names.meanings.cache_clear()
                    try:
                        with patch.object(names, 'MEANINGS_PATH', path), self.assertRaises(ValueError):
                            names.meanings()
                    finally:
                        names.meanings.cache_clear()
        self.assertEqual(len(names.meanings()), 1554)


if __name__ == '__main__':
    unittest.main()

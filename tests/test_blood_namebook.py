"""The portable name book keeps every fixed name and marks authored meanings."""
from contextlib import redirect_stdout
from dataclasses import dataclass
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from asaa import blood_namebook as book, blood_names


@dataclass(frozen=True)
class Source:
    title: str
    url: str


@dataclass(frozen=True)
class Meaning:
    name: str
    day_of_year: int
    gender: str
    meaning: str
    invented: bool
    background: str
    sources: tuple


def sample(**changes):
    values = dict(name='Rubino', day_of_year=1, gender='male',
                  meaning='Punaisen elämänkantaja.', invented=True,
                  background='Veren punaisen värin taustalla on hemoglobiini.',
                  sources=(Source('Blood and its components', 'https://example.test/blood'),))
    values.update(changes)
    return Meaning(**values)


class BookParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []
        self.names = []
        self.current_day = None
        self.heading = None
        self.count_inventions = 0
        self.sources = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'section' and attrs.get('class') == 'day':
            self.current_day = int(attrs['data-day'])
            self.days.append(self.current_day)
        if tag == 'h3':
            self.heading = [self.current_day, attrs['id'], '']
        if tag == 'span' and attrs.get('class') == 'invented':
            self.count_inventions += 1
        if tag == 'a':
            self.sources.append(attrs['href'])

    def handle_data(self, data):
        if self.heading is not None:
            self.heading[2] += data

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.names.append(tuple(self.heading))
            self.heading = None


class BloodNamebookTests(unittest.TestCase):
    def test_every_fixed_name_occurs_on_its_unchanged_calendar_day(self):
        rendered = book.render_html()
        parser = BookParser()
        parser.feed(rendered)
        expected = []
        for day, pair in enumerate(blood_names.catalog(), 1):
            expected.extend(((day, f'name-{day}-male', pair.male),
                             (day, f'name-{day}-female', pair.female)))
        self.assertEqual(parser.names, expected)
        self.assertEqual(parser.days, list(range(1, 778)))
        self.assertEqual(parser.count_inventions,
                         sum(item.invented for item in blood_names.meanings()))
        self.assertIn('Esimerkkipäivä 26.6.2026', rendered)
        self.assertIn('111. viikko · 7. päivä', rendered)
        self.assertIn('Esimerkkipäivä 10.8.2028', rendered)

    def test_invention_marker_is_literal_and_does_not_mark_factual_background(self):
        rendered = book.render_html((sample(), sample(name='Rubina', gender='female', invented=False)))
        parser = BookParser()
        parser.feed(rendered)
        self.assertEqual(parser.count_inventions, 1)
        self.assertIn('** tämän keksin :)', rendered)
        self.assertIn('Sanatausta ja vaikutteet', rendered)
        self.assertIn('Lähde kertoo sanataustasta; se ei vahvista keksittyä nimenselitystä.', rendered)
        self.assertIn('<dd>Veren punaisen värin taustalla on hemoglobiini.</dd>', rendered)
        self.assertEqual(parser.sources, ['https://example.test/blood'] * 2)

    def test_html_escapes_names_meanings_backgrounds_and_links(self):
        item = sample(name='Eve<script>alert(1)</script>', meaning='A & B <guardian>',
                      background='<img src=x onerror=alert(1)>',
                      sources=(Source('A <source> & B', 'https://example.test/?q="x"&p=<tag>'),))
        rendered = book.render_html((item,))
        self.assertNotIn('<script>alert(1)</script>', rendered)
        self.assertNotIn('<img src=x', rendered)
        self.assertIn('Eve&lt;script&gt;alert(1)&lt;/script&gt;', rendered)
        self.assertIn('A &amp; B &lt;guardian&gt;', rendered)
        self.assertIn('href="https://example.test/?q=&quot;x&quot;&amp;p=&lt;tag&gt;"', rendered)
        parser = BookParser()
        parser.feed(rendered)
        self.assertEqual(parser.names[0][2], item.name)

    def test_non_web_source_links_are_rejected(self):
        for url in ('javascript:alert(1)', 'file:///etc/passwd', '//example.test', 'https:missing-host'):
            with self.subTest(url=url):
                item = sample(sources=(Source('Invalid source', url),))
                with self.assertRaises(ValueError):
                    book.render_html((item,))
                with self.assertRaises(ValueError):
                    book.render_markdown((item,))

    def test_html_is_offline_searchable_accessible_and_printable_as_a_whole(self):
        rendered = book.render_html((sample(),))
        for unwanted in ('<script src=', '<link ', 'fetch(', 'XMLHttpRequest', 'eval(', 'document.write('):
            self.assertNotIn(unwanted, rendered)
        for expected in ('<html lang="fi">', '<meta charset="utf-8">', 'role="search"',
                         'aria-live="polite"', 'id="query"', 'id="day"', 'id="week"',
                         'entry.dataset.search.includes(word)', 'count.textContent', '@media print',
                         '.day[hidden],.entry[hidden] { display:block!important; }',
                         'window.print()', '--bg:white', 'Voit säilyttää tämän tiedoston'):
            self.assertIn(expected, rendered)

    def test_markdown_keeps_every_pair_and_literal_markers(self):
        rendered = book.render_markdown()
        for day, pair in enumerate(blood_names.catalog(), 1):
            self.assertIn(f'## Vuoden päivä {day}/777', rendered)
            self.assertIn(f'### {pair.male} · Miehen nimi', rendered)
            self.assertIn(f'### {pair.female} · Naisen nimi', rendered)
        self.assertIn('`**` tämän keksin :)', rendered)
        self.assertEqual(rendered.count('### '), 1554)
        self.assertEqual(rendered.count(' `**`'),
                         sum(item.invented for item in blood_names.meanings()))

    def test_cli_writes_utf8_only_to_requested_destinations(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            html = root / 'kirja' / 'nimet.html'
            markdown = root / 'nimet.md'
            with patch.object(blood_names, 'meanings', return_value=(sample(),), create=True), redirect_stdout(StringIO()):
                self.assertEqual(book.main(['--html', str(html), '--markdown', str(markdown)]), 0)
            self.assertIn('Punaisen elämänkantaja.', html.read_text(encoding='utf-8'))
            self.assertIn('Rubino', markdown.read_text(encoding='utf-8'))
            self.assertEqual({path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()},
                             {'kirja/nimet.html', 'nimet.md'})

    def test_cli_requires_distinct_output_paths(self):
        with redirect_stdout(StringIO()), patch('sys.stderr', new_callable=StringIO):
            with self.assertRaises(SystemExit):
                book.main([])
            with self.assertRaises(SystemExit):
                book.main(['--html', 'same.txt', '--markdown', 'same.txt'])


if __name__ == '__main__':
    unittest.main()

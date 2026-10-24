"""The name book exposes authored meanings, real source links and plain-text copies."""
import copy
from datetime import timedelta
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from asaa import blood_names, blood_time
from tests import test_veri_names_ui as fixture


class BloodMeaningsUiTests(unittest.TestCase):
    setUp = fixture.VeriNamesUiTests.setUp
    tearDown = fixture.VeriNamesUiTests.tearDown

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_selected_day_shows_both_meanings_and_opens_the_same_name_in_the_book(self):
        day = blood_time.EPOCH_DATE + timedelta(days=776)
        calendar = self.window.page_widgets['blood']
        calendar.set_day(day)
        pair = blood_names.names_at(777)
        for name in (pair.male, pair.female):
            entry = blood_names.meaning_for_name(name)
            self.assertIn(name, calendar.selected_meanings.text())
            self.assertIn(entry.label, calendar.selected_meanings.text())
        calendar.open_meaning_book()
        self.app.processEvents()
        book = self.window.page_widgets['names']
        self.assertTrue(self.window.navigation['names'].isChecked())
        self.assertEqual(book.tabs.currentIndex(), 2)
        self.assertEqual(book.meaning_name.text(), pair.male)
        self.assertEqual(book.meaning_list.currentItem().data(Qt.ItemDataRole.UserRole), pair.male)
        for name in (pair.male, pair.female):
            self.assertIn(blood_names.meaning_for_name(name).label, book.blood_meanings.text())

    def test_search_finds_names_and_meanings_without_changing_the_birthday_or_notes(self):
        book = self.window.page_widgets['names']
        before = copy.deepcopy(self.state.data)
        birthday = book.date.date()
        book.tabs.setCurrentIndex(2)
        self.assertEqual(book.meaning_list.count(), 1554)
        book.meaning_search.setText('hEmErA')
        self.app.processEvents()
        visible = [book.meaning_list.item(i).data(Qt.ItemDataRole.UserRole)
                   for i in range(book.meaning_list.count())]
        self.assertIn('Hemera', visible)
        self.assertLess(len(visible), 1554)
        meaning = blood_names.meaning_for_name('Rubino').meaning
        book.meaning_search.setText(meaning)
        self.app.processEvents()
        visible = [book.meaning_list.item(i).data(Qt.ItemDataRole.UserRole)
                   for i in range(book.meaning_list.count())]
        self.assertIn('Rubino', visible)
        book.meaning_search.setText('nimeä-ei-ole-tässä-kirjassa')
        self.assertEqual(book.meaning_list.count(), 0)
        self.assertEqual(book.meaning_name.text(), 'Nimeä ei löytynyt')
        self.assertFalse(book.meaning_copy.isEnabled())
        self.assertEqual(book.meaning_sources.toolTip(), '')
        self.assertEqual(book.date.date(), birthday)
        self.assertEqual(self.state.data, before)

    def test_copy_preserves_invented_marker_and_keeps_background_sources_separate(self):
        book = self.window.page_widgets['names']
        book.meaning_search.setText('Rubino')
        book.tabs.setCurrentIndex(2)
        entry = blood_names.meaning_for_name(book.meaning_name.text())
        self.assertEqual(book.meaning_text.textFormat(), Qt.TextFormat.PlainText)
        self.assertEqual(book.meaning_background.textFormat(), Qt.TextFormat.PlainText)
        self.assertIn(entry.label, book.meaning_text.text())
        self.assertIn('** tämän keksin :)', book.meaning_text.text())
        self.assertIn(entry.background, book.meaning_background.text())
        self.assertTrue(book.meaning_sources.textInteractionFlags() &
                        Qt.TextInteractionFlag.LinksAccessibleByKeyboard)
        for source in entry.sources:
            self.assertIn(source.title, book.meaning_sources.text())
            self.assertIn(source.url, book.meaning_sources.toolTip())
        book.meaning_copy.click()
        copied = QApplication.clipboard().text()
        self.assertIn(entry.name, copied)
        self.assertIn(entry.meaning, copied)
        self.assertIn('** tämän keksin :)', copied)
        self.assertIn('SANATAUSTA\n' + entry.background, copied)
        self.assertIn('SANATAUSTAN LÄHTEET', copied)
        for source in entry.sources:
            self.assertIn(source.url, copied)

    def test_all_name_tabs_fit_the_minimum_window_and_the_book_renders(self):
        self.window.resize(1020, 720)
        self.controller.open_page('names')
        book = self.window.page_widgets['names']
        for index in (0, 1, 2):
            book.tabs.setCurrentIndex(index)
            self.app.processEvents()
            scroll = self.window.pages.currentWidget()
            self.assertEqual(scroll.horizontalScrollBar().maximum(), 0,
                f'tab={index}, page={book.width()}, minimum={book.minimumSizeHint().width()}')
        self.assertFalse(book.grab().isNull())
        self.assertTrue(book.meaning_list.isVisible())
        self.assertEqual(book.tabs.tabText(0), 'Oma nimi')
        self.assertEqual(book.tabs.tabText(1), 'Suomalainen kuukalenteri')
        self.assertEqual(book.tabs.tabText(2), 'Veri Ajan nimikirja')

    def test_printable_book_button_opens_only_the_bundled_local_html(self):
        book = self.window.page_widgets['names']
        with patch('asaa.celestial_ui.QDesktopServices.openUrl', return_value=True) as opened:
            self.assertFalse(opened.called)
            book.meaning_print.click()
            opened.assert_called_once()
            url = opened.call_args.args[0]
            self.assertTrue(url.isLocalFile())
            expected = Path(__file__).resolve().parents[1]/'assets/namebooks/veri-ajan-nimikirja.html'
            self.assertEqual(Path(url.toLocalFile()), expected)


if __name__ == '__main__':
    unittest.main()

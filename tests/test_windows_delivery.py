"""Windows package artwork and explicit, read-only wallpaper selection."""
import importlib.util
from dataclasses import asdict
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent, QSize
from PyQt6.QtWidgets import QApplication, QProxyStyle, QStyle

from asaa.windows_ui import WindowsAppearancePage
from tests.layout_diagnostics import layout_diagnostics


ROOT = Path(__file__).resolve().parents[1]


class WindowsDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def test_package_contains_every_bundled_wallpaper_and_catalog(self):
        spec = importlib.util.spec_from_file_location('windows_builder', ROOT / 'packaging/build_windows.py')
        builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        files = {path.relative_to(ROOT).as_posix() for path in builder.source_files()}
        self.assertIn('assets/wallpapers/catalog.json', files)
        for path in (ROOT / 'assets/wallpapers').rglob('*.png'):
            self.assertIn(path.relative_to(ROOT).as_posix(), files)

    def test_package_includes_the_complete_veri_names_database(self):
        spec = importlib.util.spec_from_file_location('windows_names_builder', ROOT / 'packaging/build_windows.py')
        builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        sources = {path.relative_to(ROOT).as_posix(): path for path in builder.source_files()}
        database = sources['assets/blood-names.json']
        self.assertTrue(database.is_file())
        self.assertGreater(database.stat().st_size, 0)
        payload = json.loads(database.read_text(encoding='utf-8'))
        self.assertEqual(payload['year_days'], 777)
        self.assertEqual(len(payload['pairs']), 777)
        self.assertIn('asaa/blood_names.py', sources)
        self.assertIn('tests/test_blood_names.py', sources)

    def test_package_includes_all_meanings_and_current_offline_namebooks(self):
        from asaa import blood_names, blood_namebook

        spec = importlib.util.spec_from_file_location('windows_meanings_builder', ROOT / 'packaging/build_windows.py')
        builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        sources = {path.relative_to(ROOT).as_posix(): path for path in builder.source_files()}
        self.assertTrue(sources['assets/blood-name-meanings.json'].is_file())
        entries = blood_names.meanings()
        expected = {name for pair in blood_names.catalog() for name in (pair.male, pair.female)}
        self.assertEqual({entry.name for entry in entries}, expected)
        self.assertEqual(len(entries), 1554)
        html = sources['assets/namebooks/veri-ajan-nimikirja.html'].read_text(encoding='utf-8')
        markdown = sources['assets/namebooks/veri-ajan-nimikirja.md'].read_text(encoding='utf-8')
        self.assertEqual(html, blood_namebook.render_html())
        self.assertEqual(markdown, blood_namebook.render_markdown())
        for name in expected:
            self.assertIn(name, html)
            self.assertIn(name, markdown)
        self.assertIn('tämän keksin :)', html)
        self.assertNotIn('src="https://', html)
        for test in ('blood_meanings', 'blood_meanings_ui', 'blood_namebook', 'blood_calendar_ui'):
            self.assertIn(f'tests/test_{test}.py', sources)

    def test_calendar_grids_fit_with_wide_native_button_minimums(self):
        from asaa import blood_ui, blood_calendar_ui, celestial_ui
        from tests import test_veri_names_ui as fixture

        class WideNativeButtons(QProxyStyle):
            def sizeFromContents(self, kind, option, size, widget=None):
                result = super().sizeFromContents(kind, option, size, widget)
                if kind == QStyle.ContentsType.CT_PushButton:
                    long_tools = ('Oma nimesi ajanlaskuissa', 'Suomalainen kuukalenteri',
                                  'Kuu, valo ja aurinko')
                    minimum = 346 if widget and widget.text().startswith(long_tools) else 112
                    return QSize(max(minimum, result.width()), result.height())
                return result

        with patch.object(blood_ui, 'IS_WINDOWS', True, create=True), \
                patch.object(blood_calendar_ui, 'IS_WINDOWS', True, create=True), \
                patch.object(celestial_ui, 'IS_WINDOWS', True, create=True):
            case = fixture.VeriNamesUiTests('test_minimum_window_keeps_veri_calendar_within_the_viewport')
            case.app = self.app
            case.setUp()
            try:
                case.controller.configure({'theme': 'windows_light', 'wallpaper_follow_theme': False})
                self.app.setStyle(WideNativeButtons('Fusion'))
                case.window.resize(1020, 720)
                def assert_page_fits(page):
                    scroll = case.window.pages.currentWidget()
                    overflow = scroll.horizontalScrollBar().maximum()
                    self.assertEqual(overflow, 0, layout_diagnostics(page, scroll) if overflow else None)

                def assert_grid_text_fits(grid):
                    marked = grid.visible_days[0]
                    case.state.save_note(marked, 'Luettavuustestin kalenterimerkintä')
                    grid.render(); self.app.processEvents()
                    self.assertIn(len(grid.day_buttons), (7, 35))
                    self.assertEqual(len(grid.day_buttons), len(grid.visible_days))
                    for item, day in zip(grid.day_buttons, grid.visible_days):
                        lines = item.text().splitlines()
                        metrics = item.fontMetrics()
                        widths = [metrics.horizontalAdvance(line) for line in lines]
                        text_height = metrics.height() + (len(lines) - 1) * metrics.lineSpacing()
                        evidence = json.dumps(dict(text=item.text(), font=item.font().toString(),
                            widths=widths, text_height=text_height,
                            contents=[item.contentsRect().width(), item.contentsRect().height()],
                            size_hint=[item.sizeHint().width(), item.sizeHint().height()]), ensure_ascii=False)
                        self.assertGreaterEqual(item.contentsRect().width(), max(widths), evidence)
                        self.assertGreaterEqual(item.contentsRect().height(), text_height, evidence)
                        self.assertEqual(item.property('civil_date'), day)
                        number = blood_ui.blood_time.from_date(day).day_of_year
                        self.assertEqual(item.accessibleName(),
                            f'Vuoden päivä {number} · {day:%d.%m.%Y}'
                            + (' · kalenterimerkintä' if case.state.note(day) else ''))
                        self.assertEqual(item.accessibleDescription(), item.toolTip())

                case.controller.open_page('blood'); self.app.processEvents()
                page = case.window.page_widgets['blood']
                assert_page_fits(page)
                assert_grid_text_fits(page.calendar_grid)
                case.controller.open_page('names'); self.app.processEvents()
                page = case.window.page_widgets['names']
                for index in range(page.tabs.count()):
                    page.tabs.setCurrentIndex(index); self.app.processEvents()
                    assert_page_fits(page)
                case.controller.open_calendar('blood', case.now.date()); self.app.processEvents()
                self.assertTrue(case.window.navigation['calendar'].isChecked())
                page = case.window.page_widgets['calendar']
                self.assertEqual(page.selector.currentData(), 'blood')
                assert_page_fits(page)
                assert_grid_text_fits(page.blood_calendar)
                for width in (1560, 1400, 1350, 1300, 1200, 1100, 1020):
                    case.window.resize(width, 720); self.app.processEvents()
                    assert_page_fits(page)
                    assert_grid_text_fits(page.blood_calendar)
            finally:
                case.tearDown(); self.app.setStyle('Fusion')

    def test_wallpaper_selection_opens_only_the_selected_local_image(self):
        controller = SimpleNamespace(state=SimpleNamespace(path=ROOT / 'state-not-written.json'))
        with patch('asaa.windows_ui.QDesktopServices.openUrl', return_value=True) as opened:
            page = WindowsAppearancePage(controller)
            try:
                self.assertTrue(page.wallpapers)
                self.assertEqual(page.wallpapers[page.wallpaper.currentIndex()].theme, 'blood')
                self.assertIsNotNone(page.preview.pixmap())
                self.assertFalse(page.preview.pixmap().isNull())
                self.assertFalse(opened.called)
                index = len(page.wallpapers) - 1
                page.wallpaper.setCurrentIndex(index)
                self.assertFalse(opened.called)
                self.assertTrue(page.open_wallpaper())
                url = opened.call_args.args[0]
                self.assertTrue(url.isLocalFile())
                self.assertEqual(Path(url.toLocalFile()), page.wallpapers[index].path)
            finally:
                page.close(); page.deleteLater()
                self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_veriyo_is_available_in_windows_pickers_and_persists(self):
        from tempfile import TemporaryDirectory
        from asaa import theme
        from asaa.platform_support import WINDOWS_THEMES
        from asaa.state import State
        from asaa.widget_themes import widget_theme_choices
        with patch.object(theme, 'IS_WINDOWS', True):
            self.assertEqual(set(theme.available_themes()), {*WINDOWS_THEMES, 'blood'})
            self.assertIn('blood', {key for _, key in widget_theme_choices('combined')})
            with TemporaryDirectory() as folder:
                state = State(Path(folder) / 'state.json')
                state.configure({'theme': 'blood', 'time_theme': 'blood',
                                 'widget_themes': {'blood': 'blood', 'combined': 'blood'},
                                 'clock_displays': {'blood': {'mode': 'otava_both'}}})
                self.assertEqual(State(state.path).settings, state.settings)

    def test_high_contrast_overrides_then_restores_veriyo_without_changing_selection(self):
        from asaa import theme, windows_appearance
        from asaa.widget_themes import widget_theme
        colors = dict(background='#000000', surface='#000000', border='#ffffff',
                      accent='#ffff00', text='#ffffff', muted='#ffffff', motif='windows')
        with patch.object(theme, 'IS_WINDOWS', True), \
                patch.object(windows_appearance, 'windows_colors', return_value=colors), \
                patch.object(windows_appearance, 'high_contrast', return_value=True):
            try:
                self.assertTrue(theme.refresh_windows_themes())
                self.assertEqual(asdict(theme.THEMES['blood']), colors)
                self.assertEqual(theme.CALENDAR_THEMES['blood'], theme.THEMES['blood'])
            finally:
                with patch.object(windows_appearance, 'high_contrast', return_value=False):
                    theme.refresh_windows_themes()
        self.assertEqual(theme.THEMES['blood'], theme.BLOOD_THEME)
        self.assertEqual(theme.CALENDAR_THEMES['blood'], theme.BLOOD_THEME)
        theme.refresh_windows_themes()


if __name__ == '__main__': unittest.main()

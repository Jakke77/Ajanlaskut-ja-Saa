"""Windows package artwork and explicit, read-only wallpaper selection."""
import importlib.util
from dataclasses import asdict
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication

from asaa.windows_ui import WindowsAppearancePage


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

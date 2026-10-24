"""Windows package artwork and explicit, read-only wallpaper selection."""
import importlib.util
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


if __name__ == '__main__': unittest.main()

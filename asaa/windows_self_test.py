"""Offline Windows acceptance checks in temporary storage, without OS writes."""
from contextlib import ExitStack
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication


def run_tests(app, preview_dir=None):
    from .app import Controller, request_existing
    from .state import State, DEFAULTS
    from . import platform_support, ui, theme
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'tests.test_windows_support', 'tests.test_weather_network',
        'tests.test_forecast', 'tests.test_providers', 'tests.test_display_geometry',
        'tests.test_windows_delivery', 'tests.test_blood_time', 'tests.test_otava',
        'tests.test_blood_ui', 'tests.test_otava_clock'])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): return 1
    # The same acceptance route also runs on Linux CI with Windows UI selection.
    # Native Windows APIs remain enabled only on an actual Windows runtime.
    with TemporaryDirectory(prefix='ajanlaskut-windows-') as directory, ExitStack() as stack:
        import asaa.app as app_module
        for module in (app_module, ui, theme): stack.enter_context(patch.object(module, 'IS_WINDOWS', True))
        stack.enter_context(patch.dict(DEFAULTS, theme='windows_system', font='Segoe UI', wallpaper_follow_theme=False))
        state = State(Path(directory) / 'state.json')
        controller = Controller(app, state, network=False)
        try:
            controller.restore_widgets(); controller.listen(); controller.window.show(); app.processEvents()
            settings = controller.window.page_widgets['settings']
            assert {settings.theme.itemData(i) for i in range(settings.theme.count())} == {*platform_support.WINDOWS_THEMES, 'blood'}
            for selected in platform_support.WINDOWS_THEMES:
                controller.configure({'theme': selected}); app.processEvents()
                assert controller.weather.paint_palette == theme.THEMES[selected]
                assert all(widget.theme == theme.THEMES[selected]
                           for key, widget in controller.widgets.items() if key != 'weather')
                for page in controller.window.page_widgets:
                    controller.open_page(page); app.processEvents()
                if preview_dir:
                    target = Path(preview_dir); target.mkdir(parents=True, exist_ok=True)
                    settings.load()
                    controller.open_page('settings'); app.processEvents()
                    assert controller.window.grab().save(str(target / (selected + '.png')))
            controller.configure({'theme': 'windows_system'})
            from . import windows_appearance
            before = state.path.read_bytes()
            with patch.object(windows_appearance, 'high_contrast', return_value=False), \
                    patch.object(windows_appearance, 'apps_are_dark', return_value=True):
                controller.appearance_watcher.refresh(); app.processEvents()
                assert controller.weather.paint_palette.background == '#202020'
                assert state.path.read_bytes() == before
            day = date(2026, 10, 24)
            state.save_note(day, 'Windows-testin merkintä')
            assert State(state.path).note(day) == 'Windows-testin merkintä'
            assert request_existing(state.path, 'settings')
            # Pump the IPC callback and the theme watcher without a second QApplication.
            from PyQt6.QtTest import QTest
            QTest.qWait(100)
            assert controller.window.navigation['settings'].isChecked()
            settings.load(); settings.all_widgets_theme.setChecked(True); settings.save(); app.processEvents()
            assert not settings.status.text().startswith('Virhe')
            assert not (state.path.parent / 'wallpaper-previous.json').exists()
            assert not (state.path.parent / 'icon-theme-previous.json').exists()
            print('PASS: Windows themes, all views, widgets, notes, IPC; no desktop or time-service writes')
        finally:
            controller.shutdown(); controller.window.close(); controller.window.deleteLater()
            for widget in controller.widgets.values(): widget.hide(); widget.deleteLater()
            controller.deleteLater(); app.sendPostedEvents(None, QEvent.Type.DeferredDelete); app.processEvents()
    return 0

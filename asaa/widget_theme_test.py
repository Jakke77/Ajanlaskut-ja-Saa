"""Independent widget palettes exercised through the real settings pages."""
import copy
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from .clock_config import PROFILE_KEYS
from .state import State
from .theme import THEMES, apply_theme
from .widgets import WIDGET_LABELS


def acceptance(controller, app, preview_dir=None):
    before = copy.deepcopy(controller.state.data)
    backend = controller.wallpapers.backend
    backgrounds = copy.deepcopy(backend.values)
    calls = len(backend.calls)
    page = controller.window.page_widgets['widgets']
    clocks = controller.window.page_widgets['clocks']
    settings = controller.window.page_widgets['settings']
    weather = controller.weather
    weather_before = (weather.selected, weather.size(), weather.pos(), weather.timer.interval(),
                      weather._last_fetch, weather.forecast, controller.daily.timer.interval())
    deadline = controller.time_rotation.deadline
    try:
        assert set(page.themes) == set(WIDGET_LABELS)
        page.themes['combined'].setCurrentIndex(page.themes['combined'].findData('ubuntu'))
        page.themes['weather'].setCurrentIndex(page.themes['weather'].findData('frost'))
        app.processEvents()
        assert controller.state.data == before, 'A draft must not change saved or live themes.'
        with patch.object(weather, 'apply_options') as apply_options, \
             patch.object(weather, 'refresh') as refresh, patch.object(weather, 'load_windy') as load_windy:
            page.save();app.processEvents()
            assert not apply_options.called and not refresh.called and not load_windy.called
        assert controller.widgets['combined'].theme == THEMES['ubuntu']
        assert controller.widgets['combined'].analog_clock
        assert weather.paint_palette == THEMES['frost']
        assert (weather.selected, weather.size(), weather.pos(), weather.timer.interval(),
                weather._last_fetch, weather.forecast, controller.daily.timer.interval()) == weather_before
        assert controller.time_rotation.deadline == deadline
        assert backend.values == backgrounds and len(backend.calls) == calls
        for key in ('notes', 'reminders', 'geometry', 'widget_sizes'):
            assert controller.state.data.get(key) == before.get(key)

        # A global change reaches only followers. Explicit palettes remain pinned.
        controller.configure({'theme': 'ubuntu'});app.processEvents()
        assert weather.paint_palette == THEMES['frost']
        for key in WIDGET_LABELS:
            if key != 'weather':assert controller.widgets[key].theme == THEMES['ubuntu']

        # Another page's save cannot replace unrelated themes or content drafts.
        page.themes['daily'].setCurrentIndex(page.themes['daily'].findData('copper'))
        overrides = controller.options['widget_themes'];overrides['star_calendar'] = 'frost'
        controller.configure({'widget_themes': overrides});page.save();app.processEvents()
        assert controller.options['widget_themes']['star_calendar'] == 'frost'
        assert controller.widgets['daily'].theme == THEMES['copper']
        clocks.load()
        clocks.target.setCurrentIndex(clocks.target.findData('star'))
        clocks.theme.setCurrentIndex(clocks.theme.findData('frost'))
        clocks.target.setCurrentIndex(clocks.target.findData('civil'))
        clocks.theme.setCurrentIndex(clocks.theme.findData('calendar'))
        clocks.fields['note'].setChecked(not clocks.fields['note'].isChecked())
        civil_note = clocks.fields['note'].isChecked()
        profiles = controller.options['clock_profiles']
        profiles['combined']['note'] = not profiles['combined']['note']
        controller.configure({'clock_profiles': profiles})
        calendars = controller.calendars
        with patch.object(weather, 'apply_shared_options') as shared_options, \
             patch.object(weather, 'refresh') as refresh, patch.object(weather, 'load_windy') as load_windy, \
             patch.object(controller.daily.timer, 'start') as daily_start:
            clocks.save();app.processEvents()
            assert not any(item.called for item in (shared_options, refresh, load_windy, daily_start))
        assert controller.calendars is calendars
        assert controller.options['clock_profiles']['civil']['note'] == civil_note
        assert controller.options['clock_profiles']['combined']['note'] == profiles['combined']['note']
        assert controller.options['widget_themes']['star'] == 'frost'
        assert controller.options['widget_themes']['civil'] == 'calendar'
        assert controller.options['widget_themes']['weather'] == 'frost'
        assert controller.options['time_theme'] == before['settings']['time_theme']
        assert controller.widgets['star'].theme == THEMES['frost']
        assert not controller.widgets['civil'].analog_clock
        assert State(controller.state.path).settings['widget_themes'] == controller.options['widget_themes']

        # A failed save leaves the active palette and the on-disk data unchanged.
        saved = copy.deepcopy(controller.state.data);disk = controller.state.path.read_bytes()
        palette = weather.paint_palette
        page.themes['weather'].setCurrentIndex(page.themes['weather'].findData('copper'))
        with patch('asaa.state.atomic_json', side_effect=OSError('Testin tallennusvirhe')):
            page.save();app.processEvents()
        assert controller.state.data == saved and controller.state.path.read_bytes() == disk
        assert weather.paint_palette == palette

        # Explicitly apply one theme to every widget from Settings.
        settings.load();settings.all_widgets_theme.setChecked(True)
        settings.theme.setCurrentIndex(settings.theme.findData('ubuntu'))
        with patch.object(weather, 'apply_options') as apply_options, \
             patch.object(weather, 'refresh') as refresh, patch.object(weather, 'load_windy') as load_windy, \
             patch.object(controller.daily.timer, 'start') as daily_start:
            settings.save();app.processEvents()
            assert not any(item.called for item in (apply_options, refresh, load_windy, daily_start))
        assert controller.options['widget_themes'] == {} and controller.options['time_theme'] == 'shared'
        assert not settings.all_widgets_theme.isChecked()
        assert weather.paint_palette == THEMES['ubuntu']
        for key in WIDGET_LABELS:
            assert (weather.paint_palette if key == 'weather' else controller.widgets[key].theme) == THEMES['ubuntu']
        assert all(controller.widgets[key].analog_clock for key in PROFILE_KEYS)
        print('PASS: all 8 independent widget themes, shared followers, cross-page drafts, save failures and apply-to-all')
        print('PASS: weather palette change preserves forecast/provider, timers, geometry and rotation without network or Windy reload')

        if preview_dir:
            target = Path(preview_dir);target.mkdir(parents=True, exist_ok=True)
            page.edited_themes.clear()
            controller.configure({'widget_themes': {'weather': 'frost', 'shadow_calendar': 'copper'}})
            controller.open_page('widgets');app.processEvents()
            controller.window.footer.setText('TEEMAVALINTOJEN ESIKATSELU · esimerkkisää, ei oikea ennuste')
            assert controller.window.grab().save(str(target/'widget-themes.png'))
            combined = controller.widgets['combined'];combined.grab()
            hero = QImage(1920, 1080, QImage.Format.Format_RGB32);hero.fill(QColor('#17121f'))
            painter = QPainter(hero);painter.setPen(QColor('#fff4ed'))
            font = QFont('DejaVu Sans');font.setPixelSize(28);painter.setFont(font)
            painter.drawText(46, 60, 'OMAT TEEMAT · UBUNTU-KELLO, HALLA-SÄÄ JA KUPARI-KALENTERI')
            painter.drawPixmap(60, 108, combined.grab())
            painter.drawPixmap(520, 108, weather.grab())
            painter.drawPixmap(1310, 108, controller.widgets['shadow_calendar'].grab())
            font.setPixelSize(16);painter.setFont(font);painter.setPen(QColor('#c6aebd'))
            painter.drawText(46, 1035, 'Sovelluksen Qt-esikatselu · esimerkkisää, ei oikea ennuste')
            painter.end();assert hero.save(str(target/'widget-theme-desktop.png'))
    finally:
        backend.values = backgrounds
        controller.state.commit(before)
        controller.time_rotation.configure(controller.options)
        apply_theme(app,controller.options);weather.apply_shared_options()
        page.edited_themes.clear();clocks.load();settings.load()
        controller.settings_changed.emit();controller.restore_widgets();app.processEvents()

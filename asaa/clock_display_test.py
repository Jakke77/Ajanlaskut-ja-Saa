"""Exercise saved clock display and digit sizes through their actual Qt controls."""
import copy
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtGui import QColor, QFont, QImage, QPainter

from .clock_config import PROFILE_KEYS, SYSTEMS
from .state import State
from .theme import THEMES, apply_theme


def acceptance(controller, app, preview_dir=None):
    before = copy.deepcopy(controller.state.data)
    backend = controller.wallpapers.backend
    backgrounds = copy.deepcopy(backend.values)
    wallpaper_calls = len(backend.calls)
    page = controller.window.page_widgets['clocks']
    widget = controller.widgets['combined']
    system_override = widget.system_override
    footer = controller.window.footer.text()
    running = controller.tick_timer.isActive()
    controller.tick_timer.stop()
    demo = datetime(2026, 10, 11, 10, 10, 30, tzinfo=controller.calendars.zone)

    def draw(seconds=True):
        with patch.object(controller.calendars, 'now', return_value=demo):
            app.processEvents()
            image = widget.grab()
        value = demo.strftime('%H:%M:%S' if seconds else '%H:%M')
        return image, [row for row in widget.text_layout if row[0] == value]

    def quiet_save():
        calendars = controller.calendars
        with ExitStack() as stack:
            calls = [stack.enter_context(patch.object(obj, name)) for obj, name in (
                (controller.weather, 'apply_shared_options'),
                (controller.weather, 'refresh'), (controller.weather, 'load_windy'),
                (controller.daily.timer, 'start'))]
            page.save();app.processEvents()
            assert not any(call.called for call in calls)
        assert controller.calendars is calendars

    try:
        # Each clock's own settings button selects that clock without changing saved options.
        for key in PROFILE_KEYS:
            cog = next(button for button in controller.widgets[key].buttons if button.text() == '⚙')
            cog.click();app.processEvents()
            assert page.target.currentData() == key and page.editing == key
            assert controller.state.data == before
        next(button for button in widget.buttons if button.text() == '⚙').click()
        assert page.target.currentData() == 'combined' and page.editing == 'combined'

        # An absent display preference retains both Ubuntu's dial and other themes' digits.
        controller.configure({'clock_displays': {}})
        for theme in ('copper', 'frost', 'ubuntu'):
            controller.configure({'widget_themes': {'combined': theme}})
            _, digits = draw(controller.options['seconds'])
            assert digits and widget.digital_clock
            assert widget.analog_clock == (theme == 'ubuntu')
            for mode in ('digital', 'analog', 'both'):
                controller.configure({'clock_displays': {'combined': {'mode': mode}}})
                _, digits = draw(controller.options['seconds'])
                assert widget.theme == THEMES[theme]
                assert bool(digits) == (mode != 'analog')
                assert widget.analog_clock == (mode != 'digital')
            controller.configure({'clock_displays': {}})

        # The display and digit-size drafts affect only the preview until Save.
        controller.configure({'widget_themes': {'combined': 'copper'}, 'clock_displays': {}})
        page.target.setCurrentIndex(page.target.findData('combined'));page.load()
        saved = copy.deepcopy(controller.state.data)
        deadline = controller.time_rotation.deadline
        other_clocks = {key: (item.theme, item.clock_mode, item.size(), item.pos())
                        for key, item in controller.widgets.items()
                        if key in PROFILE_KEYS and key != 'combined'}
        weather = controller.weather
        weather_before = (weather.selected, weather.forecast, weather._last_fetch,
                          weather.size(), weather.pos(), weather.paint_palette,
                          weather.timer.interval(), controller.daily.timer.interval())
        cache_directory = controller.state.path.parent / 'weather-cache'
        cache_before = {path.relative_to(cache_directory): path.read_bytes()
                        for path in cache_directory.rglob('*') if path.is_file()}
        page.display_mode.setCurrentIndex(page.display_mode.findData('analog'))
        page.shared_digit_scale.setChecked(False);page.digit_scale.setValue(80)
        app.processEvents()
        assert controller.state.data == saved and widget.clock_mode == 'digital'
        assert page.preview_widget.clock_mode == 'analog'
        assert not page.preview_label.pixmap().isNull()
        quiet_save()
        assert widget.clock_mode == 'analog'
        assert State(controller.state.path).settings['clock_displays']['combined'] == {
            'mode': 'analog', 'digit_scale': 80}
        assert controller.time_rotation.deadline == deadline
        assert weather_before == (weather.selected, weather.forecast, weather._last_fetch,
                                  weather.size(), weather.pos(), weather.paint_palette,
                                  weather.timer.interval(), controller.daily.timer.interval())
        assert cache_before == {path.relative_to(cache_directory): path.read_bytes()
                                for path in cache_directory.rglob('*') if path.is_file()}
        assert backend.values == backgrounds and len(backend.calls) == wallpaper_calls
        for key in ('notes', 'reminders', 'geometry', 'widget_sizes'):
            assert controller.state.data.get(key) == saved.get(key)
        assert other_clocks == {key: (item.theme, item.clock_mode, item.size(), item.pos())
                                for key, item in controller.widgets.items()
                                if key in PROFILE_KEYS and key != 'combined'}

        # Concurrent saves merge edited fields, including another field on the same clock.
        page.display_mode.setCurrentIndex(page.display_mode.findData('both'))
        displays = controller.options['clock_displays']
        displays['combined']['digit_scale'] = 140
        displays['civil'] = {'mode': 'analog', 'digit_scale': 120}
        profiles = controller.options['clock_profiles']
        profiles['combined']['note'] = not profiles['combined']['note']
        controller.configure({'clock_displays': displays, 'clock_profiles': profiles})
        quiet_save()
        assert controller.options['clock_displays']['combined'] == {'mode': 'both', 'digit_scale': 140}
        assert controller.options['clock_displays']['civil'] == displays['civil']
        assert controller.options['clock_profiles']['combined']['note'] == profiles['combined']['note']
        page.digit_scale.setValue(80)
        page.fields['note'].setChecked(not page.fields['note'].isChecked())
        note = page.fields['note'].isChecked()
        displays = controller.options['clock_displays'];displays['combined']['mode'] = 'digital'
        controller.configure({'clock_displays': displays});quiet_save()
        assert controller.options['clock_displays']['combined'] == {'mode': 'digital', 'digit_scale': 80}
        assert controller.options['clock_profiles']['combined']['note'] == note

        # A write failure must retain the active renderer, file, and draft for retry.
        saved = copy.deepcopy(controller.state.data);disk = controller.state.path.read_bytes()
        page.display_mode.setCurrentIndex(page.display_mode.findData('analog'))
        with patch('asaa.state.atomic_json', side_effect=OSError('Testin tallennusvirhe')):
            page.save();app.processEvents()
        assert controller.state.data == saved and controller.state.path.read_bytes() == disk
        assert widget.clock_mode == 'digital' and page.display_mode.currentData() == 'analog'
        quiet_save();assert widget.clock_mode == 'analog'

        # Digital font sizes grow in the rendered output, also inside the analogue dial.
        controller.configure({'font': 'DejaVu Sans', 'seconds': True})
        for mode in ('digital', 'both'):
            sizes = []
            for scale in (80, 140):
                controller.configure({'clock_displays': {'combined': {'mode': mode, 'digit_scale': scale}}})
                _, digits = draw()
                assert len(digits) == 1
                sizes.append(digits[0][2])
            assert sizes[1] > sizes[0], (mode, sizes)
        page.load();page.shared_digit_scale.setChecked(True);quiet_save()
        assert 'digit_scale' not in controller.options['clock_displays']['combined']
        sizes = []
        for scale in (80, 140):
            controller.configure({'widget_clock_scale': scale});_, digits = draw()
            sizes.append(digits[0][2])
        assert sizes[1] > sizes[0], sizes

        # Every mode remains readable with all content, calendars, seconds and supported fonts.
        profiles = controller.options['clock_profiles']
        profiles['combined'] = {field: True for field in profiles['combined']}
        controller.configure({'clock_profiles': profiles, 'widget_text_scale': 160,
                              'widget_clock_scale': 140, 'opacity': 0})
        for font in ('Ubuntu', 'DejaVu Sans', 'DejaVu Sans Mono'):
            controller.configure({'font': font})
            for mode in ('digital', 'analog', 'both'):
                controller.configure({'clock_displays': {'combined': {'mode': mode, 'digit_scale': 140}}})
                size = widget.size()
                for seconds in (False, True):
                    controller.configure({'seconds': seconds})
                    for system in SYSTEMS:
                        widget.system_override = system
                        image, digits = draw(seconds)
                        assert widget.size() == size and image.toImage().pixelColor(0, 0).alpha() == 0
                        assert bool(digits) == (mode != 'analog')
                        for _, rect, _, ink_height, ink_width in widget.text_layout:
                            assert ink_height <= rect.height()+.1 and ink_width <= rect.width()+1
                            assert rect.left() >= 0 and rect.right() <= widget.logical_width+.1
                            assert rect.top() >= 0 and rect.bottom() <= widget.logical_height+.1
                        for i, (_, rect, *_) in enumerate(widget.text_layout):
                            assert not any(rect.intersects(other[1]) for other in widget.text_layout[i+1:])
        widget.system_override = system_override
        print('PASS: clock display/digit drafts, persistence, field merges, failed writes and unrelated weather/wallpaper preservation')
        print('PASS: digital, analogue and both modes in each palette; actual digit sizing, inheritance, font/calendar/seconds bounds')

        if preview_dir:
            target = Path(preview_dir);target.mkdir(parents=True, exist_ok=True)
            profiles = controller.options['clock_profiles']
            profiles['combined'] = {field: field in ('clock', 'date', 'weekday', 'civil_date')
                                    for field in profiles['combined']}
            controller.configure({'clock_profiles': profiles, 'widget_themes': {'combined': 'ubuntu'},
                                  'font': 'Ubuntu', 'opacity': 100, 'scale': 100,
                                  'widget_text_scale': 130, 'widget_clock_scale': 100, 'seconds': True})
            widget.system_override = 'civil'
            hero = QImage(1920, 1080, QImage.Format.Format_RGB32);hero.fill(QColor('#17121f'))
            painter = QPainter(hero);painter.setPen(QColor('#fff4ed'))
            font = QFont('DejaVu Sans');font.setPixelSize(32);painter.setFont(font)
            painter.drawText(65, 70, 'OMA KELLO · KOLME NÄYTTÖTAPAA')
            font.setPixelSize(23);painter.setFont(font)
            for x, mode, title in ((80, 'digital', 'Digitaalinen'), (690, 'analog', 'Analoginen'),
                                   (1300, 'both', 'Analoginen ja digitaalinen')):
                controller.configure({'clock_displays': {'combined': {'mode': mode, 'digit_scale': 120}}})
                image, _ = draw();painter.drawText(x, 132, title);painter.drawPixmap(x, 163, image)
            font.setPixelSize(17);painter.setFont(font);painter.setPen(QColor('#c6aebd'))
            painter.drawText(65, 1027, 'Sovelluksen Qt-esikatselu · esimerkkiaika 11.10.2026 klo 10.10.30')
            painter.end();assert hero.save(str(target/'clock-display-desktop.png'))
            page.target.setCurrentIndex(page.target.findData('combined'));page.load()
            controller.open_page('clocks')
            controller.window.footer.setText('KELLON ASETUSTEN ESIKATSELU · esimerkkiaika, ei oikea kellonaika')
            with patch.object(controller.calendars, 'now', return_value=demo):
                app.processEvents();page.refresh_preview()
                assert controller.window.grab().save(str(target/'clock-displays.png'))
    finally:
        widget.system_override = system_override
        backend.values = backgrounds
        controller.state.commit(before)
        controller.time_rotation.configure(controller.options)
        apply_theme(app, controller.options);controller.weather.apply_shared_options()
        page.load();controller.window.page_widgets['settings'].load()
        controller.window.footer.setText(footer)
        controller.settings_changed.emit();controller.restore_widgets();app.processEvents()
        if running:controller.tick_timer.start(1000)

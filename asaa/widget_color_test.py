"""Verify real widget text colors and independent clock digits through Qt controls."""
import copy
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QImage

from .clock_config import PROFILE_KEYS
from .state import State
from .theme import THEMES, apply_theme
from .widgets import WIDGET_LABELS


def color_pixels(pixmap, color):
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    target = QColor(color)
    return image.bits().asstring(image.sizeInBytes()).count(
        bytes((target.red(), target.green(), target.blue(), 255)))


def acceptance(controller, app, preview_dir=None):
    before = copy.deepcopy(controller.state.data)
    backend = controller.wallpapers.backend
    backgrounds = copy.deepcopy(backend.values)
    wallpaper_calls = len(backend.calls)
    widgets = controller.window.page_widgets['widgets']
    clocks = controller.window.page_widgets['clocks']
    footer = controller.window.footer.text()
    running = controller.tick_timer.isActive()
    controller.tick_timer.stop()
    demo = datetime(2026, 10, 11, 10, 10, 30, tzinfo=controller.calendars.zone)

    def palette(key):
        item = controller.widgets[key]
        return item.paint_palette if key == 'weather' else item.theme

    def pick(control, color):
        with patch('asaa.color_control.QColorDialog.getColor', return_value=QColor(color)):
            control.button.click()
        app.processEvents()

    def quiet_save(page):
        calendars = controller.calendars
        deadline = controller.time_rotation.deadline
        with ExitStack() as stack:
            calls = [stack.enter_context(patch.object(obj, name)) for obj, name in (
                (controller.weather, 'apply_shared_options'),
                (controller.weather, 'refresh'), (controller.weather, 'load_windy'),
                (controller.daily.timer, 'start'))]
            page.save();app.processEvents()
            assert not any(call.called for call in calls)
        assert controller.calendars is calendars and controller.time_rotation.deadline == deadline

    def native(key):
        with patch.object(controller.calendars, 'now', return_value=demo):
            app.processEvents()
            return controller.widgets[key].grab()

    def digits_have_color(item, color):
        with patch.object(controller.calendars, 'now', return_value=demo):
            image = item.grab()
        rows = [row for row in item.text_layout
                if row[0] in (demo.strftime('%H:%M:%S'), demo.strftime('%H:%M'))]
        assert len(rows) == 1
        rect = rows[0][1]
        scale = item.draw_scale
        area = QRect(round(rect.x()*scale), round(rect.y()*scale),
                     round(rect.width()*scale), round(rect.height()*scale))
        return color_pixels(image.copy(area), color) > 0

    try:
        controller.configure({'widget_text_colors': {},
                              'clock_displays': {key: {'mode': 'digital'} for key in PROFILE_KEYS}})
        assert set(widgets.text_colors) == set(WIDGET_LABELS)
        base_palettes = {key: palette(key) for key in WIDGET_LABELS}
        saved = copy.deepcopy(controller.state.data)
        disk = controller.state.path.read_bytes()
        draft = copy.deepcopy(widgets.text_color_drafts)
        # Closing the actual color picker leaves both its draft and saved data unchanged.
        with patch('asaa.color_control.QColorDialog.getColor', return_value=QColor()):
            widgets.text_colors['daily'].button.click()
        assert widgets.text_color_drafts == draft
        assert controller.state.data == saved and controller.state.path.read_bytes() == disk

        colors = dict(zip(WIDGET_LABELS, ('#ff70ca', '#c3ff70', '#70fff0', '#d3f08a',
                                         '#ffc877', '#88baff', '#d7aaff', '#ffae9c')))
        for key, color in colors.items():
            pick(widgets.text_colors[key], color)
            assert widgets.text_colors[key].value == color
        assert controller.state.data == saved and controller.state.path.read_bytes() == disk
        assert base_palettes == {key: palette(key) for key in WIDGET_LABELS}
        weather = controller.weather
        weather_before = (weather.selected, weather.forecast, weather._last_fetch,
                          weather.size(), weather.pos(), weather.timer.interval())
        quiet_save(widgets)
        assert State(controller.state.path).settings['widget_text_colors'] == colors
        for key, color in colors.items():
            assert palette(key).text == color and palette(key).muted == color
            assert color_pixels(native(key), color), (key, 'Saved text color was not rendered.')
        assert weather_before == (weather.selected, weather.forecast, weather._last_fetch,
                                  weather.size(), weather.pos(), weather.timer.interval())
        assert backend.values == backgrounds and len(backend.calls) == wallpaper_calls
        for key in ('notes', 'reminders', 'geometry', 'widget_sizes'):
            assert controller.state.data.get(key) == saved.get(key)

        # Explicit colors survive a shared-theme change; inheritance removes just one override.
        controller.configure({'wallpaper_follow_theme': False})
        controller.configure({'theme': 'ubuntu'})
        assert all(palette(key).text == color for key, color in colors.items())
        saved = copy.deepcopy(controller.state.data)
        widgets.text_colors['shadow_calendar'].inherit.setChecked(True)
        assert controller.state.data == saved
        quiet_save(widgets)
        assert 'shadow_calendar' not in controller.options['widget_text_colors']
        assert palette('shadow_calendar').text == THEMES['ubuntu'].text

        # Saving a draft preserves concurrently changed colors, themes, and clock settings.
        pick(widgets.text_colors['weather'], '#80ecff')
        widgets.themes['weather'].setCurrentIndex(widgets.themes['weather'].findData('frost'))
        concurrent_colors = controller.options['widget_text_colors']
        concurrent_colors['daily'] = '#f2ff99'
        concurrent_themes = controller.options['widget_themes'];concurrent_themes['star_calendar'] = 'copper'
        displays = controller.options['clock_displays'];displays['star']['mode'] = 'both'
        controller.configure({'widget_text_colors': concurrent_colors,
                              'widget_themes': concurrent_themes, 'clock_displays': displays})
        quiet_save(widgets)
        assert controller.options['widget_text_colors']['weather'] == '#80ecff'
        assert controller.options['widget_text_colors']['daily'] == '#f2ff99'
        assert controller.options['widget_themes']['weather'] == 'frost'
        assert controller.options['widget_themes']['star_calendar'] == 'copper'
        assert controller.options['clock_displays']['star']['mode'] == 'both'

        saved = copy.deepcopy(controller.state.data);disk = controller.state.path.read_bytes()
        old_palette = palette('weather')
        pick(widgets.text_colors['weather'], '#ff9f7c')
        with patch('asaa.state.atomic_json', side_effect=OSError('Testin tallennusvirhe')):
            widgets.save();app.processEvents()
        assert controller.state.data == saved and controller.state.path.read_bytes() == disk
        assert palette('weather') == old_palette and widgets.text_colors['weather'].value == '#ff9f7c'
        quiet_save(widgets);assert palette('weather').text == '#ff9f7c'

        # Each clock previews its own inherited text color and its independent digit color.
        digit_colors = dict(zip(PROFILE_KEYS, ('#ff4fd8', '#8eff66', '#66dcff', '#ffe166')))
        for key, color in digit_colors.items():
            controller.open_clock(key)
            clocks.load()
            inherited = palette(key).text
            with patch.object(controller.calendars, 'now', return_value=demo):
                clocks.refresh_preview()
                assert clocks.preview_widget.theme.text == inherited
                assert digits_have_color(clocks.preview_widget, inherited)
            saved = copy.deepcopy(controller.state.data)
            draft = copy.deepcopy(clocks.display_drafts)
            with patch('asaa.color_control.QColorDialog.getColor', return_value=QColor()):
                clocks.digit_color.button.click()
            assert clocks.display_drafts == draft and controller.state.data == saved
            pick(clocks.digit_color, color)
            assert controller.state.data == saved
            with patch.object(controller.calendars, 'now', return_value=demo):
                clocks.refresh_preview()
                assert digits_have_color(clocks.preview_widget, color)
            assert palette(key).text == inherited
            quiet_save(clocks)
            assert State(controller.state.path).settings['clock_displays'][key]['digit_color'] == color
            assert digits_have_color(controller.widgets[key], color)
        controller.open_clock('combined');clocks.load()
        saved = copy.deepcopy(controller.state.data)
        clocks.digit_color.inherit.setChecked(True)
        with patch.object(controller.calendars, 'now', return_value=demo):
            clocks.refresh_preview()
            assert digits_have_color(clocks.preview_widget, palette('combined').text)
        assert controller.state.data == saved
        quiet_save(clocks)
        assert 'digit_color' not in controller.options['clock_displays']['combined']
        assert all(controller.options['clock_displays'][key]['digit_color'] == digit_colors[key]
                   for key in PROFILE_KEYS if key != 'combined')

        # A digit-color draft merges with newer mode, size, other-clock, and note preferences.
        pick(clocks.digit_color, '#b4ff90')
        displays = controller.options['clock_displays']
        displays['combined'].update({'mode': 'both', 'digit_scale': 130})
        displays['civil']['digit_color'] = '#ffc090'
        profiles = controller.options['clock_profiles'];profiles['combined']['note'] = True
        controller.configure({'clock_displays': displays, 'clock_profiles': profiles})
        quiet_save(clocks)
        assert controller.options['clock_displays']['combined'] == {
            'mode': 'both', 'digit_scale': 130, 'digit_color': '#b4ff90'}
        assert controller.options['clock_displays']['civil']['digit_color'] == '#ffc090'
        assert controller.options['clock_profiles']['combined']['note']
        saved = copy.deepcopy(controller.state.data);disk = controller.state.path.read_bytes()
        pick(clocks.digit_color, '#ff8ee6')
        with patch('asaa.state.atomic_json', side_effect=OSError('Testin tallennusvirhe')):
            clocks.save();app.processEvents()
        assert controller.state.data == saved and controller.state.path.read_bytes() == disk
        assert digits_have_color(controller.widgets['combined'], '#b4ff90')
        quiet_save(clocks);assert digits_have_color(controller.widgets['combined'], '#ff8ee6')
        assert backend.values == backgrounds and len(backend.calls) == wallpaper_calls
        print('PASS: all 8 widget text colors, native pixels, picker cancellation, saved inheritance, draft merges and failed-write retry')
        print('PASS: independent digit colors for all 4 clocks, immediate previews, widget-color inheritance and quiet weather/wallpaper preservation')

        if preview_dir:
            target = Path(preview_dir);target.mkdir(parents=True, exist_ok=True)
            controller.open_clock('combined')
            controller.window.footer.setText('VÄRIASETUSTEN ESIKATSELU · esimerkkiaika, ei oikea kellonaika')
            with patch.object(controller.calendars, 'now', return_value=demo):
                app.processEvents();clocks.refresh_preview()
                assert controller.window.grab().save(str(target/'clock-colors.png'))
            controller.open_page('widgets');app.processEvents()
            controller.window.footer.setText('WIDGETTIEN VÄRIASETUSTEN ESIKATSELU · valinnat koskevat kutakin widgetiä')
            assert controller.window.grab().save(str(target/'widget-colors.png'))
    finally:
        backend.values = backgrounds
        controller.state.commit(before)
        controller.time_rotation.configure(controller.options)
        apply_theme(app, controller.options);controller.weather.apply_shared_options()
        widgets.edited_text_colors.clear();widgets.edited_themes.clear()
        clocks.load();controller.window.page_widgets['settings'].load()
        controller.window.footer.setText(footer)
        controller.settings_changed.emit();controller.restore_widgets();app.processEvents()
        if running:controller.tick_timer.start(1000)

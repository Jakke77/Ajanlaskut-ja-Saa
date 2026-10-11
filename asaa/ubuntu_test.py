"""Ubuntu acceptance and previews using the caller's isolated test controller."""
import copy
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse
from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter
from .clock_config import PROFILE_KEYS, SYSTEMS
from .theme import THEMES, apply_theme
from .widget_themes import widget_theme


def acceptance(controller, app, preview_dir=None):
    before = copy.deepcopy(controller.state.data)
    backend = controller.wallpapers.backend
    background = copy.deepcopy(backend.values)
    weather = (controller.weather.selected, controller.weather.size(), controller.weather.pos(),
               controller.weather.paint_palette, controller.daily.timer.interval())
    deadline = controller.time_rotation.deadline
    clock_palettes = {key: widget_theme(controller.options,key,controller.widgets[key].system)
                      for key in PROFILE_KEYS if key != 'combined'}
    page = controller.window.page_widgets['clocks']
    try:
        # The draft changes only the preview; Save explicitly applies the clock theme.
        page.theme.setCurrentIndex(page.theme.findData('ubuntu'));app.processEvents()
        assert controller.state.data == before
        assert page.preview_widget.analog_clock and not page.preview_label.pixmap().isNull()
        with patch.object(controller.weather, 'apply_shared_options') as apply_weather:
            page.save();app.processEvents()
            assert not apply_weather.called
        assert controller.options['widget_themes']['combined'] == 'ubuntu'
        assert controller.time_rotation.deadline == deadline
        assert weather == (controller.weather.selected, controller.weather.size(), controller.weather.pos(),
                           controller.weather.paint_palette, controller.daily.timer.interval())
        assert backend.values == background
        assert controller.state.data['notes'] == before['notes']
        assert controller.state.data['reminders'] == before['reminders']
        assert controller.state.data.get('widget_sizes') == before.get('widget_sizes')
        assert controller.widgets['combined'].analog_clock
        for key in PROFILE_KEYS:
            widget = controller.widgets[key];widget.grab()
            assert widget.theme == (THEMES['ubuntu'] if key == 'combined' else clock_palettes[key])

        # The global theme is also selectable with the existing wallpaper-follow policy.
        settings = controller.window.page_widgets['settings'];settings.load()
        settings.theme.setCurrentIndex(settings.theme.findData('ubuntu'));settings.save();app.processEvents()
        assert controller.options['theme'] == 'ubuntu'
        assert controller.weather.paint_palette == THEMES['ubuntu']
        assert backend.values['org.gnome.desktop.screensaver'] == background['org.gnome.desktop.screensaver']
        uri = backend.values['org.gnome.desktop.background']['picture-uri']
        preserved = Path(unquote(urlparse(uri).path))
        assert preserved.read_bytes() == controller.wallpapers.library.for_theme('ubuntu').path.read_bytes()
        assert controller.window.theme_title.text().startswith('UBUNTU')
        controller.configure({'time_theme': 'shared', 'widget_themes': {}});app.processEvents()
        assert controller.widgets['combined'].analog_clock

        profiles = controller.options['clock_profiles']
        profiles['combined'] = {field: True for field in profiles['combined']}
        controller.configure({'clock_profiles': profiles, 'time_theme': 'ubuntu'})
        widget = controller.widgets['combined']
        size, position = widget.size(), widget.pos()
        for font in ('Ubuntu', 'DejaVu Sans', 'DejaVu Sans Mono'):
            for scale in (80, 160):
                controller.configure({'font': font, 'widget_text_scale': scale, 'widget_clock_scale': 140})
                for system in SYSTEMS:
                    controller.select_time(system);app.processEvents();widget.grab()
                    assert widget.size() == size and widget.pos() == position
                    for _, rect, _, ink_height, ink_width in widget.text_layout:
                        assert ink_height <= rect.height()+.1 and ink_width <= rect.width()+1
                        assert rect.bottom() <= widget.logical_height
                    for i, (_, rect, *_) in enumerate(widget.text_layout):
                        assert not any(rect.intersects(other[1]) for other in widget.text_layout[i+1:])
        controller.configure({'seconds': False, 'opacity': 0})
        app.processEvents();image = widget.grab().toImage()
        assert image.pixelColor(0, 0).alpha() == 0
        assert any(len(value) == 5 and value[2] == ':' for value, *_ in widget.text_layout)
        print('PASS: Ubuntu draft/save, shared palette/wallpaper, clock-only isolation, fonts, calendars, seconds and transparent background')

        if preview_dir:
            preview_dir = Path(preview_dir);preview_dir.mkdir(parents=True, exist_ok=True)
            # Native rendering with a fixed, visibly labelled example time.
            controller.tick_timer.stop()
            demo = datetime(2026, 10, 10, 10, 10, 30, tzinfo=controller.calendars.zone)
            profiles = controller.options['clock_profiles']
            profiles['combined'] = {field: field in ('clock', 'date', 'weekday', 'civil_date')
                                    for field in profiles['combined']}
            controller.configure({'clock_profiles': profiles, 'font': 'Ubuntu', 'opacity': 100,
                                  'widget_text_scale': 130, 'widget_clock_scale': 100, 'scale': 100,
                                  'seconds': True, 'time_mode': 'fixed', 'time_system': 'civil'})
            with patch.object(controller.calendars, 'now', return_value=demo):
                app.processEvents()
                assert widget.grab().save(str(preview_dir/'ubuntu-clock.png'))
                controller.open_page('settings');app.processEvents()
                assert controller.window.grab().save(str(preview_dir/'ubuntu-settings.png'))
                hero = QImage(1920, 1080, QImage.Format.Format_RGB32)
                hero.fill(QColor('#17121f'));painter = QPainter(hero)
                painter.drawImage(hero.rect(), QImage(str(controller.wallpapers.library.for_theme('ubuntu').path)))
                painter.setPen(QColor('#fff4ed'));font = QFont('DejaVu Sans');font.setPixelSize(32)
                painter.setFont(font);painter.drawText(1050, 160, 'UBUNTU · OMA HETKI')
                font.setPixelSize(17);painter.setFont(font);painter.setPen(QColor('#c6aebd'))
                painter.drawText(1050, 198, 'Ajanlaskut ja Sää · analoginen ja digitaalinen kello')
                painter.drawPixmap(1120, 254, widget.grab())
                painter.drawText(1050, 963, 'Sovelluksen esikatselu · esimerkkiaika 10.10.2026 klo 10.10.30')
                painter.end();assert hero.save(str(preview_dir/'ubuntu-desktop.png'))
    finally:
        backend.values = background
        controller.state.commit(before)
        controller.time_rotation.configure(controller.options)
        apply_theme(app, controller.options);controller.weather.apply_shared_options()
        controller.settings_changed.emit();controller.restore_widgets();app.processEvents()
        controller.tick_timer.start(1000)


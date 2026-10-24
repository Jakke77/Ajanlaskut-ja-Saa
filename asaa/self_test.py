"""Isolated Qt acceptance checks and clearly labelled synthetic previews."""
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPainter, QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from .app import Controller, request_existing
from .state import State
from .weather.forecast import Forecast, Hour, UTC
from .weather.providers import slots, common_scales, Place
from .windowing_test import acceptance as windowing_acceptance


def demo_weather(controller):
    """Preview data only; never saved as a real weather cache."""
    now = datetime.now(UTC)
    times = slots(now, 24)
    hours = tuple(Hour(t, 9.5-i*.21, .3 if 7<=i<=10 else 0, 3.2+i*.07,
        7+i*.04, 210+i*2, 'partlycloudy_day' if i<6 else 'cloudyrain' if 7<=i<=10 else 'cloudy', 8.1-i*.21)
        for i,t in enumerate(times))
    forecast = Forecast(hours, now, now)
    controller.weather.forecasts = {key: forecast for key in ('yr','foreca','fmi')}
    controller.weather.forecast = forecast
    controller.weather.scales = common_scales([forecast],controller.weather.times)
    controller.daily.payload = {'weather': [
        {'date': (controller.calendars.now().date()+timedelta(days=n)).isoformat(),
         'mintempC': str(4+n), 'maxtempC': str(10-n),
         'hourly': [{'time':'1200', 'lang_fi':[{'value':'Puolipilvistä'}], 'chanceofrain': str(15+n*20)}]}
        for n in range(3)]}
    controller.daily.saved = now
    controller.weather.changed.emit();controller.daily.changed.emit()


def run_tests(app, preview_dir=None):
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(root/'tests'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): return 1
    with TemporaryDirectory(prefix='ajanlaskut-test-') as folder:
        from tests.test_wallpapers import MemoryBackend
        state = State(Path(folder)/'state.json')
        backend = MemoryBackend()
        controller = Controller(app, state, network=False, wallpaper_backend=backend)
        try:
            assert backend.calls==[],'Startup must never set a wallpaper'
            controller.restore_widgets()
            app.processEvents()
            assert set(k for k,w in controller.widgets.items() if w.isVisible()) == {'weather','combined'}
            assert controller.daily.timer.interval() == 77*60_000
            assert not controller.weather.network_enabled
            controller.open_page('overview');app.processEvents()
            for key in controller.window.page_widgets:
                controller.open_page(key);app.processEvents()
                assert controller.window.navigation[key].isChecked()
            for key in ('shadow','star','shadow_calendar','star_calendar','civil','daily','blood'):
                controller.set_widget(key,True);app.processEvents()
                assert controller.widgets[key].isVisible()
                assert not controller.widgets[key].grab().isNull()
            controller.widgets['civil'].close();app.processEvents()
            assert not state.settings['widgets']['civil']
            controller.configure({'theme':'frost','scale':90,'opacity':60,'font':'DejaVu Sans','seconds':False})
            app.processEvents()
            assert controller.weather.paint_palette.accent == '#a3cfe9'
            for key,widget in controller.widgets.items():
                options = widget.options
                assert options['scale']==90 and options['opacity']==60 and options['font']=='DejaVu Sans'
            assert State(state.path).settings['theme']=='frost'
            controller.configure({'theme':'copper','scale':77,'opacity':77,'font':'Ubuntu','seconds':True})
            calendar=controller.window.page_widgets['calendar']
            today=controller.calendars.now().date()
            state.save_note(today,'Testimerkintä')
            for system in ('shadow','star','civil'):
                calendar.set_day(system,today);app.processEvents()
                assert calendar.note.text()=='Testimerkintä'
                assert len(calendar.day_buttons) in (28,29,30,31)
                calendar.year.setValue(calendar.year.maximum());calendar.month_box.setCurrentIndex(calendar.month_box.count()-1)
                calendar.step(1);app.processEvents()
                assert calendar.month<=controller.calendars.last_month(system)
            controller.listen()
            assert request_existing(state.path,'settings')
            QTest.qWait(80)
            assert controller.window.navigation['settings'].isChecked()
            widget_page=controller.window.page_widgets['widgets']
            widget_page.checks['daily'].setChecked(False);app.processEvents()
            assert not controller.widgets['daily'].isVisible()
            controller.weather.select_provider('windy');controller.open_page('weather');app.processEvents()
            map_page=controller.window.page_widgets['weather']
            assert map_page.windy is not None and map_page.windy.view is None
            assert 'embed.windy.com' in map_page.windy.url
            controller.weather.select_provider('foreca');app.processEvents()
            with patch('asaa.startup.set_autostart') as startup:
                try:controller.configure({'autostart':True,'opacity':-1})
                except ValueError:pass
                assert not startup.called
            demo_weather(controller)
            clock_acceptance(controller,app,preview_dir)
            from .ubuntu_test import acceptance as ubuntu_acceptance
            ubuntu_acceptance(controller,app,preview_dir)
            from .widget_theme_test import acceptance as widget_theme_acceptance
            widget_theme_acceptance(controller,app,preview_dir)
            from .clock_display_test import acceptance as clock_display_acceptance
            clock_display_acceptance(controller,app,preview_dir)
            from .widget_color_test import acceptance as widget_color_acceptance
            widget_color_acceptance(controller,app,preview_dir)
            dimensions={key:widget.size() for key,widget in controller.widgets.items()}
            positions={key:widget.pos() for key,widget in controller.widgets.items()}
            settings=controller.window.page_widgets['settings']
            settings.text_scale.setValue(160);settings.clock_scale.setValue(140);settings.save()
            app.processEvents()
            assert State(state.path).settings['widget_text_scale']==160
            assert State(state.path).settings['widget_clock_scale']==140
            for font in ('Ubuntu','DejaVu Sans','DejaVu Sans Mono'):
                controller.configure({'font':font})
                for scale in (80,100,130,160):
                    controller.configure({'widget_text_scale':scale})
                    app.processEvents()
                    for key,widget in controller.widgets.items():
                        assert widget.size()==dimensions[key] and widget.pos()==positions[key]
                        assert not widget.grab().isNull()
                        if key=='weather':
                            assert widget.options['widget_text_scale']==scale
                            for value,rect,pixels in widget.text_layout:
                                assert rect.left()>=-1 and rect.right()<=720+1,(value,rect)
                                assert rect.top()>=-1 and rect.bottom()<=460+1,(value,rect)
                        else:
                            for _,rect,pixels,ink_height,ink_width in widget.text_layout:
                                assert ink_height<=rect.height()+.1 and ink_width<=rect.width()+1
                                assert rect.bottom()<=widget.logical_height
                            for i,(_,rect,*_) in enumerate(widget.text_layout):
                                assert not any(rect.intersects(other[1]) for other in widget.text_layout[i+1:])
            controller.configure({'font':'Ubuntu','widget_text_scale':130,'widget_clock_scale':100})
            settings.load()
            print('PASS: font controls persist, three font families and all size limits fit without resizing or moving widgets')
            windowing_acceptance(controller,app)
            # Actual buttons, gallery and routing; system backend is an isolated double.
            from .wallpapers import DESKTOP, SAVER, DIA
            import copy
            wallpaper_page=controller.window.page_widgets['wallpapers']
            assert len(wallpaper_page.items)>=1 and wallpaper_page.desktop_button.isEnabled()
            before=copy.deepcopy(backend.values)
            wallpaper_page.desktop_button.click();app.processEvents()
            assert backend.values[SAVER]==before[SAVER]
            assert backend.values[DESKTOP]['picture-uri']==backend.values[DESKTOP]['picture-uri-dark']
            wallpaper_page.lock_button.click();app.processEvents()
            assert backend.values[DIA]['lock-mode']=='single'
            assert backend.values[SAVER]['lock-enabled'] and backend.values[SAVER]['lock-delay']==0
            for key,widget in controller.widgets.items():
                controls=[b for b,_ in widget.controls] if key=='weather' else widget.buttons
                action=next(b for b in controls if b.accessibleName().startswith('Taustakuvat'))
                action.click();app.processEvents()
                assert controller.window.navigation['wallpapers'].isChecked()
            assert request_existing(state.path,'wallpapers');QTest.qWait(80)
            assert controller.window.navigation['wallpapers'].isChecked()
            # Two distinct local images enable the slideshow controls.
            fixture=Path(folder)/'QA-testikuva.png'
            test_image=QImage(32,18,QImage.Format.Format_RGB32);test_image.fill(QColor('#a3cfe9'))
            assert test_image.save(str(fixture))
            controller.wallpapers.library.add(fixture);wallpaper_page.reload()
            wallpaper_page.mode.setCurrentIndex(wallpaper_page.mode.findData('slideshow'))
            for index in range(wallpaper_page.gallery.count()):wallpaper_page.gallery.item(index).setSelected(True)
            assert wallpaper_page.both_button.isEnabled()
            wallpaper_page.interval.setValue(77);wallpaper_page.both_button.click();app.processEvents()
            assert backend.values[DIA]['lock-interval']==77 and backend.values[DIA]['desktop-interval']==77
            assert State(state.path).settings['wallpaper_mode']=='slideshow'
            controller.wallpapers.restore()
            assert backend.values[SAVER]['lock-enabled']
            controller.wallpapers.library.imports.unlink()  # Temporary QA data only.
            wallpaper_page.mode.setCurrentIndex(0);wallpaper_page.reload()
            print('PASS: gallery, all widget shortcuts, desktop/lock separation, 77-minute slideshows and undo; no real GNOME writes')
            from .wallpaper_test import acceptance as wallpaper_acceptance
            wallpaper_acceptance(controller,app,backend)
            if preview_dir:
                preview_dir=Path(preview_dir);preview_dir.mkdir(parents=True,exist_ok=True)
                controller.tick_timer.stop()
                controller.window.resize(1280,960)
                demo_weather(controller)
                calendar.set_day('shadow',today)
                controller.window.footer.setText('KÄYTTÖLIITTYMÄN ESIKATSELU · esimerkkisää, ei oikea ennuste')
                for key in ('overview','calendar','clocks','weather','widgets','settings','wallpapers'):
                    controller.open_page(key);QTest.qWait(30)
                    assert controller.window.grab().save(str(preview_dir/f'{key}.png'))
                controller.configure({'theme':'frost'})
                controller.window.footer.setText('KÄYTTÖLIITTYMÄN ESIKATSELU · esimerkkisää, ei oikea ennuste')
                controller.open_page('overview');QTest.qWait(30)
                assert controller.window.grab().save(str(preview_dir/'frost.png'))
                controller.configure({'theme':'copper'})
                image=QImage(1300,720,QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(QColor('#17131d'))
                painter=QPainter(image);painter.setPen(QColor('#ef986e'));painter.drawText(30,32,'AJANLASKUT JA SÄÄ · TYÖPÖYTÄWIDGETIT · ESIMERKKISÄÄ')
                x=24
                for key in ('star','shadow','weather'):
                    widget=controller.widgets[key]
                    painter.drawPixmap(x,100,widget.grab());x+=widget.width()+22
                for x,key in ((30,'shadow_calendar'),(405,'star_calendar')):
                    painter.drawPixmap(x,490,controller.widgets[key].grab().scaledToHeight(205))
                painter.end();assert image.save(str(preview_dir/'desktop-widgets.png'))
            print('PASS: shared appearance, all 9 widgets, calendars, persistence and single-instance routing')
            selected_before=state.settings['widgets']
            QTimer.singleShot(0,controller.quit)
            app.exec()
            assert controller.stopping and State(state.path).settings['widgets']==selected_before
            print('PASS: deliberate exit keeps widget selections unchanged')
        finally:
            controller.shutdown()
            for widget in controller.widgets.values():widget.hide()
            controller.window.hide();app.processEvents()
    return 0

def clock_acceptance(controller, app, preview_dir):
    import copy
    from .clock_config import FIELD_LABELS, SYSTEMS
    from .almanac_ui import AlmanacDialog
    before=copy.deepcopy(controller.state.data)
    weather=(controller.weather.selected,controller.weather.size(),controller.weather.pos(),controller.weather.paint_palette)
    with patch.object(controller.weather,'apply_shared_options') as apply_weather:
        controller.configure({'time_theme':'calendar','widget_themes':{}})
        for system in SYSTEMS:
            controller.select_time(system);app.processEvents()
            assert not apply_weather.called
            widget=controller.widgets['combined'];assert widget.system==system
            if preview_dir:
                target=Path(preview_dir);target.mkdir(parents=True,exist_ok=True)
                assert widget.grab().save(str(target/f'clock-{system}.png'))
        profiles=controller.options['clock_profiles'];profiles['combined']={key:True for key in FIELD_LABELS}
        controller.configure({'clock_profiles':profiles});app.processEvents()
        size=widget.size();position=widget.pos()
        for system in SYSTEMS:
            controller.select_time(system);app.processEvents();widget.grab()
            assert widget.size()==size and widget.pos()==position
            assert widget.theme.accent != controller.widgets['weather'].paint_palette.accent or system=='shadow'
            values=[item[0] for item in widget.text_layout]
            assert 'PÄIVÄN MERKINTÄ' in values and 'SEURAAVA MUISTUTUS' in values
        for font in ('Ubuntu','DejaVu Sans','DejaVu Sans Mono'):
            for scale in (80,160):
                controller.configure({'font':font,'widget_text_scale':scale,'widget_clock_scale':140})
                for system in SYSTEMS:
                    controller.select_time(system);app.processEvents();widget.grab()
                    for _,rect,pixels,ink_height,ink_width in widget.text_layout:
                        assert ink_height<=rect.height()+.1 and ink_width<=rect.width()+1
                    for i,(_,rect,*_) in enumerate(widget.text_layout):
                        assert not any(rect.intersects(other[1]) for other in widget.text_layout[i+1:])
                    assert widget.size()==size and widget.pos()==position
        controller.configure({'font':before['settings']['font'],'widget_text_scale':before['settings']['widget_text_scale'],
                              'widget_clock_scale':before['settings']['widget_clock_scale']})
        assert apply_weather.called  # Global typography still updates every widget.
        apply_weather.reset_mock()
        page=controller.window.page_widgets['clocks'];controller.open_page('clocks');app.processEvents()
        previous=copy.deepcopy(controller.state.data)
        for check in page.fields.values():check.setChecked(False)
        page.fields['clock'].setChecked(True);app.processEvents()
        assert controller.state.data==previous  # Draft preview is read-only.
        page.save();app.processEvents();widget.grab()
        assert [block[0] for block in __import__('asaa.clock_config',fromlist=['clock_layout']).clock_layout(widget.profile)[0]]==['clock']
        assert controller.state.settings['clock_profiles']['combined']['clock']
        assert not controller.state.settings['clock_profiles']['combined']['weather']
        page.load()
        page.mode.setCurrentIndex(page.mode.findData('random'));page.interval.setValue(5);page.save()
        assert controller.time_rotation.mode=='random' and controller.time_rotation.interval==5
        calendar=controller.window.page_widgets['calendar'];calendar.set_day('star')
        dialog=AlmanacDialog(controller,calendar);dialog.visible.setChecked(True)
        dialog.cell.setCurrentIndex(dialog.cell.findData('hebrew'));dialog.save();app.processEvents()
        assert calendar.extras.isVisible() or bool(calendar.extras.text())
        assert any('\n' in cell.text() for cell in calendar.day_buttons)
        calendar.extras_visible.setChecked(False);app.processEvents()
        assert not calendar.extras.text() and all('\n' not in cell.text() for cell in calendar.day_buttons)
        controller.configure({'calendar_extras_visible':True})
        calendar.set_day('star');controller.open_page('calendar');app.processEvents()
        assert calendar.width()<=controller.window.pages.width(), 'Calendar must not overflow the main viewport.'
        if preview_dir:
            controller.window.footer.setText('KÄYTTÖLIITTYMÄN ESIKATSELU · esimerkkisää, ei oikea ennuste')
            assert controller.window.grab().save(str(Path(preview_dir)/'star-calendars.png'))
            dialog=AlmanacDialog(controller,calendar)
            for check in dialog.checks.values():check.setChecked(True)
            dialog.show();app.processEvents();assert dialog.grab().save(str(Path(preview_dir)/'calendar-options.png'));dialog.reject()
        controller.combine_clocks();app.processEvents()
        assert controller.widgets['combined'].isVisible()
        assert all(not controller.widgets[key].isVisible() for key in SYSTEMS)
        assert weather==(controller.weather.selected,controller.weather.size(),controller.weather.pos(),controller.weather.paint_palette)
        assert not apply_weather.called
    assert controller.state.data['notes']==before['notes'] and controller.state.data['reminders']==before['reminders']
    controller.state.commit(before);controller.time_rotation.configure(controller.options)
    controller.restore_widgets();controller.settings_changed.emit();app.processEvents()
    print('PASS: clock selection, rotation, live draft preview, all content fields, calendar visibility and merge; weather untouched')

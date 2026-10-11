"""Qt checks for theme wallpaper policy; only the isolated MemoryBackend is used."""
import copy
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtCore import Qt,QPoint,QRect
from PyQt6.QtTest import QTest
from .wallpapers import DESKTOP,SAVER,DIA
from .state import State


def choose(combo,value,app):
    """Dispatch real popup mouse events rather than setting the saved value."""
    combo.showPopup();app.processEvents()
    view=combo.view();index=combo.model().index(combo.findData(value),0)
    view.scrollTo(index);app.processEvents()
    point=view.visualRect(index).center()
    QTest.mouseMove(view.viewport(),point)
    QTest.mouseClick(view.viewport(),Qt.MouseButton.LeftButton,pos=point)
    app.processEvents();combo.hidePopup()


def click_with_visible_feedback(page,scroll,action,app):
    """Only scroll before the click, then require feedback in the same viewport."""
    scroll.ensureWidgetVisible(action,50,70);app.processEvents()
    viewport=scroll.viewport()
    assert viewport.rect().contains(QRect(action.mapTo(viewport,QPoint(0,0)),action.size()))
    position=scroll.verticalScrollBar().value()
    QTest.mouseClick(action,Qt.MouseButton.LeftButton,pos=action.rect().center())
    app.processEvents();app.processEvents()
    assert page.status.text()
    assert viewport.rect().contains(QRect(page.status.mapTo(viewport,QPoint(0,0)),page.status.size()))
    assert scroll.verticalScrollBar().value()==position,'Feedback must be visible without further scrolling'


def acceptance(controller,app,backend,preview_dir=None):
    before=copy.deepcopy(controller.state.data)
    backgrounds=copy.deepcopy(backend.values)
    try:
        controller.configure({'theme':'copper','wallpaper_follow_theme':True,'wallpaper_theme_target':'desktop'})
        backend.calls.clear()
        geometry=copy.deepcopy(controller.state.data['geometry'])
        sizes=copy.deepcopy(controller.state.data.get('widget_sizes',{}))
        lock=copy.deepcopy(backend.values[SAVER])
        dia_lock={key:value for key,value in backend.values[DIA].items() if key.startswith('lock-')}
        controller.configure({'theme':'frost'});app.processEvents()
        frost=backend.values[DESKTOP]['picture-uri']
        item=controller.wallpapers.library.for_theme('frost')
        assert frost==controller.wallpapers.library.preserve(item.path).as_uri()
        assert backend.values[SAVER]==lock
        assert {key:value for key,value in backend.values[DIA].items() if key.startswith('lock-')}==dia_lock
        assert controller.state.data['geometry']==geometry and controller.state.data.get('widget_sizes',{})==sizes
        assert State(controller.state.path).settings['theme']=='frost'
        backend.calls.clear()
        controller.configure({'theme':'frost','font':'Ubuntu'});controller.tick();app.processEvents()
        assert not backend.calls,'Same theme, fonts and clock rotation must not change backgrounds'
        page=controller.window.page_widgets['wallpapers']
        controller.open_page('wallpapers');app.processEvents()
        backend.dia=False;page.theme_options.load();page.refresh_current()
        choose(page.theme_options.behavior,False,app)
        assert page.theme_options.behavior.currentData() is False
        assert not page.theme_options.target.isEnabled()
        choose(page.theme_options.behavior,True,app)
        assert page.theme_options.target.isEnabled()
        for target in ('lock','both'):
            index=page.theme_options.target.findData(target)
            assert not page.theme_options.target.model().item(index).isEnabled()
            assert 'vaatii Dia Wall 77' in page.theme_options.target.itemText(index)
            choose(page.theme_options.target,target,app)
            assert page.theme_options.target.currentData()=='desktop'
        assert 'lukitusnäyttö käyttää työpöydän taustaa' in page.theme_options.support.text()
        choose(page.mode,'slideshow',app)
        assert page.mode.currentData()=='slideshow'
        assert 'vaatii Dia Wall 77' in page.mode.currentText()
        assert not any(button.isEnabled() for button in (page.desktop_button,page.lock_button,page.both_button))
        choose(page.mode,'single',app)
        assert page.mode.currentData()=='single'
        backend.dia=True;page.theme_options.load();page.refresh_current()
        choose(page.theme_options.target,'both',app)
        assert page.theme_options.target.currentData()=='both'
        choose(page.theme_options.behavior,False,app)
        data=copy.deepcopy(controller.state.data);raw=controller.state.path.read_bytes()
        controller.settings_changed.emit();app.processEvents()
        page.hide();page.show();app.processEvents()
        assert page.theme_options.behavior.currentData() is False
        assert page.theme_options.target.currentData()=='both'
        assert controller.state.data==data and controller.state.path.read_bytes()==raw
        assert not backend.calls,'Popup choices and unrelated refreshes must remain read-only drafts'
        print('PASS: wallpaper popup mouse choices work; missing Dia targets explain their limit, drafts survive refresh/reopen')
        page.theme_options.behavior.setCurrentIndex(page.theme_options.behavior.findData(False))
        page.save_theme_policy();app.processEvents()
        assert not controller.options['wallpaper_follow_theme'] and not backend.calls
        controller.configure({'theme':'copper'});app.processEvents()
        assert backend.values[DESKTOP]['picture-uri']==frost and not backend.calls
        assert not State(controller.state.path).settings['wallpaper_follow_theme']
        settings=controller.window.page_widgets['settings'];settings.load()
        assert settings.wallpaper_options.behavior.currentData() is False
        for width in (1020,1280):
            controller.window.resize(width,860)
            for key in ('settings','wallpapers'):
                controller.open_page(key);app.processEvents()
                scroll=controller.window.pages.currentWidget()
                assert controller.window.page_widgets[key].width()<=scroll.viewport().width(),(key,width)
        controller.configure({'wallpaper_follow_theme':True,'wallpaper_theme_target':'both'})
        assert not backend.calls,'Saving the policy alone is not an immediate wallpaper trigger'
        controller.configure({'theme':'frost'})
        assert backend.values[DIA]['lock-current-uri']==frost and backend.values[DIA]['desktop-current-uri']==frost
        assert backend.values[SAVER]['lock-enabled'] and backend.values[SAVER]['lock-delay']==0
        assert backend.values[DIA]['clock-visible']
        for failure in ('app','backend'):
            previous_state=copy.deepcopy(controller.state.data);previous_background=copy.deepcopy(backend.values)
            if failure=='app':
                with patch.object(controller.state,'commit',side_effect=OSError('disk full')):
                    try:controller.configure({'theme':'copper'})
                    except OSError:pass
                    else:raise AssertionError('Expected application storage failure')
            else:
                backend.fail=SAVER
                try:controller.configure({'theme':'copper'})
                except OSError:pass
                else:raise AssertionError('Expected backend storage failure')
            assert controller.state.data==previous_state and backend.values==previous_background
        backend.dia=False
        try:controller.configure({'theme':'copper'})
        except ValueError:pass
        else:raise AssertionError('An unavailable lock backend must not partially commit a theme')
        assert controller.options['theme']=='frost' and backend.values[DESKTOP]['picture-uri']==frost
        backend.dia=True
        # The explicit current-theme button works even while keep mode is selected.
        controller.configure({'wallpaper_follow_theme':False,'wallpaper_theme_target':'desktop','theme':'copper'})
        page.theme_options.target.setCurrentIndex(0);page.apply_current_theme();app.processEvents()
        copper=controller.wallpapers.library.preserve(controller.wallpapers.library.for_theme('copper').path).as_uri()
        assert backend.values[DESKTOP]['picture-uri']==copper
        assert not controller.options['wallpaper_follow_theme']
        # At the recorded user's window size, action results must be visible
        # beside the buttons, including a failed backend write.
        controller.configure({'theme':'ubuntu','wallpaper_follow_theme':False,'wallpaper_theme_target':'desktop'})
        controller.window.resize(1440,800);controller.open_page('wallpapers');app.processEvents()
        page.theme_options.target.setCurrentIndex(page.theme_options.target.findData('desktop'))
        copper_index=next(index for index,item in enumerate(page.items) if item.theme=='copper')
        page.gallery.clearSelection();page.gallery.setCurrentRow(copper_index);app.processEvents()
        assert page.selected()[0].theme=='copper'
        assert page.current_theme_button.text()=='Aseta Ubuntu-teeman tausta'
        assert 'Galleriassa valittu kuva' in page.current_theme_button.toolTip()
        scroll=controller.window.pages.currentWidget()
        backend.calls.clear()
        click_with_visible_feedback(page,scroll,page.save_theme_button,app)
        assert page.status.text().startswith('Tallennettu') and not backend.calls
        click_with_visible_feedback(page,scroll,page.current_theme_button,app)
        ubuntu=controller.wallpapers.library.preserve(controller.wallpapers.library.for_theme('ubuntu').path).as_uri()
        assert backend.values[DESKTOP]['picture-uri']==ubuntu and ubuntu!=copper
        assert page.selected()[0].theme=='copper'
        assert page.status.text().startswith('Teeman tausta asetettu:')
        if preview_dir:
            preview_dir=Path(preview_dir);preview_dir.mkdir(parents=True,exist_ok=True)
            assert controller.window.grab().save(str(preview_dir/'wallpaper-feedback-success.png'))
        previous_state=copy.deepcopy(controller.state.data);raw=controller.state.path.read_bytes()
        previous_background=copy.deepcopy(backend.values)
        backend.fail=DESKTOP
        click_with_visible_feedback(page,scroll,page.current_theme_button,app)
        assert 'simulated storage failure' in page.status.text()
        assert controller.state.data==previous_state and controller.state.path.read_bytes()==raw
        assert backend.values==previous_background
        if preview_dir:
            assert controller.window.grab().save(str(preview_dir/'wallpaper-feedback-error.png'))
        controller.configure({'theme':'frost'});app.processEvents()
        assert page.current_theme_button.text()=='Aseta Halla-teeman tausta'
        print('PASS: wallpaper success/error feedback stays visible at 1440x800; named theme action differs from selected gallery image')
        print('PASS: Halla/Kupari follow by default, keep policy persists, desktop/lock scope and unchanged clock/widget geometry')
        print('PASS: no startup/font/rotation wallpaper writes; failed settings/backend save restores both theme and backgrounds')
    finally:
        backend.dia=True;backend.fail=None;backend.values=backgrounds
        controller.state.commit(before)
        from .theme import apply_theme
        apply_theme(controller.app,controller.options);controller.settings_changed.emit()
        controller.window.page_widgets['settings'].load();app.processEvents()

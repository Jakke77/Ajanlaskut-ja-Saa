"""Single QApplication owns all calendars, weather services and desktop windows."""
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import sys
from PyQt6.QtCore import QObject, QTimer, QLockFile, QUrl, QCoreApplication, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QMessageBox
from .calendar import Calendars
from .state import State, data_directory
from .theme import apply_theme
from .widget_themes import widget_theme
from .services import SharedWeather, DailyWeather
from .widgets import DesktopSurface, WIDGET_LABELS
from .wallpapers import WallpaperManager
from .icon_themes import IconThemeManager
from .clock_config import ClockRotation, SYSTEMS, PROFILE_KEYS
from .windowing import WindowLayers
from . import VERSION
from .about import AboutDialog
from .platform_support import IS_WINDOWS, WINDOWS_THEMES

ROOT = Path(__file__).resolve().parents[1]

def server_name(path):
    return 'ajanlaskut-ja-saa-' + sha256(str(Path(path).resolve()).encode()).hexdigest()[:16]

def request_existing(path, mode='main'):
    socket = QLocalSocket()
    socket.connectToServer(server_name(path))
    if not socket.waitForConnected(500): return False
    socket.write(json.dumps({'mode': mode}).encode()+b'\n')
    socket.waitForBytesWritten(1000);socket.disconnectFromServer();return True

class Controller(QObject):
    clock_changed=pyqtSignal()
    settings_changed=pyqtSignal()
    notes_changed=pyqtSignal()
    def __init__(self,app,state,network=True,wallpaper_backend=None,icon_backend=None):
        super().__init__();self.app,self.state=app,state;self.stopping=False
        self.calendars=Calendars(state.settings['zone'],state.settings['star_epoch'])
        self.time_rotation=ClockRotation(state.settings)
        self.icon=QIcon(str(ROOT/'assets/icon.svg'))
        self.widgets={};self.window=None;self.tray=None;self.server=None;self.sound=None
        self.layers=WindowLayers(self)
        self.wallpapers=WallpaperManager(ROOT/'assets/wallpapers',state.path.parent,wallpaper_backend)
        self.icon_themes=IconThemeManager(ROOT/'assets/icon-themes',state.path.parent,icon_backend)
        apply_theme(app,self.options)
        self.weather=SharedWeather(self,network=network)
        self.daily=DailyWeather(self,network=network)
        self.widgets['weather']=self.weather
        from .ui import MainWindow
        self.window=MainWindow(self)
        self.appearance_watcher=None
        if IS_WINDOWS:
            from .windows_appearance import WindowsAppearanceWatcher
            self.appearance_watcher=WindowsAppearanceWatcher(self)
        self.tick_timer=QTimer(self);self.tick_timer.timeout.connect(self.tick);self.tick_timer.start(1000)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray=QSystemTrayIcon(self.icon,self)
            self.tray.setToolTip('Ajanlaskut ja Sää')
            menu=QMenu(self.window)
            menu.addAction('Avaa Ajanlaskut ja Sää',lambda:self.open_page('overview'))
            menu.addAction('Työpöytäwidgetit',lambda:self.open_page('widgets'))
            menu.addAction('Ajanlaskuwidgetit',lambda:self.open_page('clocks'))
            menu.addAction('Taustakuvat',lambda:self.open_page('wallpapers'))
            menu.addAction('Yhteiset asetukset',lambda:self.open_page('settings'))
            menu.addAction('Tietoa sovelluksesta',self.show_about)
            menu.addSeparator();menu.addAction('Lopeta sovellus',self.quit)
            self.tray.setContextMenu(menu);self.tray.activated.connect(lambda why:self.open_page('overview') if why==QSystemTrayIcon.ActivationReason.Trigger else None)
            self.tray.show()
        app.aboutToQuit.connect(self.shutdown)

    @property
    def options(self):return self.state.settings

    def show_about(self):
        dialog=AboutDialog(VERSION,ROOT,self.window)
        try:dialog.exec()
        finally:dialog.deleteLater()

    def restore_widgets(self):
        for key,enabled in self.options['widgets'].items():
            self.set_widget(key,enabled,persist=False)

    def set_widget(self,key,enabled,persist=True):
        if key not in WIDGET_LABELS:raise ValueError('Tuntematon widget')
        if persist:
            settings=self.options['widgets'];settings[key]=enabled
            try:self.state.configure({'widgets':settings})
            except OSError as error:
                self.storage_error(error);return False
        if enabled and key not in self.widgets:self.widgets[key]=DesktopSurface(self,key)
        if key in self.widgets:
            item=self.widgets[key]
            if enabled:
                item.show()
                if key=='weather':
                    item.ensure_on_screen()
                    if item.uses_web_view:item.load_web_view()
                else:item.clamp()
                self.layers.sync()
            else:item.hide()
        if persist:
            self.settings_changed.emit()
        return True

    def storage_error(self,error):
        QMessageBox.warning(self.window,'Tietoja ei voitu tallentaa',f'{error}\n\nTarkista levyn vapaa tila ja tiedoston käyttöoikeudet.')

    def visible_widgets(self):return any(w.isVisible() for w in self.widgets.values())

    def configure(self,changes):
        before=self.options
        previous=before['autostart'];candidate=self.state.configured_data(changes)
        changed_start=changes.get('autostart',previous) != previous
        def commit():
            if changed_start:
                from .startup import set_autostart
                set_autostart(changes['autostart'])
            try:self.state.commit(candidate)
            except OSError:
                if changed_start:set_autostart(previous)
                raise
        options=candidate['settings']
        # Nest the two reversible desktop operations around the durable app
        # commit, so a failure restores the icons, background and settings.
        shared_theme_changed=options['theme']!=before['theme']
        def commit_icons():
            if shared_theme_changed and options['icon_follow_theme'] and not IS_WINDOWS and options['theme'] not in WINDOWS_THEMES:
                self.icon_themes.apply(options['theme'],commit=commit)
            else:commit()
        # No startup, fonts, per-widget changes or rotation trigger a write.
        if shared_theme_changed and options['wallpaper_follow_theme'] and not IS_WINDOWS and options['theme'] not in WINDOWS_THEMES:
            picture=self.wallpapers.library.for_theme(options['theme'])
            self.wallpapers.apply([picture.path],options['wallpaper_theme_target'],commit=commit_icons)
        else:commit_icons()
        self.time_rotation.configure(self.options)
        changed_keys={key for key in changes if options.get(key)!=before.get(key)}
        if changed_keys <= {'theme', 'widget_themes', 'time_theme', 'widget_text_colors'}:
            if options['theme'] != before['theme']:
                apply_theme(self.app,self.options)
            if widget_theme(before,'weather') != widget_theme(options,'weather'):
                self.weather.apply_widget_theme()
            self.settings_changed.emit();self.clock_changed.emit()
            return
        clock_only={'time_mode','time_system','time_systems','time_interval','time_theme','widget_themes','clock_profiles','clock_weather',
                    'clock_displays','widget_clock_scale','widget_text_colors',
                    'calendar_extras_visible','calendar_extras','calendar_extras_scope','calendar_extra_cell',
                    'wallpaper_follow_theme','wallpaper_theme_target','icon_follow_theme'}
        if changed_keys <= clock_only:
            if widget_theme(before,'weather') != widget_theme(options,'weather'):
                self.weather.apply_widget_theme()
            self.settings_changed.emit();self.clock_changed.emit()
            return
        self.calendars=Calendars(self.options['zone'],self.options['star_epoch'])
        apply_theme(self.app,self.options);self.weather.apply_shared_options()
        self.daily.timer.start(self.options['refresh_minutes']*60_000)
        self.settings_changed.emit();self.clock_changed.emit()
        page=self.window.page_widgets['calendar'];page.set_day(page.system,page.selected)
        self.window.page_widgets['weather'].sync()

    def set_wallpaper(self,paths,target,mode='single',interval=77,shuffle=True):
        changes={'wallpaper_mode':mode,'wallpaper_interval':interval,'wallpaper_shuffle':shuffle}
        candidate=self.state.configured_data(changes)
        self.wallpapers.apply(paths,target,mode,interval,shuffle,commit=lambda:self.state.commit(candidate))
        self.settings_changed.emit()

    def set_icon_theme(self):
        self.icon_themes.apply(self.options['theme'])
        self.settings_changed.emit()

    def install_icon_themes(self,all_apps=False):
        result=self.icon_themes.install(all_apps=all_apps)
        self.settings_changed.emit()
        return result

    def restore_icon_theme(self):
        candidate=self.state.configured_data({'icon_follow_theme':False})
        self.icon_themes.restore(commit=lambda:self.state.commit(candidate))
        self.settings_changed.emit()

    def use_system_default_icons(self):
        candidate=self.state.configured_data({'icon_follow_theme':False})
        self.icon_themes.apply_default(commit=lambda:self.state.commit(candidate))
        try:
            if self.icon_themes.launcher_registry_exists():
                self.icon_themes.restore_launchers()
        except Exception as error:
            raise OSError('Järjestelmän oletuskuvakkeet käytössä, mutta '
                          'sovelluskuvakkeiden palautus epäonnistui: '+str(error)) from error
        finally:
            self.settings_changed.emit()

    def restore_icon_launchers(self):
        self.icon_themes.restore_launchers()
        self.settings_changed.emit()

    def open_page(self,key):
        if self.window.isMinimized():self.window.showNormal()
        else:self.window.show()
        self.layers.sync()
        self.window.show_page(key);self.window.raise_();self.window.activateWindow()

    def open_calendar(self,system,day=None):
        if system == 'blood' and day is None:
            from .blood_time import at
            day=at(self.calendars.now()).civil
        self.window.page_widgets['calendar'].set_day(system,day)
        self.open_page('calendar')

    def open_clock(self,key):
        if key not in PROFILE_KEYS:raise ValueError('Tuntematon kellowidget')
        page=self.window.page_widgets['clocks']
        page.target.setCurrentIndex(page.target.findData(key))
        self.open_page('clocks')

    def select_time(self, system):
        if system not in SYSTEMS: raise ValueError('Tuntematon ajanlasku')
        try:self.configure({'time_mode':'fixed','time_system':system})
        except OSError as error:self.storage_error(error);return False
        return True

    def step_time(self, direction=1):
        if self.options['time_mode']=='fixed':
            target=SYSTEMS[(SYSTEMS.index(self.time_rotation.current)+direction)%len(SYSTEMS)]
            self.select_time(target)
        else:
            self.time_rotation.advance(direction);self.clock_changed.emit()

    def combine_clocks(self):
        """Explicit merge: keep every old position and all weather options untouched."""
        import copy
        candidate=copy.deepcopy(self.state.data)
        choices=candidate['settings']['widgets']
        previous=next((key for key in SYSTEMS if choices[key]), 'shadow')
        if 'combined' not in candidate['geometry'] and previous in candidate['geometry']:
            candidate['geometry']['combined']=candidate['geometry'][previous].copy()
        choices['combined']=True
        for key in SYSTEMS: choices[key]=False
        self.state.commit(candidate)
        for key in ('combined',*SYSTEMS): self.set_widget(key,choices[key],persist=False)
        self.settings_changed.emit()

    def reset_positions(self):
        import copy
        data=copy.deepcopy(self.state.data);data['geometry']={}
        try:self.state.commit(data)
        except OSError as error:self.storage_error(error);return
        for key,widget in self.widgets.items():
            if key=='weather':widget.restore_position()
            else:widget.restore_position()

    def tick(self):
        self.time_rotation.poll()
        self.clock_changed.emit()
        try:due=self.state.take_due(self.calendars.now())
        except OSError:return
        for item in due:
            if self.tray:self.tray.showMessage('Kalenterimuistutus',item['title'],QSystemTrayIcon.MessageIcon.Information,10000)
            else:
                box=QMessageBox(self.window);box.setWindowTitle('Kalenterimuistutus');box.setText(item['title']);box.setStandardButtons(QMessageBox.StandardButton.Ok);box.setModal(False);box.show()
                box.setAttribute(__import__('PyQt6.QtCore',fromlist=['Qt']).Qt.WidgetAttribute.WA_DeleteOnClose)
            if self.options['sound']:
                from PyQt6.QtMultimedia import QSoundEffect
                if self.sound is None:
                    self.sound=QSoundEffect(self);self.sound.setSource(QUrl.fromLocalFile(str(ROOT/'assets/huuhkaja.wav')))
                self.sound.play()
        if due:self.notes_changed.emit()

    def listen(self):
        name=server_name(self.state.path)
        QLocalServer.removeServer(name)
        self.server=QLocalServer(self);self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        if not self.server.listen(name):raise OSError(self.server.errorString())
        self.server.newConnection.connect(self.receive)

    def receive(self):
        while self.server.hasPendingConnections():
            connection=self.server.nextPendingConnection()
            def read(conn=connection):
                if not conn.canReadLine():return
                raw=bytes(conn.readLine(256))
                try:
                    mode=json.loads(raw).get('mode')
                    if mode=='widgets':self.restore_widgets()
                    elif mode in ('main','overview'):self.open_page('overview')
                    elif mode in ('weather','calendar','sunmoon','names','widgets','settings','wallpapers','clocks','blood'):self.open_page(mode)
                except (ValueError,AttributeError):pass
                conn.disconnectFromServer()
            connection.readyRead.connect(read);connection.disconnected.connect(connection.deleteLater);read()

    def quit(self):
        # A deliberate application exit must not look like hiding each widget.
        self.shutdown();self.app.quit()

    def shutdown(self):
        if self.stopping:return
        if self.appearance_watcher:self.appearance_watcher.shutdown()
        self.stopping=True;self.layers.shutdown();self.tick_timer.stop();self.daily.shutdown()
        self.weather.shutdown()
        page=self.window.page_widgets['weather']
        page.stop_web_views()
        self.window.page_widgets['sunmoon'].stop()
        if self.tray:self.tray.hide()
        if self.server:self.server.close()

def run(args):
    QCoreApplication.setApplicationName('AjanlaskutJaSaa');QCoreApplication.setOrganizationName('Jakke77')
    QCoreApplication.setApplicationVersion(VERSION)
    QApplication.setDesktopFileName('ajanlaskut-ja-saa')
    app=QApplication([sys.argv[0]])
    app.setApplicationDisplayName('Ajanlaskut ja Sää');app.setStyle('Fusion');app.setQuitOnLastWindowClosed(False)
    if args.self_test:
        if IS_WINDOWS:
            from .windows_self_test import run_tests
            return run_tests(app,args.preview_dir)
        from .self_test import run_tests
        return run_tests(app,args.preview_dir)
    path=args.data_dir/'state.json' if args.data_dir else data_directory()/'state.json'
    if request_existing(path,'widgets' if args.widgets_only else (args.page or 'main')):return 0
    path.parent.mkdir(parents=True,exist_ok=True)
    lock=QLockFile(str(path)+'.lock');lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        QMessageBox.warning(None,'Sovellus on jo käynnissä','Sama kalenteritiedosto on toisessa ikkunassa käytössä.');return 1
    try:
        state=State(path)
        try:state.import_legacy()
        except (OSError,ValueError,KeyError,TypeError) as error:
            QMessageBox.warning(None,'Vanhojen merkintöjen tuonti',f'Vanhojen kalenterien merkintöjä ei voitu tuoda:\n{error}\nVoit käyttää uutta sovellusta.')
        controller=Controller(app,state,network=not args.offline);controller.listen()
        if not args.no_widgets:controller.restore_widgets()
        if not args.widgets_only or (not controller.visible_widgets() and controller.tray is None):controller.open_page(args.page or 'overview')
        signal.signal(signal.SIGINT,lambda *_:controller.quit());signal.signal(signal.SIGTERM,lambda *_:controller.quit())
        return app.exec()
    except (OSError,ValueError,KeyError,TypeError) as error:
        QMessageBox.critical(None,'Sovellus ei käynnistynyt',str(error));return 1
    finally:lock.unlock()

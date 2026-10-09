"""One forecast source and one shared settings object for every window."""
from dataclasses import asdict
from datetime import datetime, date
import json
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import quote
from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import QMenu, QApplication
from .theme import THEMES
from .weather.forecast import ForecastCache, UTC
from .weather.providers import Place, slots, common_scales
from .weather.widget import WeatherWidget
from .windowing import WidgetFrame

class SettingsBridge:
    def __init__(self, controller): self.controller = controller
    def value(self, key, default=None, type=None):
        settings = self.controller.state.settings
        if key == 'theme': value = 'ubuntu'
        elif key == 'place': value = json.dumps(settings['place'], ensure_ascii=False)
        elif key in ('x', 'y'):
            geometry = self.controller.state.geometry('weather')
            value = geometry[0 if key == 'x' else 1] if geometry else default
        else: value = settings.get(key, default)
        return type(value) if type and value is not None else value
    def setValue(self, key, value):
        if key in ('x', 'y'):
            current = self.controller.state.geometry('weather') or [value if key == 'x' else 0, value if key == 'y' else 0]
            current[0 if key == 'x' else 1] = value
            self.controller.state.geometry('weather', current)
        elif key == 'place': self.controller.state.configure({'place': json.loads(value)})
        elif key in self.controller.state.settings and key != 'theme': self.controller.state.configure({key: value})
    def sync(self): pass

class SharedWeather(WeatherWidget):
    """Original weather graph hosted by the new application's controller."""
    def __init__(self, controller, network=True):
        self.controller = controller
        self._last_fetch = None
        cache_dir = controller.state.path.parent / 'weather-cache'
        old = Path.home() / '.cache/pollonkangas-saa'
        if not cache_dir.exists() and old.is_dir():
            shutil.copytree(old, cache_dir, ignore=shutil.ignore_patterns('*.lock'))
        super().__init__(SettingsBridge(controller), ForecastCache(cache_dir), network=False, integrated=True)
        self.frame=WidgetFrame(self,controller,'weather')
        self.add_button('▧', 'Taustakuvat · työpöytä ja lukitusnäyttö', lambda: controller.open_page('wallpapers'), (466,20,32,28))
        self.header_title_width = 418
        self.network_enabled = network
        self.setWindowTitle('Ajanlaskut ja Sää · sääwidget')
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self.tick)
        self.timer.start(60_000)
        self.apply_shared_options()
        if network: QTimer.singleShot(0, self.refresh)

    def apply_shared_options(self):
        options = self.controller.state.settings
        self.paint_palette = THEMES[options['theme']]
        self.display_zone = ZoneInfo(options['zone'])
        self.apply_options({**self.options, **{k: options[k] for k in ('scale', 'opacity', 'locked', 'on_top', 'font', 'widget_text_scale', 'widget_clock_scale', 'windy_zoom', 'windy_layer')}, 'theme': 'ubuntu'})
        for button,_ in self.controls:
            button.setStyleSheet(f'QToolButton {{color:{self.paint_palette.accent};background:transparent;border:0;padding:0;font:16px "{options["font"]}";}} QToolButton:hover,QToolButton:focus {{background:{self.paint_palette.border};border-radius:7px;}}')
        self.setAccessibleName('Sääwidget · ' + self.place.name)

    def restore_position(self):
        area = QApplication.primaryScreen().availableGeometry()
        position = self.controller.state.geometry('weather') or [area.right()+1-self.width()-28, area.bottom()+1-self.height()-24]
        self.move(*position[:2]);self.ensure_on_screen()

    def save_position(self):
        saved=self.controller.state.geometry('weather')
        try:self.controller.state.geometry('weather',[self.x(),self.y()]+(saved[2:] if saved else []))
        except OSError as error:
            if not self.stopping:self.controller.storage_error(error)

    def tick(self):
        self.times = slots()
        self.forecasts = {k: cache.cached() for k, cache in self.caches.items()}
        self.forecast = self.forecasts.get(self.selected)
        self.scales = common_scales(self.forecasts.values(), self.times)
        self.update_accessibility(); self.update(); self.changed.emit()
        interval = self.controller.state.settings['refresh_minutes'] * 60
        if self.network_enabled and (self._last_fetch is None or (datetime.now(UTC)-self._last_fetch).total_seconds() >= interval):
            self.refresh(automatic=True)

    def refresh(self, automatic=False):
        if not self.network_enabled: return
        if self.worker and self.worker.isRunning(): return
        self._last_fetch = datetime.now(UTC)
        super().refresh(automatic)

    def open_expanded(self): self.controller.open_page('weather')
    def open_settings(self): self.controller.open_page('settings')

    def make_menu(self):
        menu = QMenu(self)
        menu.addAction('Avaa sää sovelluksessa', self.open_expanded)
        menu.addAction('Vaihda sääpalvelua', lambda: self.switch_provider(1))
        menu.addAction('Hae paikka…', self.open_place)
        menu.addAction('Päivitä ennuste', self.refresh)
        menu.addAction('Yhteiset asetukset', self.open_settings)
        menu.addAction('Taustakuvat · työpöytä ja lukitusnäyttö', lambda: self.controller.open_page('wallpapers'))
        menu.addAction('Piilota sääwidget', lambda: self.controller.set_widget('weather', False))
        menu.addAction('Palauta tämän widgetin oletuskoko',self.frame.reset)
        return menu

    def set_place(self, place):
        try:super().set_place(place)
        except OSError as error:self.controller.storage_error(error);return
        if hasattr(self.controller, 'daily'):
            self.controller.daily.configure()
            self.controller.settings_changed.emit()

    def closeEvent(self, event):
        if self.stopping: event.accept()
        else:
            self.controller.set_widget('weather', False)
            event.ignore()

    def load_windy(self, *, force=False):
        # A hidden desktop surface does not initiate an extra embedded map.
        if self.isVisible(): super().load_windy(force=force)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if hasattr(self.controller, 'daily'):
            self.controller.settings_changed.emit()


class DailyWeather(QObject):
    """Varjosää's daily forecast, shared by the clock cards and compact widget."""
    changed = pyqtSignal()
    def __init__(self, controller, network=True):
        super().__init__(controller)
        self.controller, self.network = controller, network
        self.manager = QNetworkAccessManager(self)
        self.reply = None
        self.path = controller.state.path.parent / 'daily-cache.json'
        self.payload = {}
        self.saved = None
        self.error = ''
        self.loaded_key = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.configure()

    def configure(self):
        self.timer.start(self.controller.state.settings['refresh_minutes'] * 60_000)
        if self.reply:
            self.reply.abort()
        self.payload, self.saved, self.loaded_key = {}, None, None
        try:
            payload = json.loads(self.path.read_text(encoding='utf-8'))
            if payload.get('key') == self.key:
                self.payload = payload['data']; self.loaded_key = self.key
                self.saved = datetime.fromisoformat(payload['saved'])
        except (OSError, ValueError, KeyError, TypeError): pass
        self.changed.emit()
        if self.network: QTimer.singleShot(0, self.refresh)

    @property
    def key(self): return Place(**self.controller.state.settings['place']).key

    def refresh(self):
        if not self.network or self.reply: return
        if self.saved and (datetime.now(UTC) - self.saved).total_seconds() < self.controller.state.settings['refresh_minutes'] * 60:
            return
        key = self.key
        request = QNetworkRequest(QUrl('https://wttr.in/' + quote(key, safe=',') + '?format=j1&lang=fi'))
        request.setRawHeader(b'User-Agent', b'Ajanlaskut-ja-Saa/1.0')
        request.setTransferTimeout(15_000)
        reply = self.manager.get(request)
        self.reply = reply
        reply.finished.connect(lambda: self.finished(reply, key))

    def finished(self, reply, key):
        if self.reply is reply: self.reply = None
        if key != self.key:
            reply.deleteLater(); return
        try:
            if reply.error() != reply.NetworkError.NoError: raise ValueError('Sääpalveluun ei saatu yhteyttä')
            data = json.loads(bytes(reply.readAll()))
            if not isinstance(data.get('weather'), list) or not data['weather']: raise ValueError('Päiväennuste puuttuu')
            self.payload, self.saved, self.loaded_key, self.error = data, datetime.now(UTC), key, ''
            from .state import atomic_json
            atomic_json(self.path, {'key': key, 'saved': self.saved.isoformat(), 'data': data})
        except (ValueError, TypeError, KeyError, OSError) as error: self.error = str(error)
        reply.deleteLater(); self.changed.emit()

    def lines(self):
        today = self.controller.calendars.now().date()
        lines = []
        for item in self.payload.get('weather', []):
            try:
                day = date.fromisoformat(item['date'])
                if day < today: continue
                hours = item.get('hourly', [])
                noon = min(hours, key=lambda h: abs(int(h.get('time', 0))-1200)) if hours else {}
                description = (noon.get('lang_fi') or noon.get('weatherDesc') or [{'value': ''}])[0]['value']
                rain = max([int(h.get('chanceofrain', 0)) for h in hours] or [0])
                lines.append(f'{day:%d.%m.}  {item["mintempC"]}…{item["maxtempC"]} °C · {description} · {rain} %')
            except (ValueError, KeyError, TypeError): continue
        return lines[:3]

    def shutdown(self):
        self.timer.stop()
        if self.reply:
            self.reply.abort()

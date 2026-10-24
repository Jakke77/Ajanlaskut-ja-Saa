"""Movable, translucent forecast graphs inspired by the user's Conky theme."""
from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import asdict
import math
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QFont, QFontMetricsF, QIcon, QPainter, QPainterPath, QPen, QLinearGradient
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QMenu, QSpinBox, QSystemTrayIcon, QVBoxLayout, QWidget,
    QToolButton, QComboBox, QSlider, QMessageBox)

from .forecast import Forecast, ForecastCache, LOCATION, TZ, UTC
from .providers import (PROVIDERS, NAMES, Place, read_place, provider_caches, slots, aligned, common_scales)
from zoneinfo import ZoneInfo
from .windy_view import WindyView, WeatherWebView
import json

WIDTH, HEIGHT = 720, 460
ROOT = Path(__file__).resolve().parent
DEFAULTS = {"scale": 77, "opacity": 28, "locked": True, "on_top": False, "theme": "ubuntu", "font": "Ubuntu", "widget_text_scale": 130, "windy_zoom": 9, "windy_layer": "temp"}


def read_options(settings):
    options = {}
    for key, default in DEFAULTS.items():
        try:
            options[key] = settings.value(key, default, type=type(default))
        except (TypeError, ValueError):
            options[key] = default
    options["scale"] = max(75, min(180, options["scale"]))
    options["opacity"] = max(0, min(100, options["opacity"]))
    if options["theme"] not in ("ubuntu", "classic"):
        options["theme"] = "ubuntu"
    options["windy_zoom"] = max(3,min(12,options["windy_zoom"]))
    if options["windy_layer"] not in ("temp","wind","rain","clouds"): options["windy_layer"]="temp"
    return options


class FetchThread(QThread):
    result = pyqtSignal(str, str, object, str)

    def __init__(self, caches, place_key, selected, parent=None):
        super().__init__(parent)
        self.caches, self.place_key = caches, place_key
        self.order = [selected] + [k for k in PROVIDERS if k != selected]

    def run(self):
        for key in self.order:
            if self.isInterruptionRequested(): return
            try:
                f = self.caches[key].fetch()
                self.result.emit(self.place_key,key,f,f.error)
            except Exception as exc:
                self.result.emit(self.place_key,key,None,str(exc))


def color(hex_value, alpha=1.0):
    result = QColor(hex_value)
    result.setAlphaF(max(0, min(1, alpha)))
    return result


def draw_text(p, value, x, y, size=10, shade="#d6d8dc", bold=False, right=False, max_width=None, fit=False):
    font = QFont(p.font().family())
    pixels=round(size*getattr(p,'text_scale',1))
    font.setPixelSize(pixels)
    font.setBold(bold)
    metrics=QFontMetricsF(font)
    while fit and max_width and pixels>6 and metrics.horizontalAdvance(value)>max_width:
        pixels-=1;font.setPixelSize(pixels);metrics=QFontMetricsF(font)
    if max_width is not None:value=metrics.elidedText(value,Qt.TextElideMode.ElideRight,max_width)
    p.setFont(font)
    p.setPen(QColor(shade))
    if right:
        x -= p.fontMetrics().horizontalAdvance(value)
    p.drawText(QPointF(x, y), value)
    if hasattr(p,'text_layout'):
        p.text_layout.append((value,QRectF(x,y-metrics.ascent(),metrics.horizontalAdvance(value),metrics.height()),pixels))


def draw_line(p, x1, y1, x2, y2, shade, width=1, alpha=1, dashed=False):
    pen = QPen(color(shade, alpha), width)
    if dashed:
        pen.setStyle(Qt.PenStyle.DashLine)
    p.setPen(pen)
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def draw_icon(p, x, y, symbol, scale=1, unknown_shade="#b8b0ba"):
    if symbol == "unknown":
        draw_text(p,"?",x-3,y+4,12,unknown_shade)
        return
    p.save()
    p.translate(x, y)
    p.scale(scale, scale)
    p.setPen(Qt.PenStyle.NoPen)
    clear = symbol.startswith("clearsky")
    sunny = clear or "fair" in symbol or "partly" in symbol
    night = "night" in symbol
    if sunny:
        p.setBrush(QColor("#cfd7e5" if night else "#f3ab45"))
        if night:
            moon = QPainterPath(); moon.addEllipse(QPointF(-4,-5),6,6)
            cutout = QPainterPath(); cutout.addEllipse(QPointF(-1,-7),5.5,5.5)
            p.drawPath(moon.subtracted(cutout))
        else:
            p.drawEllipse(QPointF(-4,-5),6,6)
            for i in range(8):
                a = i * math.pi / 4
                draw_line(p, -4 + math.cos(a) * 8, -5 + math.sin(a) * 8,
                          -4 + math.cos(a) * 11, -5 + math.sin(a) * 11, "#f3ab45", 1.2)
    if not clear:
        path = QPainterPath()
        path.addEllipse(QRectF(-13, -3, 12, 11))
        path.addEllipse(QRectF(-7, -10, 16, 17))
        path.addEllipse(QRectF(3, -3, 13, 11))
        path.addRect(QRectF(-8, 0, 18, 8))
        path.setFillRule(Qt.FillRule.WindingFill)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#bdc3ca"))
        p.drawPath(path.simplified())
    if "snow" in symbol or "sleet" in symbol:
        for dx in (-7, 1, 9):
            draw_line(p, dx, 11, dx, 16, "#cce9fa", 1.3)
            draw_line(p, dx - 2, 12, dx + 2, 15, "#cce9fa", 1.3)
            draw_line(p, dx - 2, 15, dx + 2, 12, "#cce9fa", 1.3)
    if "rain" in symbol or "sleet" in symbol:
        for dx in (-7, 1, 9):
            draw_line(p, dx, 11, dx - 2, 16, "#59a9db", 1.5)
    if "thunder" in symbol:
        draw_line(p, 3, 6, -1, 13, "#f3ab45", 2)
        draw_line(p, -1, 13, 4, 13, "#f3ab45", 2)
        draw_line(p, 4, 13, 0, 20, "#f3ab45", 2)
    if symbol.startswith("fog"):
        for yy in (12, 16):
            draw_line(p, -12, yy, 15, yy, "#bdc3ca", 1.2)
    p.restore()


def draw_arrow(p, x, y, direction):
    # MET gives the direction wind comes FROM; arrow points downwind.
    angle = math.radians(direction + 180)
    x2, y2 = x + math.sin(angle) * 8, y - math.cos(angle) * 8
    draw_line(p, x, y, x2, y2, "#b5bac2", 1.2)
    for turn in (-2.55, 2.55):
        draw_line(p, x2, y2, x2 + math.sin(angle + turn) * 4,
                  y2 - math.cos(angle + turn) * 4, "#b5bac2", 1.2)


class WeatherWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, settings, cache=None, *, network=True, integrated=False):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint if integrated else Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.integrated=integrated
        self.settings = settings
        self.place = read_place(settings)
        self.directory = cache.directory if cache else None
        self.caches = provider_caches(self.place, self.directory)
        if cache and self.place == Place(): self.caches['yr'] = cache
        self.selected = settings.value('provider', 'foreca')
        if self.selected not in (*PROVIDERS,'windy'): self.selected = 'yr'
        self.forecasts = {k:c.cached() for k,c in self.caches.items()}
        self.errors = {}
        self.times = slots()
        self.scales = common_scales(self.forecasts.values(), self.times)
        self.cache = self.caches.get(self.selected,self.caches["yr"])
        self.forecast = self.forecasts.get(self.selected)
        self.network_enabled = network
        self.windy = None
        self.weather_web = None
        self.expanded = None
        self.pending_refresh = False
        self.portal = None
        self.controls = []
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.error = ""
        self.worker = None
        self.drag_offset = None
        self.stopping = False
        self.setWindowTitle("Pöllönkangas – sääwidget")
        self.setWindowIcon(QIcon(str(ROOT / "assets/icon.svg")))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.add_button('‹', 'Edellinen sääpalvelu', lambda: self.switch_provider(-1), (8,204,28,48))
        self.add_button('›', 'Seuraava sääpalvelu', lambda: self.switch_provider(1), (684,204,28,48))
        self.expand_button = self.add_button('', 'Avaa isoon ikkunaan', self.open_expanded, (510,20,32,28))
        self.expand_button.setIcon(QIcon(str(ROOT / 'assets/expand.svg')))
        self.add_button('Hae', 'Hae ennustepaikka', self.open_place, (550,20,52,28))
        self.locate_button = self.add_button('◎', 'Käytä laitteen sijaintia', self.locate, (608,20,32,28))
        from ..platform_support import IS_WINDOWS
        if IS_WINDOWS:
            self.locate_button.setToolTip('Hae sääpaikka nimellä')
            self.locate_button.setAccessibleName('Hae sääpaikka nimellä')
        self.add_button('⚙', 'Asetukset', self.open_settings, (648,20,32,28))
        self.apply_options(read_options(settings))
        self.restore_position()
        self.tray = None
        if not integrated and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self.windowIcon(), self)
            self.tray.setToolTip("Pöllönkankaan sää")
            self.tray.activated.connect(lambda reason: self.restore_widget()
                if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
            self.tray.setContextMenu(self.make_menu())
            self.tray.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        if network:
            self.timer.start(60_000)
            QTimer.singleShot(0, self.refresh)
        self.update_accessibility()
        if self.uses_web_view and not integrated: self.load_web_view()

    @property
    def available_view_modes(self):
        return ('graph',) if self.selected == 'yr' else ('graph', 'map')

    @property
    def view_mode(self):
        modes = self.settings.value('weather_views', {})
        default = 'map' if self.selected == 'windy' else 'graph'
        mode = modes.get(self.selected, default) if isinstance(modes, dict) else default
        return mode if mode in self.available_view_modes else default

    @property
    def uses_web_view(self):
        return self.view_mode == 'map' or self.selected == 'windy'

    @property
    def web_view(self):
        if not self.uses_web_view:
            return None
        return self.windy if self.selected == 'windy' and self.view_mode == 'map' else self.weather_web

    @property
    def foreca_source_url(self):
        return self.caches['foreca'].read().get('source_url', '')

    def set_view_mode(self, mode):
        if mode not in self.available_view_modes:
            raise ValueError('Tämä sääpalvelu ei tue valittua näkymää.')
        if mode == self.view_mode:
            return False
        saved = self.settings.value('weather_views', {})
        modes = {key: ('map' if key == 'windy' else 'graph') for key in (*PROVIDERS, 'windy')}
        if isinstance(saved, dict):
            modes.update(saved)
        modes[self.selected] = mode
        self.settings.setValue('weather_views', modes)
        self.settings.sync()
        self.sync_web_view()
        self.update_accessibility(); self.update(); self.changed.emit()
        if self.tray:
            self.tray.setContextMenu(self.make_menu())
        return True

    def add_view_actions(self, menu):
        for mode in self.available_view_modes:
            title = ('Tuntiennuste' if self.selected == 'windy' else 'Ennustegraafi') if mode == 'graph' else 'Sääkartta' if self.selected == 'windy' else 'Sadetutka'
            action = menu.addAction(title)
            action.setCheckable(True)
            action.setChecked(mode == self.view_mode)
            action.triggered.connect(lambda checked, value=mode: self.set_view_mode(value))

    def sync_web_view(self):
        for view in (self.windy, self.weather_web):
            if view and view is not self.web_view:
                view.hide()
        if self.uses_web_view:
            self.load_web_view()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'options') and self.uses_web_view:
            self.load_web_view()

    def apply_options(self, options):
        visible, position = self.isVisible(), self.pos()
        self.options = DEFAULTS | dict(options)
        if self.integrated:
            from ..windowing import apply_layer
            apply_layer(self,self.controller.layers.on_top())
            self.setMinimumSize(round(WIDTH*.6),round(HEIGHT*.6))
            saved=self.controller.state.widget_size('weather')
            size=saved or [round(WIDTH*self.options['scale']/100),round(HEIGHT*self.options['scale']/100)]
            if getattr(self,'frame',None):
                from PyQt6.QtCore import QSize
                size=self.frame.size(QSize(*size))
                size=[size.width(),size.height()]
            self.resize(*size)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.options["on_top"])
            self.setWindowFlag(Qt.WindowType.WindowStaysOnBottomHint, not self.options["on_top"])
            self.setFixedSize(round(WIDTH*self.options['scale']/100),round(HEIGHT*self.options['scale']/100))
        self.layout_controls()
        self.setCursor(Qt.CursorShape.ArrowCursor if self.options["locked"] else Qt.CursorShape.SizeAllCursor)
        if visible:
            self.show()
            self.move(position)
            self.ensure_on_screen()
        self.update()
        self.changed.emit()

    def restore_position(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        try:
            x = self.settings.value("x", area.right() + 1 - self.width() - 38, type=int)
            y = self.settings.value("y", area.top() + 70, type=int)
        except (TypeError, ValueError):
            x, y = area.x() + 40, area.y() + 40
        self.move(x, y)
        self.ensure_on_screen()

    def ensure_on_screen(self):
        screens = QApplication.screens()
        if not screens:
            return
        rect = self.geometry()
        if any(s.availableGeometry().contains(rect) for s in screens):
            return
        screen = QApplication.screenAt(rect.center()) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        self.move(max(area.left(), min(self.x(), area.right() - self.width() + 1)),
                  max(area.top(), min(self.y(), area.bottom() - self.height() + 1)))

    def save_position(self):
        self.settings.setValue("x", self.x())
        self.settings.setValue("y", self.y())
        self.settings.sync()

    def restore_widget(self):
        if self.expanded and self.expanded.isVisible():
            self.open_expanded()
            return
        self.show()
        self.ensure_on_screen()
        # Only raise on explicit launcher/tray activation, never each refresh.
        self.raise_()

    def tick(self):
        self.times = slots()
        self.forecasts = {k:c.cached() for k,c in self.caches.items()}
        self.forecast = self.forecasts.get(self.selected)
        self.scales = common_scales(self.forecasts.values(),self.times)
        self.update_accessibility()
        self.update()
        self.changed.emit()
        self.refresh(automatic=True)

    def refresh(self, automatic=False):
        if not self.network_enabled or self.stopping:
            return
        if self.uses_web_view and not automatic:
            self.load_web_view(force=True)
        if self.stopping or (self.worker and self.worker.isRunning()):
            return
        self.worker = FetchThread(self.caches, self.place.key, self.selected if self.selected in PROVIDERS else "yr", self)
        self.worker.result.connect(self.provider_received)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def worker_finished(self):
        worker = self.sender()
        if self.worker is worker:
            self.worker = None
        worker.deleteLater()
        if self.pending_refresh and not self.stopping:
            self.pending_refresh = False
            self.refresh()

    def add_button(self, text, name, action, rect):
        button = QToolButton(self)
        button.setText(text)
        button.setToolTip(name)
        button.setAccessibleName(name)
        button.setCursor(Qt.CursorShape.ArrowCursor)
        button.setStyleSheet('QToolButton {color:#f4d6c6;background:transparent;border:0; font:16px Ubuntu;}'
                            'QToolButton:hover,QToolButton:focus {background:rgba(210,98,55,90);border-radius:7px;}')
        button.clicked.connect(action)
        self.controls.append((button,rect))
        return button

    def layout_controls(self):
        scale=min(self.width()/WIDTH,self.height()/HEIGHT) if self.integrated else self.options['scale']/100
        width,height=self.width()/scale,self.height()/scale
        for button,rect in self.controls:
            x,y,w,h=rect
            if self.integrated and x>400:x+=width-WIDTH
            button.setGeometry(*(round(v*scale) for v in (x,y,w,h)))
        for view in (self.windy, self.weather_web):
            if view and view.parentWidget() is self:
                view.setGeometry(round(36*scale),round(92*scale),round((width-72)*scale),round((height-145)*scale))

    def resizeEvent(self,event):
        if hasattr(self,'options'):self.layout_controls()
        super().resizeEvent(event)

    def switch_provider(self, offset):
        keys = (*PROVIDERS,'windy')
        self.select_provider(keys[(keys.index(self.selected)+offset)%len(keys)])

    def select_provider(self, key):
        if key not in (*PROVIDERS,'windy'): return
        self.settings.setValue('provider',key)
        self.selected = key
        self.cache = self.caches.get(key,self.caches['yr'])
        self.forecast = self.forecasts.get(key)
        self.error = self.errors.get(key,'')
        self.sync_web_view()
        self.update_accessibility(); self.update(); self.changed.emit()

    def load_web_view(self, *, force=False):
        if self.stopping or not self.uses_web_view:
            return
        if self.selected == 'windy' and self.view_mode == 'map':
            self.load_windy(force=force)
            return
        if self.weather_web is None:
            self.weather_web = WeatherWebView(self, network=self.network_enabled)
        self.layout_controls()
        self.weather_web.load_source(self.selected, self.view_mode, self.place,
            self.options['windy_zoom'], self.options['windy_layer'], self.foreca_source_url, force=force)
        if self.expanded and self.expanded.isVisible():
            self.expanded.sync()
        else:
            self.weather_web.show()

    def load_windy(self, *, force=False):
        if self.stopping or self.selected != 'windy' or self.view_mode != 'map':
            return
        if not self.windy:
            self.windy = WindyView(self,network=self.network_enabled)
        self.layout_controls()
        self.windy.load(self.place,self.options['windy_zoom'],self.options['windy_layer'],force=force)
        if self.expanded and self.expanded.isVisible():
            self.expanded.sync()
        else: self.windy.show()

    def open_expanded(self):
        raise NotImplementedError('The host application provides the forecast page')

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right):
            self.switch_provider(-1 if event.key()==Qt.Key.Key_Left else 1)
            event.accept()
        else: super().keyPressEvent(event)

    def provider_received(self, place_key, key, forecast, error):
        if self.stopping or place_key != self.place.key: return
        self.forecasts[key] = forecast
        self.errors[key] = error
        self.scales = common_scales(self.forecasts.values(),self.times)
        if key == self.selected:
            self.forecast, self.error = forecast, error
            if self.selected == 'foreca' and self.view_mode == 'map':
                self.load_web_view()
        self.update_accessibility(); self.update(); self.changed.emit()

    def received(self, forecast):
        self.provider_received(self.place.key,self.selected,forecast,forecast.error)

    def failed(self, message):
        self.provider_received(self.place.key,self.selected,self.cache.cached(),message)

    def set_place(self, place):
        self.settings.setValue('place',json.dumps(asdict(place),ensure_ascii=False))
        self.settings.sync()
        self.place = place
        self.caches = provider_caches(place,self.directory)
        self.forecasts = {k:c.cached() for k,c in self.caches.items()}
        self.errors = {}
        self.cache = self.caches.get(self.selected,self.caches["yr"])
        self.forecast, self.error = self.forecasts.get(self.selected), ''
        if self.uses_web_view: self.load_web_view()
        self.times = slots()
        self.scales = common_scales(self.forecasts.values(),self.times)
        self.update_accessibility(); self.update(); self.changed.emit()
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption(); self.pending_refresh = True
        elif self.network_enabled: self.refresh()

    def open_place(self):
        from .place_dialog import PlaceDialog
        dialog = PlaceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.place:
            self.set_place(dialog.place)

    def locate(self):
        from ..platform_support import IS_WINDOWS
        if IS_WINDOWS:
            self.open_place()
            return
        if self.portal and self.portal.active: return
        answer = QMessageBox.question(self,'Käytä laitteen sijaintia',
            'Saako widget hakea laitteen sijainnin tätä ennustetta varten?\n\n'
            'Ubuntu pyytää tarvittaessa sijaintiluvan. Koordinaatit lähetetään MET Norwaylle, '
            'Forecalle, Ilmatieteen laitokselle ja wttr.in-palvelulle ennusteiden hakemista varten. '
            'Paikka tallennetaan tälle koneelle. Sijaintia ei seurata taustalla.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        from .location_portal import LocationPortal
        self.portal = LocationPortal(self)
        self.portal.located.connect(self.located)
        self.portal.failed.connect(self.location_failed)
        self.locate_button.setEnabled(False)
        parent = f'x11:{int(self.winId()):x}' if QApplication.platformName()=='xcb' else ''
        self.portal.start(parent)

    def located(self, lat, lon):
        self.locate_button.setEnabled(True)
        self.set_place(Place('Oma sijainti',round(lat,4),round(lon,4)))

    def location_failed(self, message):
        self.locate_button.setEnabled(True)
        QMessageBox.information(self,'Sijaintihaku',message)

    def update_accessibility(self):
        text = self.place.name + '. ' + NAMES.get(self.selected,'WINDY') + '. '
        if self.uses_web_view:
            text += 'Tuntiennuste.' if self.view_mode == 'graph' else 'Sääkartta.' if self.selected == 'windy' else 'Sadetutka.'
        elif self.forecast:
            text += '; '.join(f'Klo {h.time.astimezone(ZoneInfo(self.place.timezone)):%H}: '
                f'{h.temperature:.1f} °C, sade {h.rain if h.rain is not None else "ei tietoa"} mm, tuuli {h.wind:.1f} m/s'
                for h in self.forecast.hours[:12])
        else: text += self.error or 'Haetaan ennustetta.'
        self.setAccessibleName(text)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale=min(self.width()/WIDTH,self.height()/HEIGHT)
        p.scale(scale,scale)
        self.paint_content(p,width=self.width()/scale,height=self.height()/scale)

    def paint_content(self, p, *, width=WIDTH, height=HEIGHT, times=None, scales=None, expanded=False):
        palette = getattr(self, 'paint_palette', None)
        accent = palette.accent if palette else '#ed9164'
        background = palette.background if palette else '#100e15'
        surface = palette.surface if palette else '#321e27'
        text = palette.text if palette else '#d6d8dc'
        muted = palette.muted if palette else None
        times = self.times if times is None else times
        scales = self.scales if scales is None else scales
        extra = max(0, height-HEIGHT)
        rain_bottom = 274+extra*.45
        wind_top, wind_bottom = 311+extra*.45, 373+extra
        p.setFont(QFont(self.options["font"]))
        p.text_scale=1 if expanded else self.options.get('widget_text_scale',100)/100
        p.text_layout=[]
        if not expanded:self.text_layout=p.text_layout
        text_extra=p.text_scale-1
        opacity = 1 if expanded else self.options['opacity']/100
        if opacity > 0:
            if palette:
                from ..theme import paint_panel
                paint_panel(p, QRectF(0, 0, width, height), palette, opacity)
            else:
                if self.options['theme']=='ubuntu':
                    gradient = QLinearGradient(0,0,width,height)
                    gradient.setColorAt(0,color(surface,opacity))
                    gradient.setColorAt(.5,color(background,opacity))
                    gradient.setColorAt(1,color(background,opacity))
                    p.setBrush(gradient)
                else: p.setBrush(color('#111218',opacity))
                p.setPen(QPen(color(accent,.55*opacity),1))
                p.drawRoundedRect(QRectF(.5,.5,width-1,height-1),16,16)
                if self.options['theme']=='ubuntu':
                    p.save()
                    clip = QPainterPath(); clip.addRoundedRect(QRectF(1,1,width-2,height-2),16,16)
                    p.setClipPath(clip)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(color(accent,.12*opacity),.7))
                    p.drawEllipse(QRectF(420,-172,360,360))
                    p.drawEllipse(QRectF(408,-184,384,384))
                    for i in range(25):
                        x,y = (i*83+41)%width,(i*37+11)%HEIGHT
                        p.setPen(QPen(color('#edaa89',.22*opacity),1))
                        p.drawPoint(QPointF(x,y))
                    p.restore()
        title = self.place.name.upper()
        draw_text(p,title,36,38,20,accent,True,max_width=width-72 if expanded else getattr(self,'header_title_width',466)+width-WIDTH)
        zone = getattr(self, 'display_zone', ZoneInfo(self.place.timezone))
        first, last = times[0].astimezone(zone),times[-1].astimezone(zone)
        if self.uses_web_view:
            subtitle = ('Tuntiennuste ja ennusteaika palvelun omalla aikajanalla' if self.view_mode == 'graph'
                else 'Ennusteaika valitaan kartan aikajanalta' if self.selected == 'windy'
                else 'Sateen havainnot ja animaatio palvelun omassa sadetutkassa')
        else:
            subtitle = f'{first:%d.%m. %H} – {last:%d.%m. %H} · {len(times)} tuntia · {zone.key}'
        draw_text(p,subtitle,36,58,10,muted or '#b6b0bd',max_width=width-72)
        source_name = NAMES.get(self.selected, 'WINDY')
        if self.uses_web_view:
            source_name += ' · ' + ('TUNTIENNUSTE' if self.view_mode == 'graph' else 'KARTTA' if self.selected == 'windy' else 'SADETUTKA')
        draw_text(p,source_name,36,83,11,accent,True)
        for i,key in enumerate((*PROVIDERS,'windy')):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(accent if key==self.selected else palette.border if palette else '#66545c'))
            p.drawEllipse(QPointF(width-87+i*14,78),3,3)
        if self.uses_web_view:
            if self.expanded and self.expanded.isVisible():
                draw_text(p,'Näkymä on avoinna isossa ikkunassa',width/2-135,230,16,text if palette else '#f7ccb3')
            elif expanded:
                draw_text(p,'Avaa '+('tuntiennuste' if self.view_mode == 'graph' else 'kartta')+' sääsivulta',64,164,18,text)
            detail = 'Windy.com · tuntiennuste valitulle paikalle' if self.view_mode == 'graph' else ('Windy.com · kartalla oma ennusteaika ja väriskaala' if self.selected == 'windy' else source_name.split(' · ')[0]+' · palvelun oma sadetutka ja aikajana')
            draw_text(p,detail,36,height-16,9,muted or '#ad98a6')
            return
        hours = aligned(self.forecast,times)
        xs = [64+i*(width-136)/(len(times)-1) for i in range(len(times))]
        if not self.forecast:
            draw_text(p,'Ennustetta ei saatavilla' if self.error else 'Haetaan sääennustetta…',64,164,18,text)
            draw_text(p,self.error or 'Palvelut latautuvat hetken. Voit vaihtaa palvelua nuolilla.',64,192,11,muted or '#bbb3bd')
        else:
            for x,t,h in zip(xs,times,hours):
                local = t.astimezone(zone)
                if expanded and (t == times[0] or local.hour == 0):
                    draw_text(p,local.strftime('%d.%m.'),x-15,92,9,accent)
                    if t != times[0]: draw_line(p,x,96,x,394+extra,accent,1,.4,True)
                draw_text(p,local.strftime('%H'),x+7,108,11,text,right=True)
                if h:
                    draw_icon(p,x,126,h.symbol,.78,muted or '#b8b0ba')
                    draw_text(p,f'{h.temperature:.0f}°',x+12,161+20*text_extra,18,text if palette else '#fff1e7',True,right=True,max_width=(width-136)/(len(times)-1)-4,fit=True)
                    if h.feels_like is not None:
                        draw_text(p,f'{h.feels_like:.0f}°',x+8,178+35*text_extra,10,muted or '#b8b0ba',right=True,max_width=(width-136)/(len(times)-1)-4,fit=True)
                    draw_arrow(p,x,387+extra,h.direction)
                else: draw_text(p,'—',x+7,161,15,text,right=True)
                draw_line(p,x,193,x,372+extra,muted or '#b9aebd',.6,.13)
            if any(h and h.feels_like is not None for h in hours):
                draw_text(p,'tuntuu',12,178+35*text_extra,8,muted or '#b8b0ba',max_width=43)
            draw_text(p,'LÄMPÖ °C',64,194+40*text_extra,9,'#ee9368',True)
            self.plot(p,xs,hours,'temperature',206+40*text_extra,rain_bottom,scales.temperature,'#f18a54')
            draw_text(p,'TUULI m/s',64,298+extra*.45,9,'#bca6f3',True)
            self.plot(p,xs,hours,'wind',wind_top,wind_bottom,(0,scales.wind),'#b096ed')
            self.draw_series(p,xs,[h.gust if h else None for h in hours],wind_top,wind_bottom,0,scales.wind,'#d7c3ff',1.2,True)
            # Separate precipitation axis in mm per hour, shared by every source.
            for x,h in zip(xs,hours):
                if h and h.rain:
                    height = h.rain/scales.rain*(60+extra*.45)
                    p.fillRect(QRectF(x-5,rain_bottom-height,10,height),color('#5faee2',.60))
            self.draw_series(p,xs,[h.temperature if h else None for h in hours],206+40*text_extra,rain_bottom,*scales.temperature,'#f18a54',2.3)
            draw_text(p,f'{scales.rain:g}',width-30,214,9,'#77b8e8',right=True)
            draw_text(p,'mm/h',width-28,229,8,'#77b8e8',right=True)
            draw_text(p,'0',width-30,rain_bottom+2,9,'#77b8e8',right=True)
            rain = sum(h.rain or 0 for h in hours if h)
            partial = any(not h or h.rain is None for h in hours)
            draw_text(p,f'Sade {rain:.1f} mm'+(' · osittainen' if partial else ''),width-71,rain_bottom+3,10,'#77b8e8',right=True)
        draw_text(p,'━ lämpö   ▪ sade   ━ tuuli   ╌ puuskat',36,414+extra,10,muted or '#c7bdc8')
        draw_text(p,'Yhteiset asteikot',width-36,414+extra,10,muted or '#b1a5b1',right=True)
        if self.forecast:
            f = self.forecast
            stamp = f.updated if self.selected=='yr' else f.fetched
            status = ('välimuisti · ' if self.error or f.error else '') + ('vanha · ' if f.stale() else '')
            status += ('päivitetty ' if self.selected=='yr' else 'haettu ') + stamp.astimezone(zone).strftime('%H:%M')
        else: status = 'Oikea painike: valikko'
        source = {'yr':'MET Norway · CC BY 4.0', 'foreca':'Foreca.fi · julkinen tuntiennuste', 'fmi':'Ilmatieteen laitos · avoin data'}[self.selected]
        if self.selected=='foreca':
            resolved = self.caches['foreca'].read().get('resolved_name','')
            if resolved: source += ' · ' + resolved
        draw_text(p,source,36,436+extra,9,muted or '#a99aaa',max_width=width*.64-72)
        draw_text(p,status,width-36,436+extra,9,muted or '#baabb9',right=True,max_width=width*.36-18)

    def plot(self,p,xs,hours,field,top,bottom,limits,shade):
        lo,hi = limits
        palette = getattr(self, 'paint_palette', None)
        for frac in (0,.5,1):
            y = bottom-frac*(bottom-top)
            draw_line(p,xs[0],y,xs[-1],y,palette.muted if palette else '#c7b6c5',.6,.24)
            draw_text(p,f'{lo+frac*(hi-lo):g}',52,y+3,9,palette.muted if palette else '#bcaabb',right=True)
        self.draw_series(p,xs,[getattr(h,field) if h else None for h in hours],top,bottom,lo,hi,shade,2.2)

    @staticmethod
    def draw_series(p, xs, values, top, bottom, lo, hi, shade, width, dashed=False):
        for i in range(len(xs) - 1):
            if values[i] is None or values[i + 1] is None:
                continue
            ya = bottom - (values[i] - lo) / (hi-lo) * (bottom-top)
            yb = bottom - (values[i+1] - lo) / (hi-lo) * (bottom-top)
            draw_line(p, xs[i], ya, xs[i+1], yb, shade, width, dashed=dashed)
        if len(xs) == 1 and values[0] is not None:
            p.setPen(QPen(QColor(shade), width))
            p.drawPoint(QPointF(xs[0], bottom - (values[0] - lo) / (hi-lo) * (bottom-top)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.options["locked"]:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            if self.windowHandle() and self.windowHandle().startSystemMove():
                self.drag_offset = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
        scale=min(self.width()/WIDTH,self.height()/HEIGHT)
        x=event.position().x()/scale;virtual_width=self.width()/scale
        if self.uses_web_view:
            self.setToolTip('')
        elif self.forecast:
            i=round((x-64)/((virtual_width-136)/(len(self.times)-1)))
            hours = aligned(self.forecast,self.times)
            if 0 <= i < 12 and hours[i]:
                h = hours[i]
                rain = f'{h.rain:.1f} mm' if h.rain is not None else 'ei tietoa'
                gust = f'{h.gust:.1f} m/s' if h.gust is not None else 'ei tietoa'
                local = h.time.astimezone(getattr(self,'display_zone',ZoneInfo(self.place.timezone)))
                self.setToolTip(f'{local:%d.%m. klo %H:%M %Z}\nLämpö {h.temperature:.1f} °C\n'
                    f'Sade klo {local:%H}–{(local+timedelta(hours=1)):%H}: {rain}\n'
                    f'Tuuli {h.wind:.1f} m/s · puuskat {gust}')
            else: self.setToolTip('Tälle tunnille ei ole tietoja.')
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        self.save_position()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self.make_menu().exec(event.globalPos())

    def toggle(self, key):
        options = dict(self.options)
        options[key] = not options[key]
        self.settings.setValue(key, options[key])
        self.apply_options(options)
        self.save_position()
        if self.tray:
            self.tray.setContextMenu(self.make_menu())

    def make_menu(self):
        menu = QMenu(self)
        menu.addAction("Näytä widget", self.restore_widget)
        menu.addAction("Avaa isoon ikkunaan", self.open_expanded)
        menu.addAction("Päivitä ennuste", self.refresh)
        menu.addAction("Hae paikka…", self.open_place)
        menu.addAction("Käytä laitteen sijaintia…", self.locate)
        menu.addAction("Seuraava sääpalvelu", lambda: self.switch_provider(1))
        self.add_view_actions(menu)
        menu.addAction("Asetukset…", self.open_settings)
        for key, label in (("locked", "Lukitse sijainti"), ("on_top", "Pidä päällimmäisenä")):
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.options[key])
            action.triggered.connect(lambda checked, k=key: self.toggle(k))
        menu.addSeparator()
        links = {'yr':f'https://www.yr.no/en/forecast/daily-table/{self.place.latitude},{self.place.longitude}',
                 'foreca':self.caches['foreca'].read().get('source_url','https://www.foreca.fi/'),
                 'fmi':f'https://www.ilmatieteenlaitos.fi/saa?coordinate={self.place.latitude},{self.place.longitude}',
                 'windy':self.windy.url if self.windy else 'https://www.windy.com/'}
        if self.web_view and self.web_view.url:
            links[self.selected] = self.web_view.url
        menu.addAction('Avaa sääpalvelun sivu',lambda: QDesktopServices.openUrl(QUrl(links[self.selected])))
        menu.addAction("Säätiedot ja lisenssi…", self.show_attribution)
        menu.addSeparator()
        menu.addAction("Sulje widget", self.close)
        return menu

    def open_settings(self):
        raise NotImplementedError('The host application provides shared settings')

    def show_attribution(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Säätiedot ja lisenssi")
        layout = QVBoxLayout(dialog)
        label = QLabel('MET Norway: CC BY 4.0 · <a href="https://www.met.no/">met.no</a><br>'
            'Ilmatieteen laitos: avoin data · <a href="https://www.ilmatieteenlaitos.fi/avoin-data">fmi.fi</a><br>'
            'Foreca: julkisen Foreca.fi-sivun tuntiennuste; epävirallinen sovitin.<br>'
            'Forecan data ei kuulu tämän ohjelman MIT-lisenssiin.<br>'
            'Paikkahaku: Open-Meteo / GeoNames. Windy: viralliset kartta- ja tuntiennusteupotukset.<br>'
            'Forecan ja Ilmatieteen laitoksen sadetutkat ovat palvelujen omia sivuja; niiden tiedot ja käyttöehdot säilyvät.<br><br>'
            'Käyrät käyttävät samoja asteikkoja: widgetissä 12 tuntia, isossa ikkunassa 24 tuntia.<br>'
            'Sademäärä on alkavan tunnin kertymä; puuttuva arvo näkyy aukkona.<br>'
            'Lämpötilat ovat ennusteita, eivät sääaseman havaintoja.<br>'
            'Kupari-teema on itsenäinen Ubuntu 26.04 -henkinen teema.')
        label.setOpenExternalLinks(True)
        layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def shutdown(self):
        self.stopping = True
        self.timer.stop()
        if self.portal: self.portal.stop()
        if self.expanded: self.expanded.close()
        if self.windy: self.windy.stop()
        if self.weather_web: self.weather_web.stop()
        self.save_position()
        if self.tray:
            self.tray.hide()
        if self.worker and self.worker.isRunning():
            # Keep the QObject alive until its bounded network request ends.
            self.worker.requestInterruption()
            self.worker.wait()

    def closeEvent(self, event):
        self.shutdown()
        event.accept()
        QApplication.instance().quit()

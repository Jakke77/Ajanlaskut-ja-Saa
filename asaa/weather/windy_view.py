"""Windy's official live embed, retaining controls, attribution and map colours."""
from urllib.parse import urlencode
from PyQt6.QtCore import QTimer,QUrl
from PyQt6.QtGui import QColor,QDesktopServices
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton

try:
    from PyQt6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile,QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None


def map_url(place, zoom=9, layer='temp'):
    # Default view includes Hailuoto west of Oulu, matching the user's sample.
    lat,lon = (65.03,25.40) if place.key=='65.0701,25.5071' else (place.latitude,place.longitude)
    return 'https://embed.windy.com/embed.html?' + urlencode(dict(type='map',location='coordinates',
        lat=lat,lon=lon,zoom=zoom,overlay=layer,level='surface',product='ecmwf',
        metricTemp='°C',metricWind='m/s',metricRain='mm',marker='false'))


class WindyView(QWidget):
    def __init__(self,parent=None,*,network=True):
        super().__init__(parent)
        self.url = ''
        self.view = None
        self._loaded_url = ''
        self._loading_url = ''
        self._failed_url = ''
        self._pending = False
        self._force_pending = False
        self._stopped = False
        self._load_timer = QTimer(self)
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._start_load)
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        if QWebEngineView and network:
            self.profile = QWebEngineProfile(self)  # Off-the-record: no saved tracking cookies.
            self.profile.setHttpAcceptLanguage('fi-FI,fi;q=0.9,en;q=0.8')
            self.profile.downloadRequested.connect(lambda download: download.cancel())
            self.view = QWebEngineView(self)
            self.page = QWebEnginePage(self.profile,self.view)
            self.page.setBackgroundColor(QColor('#171720'))
            self.page.permissionRequested.connect(lambda permission: permission.deny())
            self.view.setPage(self.page)
            settings=self.view.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,False)
            settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled,False)
            self.view.setContextMenuPolicy(__import__('PyQt6.QtCore',fromlist=['Qt']).Qt.ContextMenuPolicy.NoContextMenu)
            self.view.setAccessibleName('Windyn sääkartta')
            layout.addWidget(self.view)
            self.status = QLabel('Ladataan Windyn karttaa…')
            self.status.setStyleSheet('color:#dcc2b0;background:#171720;padding:6px;')
            layout.addWidget(self.status)
            self.view.loadStarted.connect(self.loading_started)
            self.view.loadFinished.connect(self.loaded)
        else:
            label=QLabel('Windy-kartta tarvitsee Qt WebEngine -lisäosan.\n'
                'Asenna sovelluksen .deb-paketti tai requirements.txt:n riippuvuudet.\n'
                'Voit avata saman rajauksen selaimeen alla olevasta painikkeesta.' if network else 'Windy · kartta (verkkohaku pois testissä)')
            label.setWordWrap(True); label.setStyleSheet('color:#e7c8b3;padding:24px;')
            layout.addWidget(label)
        self.retry_button = QPushButton('Yritä uudelleen')
        self.retry_button.clicked.connect(self.retry)
        self.retry_button.hide()
        layout.addWidget(self.retry_button)
        self.browser_button = QPushButton('Avaa Windy selaimessa')
        self.browser_button.setStyleSheet('color:#e8cbb9;background:#211b23;border:1px solid #715246;padding:5px;')
        self.browser_button.clicked.connect(self.open_browser)
        self.browser_button.setEnabled(False)
        layout.addWidget(self.browser_button)

    def load(self,place,zoom,layer,*,force=False):
        if self._stopped:
            return
        url=map_url(place,zoom,layer)
        self.url=url
        self.browser_button.setEnabled(True)
        self._force_pending = self._force_pending or force
        # Passive forecast/style synchronisation keeps the error readable;
        # retry comes from the button, explicit refresh or reopening the map.
        self._pending = self._force_pending or url not in (self._loading_url,self._loaded_url,self._failed_url)
        self._schedule_load()

    def _schedule_load(self):
        if (self.view and not self._stopped and self._pending and not self._loading_url
                and self.isVisible() and not self._load_timer.isActive()):
            # Startup can request the map before the host has its final size.
            # Start Chromium on the next event-loop turn, after showing/layout.
            self._load_timer.start(0)

    def _start_load(self):
        if not (self.view and not self._stopped and self._pending
                and not self._loading_url and self.isVisible()):
            return
        self._pending = False
        self._force_pending = False
        self._loading_url = self.url
        self._loaded_url = ''
        self._failed_url = ''
        self.loading_started()
        self.view.load(QUrl(self.url))

    def loading_started(self):
        if self._stopped:
            return
        if not self._loading_url:
            self._loading_url = self.url
            self._loaded_url = ''
        self.status.setText('Ladataan Windyn karttaa…')
        self.status.show()
        self.retry_button.hide()

    def loaded(self,ok):
        if self._stopped or not self._loading_url:
            return
        completed_url = self._loading_url
        self._loading_url = ''
        self._loaded_url = completed_url if ok else ''
        self._failed_url = '' if ok else completed_url
        self.status.setVisible(not ok)
        self.retry_button.setVisible(not ok)
        if not ok:
            self.status.setText('Windyn kartta ei latautunut. Tarkista yhteys, yritä uudelleen tai avaa selaimessa.')
        # One navigation at a time keeps loadFinished tied to its requested URL.
        # Changes made during loading use the latest place and layer afterwards.
        self._schedule_load()

    def retry(self):
        if self._stopped or not self.view or not self.url:
            return
        self._force_pending = True
        self._pending = True
        self._schedule_load()

    def open_browser(self):
        if self.url:
            QDesktopServices.openUrl(QUrl(self.url))

    def showEvent(self,event):
        super().showEvent(event)
        if self.url and self.url not in (self._loading_url,self._loaded_url):
            if self.url == self._failed_url:
                self._force_pending = True
            self._pending = True
        self._schedule_load()

    def hideEvent(self,event):
        self._load_timer.stop()
        super().hideEvent(event)

    def stop(self):
        self._stopped = True
        self._load_timer.stop()
        self._pending = False
        self._force_pending = False
        self._loading_url = ''
        self.retry_button.setEnabled(False)
        if self.view:
            from PyQt6 import sip
            self.view.stop()
            # A profile must outlive its pages; explicitly release in this order.
            sip.delete(self.page)
            sip.delete(self.profile)
            self.view = None

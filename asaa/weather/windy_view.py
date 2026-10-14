"""Official weather pages, retaining provider controls, branding and colours."""
from PyQt6.QtCore import QTimer,QUrl,Qt
from PyQt6.QtGui import QColor,QDesktopServices
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton
from .web_sources import map_url, source_url

try:
    from PyQt6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile,QWebEngineSettings
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None


_SOURCE_LABELS = {
    ('windy','map'): ('Windy','kartta','Windyn karttaa','Windyn kartta','Windyn sääkartta'),
    ('windy','graph'): ('Windy','tuntiennuste','Windyn tuntiennustetta','Windyn tuntiennuste','Windyn tuntiennuste'),
    ('foreca','map'): ('Foreca','sadekartta','Forecan sadekarttaa','Forecan sadekartta','Forecan sadekartta'),
    ('fmi','map'): ('Ilmatieteen laitos','sadekartta','Ilmatieteen laitoksen sadekarttaa',
                    'Ilmatieteen laitoksen sadekartta','Ilmatieteen laitoksen sadekartta'),
}


class WindyView(QWidget):
    def __init__(self,parent=None,*,network=True):
        super().__init__(parent)
        self._source = ('windy','map')
        self._network = network
        self._loading_label = ''
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
            layout.addWidget(self.view)
            self.status = QLabel('Ladataan Windyn karttaa…')
            self.status.setStyleSheet('color:#dcc2b0;background:#171720;padding:6px;')
            layout.addWidget(self.status)
            self.view.loadStarted.connect(self.loading_started)
            self.view.loadFinished.connect(self.loaded)
        else:
            self.fallback_label=QLabel()
            self.fallback_label.setWordWrap(True)
            self.fallback_label.setStyleSheet('color:#e7c8b3;padding:24px;')
            layout.addWidget(self.fallback_label)
        self.retry_button = QPushButton('Yritä uudelleen')
        self.retry_button.clicked.connect(self.retry)
        self.retry_button.hide()
        layout.addWidget(self.retry_button)
        self.browser_button = QPushButton('Avaa Windy selaimessa')
        self.browser_button.setStyleSheet('color:#e8cbb9;background:#211b23;border:1px solid #715246;padding:5px;')
        self.browser_button.clicked.connect(self.open_browser)
        self.browser_button.setEnabled(False)
        layout.addWidget(self.browser_button)
        self._update_source_labels()

    def _update_source_labels(self):
        brand, kind, loading, title, accessible = _SOURCE_LABELS[self._source]
        self.browser_button.setText(f'Avaa {brand} selaimessa')
        if self.view:
            self.view.setAccessibleName(accessible)
            if self._loading_url or not self._failed_url:
                self.status.setText(f'Ladataan {loading}…')
        else:
            self.fallback_label.setText(
                f'{title} tarvitsee Qt WebEngine -lisäosan.\n'
                'Asenna sovelluksen .deb-paketti tai requirements.txt:n riippuvuudet.\n'
                'Voit avata saman näkymän selaimeen alla olevasta painikkeesta.'
                if self._network else f'{brand} · {kind} (verkkohaku pois testissä)')

    def load(self,place,zoom,layer,*,force=False):
        if self._stopped:
            return
        self._source = ('windy','map')
        self._update_source_labels()
        self._load_url(map_url(place,zoom,layer),force=force)

    def _load_url(self,url,*,force=False):
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
        self._loading_label = _SOURCE_LABELS[self._source][3]
        self.loading_started()
        self.view.load(QUrl(self.url))

    def loading_started(self):
        if self._stopped:
            return
        if not self._loading_url:
            self._loading_url = self.url
            self._loaded_url = ''
        self.status.setText(f'Ladataan {_SOURCE_LABELS[self._source][2]}…')
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
            title = self._loading_label or _SOURCE_LABELS[self._source][3]
            self.status.setText(f'{title} ei latautunut. Tarkista yhteys, yritä uudelleen tai avaa selaimessa.')
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


class WeatherWebView(WindyView):
    """Shared map browser and Windy's own map-free hourly forecast embed."""

    def _update_source_labels(self):
        super()._update_source_labels()
        forecast = self._source == ('windy','graph')
        if self.view:
            # Match Windy's own 187 px forecast iframe. A tall viewport also
            # exposes its unused map background beneath the forecast strip.
            self.view.setMaximumHeight(187 if forecast else 16777215)
        self.layout().setAlignment(Qt.AlignmentFlag.AlignTop if forecast else Qt.AlignmentFlag(0))

    def load_source(self,provider,mode,place,zoom=9,layer='temp',foreca_url='',*,force=False):
        if self._stopped:
            return
        url = source_url(provider,mode,place,zoom,layer,foreca_url)
        self._source = (provider,mode)
        self._update_source_labels()
        self._load_url(url,force=force)

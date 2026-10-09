"""Windy's official live embed, retaining controls, attribution and map colours."""
from urllib.parse import urlencode
from PyQt6.QtCore import QUrl
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
            self.view.loadFinished.connect(self.loaded)
        else:
            label=QLabel('Windy-kartta tarvitsee Qt WebEngine -lisäosan.\n'
                'Asenna sovelluksen .deb-paketti tai requirements.txt:n riippuvuudet.\n'
                'Voit avata saman rajauksen selaimeen alla olevasta painikkeesta.' if network else 'Windy · kartta (verkkohaku pois testissä)')
            label.setWordWrap(True); label.setStyleSheet('color:#e7c8b3;padding:24px;')
            layout.addWidget(label)
        if not self.view:
            button=QPushButton('Avaa Windy selaimessa')
            button.setStyleSheet('color:#e8cbb9;background:#211b23;border:1px solid #715246;padding:5px;')
            button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url)))
            layout.addWidget(button)

    def load(self,place,zoom,layer,*,force=False):
        url=map_url(place,zoom,layer)
        if url == self.url and not force: return
        self.url=url
        if self.view:
            self.status.setText('Ladataan Windyn karttaa…'); self.status.show()
            self.view.load(QUrl(self.url))

    def loaded(self,ok):
        self.status.setVisible(not ok)
        if not ok: self.status.setText('Windyn kartta ei latautunut. Tarkista yhteys tai avaa selaimessa.')

    def stop(self):
        if self.view:
            from PyQt6 import sip
            self.view.stop()
            # A profile must outlive its pages; explicitly release in this order.
            sip.delete(self.page)
            sip.delete(self.profile)
            self.view = None

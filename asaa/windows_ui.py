"""Windows settings entry points; desktop themes remain owned by Windows."""
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from .platform_support import windows_time_server


def open_settings(page):
    return QDesktopServices.openUrl(QUrl('ms-settings:' + page))


class WindowsThemeOptions(QWidget):
    def __init__(self, controller):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        hint = QLabel('Järjestelmän teema seuraa Windowsin vaaleaa tai tummaa sovellustilaa ja '
                      'tehosteväriä. Suuren kontrastin värit tulevat aina Windowsista.')
        hint.setWordWrap(True); hint.setObjectName('muted'); layout.addWidget(hint)
        button = QPushButton('Avaa Windowsin teemat ja värit')
        button.clicked.connect(lambda: open_settings('personalization'))
        layout.addWidget(button)

    def load(self): pass
    def reset(self): pass
    def changes(self):
        return {'wallpaper_follow_theme': False, 'icon_follow_theme': False,
                'wallpaper_theme_target': 'desktop'}


class WindowsAppearancePage(QWidget):
    def __init__(self, controller):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(14)
        heading = QLabel('Windowsin oma ulkoasu'); heading.setObjectName('heading'); layout.addWidget(heading)
        hint = QLabel('Valitse työpöydän teema, taustakuva ja kuvakkeet Windowsin omissa asetuksissa. '
                      'Sovelluksen Järjestelmän teema mukautuu Windowsin värivalintaan automaattisesti.')
        hint.setWordWrap(True); layout.addWidget(hint)
        for title, page in [('Teemat', 'themes'), ('Värit ja tumma tila', 'colors'),
                            ('Työpöydän taustakuva', 'personalization-background'),
                            ('Lukitusnäytön taustakuva', 'lockscreen'),
                            ('Suuri kontrasti', 'easeofaccess-highcontrast')]:
            button = QPushButton(title)
            button.clicked.connect(lambda _, target=page: open_settings(target)); layout.addWidget(button)
        layout.addStretch(1)


def add_time_settings(layout):
    hint = QLabel('Kellot käyttävät Windowsin järjestelmäaikaa. Windows huolehtii '
                  'MIKES-synkronoinnista, kun sen Internet-aikapalvelimeksi on asetettu time.mikes.fi.\n\n'
                  'Windowsin tallennettu NTP-palvelinasetus: ' + windows_time_server() +
                  '\nTallennettu asetus ei yksin kerro viimeisen synkronoinnin onnistumisesta.')
    hint.setWordWrap(True); hint.setObjectName('muted'); layout.addWidget(hint)
    button = QPushButton('Avaa Windowsin päivämäärä ja aika')
    button.clicked.connect(lambda: open_settings('dateandtime')); layout.addWidget(button)

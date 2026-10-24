"""Windows settings entry points; desktop themes remain owned by Windows."""
from pathlib import Path
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
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
        self.wallpapers = []
        folder = Path(__file__).resolve().parents[1] / 'assets/wallpapers'
        if (folder / 'catalog.json').is_file():
            from .wallpapers import WallpaperLibrary
            self.wallpapers = WallpaperLibrary(folder, controller.state.path.parent).catalog(folder, 'Sovelluksen teema')
        if self.wallpapers:
            title = QLabel('Sovelluksen omat taustakuvat'); title.setObjectName('eyebrow'); layout.addWidget(title)
            self.wallpaper = QComboBox(); self.wallpaper.setAccessibleName('Windowsin taustakuvavalikoima')
            for item in self.wallpapers: self.wallpaper.addItem(item.title)
            self.preview = QLabel(); self.preview.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.preview.setAccessibleName('Valitun taustakuvan esikatselu')
            layout.addWidget(self.wallpaper); layout.addWidget(self.preview)
            self.wallpaper.currentIndexChanged.connect(self.show_wallpaper)
            explanation = QLabel('Veriyö on staattinen kuvitus. Avaa valittu kuva ja valitse Windowsin '
                                 'kuvankatselussa Aseta työpöydän taustakuvaksi. Voit myös valita '
                                 'kuvan alla avautuvissa Windowsin taustakuva-asetuksissa.')
            explanation.setWordWrap(True); explanation.setObjectName('muted'); layout.addWidget(explanation)
            self.open_wallpaper_button = QPushButton('Avaa valittu taustakuva')
            self.open_wallpaper_button.clicked.connect(self.open_wallpaper)
            layout.addWidget(self.open_wallpaper_button)
            blood_index = next((i for i, item in enumerate(self.wallpapers) if item.theme == 'blood'), 0)
            self.wallpaper.setCurrentIndex(blood_index); self.show_wallpaper()
        for title, page in [('Teemat', 'themes'), ('Värit ja tumma tila', 'colors'),
                            ('Työpöydän taustakuva', 'personalization-background'),
                            ('Lukitusnäytön taustakuva', 'lockscreen'),
                            ('Suuri kontrasti', 'easeofaccess-highcontrast')]:
            button = QPushButton(title)
            button.clicked.connect(lambda _, target=page: open_settings(target)); layout.addWidget(button)
        layout.addStretch(1)

    def show_wallpaper(self):
        item = self.wallpapers[self.wallpaper.currentIndex()]
        self.preview.setPixmap(QPixmap(str(item.path)).scaled(
            640, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.preview.setToolTip(item.title + '\n' + item.description)

    def open_wallpaper(self):
        item = self.wallpapers[self.wallpaper.currentIndex()]
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(item.path)))


def add_time_settings(layout):
    hint = QLabel('Kellot käyttävät Windowsin järjestelmäaikaa. Windows huolehtii '
                  'MIKES-synkronoinnista, kun sen Internet-aikapalvelimeksi on asetettu time.mikes.fi.\n\n'
                  'Windowsin tallennettu NTP-palvelinasetus: ' + windows_time_server() +
                  '\nTallennettu asetus ei yksin kerro viimeisen synkronoinnin onnistumisesta.')
    hint.setWordWrap(True); hint.setObjectName('muted'); layout.addWidget(hint)
    button = QPushButton('Avaa Windowsin päivämäärä ja aika')
    button.clicked.connect(lambda: open_settings('dateandtime')); layout.addWidget(button)

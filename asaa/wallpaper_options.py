"""Shared policy controls for Settings and the wallpaper gallery."""
from PyQt6.QtWidgets import QWidget, QComboBox, QFormLayout, QLabel


class ThemeWallpaperOptions(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller
        form=QFormLayout(self);form.setContentsMargins(0,0,0,0);form.setSpacing(12)
        self.behavior=QComboBox()
        self.behavior.addItem('Vaihda teeman mukana',True)
        self.behavior.addItem('Säilytä valittu taustakuva',False)
        self.behavior.setAccessibleName('Taustakuva teeman vaihtuessa')
        self.target=QComboBox()
        for title,key in [('Työpöytä','desktop'),('Lukitusnäyttö','lock'),('Molemmat','both')]:
            self.target.addItem(title,key)
        self.target.setAccessibleName('Teemataustan kohde')
        self.behavior.currentIndexChanged.connect(self.update_enabled)
        form.addRow('Taustakuva teeman vaihtuessa',self.behavior)
        form.addRow('Teemataustan kohde',self.target)
        hint=QLabel('Oletuksena työpöydän tausta seuraa teemaa. Valinta tulee voimaan tallennettaessa '
                    'ja vaikuttaa seuraavaan teemanvaihtoon. Käynnistys ja kellojen kierto eivät vaihda taustaa.')
        hint.setObjectName('muted');hint.setWordWrap(True);form.addRow('',hint)
        self.load()

    def load(self):
        options=self.controller.options
        self.behavior.setCurrentIndex(self.behavior.findData(options['wallpaper_follow_theme']))
        self.target.setCurrentIndex(self.target.findData(options['wallpaper_theme_target']))
        desktop,dia=self.controller.wallpapers.capabilities()
        for key in ('lock','both'):
            self.target.model().item(self.target.findData(key)).setEnabled(dia)
        self.update_enabled()

    def update_enabled(self):self.target.setEnabled(bool(self.behavior.currentData()))

    def changes(self):
        return {'wallpaper_follow_theme':self.behavior.currentData(),
                'wallpaper_theme_target':self.target.currentData()}

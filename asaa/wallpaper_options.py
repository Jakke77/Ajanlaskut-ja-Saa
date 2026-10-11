"""Shared policy controls for Settings and the wallpaper gallery."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QComboBox, QFormLayout, QLabel


class ThemeWallpaperOptions(QWidget):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.loaded_values={}
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
        self.support=QLabel();self.support.setObjectName('muted');self.support.setWordWrap(True)
        form.addRow('',self.support)
        self.load()

    def load(self):
        options=self.controller.options
        # External settings changes refresh only controls that still match their
        # last loaded value. Uncommitted policy choices remain editable drafts.
        for control,key in ((self.behavior,'wallpaper_follow_theme'),(self.target,'wallpaper_theme_target')):
            if key not in self.loaded_values or control.currentData()==self.loaded_values[key]:
                blocked=control.blockSignals(True)
                control.setCurrentIndex(control.findData(options[key]))
                control.blockSignals(blocked)
            self.loaded_values[key]=options[key]
        desktop,dia=self.controller.wallpapers.capabilities()
        for key in ('lock','both'):
            index=self.target.findData(key)
            title='Lukitusnäyttö' if key=='lock' else 'Molemmat'
            self.target.setItemText(index,title if dia else title+' · vaatii Dia Wall 77')
            self.target.model().item(index).setEnabled(dia)
            self.target.setItemData(index,'' if dia else
                'Erillinen lukituskuva tarvitsee asennetun ja käytössä olevan Dia Wall 77 -lisäosan.',
                Qt.ItemDataRole.ToolTipRole)
        self.support.setText('Dia Wall 77 käytössä: työpöydälle ja lukitusnäytölle voi valita eri kuvat.'
            if dia else ('GNOMEn lukitusnäyttö käyttää työpöydän taustaa. Valitse Työpöytä vaihtaaksesi saman kuvan '
                'myös lukitusnäyttöön. Erillinen lukituskuva tarvitsee käytössä olevan Dia Wall 77 -lisäosan.'
                if desktop else 'Taustakuvan vaihto tarvitsee GNOME-työpöydän.'))
        self.update_enabled()

    def update_enabled(self):
        following=bool(self.behavior.currentData());self.target.setEnabled(following)
        self.target.setToolTip('Valitse kohde teeman mukana vaihtuville taustakuville.' if following else
            'Kohde on käytössä, kun valitaan Vaihda teeman mukana. Säilytä valittu taustakuva ei vaihda taustaa.')

    def changes(self):
        return {'wallpaper_follow_theme':self.behavior.currentData(),
                'wallpaper_theme_target':self.target.currentData()}

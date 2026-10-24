"""Shared desktop policies and explicit icon actions for both appearance pages."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QComboBox, QFormLayout, QLabel,
    QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox)
from .theme import THEME_NAMES
from .icon_themes import THEMES as ICON_THEMES


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
        self.icon_behavior=QComboBox()
        self.icon_behavior.addItem('Säilytä nykyiset kuvakkeet',False)
        self.icon_behavior.addItem('Vaihda teeman mukana',True)
        self.icon_behavior.setAccessibleName('Kuvakkeet teeman vaihtuessa')
        self.behavior.currentIndexChanged.connect(self.update_enabled)
        form.addRow('Taustakuva teeman vaihtuessa',self.behavior)
        form.addRow('Teemataustan kohde',self.target)
        hint=QLabel('Oletuksena työpöydän tausta seuraa teemaa. Valinta tulee voimaan tallennettaessa '
                    'ja vaikuttaa seuraavaan teemanvaihtoon. Käynnistys ja kellojen kierto eivät vaihda taustaa.')
        hint.setObjectName('muted');hint.setWordWrap(True);form.addRow('',hint)
        self.support=QLabel();self.support.setObjectName('muted');self.support.setWordWrap(True)
        form.addRow('',self.support)
        form.addRow('Kuvakkeet teeman vaihtuessa',self.icon_behavior)
        icon_hint=QLabel('Kuvakkeiden vaihto on vapaaehtoinen. Valinta tallentuu yhdessä taustakuvan '
            'teemanvaihdon valinnan kanssa ja seuraa sovelluksen yhteistä teemaa.')
        icon_hint.setObjectName('muted');icon_hint.setWordWrap(True);form.addRow('',icon_hint)
        self.icon_support=QLabel();self.icon_support.setObjectName('muted');self.icon_support.setWordWrap(True)
        form.addRow('',self.icon_support)
        controller.settings_changed.connect(self.load)
        self.load()

    def load(self):
        options=self.controller.options
        # External settings changes refresh only controls that still match their
        # last loaded value. Uncommitted policy choices remain editable drafts.
        for control,key in ((self.behavior,'wallpaper_follow_theme'),(self.target,'wallpaper_theme_target'),
                            (self.icon_behavior,'icon_follow_theme')):
            value=options.get(key,False)
            if key not in self.loaded_values or control.currentData()==self.loaded_values[key]:
                blocked=control.blockSignals(True)
                control.setCurrentIndex(control.findData(value))
                control.blockSignals(blocked)
            self.loaded_values[key]=value
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
        icons_available=self.controller.icon_themes.available()
        self.icon_behavior.model().item(self.icon_behavior.findData(True)).setEnabled(icons_available)
        self.icon_support.setText('' if icons_available else 'Kuvakkeiden vaihto tarvitsee GNOME-työpöydän.')
        self.icon_support.setVisible(not icons_available)
        self.update_enabled()

    def update_enabled(self):
        following=bool(self.behavior.currentData());self.target.setEnabled(following)
        self.target.setToolTip('Valitse kohde teeman mukana vaihtuville taustakuville.' if following else
            'Kohde on käytössä, kun valitaan Vaihda teeman mukana. Säilytä valittu taustakuva ei vaihda taustaa.')

    def changes(self):
        return {'wallpaper_follow_theme':self.behavior.currentData(),
                'wallpaper_theme_target':self.target.currentData(),
                'icon_follow_theme':self.icon_behavior.currentData()}

    def reset(self):
        self.behavior.setCurrentIndex(0);self.target.setCurrentIndex(0)
        self.icon_behavior.setCurrentIndex(self.icon_behavior.findData(False))


class IconThemeActions(QWidget):
    """Immediate desktop operations never save either page's policy drafts."""
    def __init__(self,controller):
        super().__init__();self.controller=controller
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(9)
        heading=QLabel('SOVELLUSKUVAKKEET');heading.setObjectName('eyebrow');layout.addWidget(heading)
        hint=QLabel('Sovelluksen omat kuvaketeemat työpöydälle ja sovellusvalikkoon. '
            'Nykyisen teeman kuvakkeet voi ottaa käyttöön myös ilman automaattista vaihtoa.')
        hint.setObjectName('muted');hint.setWordWrap(True);layout.addWidget(hint)
        self.current=QLabel();self.current.setObjectName('muted');self.current.setWordWrap(True)
        layout.addWidget(self.current)
        self.apply_button=QPushButton('Käytä nykyisen teeman kuvakkeita')
        self.apply_button.setToolTip('Ottaa käyttöön sovelluksen tallennetun yhteisen teeman kuvakkeet.')
        self.apply_button.clicked.connect(self.apply_current_theme);layout.addWidget(self.apply_button)
        self.all_apps=QCheckBox('Väritä myös muut sovellukset yleiskuvakkeilla')
        self.all_apps.setToolTip('Muut sovellukset saavat käyttötarkoitusta vastaavan kuvakkeen '
            'oman tunnuksensa sijaan. Valinta koskee Asenna ja korjaa -painiketta.')
        layout.addWidget(self.all_apps)
        self.install_button=QPushButton('Asenna ja korjaa sovelluskuvakkeet')
        self.install_button.setToolTip('Asentaa kaikki sovelluksen kuvaketeemat ja korjaa myös '
            'Firefoxin, Thunderbirdin ja GIMPin kaltaisten sovellusten kuvakkeet.')
        self.install_button.clicked.connect(self.install);layout.addWidget(self.install_button)
        self.status=QLabel();self.status.setObjectName('status');self.status.setWordWrap(True)
        self.status.setAccessibleName('Kuvaketoiminnon palaute');layout.addWidget(self.status)
        self.default_button=QPushButton('Käytä järjestelmän oletuskuvakkeita')
        self.default_button.setToolTip('Ottaa käyttöön tämän järjestelmän oletuskuvaketeeman, '
            'palauttaa sovelluksen muuttamat sovelluskuvakkeet ja poistaa kuvakkeiden '
            'automaattisen teemanvaihdon käytöstä.')
        self.default_button.clicked.connect(self.use_system_default);layout.addWidget(self.default_button)
        restore=QHBoxLayout()
        self.restore_button=QPushButton('Palauta edellinen kuvaketeema')
        self.restore_button.setToolTip('Palauttaa aiemman työpöydän kuvaketeeman ja poistaa '
            'kuvakkeiden automaattisen teemanvaihdon käytöstä.')
        self.restore_button.clicked.connect(self.restore_theme);restore.addWidget(self.restore_button)
        self.restore_launchers_button=QPushButton('Palauta sovelluskuvakkeet')
        self.restore_launchers_button.setToolTip('Peruu Asenna ja korjaa -painikkeella tehdyt '
            'sovellusten kuvakevalinnat.')
        self.restore_launchers_button.clicked.connect(self.restore_launchers)
        restore.addWidget(self.restore_launchers_button);layout.addLayout(restore)
        controller.settings_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        manager=self.controller.icon_themes
        available=manager.available()
        self.apply_button.setEnabled(available)
        self.default_button.setEnabled(manager.default_available())
        self.restore_button.setEnabled(available and manager.backup.is_file())
        self.restore_launchers_button.setEnabled(manager.launcher_backup_exists())
        selected=manager.current() if available else ''
        names={folder:THEME_NAMES[key] for key,folder in ICON_THEMES.items()}
        self.current.setText('Käytössä: '+names.get(selected,selected or 'nykyiset työpöydän kuvakkeet')
            if available else 'Kuvakkeiden vaihto tarvitsee GNOME-työpöydän. Teemat voi silti asentaa.')

    def perform(self,action,success):
        try:
            result=action()
            self.status.setText(success(result))
        except (OSError,ValueError,KeyError,TypeError) as error:self.status.setText(str(error))
        self.refresh()

    def apply_current_theme(self):
        name=THEME_NAMES[self.controller.options['theme']]
        self.perform(self.controller.set_icon_theme,lambda _:name+'-kuvakkeet käytössä.')

    def install(self):
        def feedback(result):
            changed,unsupported=result
            message=f'Kuvaketeemat asennettu. Korjattuja sovelluskuvakkeita: {changed}. '
            if unsupported:message+='Osa sovelluksista säilytti oman kuvakkeensa. '
            return message+'Valitse Käytä nykyisen teeman kuvakkeita, jos teema ei ole vielä käytössä.'
        self.perform(lambda:self.controller.install_icon_themes(all_apps=self.all_apps.isChecked()),feedback)

    def restore_theme(self):
        self.perform(self.controller.restore_icon_theme,lambda _:
            'Edellinen kuvaketeema palautettu. Kuvakkeiden automaattinen vaihto poistettu käytöstä.')

    def use_system_default(self):
        self.perform(self.controller.use_system_default_icons,lambda _:
            'Järjestelmän oletuskuvakkeet käytössä: '+self.controller.icon_themes.current()+
            '. Kuvakkeiden automaattinen vaihto poistettu käytöstä.')

    def restore_launchers(self):
        self.perform(self.controller.restore_icon_launchers,lambda _:'Sovellusten aiemmat kuvakevalinnat palautettu.')

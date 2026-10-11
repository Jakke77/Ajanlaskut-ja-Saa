"""Theme-matched wallpaper gallery, also reachable from every desktop widget."""
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, QUrl, QItemSelectionModel
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices, QImageReader
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog,
    QComboBox, QSpinBox, QCheckBox, QMessageBox, QSizePolicy)
from .ui import label, button, card
from .wallpapers import image_size
from .theme import THEME_NAMES


class WallpapersPage(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.manager = controller.wallpapers
        self.items = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(14)
        layout.addWidget(label('TYÖPÖYTÄ JA LUKITUSNÄYTTÖ', 'eyebrow'))
        layout.addWidget(label('Oma taivas, oma taustakuva', 'heading'))
        layout.addWidget(label('Kuparin, Hallan ja Ubuntun taustakuvat sekä oma teema-repo samassa galleriassa. '
            'Erillinen lukituskuva on käytettävissä Dia Wall 77 -lisäosan kanssa.', 'muted', True))
        tools = QHBoxLayout()
        tools.addWidget(button('Lisää omia kuvia…', self.import_images))
        tools.addWidget(button('Valitse teema-repon kansio…', self.choose_folder))
        tools.addWidget(button('Päivitä galleria', self.reload))
        layout.addLayout(tools)
        self.folder = label('', 'muted', True); layout.addWidget(self.folder)
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.ViewMode.IconMode)
        self.gallery.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.gallery.setMovement(QListWidget.Movement.Static)
        self.gallery.setIconSize(QSize(230, 130)); self.gallery.setGridSize(QSize(265, 185))
        self.gallery.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.gallery.setMinimumHeight(210)
        self.gallery.setMaximumHeight(410)
        self.gallery.setAccessibleName('Taustakuvat')
        self.gallery.currentItemChanged.connect(self.preview_selected)
        self.gallery.itemSelectionChanged.connect(self.selection_changed)
        row = QHBoxLayout(); row.setSpacing(18)
        self.gallery.setMinimumWidth(275); self.gallery.setMaximumWidth(330)
        row.addWidget(self.gallery, 1)
        self.preview = QLabel()
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(180); self.preview.setMaximumHeight(280)
        self.preview.setAccessibleName('Valitun taustakuvan esikatselu')
        details = QWidget();details.setMinimumWidth(0);detail_layout = QVBoxLayout(details)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.addWidget(self.preview)
        self.description = label('', 'muted', True); detail_layout.addWidget(self.description)
        row.addWidget(details, 2); layout.addLayout(row)
        frame, content = card()
        from .wallpaper_options import ThemeWallpaperOptions
        self.theme_options=ThemeWallpaperOptions(controller)
        content.addWidget(self.theme_options)
        self.status = label('', 'status', True)
        self.status.setAccessibleName('Taustakuvatoiminnon palaute')
        content.addWidget(self.status)
        policy_actions=QHBoxLayout()
        self.save_theme_button=button('Tallenna teemanvaihdon valinta',self.save_theme_policy)
        self.current_theme_button=button('',self.apply_current_theme)
        self.current_theme_button.setToolTip('Asettaa sovelluksen nykyisen teeman oletustaustan. '
            'Galleriassa valittu kuva asetetaan Työpöydän taustaksi -painikkeella.')
        policy_actions.addWidget(self.save_theme_button)
        policy_actions.addWidget(self.current_theme_button)
        content.addLayout(policy_actions)
        controls = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItem('Yksi taustakuva', 'single')
        self.mode.addItem('Vaihtuvat kuvat · valitut kuvat', 'slideshow')
        self.mode.setAccessibleName('Taustakuvien vaihtotapa')
        self.mode.setCurrentIndex(self.mode.findData(controller.options['wallpaper_mode']))
        self.interval = QSpinBox(); self.interval.setRange(1, 77); self.interval.setSuffix(' min')
        self.interval.setAccessibleName('Taustakuvien vaihtoväli')
        self.interval.setValue(controller.options['wallpaper_interval'])
        self.shuffle = QCheckBox('Satunnainen järjestys')
        self.shuffle.setChecked(controller.options['wallpaper_shuffle'])
        controls.addWidget(self.mode, 1); controls.addWidget(self.interval); controls.addWidget(self.shuffle)
        content.addLayout(controls)
        self.hint = label('', 'muted', True); content.addWidget(self.hint)
        actions = QGridLayout()
        self.desktop_button = button('Työpöydän taustaksi', lambda: self.apply('desktop'), True)
        self.lock_button = button('Lukitusnäytön taustaksi', lambda: self.apply('lock'))
        self.both_button = button('Molempiin', lambda: self.apply('both'))
        actions.addWidget(self.desktop_button, 0, 0); actions.addWidget(self.lock_button, 0, 1)
        actions.addWidget(self.both_button, 0, 2); content.addLayout(actions)
        self.current = label('', 'muted', True); content.addWidget(self.current)
        self.support = label('', 'muted', True); content.addWidget(self.support)
        self.restore_button = button('Palauta edelliset taustat', self.restore)
        content.addWidget(self.restore_button)
        layout.addWidget(frame)
        bottom = QHBoxLayout()
        bottom.addWidget(button('Avaa teemakansio', self.open_folder))
        bottom.addWidget(button('Käytä vain sovelluksen galleriaa', self.clear_folder))
        bottom.addStretch(1); layout.addLayout(bottom)
        layout.addWidget(label('Kuvan valinta galleriassa ei vielä muuta taustakuvaa. '
            'Lukituksen toimintaa, salasanaa tai Super+L-pikanäppäintä ei muuteta.', 'muted', True))
        layout.addStretch(1)
        self.mode.currentIndexChanged.connect(self.selection_changed)
        controller.settings_changed.connect(self.sync_folder)
        self.reload()

    def selected(self):
        return [self.items[self.gallery.row(item)] for item in self.gallery.selectedItems()]

    def sync_folder(self):
        self.theme_options.load();self.refresh_current()
        directory = self.controller.options['wallpaper_directory']
        if getattr(self, 'loaded_folder', None) != directory: self.reload()

    def reload(self):
        previous = {str(item.path) for item in self.selected()}
        self.loaded_folder = self.controller.options['wallpaper_directory']
        self.folder.setText('Teema-repo: ' + self.loaded_folder if self.loaded_folder
                            else 'Sovelluksen Kupari-, Halla- ja Ubuntu-galleria · voit liittää myös erillisen teema-repon.')
        self.gallery.blockSignals(True)
        try:
            self.items = self.manager.library.list(self.loaded_folder)
            self.status.setText('')
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.items = self.manager.library.catalog(self.manager.library.bundled, 'Sovelluksen teema')
            self.status.setText(str(error) + ' Sovelluksen omat kuvat ovat yhä käytettävissä.')
        self.gallery.clear()
        for wallpaper in self.items:
            reader = QImageReader(str(wallpaper.path))
            reader.setAutoTransform(True); reader.setScaledSize(QSize(230, 130))
            pixmap = QPixmap.fromImage(reader.read())
            icon = QIcon(pixmap)
            icon.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.On)
            icon.addPixmap(pixmap, QIcon.Mode.Selected, QIcon.State.On)
            icon.addPixmap(pixmap, QIcon.Mode.Selected, QIcon.State.Off)
            item = QListWidgetItem(icon, wallpaper.title)
            item.setToolTip(wallpaper.description or str(wallpaper.path))
            self.gallery.addItem(item)
            if str(wallpaper.path) in previous: item.setSelected(True)
        self.gallery.blockSignals(False)
        if self.items:
            selected = self.gallery.selectedItems()
            if selected:
                self.gallery.setCurrentItem(selected[0], QItemSelectionModel.SelectionFlag.NoUpdate)
            else: self.gallery.setCurrentItem(self.gallery.item(0))
            self.preview_selected(self.gallery.currentItem())
        else: self.preview.clear(); self.description.setText('Lisää ensimmäinen taustakuva.')
        self.refresh_current()

    def preview_selected(self, current, previous=None):
        if not current: return
        item = self.items[self.gallery.row(current)]
        try:
            width, height = image_size(item.path)
            reader = QImageReader(str(item.path)); reader.setAutoTransform(True)
            size = QSize(width, height); size.scale(760, 250, Qt.AspectRatioMode.KeepAspectRatio)
            reader.setScaledSize(size)
            self.preview.setPixmap(QPixmap.fromImage(reader.read()))
            theme = THEME_NAMES.get(item.theme, 'Oma tausta')
            self.description.setText(f'{item.title} · {theme} · {width} × {height} · {item.source}\n{item.description}')
        except (OSError, ValueError) as error:
            self.preview.clear(); self.description.setText(str(error))

    def selection_changed(self):
        self.update_selection(*self.manager.capabilities())

    def update_selection(self, desktop, dia):
        rotating = self.mode.currentData() == 'slideshow'
        index=self.mode.findData('slideshow')
        self.mode.setItemText(index,'Vaihtuvat kuvat · valitut kuvat' if dia else
                             'Vaihtuvat kuvat · vaatii Dia Wall 77')
        self.mode.setItemData(index,'' if dia else 'Vaihtuvat taustakuvat tarvitsevat käytössä olevan Dia Wall 77 -lisäosan.',
                              Qt.ItemDataRole.ToolTipRole)
        self.interval.setEnabled(rotating); self.shuffle.setEnabled(rotating)
        self.hint.setText(f'{len(self.selected())} kuvaa valittu. ' + (
            'Valitse vähintään kaksi kuvaa Ctrl- tai Shift-näppäimellä. Vaihtoväli koskee vain taustakuvia.'
            if rotating else 'Valitse yksi kuva ja sen jälkeen kohde.'))
        if rotating and not dia:
            self.hint.setText(self.hint.text()+' Vaihtuvat kuvat eivät ole käytettävissä ilman Dia Wall 77 -lisäosaa.')
        valid = len(self.selected()) >= 2 if rotating else len(self.selected()) == 1
        self.desktop_button.setEnabled(desktop and valid and (not rotating or dia))
        self.lock_button.setEnabled(dia and valid); self.both_button.setEnabled(dia and valid)
        reason='Erillinen lukituskuva tarvitsee käytössä olevan Dia Wall 77 -lisäosan.'
        self.lock_button.setToolTip('Aseta valitut kuvat vain lukitusnäytölle.' if dia else reason)
        self.both_button.setToolTip('Aseta valitut kuvat työpöydälle ja lukitusnäytölle.' if dia else reason)

    def refresh_current(self):
        name=THEME_NAMES[self.controller.options['theme']]
        self.current_theme_button.setText('Aseta '+name+'-teeman tausta')
        desktop, dia = self.manager.capabilities()
        self.current.setText('Työpöytä: ' + self.manager.current('desktop',(desktop,dia)) +
                            '\nLukitusnäyttö: ' + self.manager.current('lock',(desktop,dia)))
        self.support.setText('Dia Wall 77 käytössä · erilliset taustat ja vaihtuvat kuvat ovat käytettävissä.'
            if dia else ('Työpöydän taustan voi vaihtaa. Erillinen lukituskuva ja diaesitys tarvitsevat '
                'käytössä olevan Dia Wall 77 -lisäosan. Ilman sitä GNOMEn lukitusnäyttö seuraa työpöydän taustaa.'
                if desktop else self.manager.error or 'Taustakuvan vaihto tarvitsee GNOME-työpöydän.'))
        self.restore_button.setEnabled(self.manager.backup.is_file())
        self.update_selection(desktop,dia)

    def apply(self, target):
        try:
            choices = self.selected()
            if not choices: raise ValueError('Valitse ensin kuva.')
            mode = self.mode.currentData()
            self.controller.set_wallpaper([item.path for item in choices],target,mode,
                                          self.interval.value(),self.shuffle.isChecked())
            name = {'desktop': 'Työpöydän tausta', 'lock': 'Lukitusnäytön tausta', 'both': 'Molemmat taustat'}[target]
            self.status.setText(name + (' vaihtuu nyt valituista kuvista.' if mode == 'slideshow'
                                       else ' asetettu: ' + choices[0].title))
        except (OSError, ValueError, KeyError, TypeError) as error: self.status.setText(str(error))
        self.refresh_current()

    def save_theme_policy(self):
        try:
            self.controller.configure(self.theme_options.changes())
            self.status.setText('Tallennettu — tausta seuraa seuraavaa teemanvaihtoa.'
                if self.controller.options['wallpaper_follow_theme'] else
                'Tallennettu — valittu tausta säilyy, vaikka teema vaihtuu.')
        except (OSError,ValueError,KeyError,TypeError) as error:self.status.setText(str(error))

    def apply_current_theme(self):
        try:
            picture=self.manager.library.for_theme(self.controller.options['theme'])
            target=self.theme_options.target.currentData()
            self.controller.set_wallpaper([picture.path],target)
            self.status.setText('Teeman tausta asetettu: '+picture.title)
        except (OSError,ValueError,KeyError,TypeError) as error:self.status.setText(str(error))
        self.refresh_current()

    def restore(self):
        if QMessageBox.question(self, 'Palauta taustakuvat',
                'Palautetaanko edellisen taustakuvavalinnan kuvat ja vaihtotapa?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        try: self.manager.restore(); self.status.setText('Edelliset taustakuvat ja vaihtotapa palautettu.')
        except (OSError, ValueError, KeyError, TypeError) as error: self.status.setText(str(error))
        self.refresh_current()

    def import_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Lisää omia taustakuvia', str(Path.home() / 'Kuvat'),
                                              'Taustakuvat (*.png *.jpg *.jpeg *.webp *.bmp)')
        if not paths: return
        errors = []
        for path in paths:
            try: self.manager.library.add(path)
            except (OSError, ValueError) as error: errors.append(Path(path).name + ': ' + str(error))
        self.reload()
        self.status.setText('\n'.join(errors) if errors else 'Kuvat lisätty. Alkuperäisiä tiedostoja ei muutettu.')

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, 'Valitse teema-repon kansio',
                self.controller.options['wallpaper_directory'] or str(Path.home() / 'Ohjelmat'))
        if not path: return
        try:
            self.manager.library.catalog(path, 'Teema-repo')
            self.controller.state.configure({'wallpaper_directory': path})
            self.controller.settings_changed.emit()
        except (OSError, ValueError, TypeError) as error: self.status.setText(str(error))

    def clear_folder(self):
        try:
            self.controller.state.configure({'wallpaper_directory': ''})
            self.controller.settings_changed.emit()
        except OSError as error: self.status.setText(str(error))

    def open_folder(self):
        path = self.controller.options['wallpaper_directory'] or str(self.manager.library.bundled)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def showEvent(self, event):
        super().showEvent(event);self.theme_options.load();self.refresh_current()

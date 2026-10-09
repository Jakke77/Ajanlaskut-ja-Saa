"""One place for calendar rotation, clock composition and a read-only live preview."""
import copy
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QComboBox, QSpinBox, QCheckBox, QLabel
from .clock_config import SYSTEMS, PROFILE_KEYS, CLOCK_TITLES, FIELD_LABELS
from .theme import CALENDAR_THEME_NAMES
from .widgets import DesktopSurface, WIDGET_LABELS
from .ui import label, button, card

class ClocksPage(QWidget):
    def __init__(self, controller):
        super().__init__();self.controller = controller
        self.loading = True;self.dirty = False;self.editing = 'combined'
        self.profiles = copy.deepcopy(controller.options['clock_profiles'])
        layout = QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(12)
        layout.addWidget(label('AJANLASKUWIDGETIT', 'eyebrow'))
        heading = QHBoxLayout();heading.addWidget(label('Yksi kello, monta ajanlaskua', 'heading'));heading.addStretch(1)
        heading.addWidget(button('Tallenna', self.save, True));layout.addLayout(heading)
        layout.addWidget(label('Sama paikallinen kellonaika. Ajanlaskun päivämäärä ja oma teema vaihtuvat. Sääwidget säilyy erillisenä ja ennallaan.', 'muted', True))
        row = QHBoxLayout()
        self.enabled = QCheckBox('Näytä yhteinen kellowidget työpöydällä')
        self.enabled.toggled.connect(self.set_visible);row.addWidget(self.enabled)
        row.addStretch(1);layout.addLayout(row)
        layout.addWidget(button('Korvaa erilliset kellot yhteisellä widgetillä', self.combine))
        split = QHBoxLayout();split.setSpacing(18);left = QVBoxLayout();split.addLayout(left, 1)
        frame, content = card();content.addWidget(label('AJANLASKUN VAIHTO', 'eyebrow'));form = QFormLayout()
        self.mode = QComboBox()
        for title, key in [('Pidä valittu ajanlasku','fixed'), ('Vaihda järjestyksessä','cycle'), ('Vaihda satunnaisesti','random')]: self.mode.addItem(title, key)
        self.system = QComboBox()
        for key in SYSTEMS: self.system.addItem(CLOCK_TITLES[key], key)
        self.interval = QSpinBox();self.interval.setRange(1,3600);self.interval.setSuffix(' sekuntia')
        self.theme = QComboBox();self.theme.addItem('Ajanlaskun oma teema', 'calendar');self.theme.addItem('Yhteinen Kupari / Halla', 'shared')
        for title, control in [('Vaihtotapa',self.mode),('Valittu ajanlasku',self.system),('Vaihtoväli',self.interval),('Kellon teema',self.theme)]:form.addRow(title,control)
        content.addLayout(form)
        self.pool = {};pool_row = QHBoxLayout()
        for key in SYSTEMS:
            check = QCheckBox(CLOCK_TITLES[key]);pool_row.addWidget(check);self.pool[key] = check
            check.toggled.connect(self.changed)
        content.addWidget(label('Vaihtoon osallistuvat ajanlaskut', 'muted'));content.addLayout(pool_row)
        content.addWidget(label('Kupari · Varjoaika / Astraali · Tähtiaika / Aamunkajo · Gregoriaaninen. Kellon paikka ja koko eivät muutu ajanlaskun vaihtuessa.', 'muted', True))
        left.addWidget(frame)
        frame, content = card();content.addWidget(label('NÄKYVÄ SISÄLTÖ', 'eyebrow'))
        self.target = QComboBox()
        for key in PROFILE_KEYS: self.target.addItem(WIDGET_LABELS[key], key)
        self.target.currentIndexChanged.connect(self.change_target);content.addWidget(self.target)
        grid = QGridLayout();self.fields = {}
        for index, (key, title) in enumerate(FIELD_LABELS.items()):
            check = QCheckBox(title);self.fields[key] = check;grid.addWidget(check,index//2,index%2);check.toggled.connect(self.changed)
        content.addLayout(grid)
        content.addWidget(label('Sisältövalinnat tallentuvat erikseen yhteiselle widgetille ja vanhoille erillisille kelloille. Kuun- ja kierronvaiheet ovat kuvitteellisia, paitsi gregoriaanisen ISO-viikko.', 'muted', True))
        content.addWidget(button('Tekstikoko ja fontti →', lambda:controller.open_page('settings')))
        content.addWidget(button('Kuu-, aurinko- ja kuu–aurinkokalenterit →', self.open_extras))
        left.addWidget(frame);left.addStretch(1)
        preview_frame, preview_content = card();preview_frame.setFixedWidth(370)
        preview_content.addWidget(label('ESIKATSELU', 'eyebrow'))
        self.preview_system = QComboBox()
        for key in SYSTEMS:self.preview_system.addItem(CLOCK_TITLES[key],key)
        preview_content.addWidget(self.preview_system)
        self.preview_label = QLabel();self.preview_label.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        preview_content.addWidget(self.preview_label)
        self.preview_caption = label('', 'muted', True);preview_content.addWidget(self.preview_caption);preview_content.addStretch(1)
        split.addWidget(preview_frame);layout.addLayout(split)
        self.status = label('Valinnat otetaan käyttöön tallentamalla.', 'muted', True);layout.addWidget(self.status)
        layout.addWidget(button('Tallenna kelloasetukset', self.save, True))
        self.preview_widget = DesktopSurface(controller, 'combined', preview=True, parent=self)
        self.preview_widget.hide()
        for control in (self.mode,self.system,self.theme):control.currentIndexChanged.connect(self.changed)
        self.interval.valueChanged.connect(self.changed)
        self.preview_system.currentIndexChanged.connect(self.refresh_preview)
        controller.clock_changed.connect(self.refresh_preview)
        controller.daily.changed.connect(self.refresh_preview)
        controller.settings_changed.connect(self.sync)
        self.load()

    def load(self):
        self.loading = True
        options = self.controller.options
        self.profiles = copy.deepcopy(options['clock_profiles'])
        for control, key in [(self.mode,'time_mode'),(self.system,'time_system'),(self.theme,'time_theme')]:control.setCurrentIndex(control.findData(options[key]))
        self.interval.setValue(options['time_interval'])
        for key, check in self.pool.items():check.setChecked(key in options['time_systems'])
        self.enabled.blockSignals(True);self.enabled.setChecked(options['widgets']['combined']);self.enabled.blockSignals(False)
        for key, check in self.fields.items():check.setChecked(self.profiles[self.editing][key])
        self.loading = False;self.dirty = False;self.refresh_preview()

    def sync(self):
        self.enabled.blockSignals(True);self.enabled.setChecked(self.controller.options['widgets']['combined']);self.enabled.blockSignals(False)
        if not self.dirty:self.load()
        else:self.refresh_preview()

    def set_visible(self, enabled):
        if not self.loading:self.controller.set_widget('combined',enabled)

    def combine(self):
        try:self.controller.combine_clocks();self.status.setText('Erilliset kellot on piilotettu. Niiden asetukset ja sijainnit säilyvät.')
        except OSError as error:self.status.setText(str(error))

    def changed(self):
        if self.loading:return
        self.dirty = True;self.status.setText('Esikatselu — tallenna, kun valinnat ovat sopivat.');self.refresh_preview()

    def change_target(self):
        if self.loading:return
        self.profiles[self.editing] = {key:check.isChecked() for key,check in self.fields.items()}
        self.editing = self.target.currentData();self.loading = True
        for key, check in self.fields.items():check.setChecked(self.profiles[self.editing][key])
        self.loading = False;self.refresh_preview()

    def refresh_preview(self):
        if self.loading:return
        fixed = self.mode.currentData() == 'fixed'
        self.system.setEnabled(fixed);self.interval.setEnabled(not fixed)
        for check in self.pool.values():check.setEnabled(not fixed)
        system = self.editing if self.editing in SYSTEMS else (self.system.currentData() if fixed else self.preview_system.currentData())
        self.preview_system.setEnabled(self.editing=='combined' and not fixed)
        self.preview_widget.profile_override = {key:check.isChecked() for key,check in self.fields.items()}
        self.preview_widget.system_override = system
        self.preview_widget.theme_override = self.theme.currentData()
        self.preview_widget.apply_options()
        pixmap = self.preview_widget.grab()
        if pixmap.width() > 324:pixmap = pixmap.scaledToWidth(324, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(pixmap)
        name = CALENDAR_THEME_NAMES[system] if self.theme.currentData()=='calendar' else 'Yhteinen teema'
        self.preview_caption.setText(f'{CLOCK_TITLES[system]} · {name}\nEsikatselu ei muuta työpöydän widgettiä. Sää käyttää yhteistä ennustetta, jos se on saatavilla.')

    def save(self):
        self.profiles[self.editing] = {key:check.isChecked() for key,check in self.fields.items()}
        changes = {'time_mode':self.mode.currentData(), 'time_system':self.system.currentData(),
            'time_interval':self.interval.value(), 'time_theme':self.theme.currentData(),
            'time_systems':[key for key,check in self.pool.items() if check.isChecked()], 'clock_profiles':copy.deepcopy(self.profiles)}
        try:
            self.controller.configure(changes);self.dirty = False;self.load();self.status.setText('Tallennettu — ajanlaskut, sisältö ja teema on otettu käyttöön.')
        except (ValueError,OSError) as error:self.status.setText(str(error))

    def open_extras(self):
        from .almanac_ui import AlmanacDialog
        AlmanacDialog(self.controller,self).exec()

    def showEvent(self, event):
        if not self.dirty:self.load()
        super().showEvent(event)

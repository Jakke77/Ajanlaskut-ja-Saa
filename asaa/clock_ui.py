"""One place for calendar rotation, clock composition and a read-only live preview."""
import copy
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QComboBox, QSpinBox, QCheckBox, QLabel
from .clock_config import SYSTEMS, PROFILE_KEYS, CLOCK_TITLES, FIELD_LABELS
from .clock_display import CLOCK_DISPLAY_CHOICES, clock_display_selection, clock_digit_scale, clock_mode
from .theme import CALENDAR_THEME_NAMES, THEME_NAMES
from .widgets import DesktopSurface, WIDGET_LABELS
from .widget_themes import widget_theme, widget_theme_choices, widget_theme_selection
from .color_control import ColorControl
from .ui import label, button, card

class ClocksPage(QWidget):
    def __init__(self, controller):
        super().__init__();self.controller = controller
        self.loading = True;self.dirty = False;self.editing = 'combined'
        self.profiles = copy.deepcopy(controller.options['clock_profiles'])
        self.theme_drafts = {};self.edited_themes = set();self.profile_edits = {};self.global_edits = set()
        self.display_drafts = {};self.display_edits = {}
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
        frame, content = card();content.addWidget(label('KELLO JA AJANLASKUN VAIHTO', 'eyebrow'));form = QFormLayout()
        self.target = QComboBox()
        for key in PROFILE_KEYS:self.target.addItem(WIDGET_LABELS[key],key)
        self.target.currentIndexChanged.connect(self.change_target)
        form.addRow('Muokattava kello',self.target)
        self.mode = QComboBox()
        for title, key in [('Pidä valittu ajanlasku','fixed'), ('Vaihda järjestyksessä','cycle'), ('Vaihda satunnaisesti','random')]: self.mode.addItem(title, key)
        self.system = QComboBox()
        for key in SYSTEMS: self.system.addItem(CLOCK_TITLES[key], key)
        self.interval = QSpinBox();self.interval.setRange(1,3600);self.interval.setSuffix(' sekuntia')
        self.theme = QComboBox()
        for title,key in widget_theme_choices(self.editing):self.theme.addItem(title,key)
        for title, control in [('Vaihtotapa',self.mode),('Valittu ajanlasku',self.system),('Vaihtoväli',self.interval),('Kellon teema',self.theme)]:form.addRow(title,control)
        self.display_mode = QComboBox();self.display_mode.setAccessibleName('Kellon näyttötapa')
        for title,key in CLOCK_DISPLAY_CHOICES:self.display_mode.addItem(title,key)
        self.digit_scale = QSpinBox();self.digit_scale.setRange(80,140);self.digit_scale.setSuffix(' %')
        self.digit_scale.setAccessibleName('Digikellon numerokoko')
        self.digit_scale.setToolTip('Valitun kellon digitaalisten numeroiden koko. Fontti valitaan yhteisistä asetuksista.')
        self.shared_digit_scale = QCheckBox('Käytä yhteistä numerokokoa')
        self.shared_digit_scale.setToolTip('Poista valinta, kun haluat säätää vain tämän kellon digitaalisia numeroita.')
        form.addRow('Näyttötapa',self.display_mode);form.addRow('Digikellon numerokoko',self.digit_scale)
        form.addRow('',self.shared_digit_scale)
        self.digit_color=ColorControl(inherit_label='Käytä widgetin tekstiväriä',title='Valitse digikellon numeroväri')
        form.addRow('Digikellon numeroväri',self.digit_color)
        content.addLayout(form)
        self.display_hint = label('', 'muted', True);content.addWidget(self.display_hint)
        self.pool = {};pool_row = QHBoxLayout()
        for key in SYSTEMS:
            check = QCheckBox(CLOCK_TITLES[key]);pool_row.addWidget(check);self.pool[key] = check
            check.toggled.connect(lambda _:self.changed(setting='time_systems'))
        content.addWidget(label('Vaihtoon osallistuvat ajanlaskut', 'muted'));content.addLayout(pool_row)
        content.addWidget(label('Kupari · Varjoaika / Astraali · Tähtiaika / Aamunkajo · Gregoriaaninen. Kellon paikka ja koko eivät muutu ajanlaskun vaihtuessa.', 'muted', True))
        content.addWidget(label('Kellon teema, näyttötapa, numerokoko, numeroväri ja näkyvä sisältö koskevat yllä valittua kellowidgetiä. Näyttötavan voi valita teemasta riippumatta. Widgetin muiden tekstien väri valitaan Työpöytäwidgetit-sivulla. Vaihtotapa koskee yhteistä kelloa.', 'muted', True))
        left.addWidget(frame)
        frame, content = card();content.addWidget(label('NÄKYVÄ SISÄLTÖ', 'eyebrow'))
        grid = QGridLayout();self.fields = {}
        for index, (key, title) in enumerate(FIELD_LABELS.items()):
            check = QCheckBox(title);self.fields[key] = check;grid.addWidget(check,index//2,index%2)
            check.toggled.connect(lambda _,field=key:self.changed(field=field))
        content.addLayout(grid)
        content.addWidget(label('Sisältövalinnat tallentuvat erikseen yhteiselle widgetille ja vanhoille erillisille kelloille. Kuun- ja kierronvaiheet ovat kuvitteellisia, paitsi gregoriaanisen ISO-viikko.', 'muted', True))
        content.addWidget(button('Yhteinen fontti ja tekstikoko →', lambda:controller.open_page('settings')))
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
        for control,key in ((self.mode,'time_mode'),(self.system,'time_system')):
            control.currentIndexChanged.connect(lambda _,setting=key:self.changed(setting=setting))
        self.theme.currentIndexChanged.connect(lambda _:self.changed(theme=True))
        self.display_mode.currentIndexChanged.connect(lambda _:self.changed(display='mode'))
        self.digit_scale.valueChanged.connect(lambda _:self.changed(display='digit_scale'))
        self.shared_digit_scale.toggled.connect(lambda _:self.changed(display='digit_scale'))
        self.digit_color.changed.connect(lambda:self.changed(display='digit_color'))
        self.interval.valueChanged.connect(lambda _:self.changed(setting='time_interval'))
        self.preview_system.currentIndexChanged.connect(self.refresh_preview)
        controller.clock_changed.connect(self.refresh_preview)
        controller.daily.changed.connect(self.refresh_preview)
        controller.settings_changed.connect(self.sync)
        self.load()

    def load(self):
        self.loading = True
        options = self.controller.options
        self.profiles = copy.deepcopy(options['clock_profiles'])
        self.theme_drafts = {key:widget_theme_selection(options,key) for key in PROFILE_KEYS}
        self.display_drafts = {key:clock_display_selection(options,key) for key in PROFILE_KEYS}
        self.edited_themes.clear();self.profile_edits.clear();self.global_edits.clear()
        self.display_edits.clear()
        for control, key in [(self.mode,'time_mode'),(self.system,'time_system')]:control.setCurrentIndex(control.findData(options[key]))
        self.theme.setCurrentIndex(self.theme.findData(self.theme_drafts[self.editing]))
        self.interval.setValue(options['time_interval'])
        for key, check in self.pool.items():check.setChecked(key in options['time_systems'])
        self.enabled.blockSignals(True);self.enabled.setChecked(options['widgets']['combined']);self.enabled.blockSignals(False)
        for key, check in self.fields.items():check.setChecked(self.profiles[self.editing][key])
        self.load_display_controls()
        self.loading = False;self.dirty = False;self.refresh_preview()

    def load_display_controls(self):
        draft=self.display_drafts[self.editing]
        self.display_mode.setCurrentIndex(self.display_mode.findData(draft['mode']))
        self.shared_digit_scale.setChecked('digit_scale' not in draft)
        self.digit_scale.setValue(clock_digit_scale(self.controller.options,self.editing,selection=draft))
        fixed=self.mode.currentData()=='fixed'
        system=self.editing if self.editing in SYSTEMS else (self.system.currentData() if fixed else self.preview_system.currentData())
        theme=widget_theme(self.controller.options,self.editing,system,selection=self.theme_drafts[self.editing])
        self.digit_color.load(draft.get('digit_color'),theme.text)

    def sync(self):
        if not self.dirty:self.load();return
        self.loading = True;options = self.controller.options
        self.enabled.blockSignals(True);self.enabled.setChecked(options['widgets']['combined']);self.enabled.blockSignals(False)
        for key in PROFILE_KEYS:
            for field,value in options['clock_profiles'][key].items():
                if field not in self.profile_edits.get(key,set()):self.profiles[key][field]=value
            if key not in self.edited_themes:self.theme_drafts[key]=widget_theme_selection(options,key)
            saved_display=clock_display_selection(options,key)
            for field in ('mode','digit_scale','digit_color'):
                if field in self.display_edits.get(key,set()):continue
                if field in saved_display:self.display_drafts[key][field]=saved_display[field]
                else:self.display_drafts[key].pop(field,None)
        for control,key in ((self.mode,'time_mode'),(self.system,'time_system')):
            if key not in self.global_edits:control.setCurrentIndex(control.findData(options[key]))
        if 'time_interval' not in self.global_edits:self.interval.setValue(options['time_interval'])
        if 'time_systems' not in self.global_edits:
            for key,check in self.pool.items():check.setChecked(key in options['time_systems'])
        self.theme.setCurrentIndex(self.theme.findData(self.theme_drafts[self.editing]))
        for key,check in self.fields.items():check.setChecked(self.profiles[self.editing][key])
        self.load_display_controls()
        self.loading=False;self.refresh_preview()

    def set_visible(self, enabled):
        if not self.loading:self.controller.set_widget('combined',enabled)

    def combine(self):
        try:self.controller.combine_clocks();self.status.setText('Erilliset kellot on piilotettu. Niiden asetukset ja sijainnit säilyvät.')
        except OSError as error:self.status.setText(str(error))

    def changed(self,setting=None,field=None,theme=False,display=None):
        if self.loading:return
        if setting:self.global_edits.add(setting)
        if field:
            self.profiles[self.editing][field]=self.fields[field].isChecked()
            self.profile_edits.setdefault(self.editing,set()).add(field)
        if theme:
            self.theme_drafts[self.editing]=self.theme.currentData();self.edited_themes.add(self.editing)
        if display:
            draft=self.display_drafts[self.editing]
            if display=='mode':draft['mode']=self.display_mode.currentData()
            elif display=='digit_color':
                if self.digit_color.value is None:draft.pop('digit_color',None)
                else:draft['digit_color']=self.digit_color.value
            elif self.shared_digit_scale.isChecked():draft.pop('digit_scale',None)
            else:draft['digit_scale']=self.digit_scale.value()
            self.display_edits.setdefault(self.editing,set()).add(display)
        self.dirty = bool(self.global_edits or self.profile_edits or self.edited_themes or self.display_edits)
        self.status.setText('Esikatselu — tallenna, kun valinnat ovat sopivat.');self.refresh_preview()

    def change_target(self):
        if self.loading:return
        self.profiles[self.editing] = {key:check.isChecked() for key,check in self.fields.items()}
        self.editing = self.target.currentData();self.loading = True
        for key, check in self.fields.items():check.setChecked(self.profiles[self.editing][key])
        self.theme.setCurrentIndex(self.theme.findData(self.theme_drafts[self.editing]))
        self.load_display_controls()
        self.loading = False;self.refresh_preview()

    def refresh_preview(self):
        if self.loading:return
        fixed = self.mode.currentData() == 'fixed'
        self.system.setEnabled(fixed);self.interval.setEnabled(not fixed)
        for check in self.pool.values():check.setEnabled(not fixed)
        system = self.editing if self.editing in SYSTEMS else (self.system.currentData() if fixed else self.preview_system.currentData())
        self.preview_system.setEnabled(self.editing=='combined' and not fixed)
        if not self.preview_system.isEnabled():
            self.preview_system.blockSignals(True);self.preview_system.setCurrentIndex(self.preview_system.findData(system));self.preview_system.blockSignals(False)
        self.preview_widget.profile_override = {key:check.isChecked() for key,check in self.fields.items()}
        self.preview_widget.system_override = system
        self.preview_widget.theme_override = self.theme.currentData()
        self.preview_widget.appearance_key_override=self.editing
        self.digit_color.set_inherited_color(self.preview_widget.theme.text)
        draft=self.display_drafts[self.editing]
        self.preview_widget.clock_display_override=copy.deepcopy(draft)
        display=clock_mode(self.controller.options,self.editing,self.preview_widget.theme,selection=draft)
        scale=clock_digit_scale(self.controller.options,self.editing,selection=draft)
        shared=self.shared_digit_scale.isChecked()
        if shared:
            self.digit_scale.blockSignals(True);self.digit_scale.setValue(scale);self.digit_scale.blockSignals(False)
        self.digit_scale.setEnabled(display in ('digital','both') and not shared)
        self.display_hint.setText('Analoginen näyttötapa ei näytä digitaalisia numeroita. Numerokoko on käytössä, kun valitset digikellon tai molemmat.' if display=='analog' else
            f'Käytössä yhteinen numerokoko: {scale} %. Poista valinta säätääksesi tämän kellon kokoa.' if shared else
            f'Tämän kellon digitaalisten numeroiden koko: {scale} %. Fontti on yhteinen.')
        self.preview_widget.apply_options()
        pixmap = self.preview_widget.grab()
        if pixmap.width() > 324:pixmap = pixmap.scaledToWidth(324, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(pixmap)
        choice = self.theme.currentData()
        name = (CALENDAR_THEME_NAMES[system] if choice=='calendar' else
                'Ubuntu' if choice=='ubuntu' else
                'Yhteinen ' + THEME_NAMES[self.controller.options['theme']] if choice=='shared' else THEME_NAMES[choice])
        display_name=dict((key,title) for title,key in CLOCK_DISPLAY_CHOICES)[display]
        size_label=f' · {scale} %' if display in ('digital','both') else ''
        self.preview_caption.setText(f'{WIDGET_LABELS[self.editing]} · {CLOCK_TITLES[system]} · {name}\n{display_name}{size_label}\nEsikatselu ei muuta työpöydän widgettiä. Sää käyttää yhteistä ennustetta, jos se on saatavilla.')

    def save(self):
        options=self.controller.options
        global_values={'time_mode':self.mode.currentData(),'time_system':self.system.currentData(),
                       'time_interval':self.interval.value(),'time_systems':[key for key,check in self.pool.items() if check.isChecked()]}
        changes={key:global_values[key] for key in self.global_edits}
        if self.edited_themes:
            themes=copy.deepcopy(options.get('widget_themes',{}))
            for key in self.edited_themes:themes[key]=self.theme_drafts[key]
            changes['widget_themes']=themes
        if self.profile_edits:
            profiles=copy.deepcopy(options['clock_profiles'])
            for key,fields in self.profile_edits.items():
                for field in fields:profiles[key][field]=self.profiles[key][field]
            changes['clock_profiles']=profiles
        if self.display_edits:
            displays=copy.deepcopy(options.get('clock_displays',{}))
            for key,fields in self.display_edits.items():
                saved=displays.setdefault(key,{})
                for field in fields:
                    if field in self.display_drafts[key]:saved[field]=self.display_drafts[key][field]
                    else:saved.pop(field,None)
                if not saved:displays.pop(key,None)
            changes['clock_displays']=displays
        if not changes:self.status.setText('Ei uusia kelloasetuksia tallennettavana.');return
        try:
            self.controller.configure(changes);self.dirty = False;self.load();self.status.setText('Tallennettu — ajanlaskut, sisältö ja teema on otettu käyttöön.')
        except (ValueError,OSError) as error:self.status.setText(str(error))

    def open_extras(self):
        from .almanac_ui import AlmanacDialog
        AlmanacDialog(self.controller,self).exec()

    def showEvent(self, event):
        if not self.dirty:self.load()
        super().showEvent(event)

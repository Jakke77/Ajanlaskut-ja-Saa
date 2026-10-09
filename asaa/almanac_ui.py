"""Visibility and scope of independently selectable real parallel calendars."""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QComboBox, QDialogButtonBox, QFormLayout
from .almanac import SPECS
from .ui import label

class AlmanacDialog(QDialog):
    def __init__(self, controller, parent):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle('Kuu-, aurinko- ja kuu–aurinkokalenterit')
        self.resize(590, 650)
        layout = QVBoxLayout(self)
        layout.addWidget(label('Valitse rinnakkaiskalenterit', 'heading'))
        layout.addWidget(label('Tähtiajan oma 510 päivän ajanlasku säilyy. Näissä näkyy saman päivän päiväys oikeissa kalentereissa.', 'muted', True))
        options = controller.options
        self.visible = QCheckBox('Näytä lisäkalenterit kalenterissa')
        self.visible.setChecked(options['calendar_extras_visible']);layout.addWidget(self.visible)
        self.checks = {}
        for key, spec in SPECS.items():
            check = QCheckBox(f'{spec.title} — {spec.kind}')
            check.setToolTip(spec.description)
            check.setChecked(key in options['calendar_extras'])
            layout.addWidget(check);self.checks[key] = check
        form = QFormLayout()
        self.scope = QComboBox()
        self.scope.addItem('Vain Tähtiajan kalenterissa', 'star');self.scope.addItem('Kaikissa kalenterinäkymissä', 'all')
        self.scope.setCurrentIndex(self.scope.findData(options['calendar_extras_scope']))
        self.cell = QComboBox();self.cell.addItem('Ei lisäpäiväystä päivien ruuduissa', 'none')
        for key, spec in SPECS.items(): self.cell.addItem(spec.title, key)
        self.cell.setCurrentIndex(self.cell.findData(options['calendar_extra_cell']))
        form.addRow('Näyttöpaikka', self.scope);form.addRow('Päivän ruudun lisäpäiväys', self.cell);layout.addLayout(form)
        layout.addWidget(label('Muunnokset tarkoittavat valitun siviilipäivän keskipäivää. Ne eivät vaihdu paikallisen auringonlaskun mukaan. Islamilainen päiväys on taulukollinen ja voi poiketa kuuhavainnoista. Persialainen laskenta on rajattu vuosille 1900–2100. Kuukauden nimet säilyvät alkuperäiskielisinä translitterointeina.', 'muted', True))
        self.status = label('', 'muted', True);layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText('Tallenna')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Peruuta')
        buttons.accepted.connect(self.save);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def save(self):
        try:
            self.controller.configure({'calendar_extras_visible': self.visible.isChecked(),
                'calendar_extras': [key for key, check in self.checks.items() if check.isChecked()],
                'calendar_extras_scope': self.scope.currentData(), 'calendar_extra_cell': self.cell.currentData()})
            self.accept()
        except (ValueError, OSError) as error: self.status.setText(str(error))

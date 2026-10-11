"""A reusable text-color override with the platform's normal color dialog."""
from PyQt6.QtCore import QSignalBlocker, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QCheckBox, QColorDialog, QPushButton, QVBoxLayout, QWidget


class ColorControl(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent=None, *, inherit_label='Käytä teeman tekstiväriä',
                 title='Valitse tekstiväri'):
        super().__init__(parent)
        self._title = title
        self._inherited = '#ffffff'
        self._custom = None
        self.inherit = QCheckBox(inherit_label, self)
        self.inherit.setChecked(True)
        self.inherit.setToolTip('Käytä teeman väriä. Poista valinta käyttääksesi omaa väriä.')
        self.button = QPushButton(self)
        self.button.setAccessibleName(title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.inherit)
        layout.addWidget(self.button)
        self.inherit.toggled.connect(self._toggle_inheritance)
        self.button.clicked.connect(self.choose_color)
        self._refresh()

    @property
    def value(self):
        """The explicit color, or None while the theme's color is selected."""
        return None if self.inherit.isChecked() else self._custom

    @staticmethod
    def _canonical(color):
        parsed = QColor(color)
        if not parsed.isValid():
            raise ValueError('Virheellinen tekstiväri.')
        return parsed.name()

    def load(self, value, inherited):
        """Load one saved or draft selection without emitting change signals."""
        inherited_color = self._canonical(inherited)
        custom_color = None if value is None else self._canonical(value)
        self._inherited = inherited_color
        self._custom = custom_color
        blocker = QSignalBlocker(self.inherit)
        self.inherit.setChecked(value is None)
        del blocker
        self._refresh()

    def set_inherited_color(self, color):
        """Refresh the theme fallback while preserving the explicit selection."""
        inherited = self._canonical(color)
        if inherited == self._inherited:
            return
        self._inherited = inherited
        self._refresh()

    def _toggle_inheritance(self, inherited):
        if not inherited and self._custom is None:
            self._custom = self._inherited
        self._refresh()
        self.changed.emit()

    def choose_color(self):
        picked = QColorDialog.getColor(QColor(self.value or self._inherited), self, self._title)
        if not picked.isValid():
            return
        self._custom = picked.name()
        blocker = QSignalBlocker(self.inherit)
        self.inherit.setChecked(False)
        del blocker
        self._refresh()
        self.changed.emit()

    def _refresh(self):
        color = self.value or self._inherited
        foreground = '#111111' if QColor(color).lightness() >= 128 else '#ffffff'
        self.button.setText(f'Valitse väri… {color}')
        self.button.setStyleSheet(
            f'QPushButton {{ background-color: {color}; color: {foreground}; '
            'border: 1px solid #808080; border-radius: 5px; padding: 6px 10px; }'
        )
        source = 'Teeman tekstiväri' if self.inherit.isChecked() else 'Oma tekstiväri'
        self.button.setToolTip(f'{source}: {color}. Avaa värivalitsin valitaksesi oman värin.')
        self.button.setAccessibleDescription(f'{source}: {color}')

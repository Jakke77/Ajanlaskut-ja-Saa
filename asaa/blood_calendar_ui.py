"""A 777-day Veri Aika year, browsed as five real weeks at a time."""
from datetime import date, datetime, timedelta
import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout,
                            QHBoxLayout, QGridLayout, QComboBox, QSizePolicy)

from . import blood_time, blood_names
from .theme import THEMES

IS_WINDOWS = sys.platform == 'win32'


MIN_DAY = date(1900, 1, 1)
MAX_DAY = date(2100, 12, 31)
WEEKS_PER_VIEW = 5
DAYS_PER_VIEW = WEEKS_PER_VIEW * 7
PERIODS_PER_YEAR = (blood_time.DAYS_PER_YEAR + DAYS_PER_VIEW - 1) // DAYS_PER_VIEW


def _label(text='', name=None):
    item = QLabel(text)
    item.setWordWrap(True)
    if name:
        item.setObjectName(name)
    return item


def _button(text, callback):
    item = QPushButton(text)
    item.clicked.connect(callback)
    return item


class BloodCalendarGrid(QWidget):
    """Seven columns and up to five week rows, without invented month rules.

    Programmatic ``set_day`` never emits. User selection and navigation emit
    ``selected_changed`` so owners can synchronize their existing details.
    The final page contains only week 111; it never borrows next year's days.
    """

    selected_changed = pyqtSignal(object)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.selected = blood_time.at(controller.calendars.now()).civil
        self.day_buttons = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        years = QHBoxLayout()
        self.previous_year = _button('‹ Vuosi', lambda: self.step_year(-1))
        self.next_year = _button('Vuosi ›', lambda: self.step_year(1))
        self.year_heading = _label('', 'eyebrow')
        years.addWidget(self.previous_year)
        years.addWidget(self.year_heading, 1)
        years.addWidget(self.next_year)
        layout.addLayout(years)
        navigation = QHBoxLayout()
        self.previous = _button('‹', lambda: self.step(-1))
        self.previous.setAccessibleName('Edellinen viiden viikon kalenterijakso')
        self.next = _button('›', lambda: self.step(1))
        self.next.setAccessibleName('Seuraava viiden viikon kalenterijakso')
        self.period = QComboBox()
        self.period.setAccessibleName('Veri Ajan viikot')
        for index in range(PERIODS_PER_YEAR):
            first = index * WEEKS_PER_VIEW + 1
            last = min(first + WEEKS_PER_VIEW - 1, blood_time.WEEKS_PER_YEAR)
            self.period.addItem(f'Viikot {first}–{last} / 111', index)
        self.period.currentIndexChanged.connect(self.change_period)
        self.today_button = _button('Nyt', self.today)
        navigation.addWidget(self.previous)
        navigation.addWidget(self.period, 1)
        navigation.addWidget(self.today_button)
        navigation.addWidget(self.next)
        layout.addLayout(navigation)
        self.range_label = _label('', 'muted')
        layout.addWidget(self.range_label)
        self.grid = QGridLayout()
        self.grid.setSpacing(7)
        layout.addLayout(self.grid)
        for column in range(7):
            heading = _label(f'{column + 1}.\npäivä', 'muted')
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(heading, 0, column)
            self.grid.setColumnStretch(column, 1)
        self.rules = _label('Ruudun numero on vuoden päivä 1–777. '
                            'Alla näkyy tavallinen päivämäärä. Viikko alkaa klo 01:07:07 Suomen aikaa. '
                            'Viiden viikon näkymät ovat selausjaksoja, eivät kuukausia.', 'muted')
        layout.addWidget(self.rules)
        controller.notes_changed.connect(self.render)
        controller.settings_changed.connect(self.render)
        self.set_day(self.selected)

    @property
    def position(self):
        return blood_time.from_date(self.selected)

    @property
    def period_index(self):
        return (self.position.day_of_year - 1) // DAYS_PER_VIEW

    @property
    def year_start(self):
        return self.selected - timedelta(days=self.position.day_of_year - 1)

    @property
    def period_start(self):
        return self.year_start + timedelta(days=self.period_index * DAYS_PER_VIEW)

    @property
    def visible_days(self):
        count = min(DAYS_PER_VIEW, blood_time.DAYS_PER_YEAR - self.period_index * DAYS_PER_VIEW)
        return tuple(self.period_start + timedelta(days=offset) for offset in range(count))

    def set_day(self, day):
        if not isinstance(day, date) or isinstance(day, datetime) or not MIN_DAY <= day <= MAX_DAY:
            raise ValueError('Valitse päivämäärä vuosilta 1900–2100.')
        self.selected = day
        self.render()

    def select_day(self, day):
        self.set_day(day)
        self.selected_changed.emit(day)

    def today(self):
        self.select_day(blood_time.at(self.controller.calendars.now()).civil)

    def step(self, delta):
        """Move one five-week page, preserving the selected offset where possible."""
        target = self.period_index + delta
        year_start = self.year_start
        year_delta, target = divmod(target, PERIODS_PER_YEAR)
        year_start += timedelta(days=year_delta * blood_time.DAYS_PER_YEAR)
        offset = (self.position.day_of_year - 1) % DAYS_PER_VIEW
        offset = min(offset, blood_time.DAYS_PER_YEAR - target * DAYS_PER_VIEW - 1)
        day = year_start + timedelta(days=target * DAYS_PER_VIEW + offset)
        self.select_day(min(max(day, MIN_DAY), MAX_DAY))

    def step_year(self, delta):
        day = self.selected + timedelta(days=delta * blood_time.DAYS_PER_YEAR)
        self.select_day(min(max(day, MIN_DAY), MAX_DAY))

    def change_period(self, index):
        if index >= 0:
            self.step(index - self.period_index)

    def render(self):
        position = self.position
        self.year_heading.setText(f'VUOSI {position.year:04d} · 777 PÄIVÄÄ · 111 VIIKKOA'
                                  if position.ordinal >= 0 else
                                  'ENNEN VERI AJAN ALKUA · 777 PÄIVÄN NIMIKIERTO')
        self.period.blockSignals(True)
        self.period.setCurrentIndex(self.period_index)
        self.period.blockSignals(False)
        days = self.visible_days
        self.range_label.setText(f'{days[0]:%d.%m.%Y}–{days[-1]:%d.%m.%Y} · '
                                 f'vuoden päivät {self.period_index * DAYS_PER_VIEW + 1}–'
                                 f'{self.period_index * DAYS_PER_VIEW + len(days)}/777')
        for item in self.day_buttons:
            self.grid.removeWidget(item)
            item.hide()
            item.deleteLater()
        self.day_buttons = []
        today = blood_time.at(self.controller.calendars.now()).civil
        theme = THEMES[self.controller.options['theme']]
        for offset, day in enumerate(days):
            item = blood_time.from_date(day)
            note = self.controller.state.note(day)
            action = _button(f'{item.day_of_year}' + (' •' if note else '') + f'\n{day:%d.%m.}',
                             lambda checked=False, selected=day: self.select_day(selected))
            action.setProperty('civil_date', day)
            action.setMinimumHeight(68)
            action.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
            action.setCheckable(True)
            action.setChecked(day == self.selected)
            action.setEnabled(MIN_DAY <= day <= MAX_DAY)
            action.setAccessibleName(f'Vuoden päivä {item.day_of_year} · {day:%d.%m.%Y}'
                                     + (' · kalenterimerkintä' if note else ''))
            tooltip = (f'{item.label}\nVuoden päivä {item.day_of_year}/777\n'
                       f'{day:%d.%m.%Y} · {item.names.label}')
            for name in (item.names.male, item.names.female):
                meaning = blood_names.meaning_for_name(name)
                tooltip += f'\n{name}: {meaning.meaning}' + (' **' if meaning.invented else '')
            if note:
                tooltip += '\n' + note
            action.setToolTip(tooltip)
            action.setAccessibleDescription(tooltip)
            if day == today and day != self.selected:
                action.setStyleSheet(f'border:2px solid {theme.accent};font-weight:bold;')
            self.grid.addWidget(action, 1 + offset // 7, offset % 7)
            self.day_buttons.append(action)
        self.previous_year.setEnabled(self.selected - timedelta(days=777) >= MIN_DAY)
        self.next_year.setEnabled(self.selected + timedelta(days=777) <= MAX_DAY)
        self.previous.setEnabled(days[0] > MIN_DAY)
        self.next.setEnabled(days[-1] < MAX_DAY)

"""Veri Aika: an uninterrupted week calendar and Oulu's live Otava sky."""
from datetime import date, timedelta

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                            QGridLayout, QDateEdit, QFrame)

from . import blood_time
from .otava_ui import OtavaView
from .theme import THEMES


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


class VeriPage(QWidget):
    """Browse real seven-day intervals without changing the live sky's time."""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        now = controller.calendars.now()
        self.selected = blood_time.at(now).civil
        self.week_start = self.selected - timedelta(days=blood_time.from_date(self.selected).weekday)
        self.follow_now = True
        self._shown_day = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(_label('SEITSEMÄN TÄHTEÄ · SEITSEMÄN PÄIVÄÄ', 'eyebrow'))
        layout.addWidget(_label('Veri Aika', 'heading'))
        self.current = _label('', 'muted')
        layout.addWidget(self.current)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.previous = _button('‹ Edellinen viikko', lambda: self.step(-1))
        self.next = _button('Seuraava viikko ›', lambda: self.step(1))
        self.today_button = _button('Nyt', self.today)
        controls.addWidget(self.previous)
        controls.addWidget(self.today_button)
        controls.addWidget(self.next)
        controls.addStretch(1)
        self.date = QDateEdit(QDate(self.selected.year, self.selected.month, self.selected.day))
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat('dd.MM.yyyy')
        self.date.setDateRange(QDate(1900, 1, 1), QDate(2100, 12, 31))
        self.date.setAccessibleName('Veri Ajan kalenterin päivämäärä')
        self.date.dateChanged.connect(self.date_changed)
        controls.addWidget(self.date)
        layout.addLayout(controls)

        frame = QFrame()
        frame.setObjectName('card')
        content = QVBoxLayout(frame)
        content.setContentsMargins(18, 16, 18, 16)
        self.week_heading = _label('', 'eyebrow')
        content.addWidget(self.week_heading)
        self.week_dates = _label('', 'muted')
        content.addWidget(self.week_dates)
        self.days = QGridLayout()
        self.days.setSpacing(8)
        content.addLayout(self.days)
        self.day_buttons = []
        for index in range(7):
            item = _button('', lambda checked=False, index=index: self.select_index(index))
            item.setCheckable(True)
            item.setMinimumHeight(70)
            self.days.addWidget(item, 0, index)
            self.days.setColumnStretch(index, 1)
            self.day_buttons.append(item)
        self.selected_label = _label('')
        content.addWidget(self.selected_label)
        self.open_day = _button('Avaa päivän merkinnät →',
                                lambda: controller.open_calendar('civil', self.selected))
        content.addWidget(self.open_day)
        layout.addWidget(frame)

        self.sky = OtavaView(controller)
        layout.addWidget(self.sky, 1)
        layout.addWidget(_label('Otava juuri nyt Oulun pohjoistaivaalla. Seitsemän tähden asento lasketaan '
                               'todellisesta ajasta; se ei ennusta tähtien näkymistä pilvien tai päivänvalon läpi.',
                               'muted'))
        layout.addWidget(_label('Dubhe · Merak · Phecda · Megrez · Alioth · Mizar · Alkaid', 'muted'))
        self.next_change = _label('', 'eyebrow')
        layout.addWidget(self.next_change)
        self.rules = _label('ALKU 26.6.2026 KLO 01:07:07 · EUROPE/HELSINKI\n'
                            'Päivä vaihtuu klo 01:07:07 Suomen aikaa. Seitsemän päivän jälkeen alkaa uusi viikko '
                            'samassa kellonajassa. Viikot jatkuvat vuodenvaihteen ja alun vuosipäivän yli. '
                            'Kesä- ja talviaika noudattavat Suomen paikallista aikaa.\n'
                            'Veri Aika on sovelluksen oma ajanlasku. Otavakellon sekuntiviisarina kiertävä '
                            'tähtikuvio on symbolinen; tämän sivun tähtitaivas näyttää Otavan todellisen asennon.',
                            'muted')
        layout.addWidget(self.rules)
        controller.clock_changed.connect(self.tick)
        controller.settings_changed.connect(self.render)
        controller.notes_changed.connect(self.render)
        self.render()
        self.tick()

    def set_day(self, day, *, follow_now=False):
        if not isinstance(day, date):
            raise TypeError('Valitse päivämäärä.')
        day = min(max(day, date(1900, 1, 1)), date(2100, 12, 31))
        self.follow_now = follow_now
        self.selected = day
        self.week_start = day - timedelta(days=blood_time.from_date(day).weekday)
        self.date.blockSignals(True)
        self.date.setDate(QDate(day.year, day.month, day.day))
        self.date.blockSignals(False)
        self.render()

    def date_changed(self, value):
        self.set_day(date(value.year(), value.month(), value.day()))

    def today(self):
        self.set_day(blood_time.at(self.controller.calendars.now()).civil, follow_now=True)
        self.tick()

    def step(self, weeks):
        self.set_day(self.selected + timedelta(days=7 * weeks))

    def select_index(self, index):
        self.set_day(self.week_start + timedelta(days=index))

    def render(self):
        selected = blood_time.from_date(self.selected)
        self.week_heading.setText(f'{selected.week}. VIIKKO' if selected.ordinal >= 0 else 'ENNEN VERI AJAN ALKUA')
        end = self.week_start + timedelta(days=6)
        self.week_dates.setText(f'{self.week_start:%d.%m.%Y} – {end:%d.%m.%Y} · viikon alku klo 01:07:07')
        today = blood_time.at(self.controller.calendars.now()).civil
        theme = THEMES[self.controller.options['theme']]
        for index, item in enumerate(self.day_buttons):
            day = self.week_start + timedelta(days=index)
            marker = ' •' if self.controller.state.note(day) else ''
            item.setText(f'{index + 1}. päivä\n{day:%d.%m.}{marker}')
            item.setChecked(day == self.selected)
            item.setStyleSheet(f'border:2px solid {theme.accent};' if day == today and day != self.selected else '')
            begin, finish = blood_time.boundary(day), blood_time.boundary(day + timedelta(days=1))
            item.setToolTip(f'{blood_time.from_date(day).label}\n'
                            f'{begin:%d.%m.%Y %H:%M:%S %Z} – {finish:%d.%m.%Y %H:%M:%S %Z}\n'
                            + self.controller.state.note(day))
        self.selected_label.setText(f'VALITTU PÄIVÄ · {selected.label}\n'
                                   f'{self.selected:%d.%m.%Y} klo 01:07:07 alkaen')
        self.previous.setEnabled(self.selected - timedelta(days=7) >= date(1900, 1, 1))
        self.next.setEnabled(self.selected + timedelta(days=7) <= date(2100, 12, 31))

    def tick(self):
        now = self.controller.calendars.now()
        current = blood_time.at(now)
        self.current.setText('JUURI NYT · ' + current.label)
        next_week = blood_time.next_week(now)
        self.next_change.setText(f'SEURAAVA VIIKKO · {next_week:%d.%m.%Y %H:%M:%S %Z}')
        if current.civil != self._shown_day:
            self._shown_day = current.civil
            if self.follow_now:
                self.set_day(current.civil, follow_now=True)
            else:
                self.render()

"""Veri Aika: 777-day years, authored daily names and Oulu's live Otava sky."""
from datetime import date, timedelta

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                            QGridLayout, QDateEdit, QFrame, QSizePolicy)

from . import blood_time
from .otava_ui import OtavaView
from .theme import THEMES
from .platform_support import IS_WINDOWS


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
        layout.addLayout(controls)
        if IS_WINDOWS:
            dates = QHBoxLayout()
            dates.addWidget(_label('Valitse päivämäärä', 'muted'))
            dates.addWidget(self.date)
            dates.addStretch(1)
            layout.addLayout(dates)
        else:
            controls.addWidget(self.date)
        years = QHBoxLayout()
        self.previous_year = _button('‹ Edellinen vuosi', lambda: self.step_year(-1))
        self.next_year = _button('Seuraava vuosi ›', lambda: self.step_year(1))
        years.addWidget(self.previous_year)
        years.addStretch(1)
        years.addWidget(_label('777 päivää · 111 viikkoa', 'muted'))
        years.addStretch(1)
        years.addWidget(self.next_year)
        layout.addLayout(years)

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
            if IS_WINDOWS:
                # Native Windows recommends a wide minimum for every button;
                # the calendar's short labels must share the seven-column row.
                item.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
            self.days.addWidget(item, 0, index)
            self.days.setColumnStretch(index, 1)
            self.day_buttons.append(item)
        self.selected_label = _label('')
        content.addWidget(self.selected_label)
        self.selected_names = _label('')
        self.selected_names.setStyleSheet('font-size:20px;')
        self.selected_names.setAccessibleName('Valitun päivän nimipari')
        content.addWidget(self.selected_names)
        self.name_lookup = _button('Oma nimi Veri Ajassa →', self.open_name_lookup)
        content.addWidget(self.name_lookup)
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
        self.next_year_change = _label('', 'muted')
        layout.addWidget(self.next_year_change)
        self.rules = _label('ALKU 26.6.2026 KLO 01:07:07 · EUROPE/HELSINKI\n'
                            'Päivä vaihtuu klo 01:07:07 Suomen aikaa. Seitsemän päivän jälkeen alkaa uusi viikko '
                            'samassa kellonajassa. Veri Ajan vuodessa on 777 päivää eli tasan 111 viikkoa. '
                            'Seuraava vuosi alkaa 777 paikallisen päivän jälkeen; vuoden päivät ja viikot alkavat silloin uudestaan ykkösestä. '
                            'Kesä- ja talviaika noudattavat Suomen paikallista aikaa.\n'
                            'Jokaisella vuoden päivällä on oma pysyvä miehen ja naisen nimipari. Veren, elämänkierron '
                            'ja biologian sanastosta innoittuneet nimet on keksitty sovellusta varten. '
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

    def step_year(self, years):
        self.set_day(self.selected + timedelta(days=blood_time.DAYS_PER_YEAR * years))

    def open_name_lookup(self):
        page = self.controller.window.page_widgets['names']
        page.set_day(self.selected)
        page.tabs.setCurrentIndex(0)
        self.controller.open_page('names')

    def select_index(self, index):
        self.set_day(self.week_start + timedelta(days=index))

    def render(self):
        selected = blood_time.from_date(self.selected)
        self.week_heading.setText(f'VUOSI {selected.year:04d} · {selected.week_of_year}. VIIKKO / 111'
                                  if selected.ordinal >= 0 else 'ENNEN VERI AJAN ALKUA')
        end = self.week_start + timedelta(days=6)
        self.week_dates.setText(f'{self.week_start:%d.%m.%Y} – {end:%d.%m.%Y} · viikon alku klo 01:07:07')
        today = blood_time.at(self.controller.calendars.now()).civil
        theme = THEMES[self.controller.options['theme']]
        for index, item in enumerate(self.day_buttons):
            day = self.week_start + timedelta(days=index)
            marker = ' •' if self.controller.state.note(day) else ''
            if IS_WINDOWS:
                # Keep all wording readable in seven native-size columns.
                # Minimum vertical policy lets Qt grow for the third line.
                item.setText(f'{index + 1}.{marker}\npäivä\n{day:%d.%m.}')
                item.setAccessibleName(f'Viikon {index + 1}. päivä · {day:%d.%m.%Y}'
                                       + (' · kalenterimerkintä' if marker else ''))
            else:
                item.setText(f'{index + 1}. päivä\n{day:%d.%m.}{marker}')
            item.setChecked(day == self.selected)
            item.setStyleSheet(f'border:2px solid {theme.accent};' if day == today and day != self.selected else '')
            begin, finish = blood_time.boundary(day), blood_time.boundary(day + timedelta(days=1))
            position = blood_time.from_date(day)
            item.setToolTip(f'{position.label}\nVuoden päivä {position.day_of_year}/777\n'
                            f'{position.names.label}\n'
                            f'{begin:%d.%m.%Y %H:%M:%S %Z} – {finish:%d.%m.%Y %H:%M:%S %Z}\n'
                            + self.controller.state.note(day))
            if IS_WINDOWS:
                item.setAccessibleDescription(item.toolTip())
        self.selected_label.setText(f'VALITTU PÄIVÄ · {selected.label}\n'
                                   f'Vuoden päivä {selected.day_of_year}/777 · '
                                   f'{self.selected:%d.%m.%Y} klo 01:07:07 alkaen')
        names = f'Miehen nimi: {selected.names.male}\nNaisen nimi: {selected.names.female}'
        self.selected_names.setText(names)
        self.selected_names.setAccessibleName('Valitun päivän nimipari\n' + names)
        self.previous.setEnabled(self.selected - timedelta(days=7) >= date(1900, 1, 1))
        self.next.setEnabled(self.selected + timedelta(days=7) <= date(2100, 12, 31))
        self.previous_year.setEnabled(self.selected - timedelta(days=blood_time.DAYS_PER_YEAR) >= date(1900, 1, 1))
        self.next_year.setEnabled(self.selected + timedelta(days=blood_time.DAYS_PER_YEAR) <= date(2100, 12, 31))

    def tick(self):
        now = self.controller.calendars.now()
        current = blood_time.at(now)
        self.current.setText(f'JUURI NYT · {current.label} · vuoden päivä {current.day_of_year}/777')
        next_week = blood_time.next_week(now)
        self.next_change.setText(f'SEURAAVA VIIKKO · {next_week:%d.%m.%Y %H:%M:%S %Z}')
        next_year = blood_time.next_year(now)
        self.next_year_change.setText(f'SEURAAVA VUOSI · {next_year:%d.%m.%Y %H:%M:%S %Z}')
        if current.civil != self._shown_day:
            self._shown_day = current.civil
            if self.follow_now:
                self.set_day(current.civil, follow_now=True)
            else:
                self.render()

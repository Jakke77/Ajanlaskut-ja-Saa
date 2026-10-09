"""One civil day shared by Gregorian, Varjoaika and Tähtiaika calendars."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from .models import shadow, star

NAMES = {'shadow': 'Varjoaika', 'star': 'Tähtiaika', 'civil': 'Gregoriaaninen kalenteri'}
MONTHS = ('Tammikuu', 'Helmikuu', 'Maaliskuu', 'Huhtikuu', 'Toukokuu', 'Kesäkuu',
          'Heinäkuu', 'Elokuu', 'Syyskuu', 'Lokakuu', 'Marraskuu', 'Joulukuu')
WEEKDAYS = ('Maanantai', 'Tiistai', 'Keskiviikko', 'Torstai', 'Perjantai', 'Lauantai', 'Sunnuntai')

@dataclass(frozen=True)
class Day:
    system: str
    year: int
    month: int
    day: int
    civil: date

    @property
    def month_name(self):
        return (shadow.MONTH_NAMES if self.system == 'shadow' else
                star.MONTHS if self.system == 'star' else MONTHS)[self.month]

    @property
    def label(self):
        suffix = f'kierto {self.year}' if self.system == 'star' else f'vuosi {self.year:04d}'
        return f'{self.day}. {self.month_name} · {suffix}'

    @property
    def weekday(self):
        if self.system == 'star':
            return star.StarDate(self.year, self.month, self.day).weekday
        return self.civil.weekday()

    @property
    def phase(self):
        if self.system == 'shadow': return shadow.moon_label(self.day)
        if self.system == 'star': return star.StarDate(self.year, self.month, self.day).phase
        return WEEKDAYS[self.weekday]


class Calendars:
    def __init__(self, zone='Europe/Helsinki', star_epoch='2026-07-01'):
        self.zone = ZoneInfo(zone)
        self.star_epoch = date.fromisoformat(star_epoch)
        star.CalendarClock('fixed', self.star_epoch)

    def now(self):
        return datetime.now(self.zone)

    def convert(self, system, civil):
        if system == 'civil': return Day(system, civil.year, civil.month - 1, civil.day, civil)
        if system == 'shadow':
            item = shadow.from_gregorian(civil)
        elif system == 'star':
            item = star.StarDate.from_ordinal((civil - self.star_epoch).days)
        else: raise ValueError('Tuntematon ajanlasku')
        return Day(system, item.year, item.month, item.day, civil)

    def civil_date(self, system, year, month, day):
        if system == 'shadow': return shadow.to_gregorian(shadow.CalendarDate(year, month, day))
        if system == 'star':
            item = star.StarDate(year, month, day)
            return self.star_epoch + timedelta(days=item.ordinal)
        if system == 'civil': return date(year, month + 1, day)
        raise ValueError('Tuntematon ajanlasku')

    def last_month(self, system):
        """Keep navigation within complete months supported by datetime."""
        last = self.convert(system, date.max)
        if system != 'civil' and last.day < 29:
            count = 13 if system == 'shadow' else 17
            index = (last.year-1)*count + last.month-1
            year, month = divmod(index, count)
            return year+1, month
        return last.year, last.month

    def bound_month(self, system, year, month):
        count = {'shadow': 13, 'star': 17, 'civil': 12}[system]
        last_year, last_month = self.last_month(system)
        index = min(max(0, (year-1)*count+month), (last_year-1)*count+last_month)
        year, month = divmod(index, count)
        return year+1, month

    def month_days(self, system, year, month):
        if system == 'civil':
            from calendar import monthrange
            numbers = range(1, monthrange(year, month + 1)[1] + 1)
        else: numbers = range(30)
        return [self.convert(system, self.civil_date(system, year, month, n)) for n in numbers]

    def step_month(self, system, year, month, delta):
        return self.bound_month(system, year, month+delta)

    def day_words(self, item, side='left'):
        if item.system == 'star': return star.day_name(star.StarDate(item.year, item.month, item.day), side)
        if item.system == 'shadow': return shadow.WEEKDAY_NAMES[item.weekday]
        return WEEKDAYS[item.weekday]

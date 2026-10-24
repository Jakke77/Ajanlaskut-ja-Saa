"""Veri Aika: 777-day years starting in Oulu on 26 June 2026.

This is the application's authored calendar, not a historical calendar.  Its
day boundary is 01:07:07 Europe/Helsinki *wall time*, so a day containing a
summer/winter time change can last 23/25 actual hours.  A year contains 111
complete seven-day weeks.  Its boundary follows 777 local calendar days, not
Gregorian New Year or the epoch's Gregorian anniversary.  There are no months.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Europe/Helsinki')
CUTOVER = time(1, 7, 7)
EPOCH_DATE = date(2026, 6, 26)
EPOCH = datetime.combine(EPOCH_DATE, CUTOVER, ZONE)
DAYS_PER_YEAR = 777
WEEKS_PER_YEAR = DAYS_PER_YEAR // 7


@dataclass(frozen=True)
class BloodDate:
    civil: date
    ordinal: int

    @property
    def system(self):
        return 'blood'

    @property
    def names(self):
        from .blood_names import names_at
        return names_at(self.day_of_year)

    @property
    def year(self):
        """One-based authored year; before-epoch values remain identifiable."""
        return self.ordinal // DAYS_PER_YEAR + 1

    @property
    def day_of_year(self):
        """One-based position in the 777-day cycle, also for birthday lookup."""
        return self.ordinal % DAYS_PER_YEAR + 1

    @property
    def week_of_year(self):
        return (self.day_of_year - 1) // 7 + 1

    @property
    def phase(self):
        from .astronomy import phase_label
        return phase_label(self.civil, ZONE.key)

    @property
    def week(self):
        """Continuous week count retained for existing navigation and callers."""
        return self.ordinal // 7 + 1

    @property
    def weekday(self):
        """Zero-based day within the uninterrupted seven-day week."""
        return self.ordinal % 7

    @property
    def day_name(self):
        return f'{self.weekday + 1}. päivä'

    @property
    def label(self):
        if self.ordinal < 0:
            return f'{-self.ordinal}. päivä ennen Veri Ajan alkua'
        return f'{self.weekday + 1}. päivä · {self.week_of_year}. viikko · vuosi {self.year:04d}'


def boundary(day):
    """The Finnish wall-clock start of this effective calendar date."""
    if not isinstance(day, date) or isinstance(day, datetime):
        raise TypeError('Päivämäärän pitää olla date-olio.')
    return datetime.combine(day, CUTOVER, ZONE)


def from_date(day):
    """Interpret a selected civil date at its 01:07:07 boundary."""
    boundary(day)
    return BloodDate(day, (day - EPOCH_DATE).days)


def at(moment):
    """Convert an actual instant; never infer the host computer's time zone."""
    if not isinstance(moment, datetime):
        raise TypeError('Aikaleiman pitää olla datetime-olio.')
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError('Aikaleima tarvitsee aikavyöhykkeen.')
    local = moment.astimezone(ZONE)
    day = local.date()
    if local.time() < CUTOVER:
        day -= timedelta(days=1)
    return from_date(day)


def next_week(moment):
    """Next strictly future week boundary, preserving Finnish wall time."""
    item = at(moment)
    return boundary(item.civil + timedelta(days=7 - item.weekday))


def next_year(moment):
    """Next strictly future 777-day boundary, at Finnish 01:07:07 wall time."""
    item = at(moment)
    return boundary(item.civil + timedelta(days=DAYS_PER_YEAR + 1 - item.day_of_year))

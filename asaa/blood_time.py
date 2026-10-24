"""Veri Aika: continuous seven-day weeks starting in Oulu on 26 June 2026.

This is the application's authored calendar, not a historical calendar.  Its
day boundary is 01:07:07 Europe/Helsinki *wall time*, so a day containing a
summer/winter time change can last 23/25 actual hours.  Weeks never restart at
Gregorian New Year or the epoch's anniversary.  There are no invented months.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Europe/Helsinki')
CUTOVER = time(1, 7, 7)
EPOCH_DATE = date(2026, 6, 26)
EPOCH = datetime.combine(EPOCH_DATE, CUTOVER, ZONE)


@dataclass(frozen=True)
class BloodDate:
    civil: date
    ordinal: int

    @property
    def system(self):
        return 'blood'

    @property
    def names(self):
        return None

    @property
    def phase(self):
        from .astronomy import phase_label
        return phase_label(self.civil, ZONE.key)

    @property
    def week(self):
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
        return f'{self.weekday + 1}. päivä · {self.week}. viikko'


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

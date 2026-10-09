"""Tähtiajan 17 × 30 = 510 päivän kalenteri; vanha solar-malli vain yhteensopivuuteen."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
import re

MONTHS = (
    "Tyhjiönkuu", "Pulsarikuu", "Kvanttikuu", "Sumukuu", "Supernovankuu",
    "Mustan aukon kuu", "Galaksin kuu", "Ionikuu", "Plasma-kuu", "Meteorikuu",
    "Komeettakuu", "Gravitaatiokuu", "Neutrinokuu", "Pimeän aineen kuu",
    "Oortin pilven kuu", "Horisonttikuu", "Singulariteettikuu",
)
WEEKDAYS = (
    "Fotonimaantai", "Orbitiivistai", "Spektrikeskiviikko", "Kehätorstai",
    "Akkreetioperjantai", "Radiolauantai", "Zenitsunnuntai",
)
SHORT_WEEKDAYS = ("Fo", "Or", "Sp", "Ke", "Ak", "Ra", "Ze")
DAYS_PER_YEAR = 510
UTC = timezone.utc
REVONTULI_DAYS = tuple(f"{number}. revontulen päivä" for number in range(1, 8))
ASTEROID_DAYS = tuple(f"{number}. asteroidin päivä" for number in range(1, 8))


def shadow_side(star, preference="right"):
    if preference == "month":
        return "right" if star.month % 2 == 0 else "left"
    if preference not in ("right", "left"):
        raise ValueError("Varjon puoli: oikea, vasen tai kuukauden mukaan.")
    return preference


def day_series(star, preference="right"):
    return REVONTULI_DAYS if shadow_side(star, preference) == "right" else ASTEROID_DAYS


def day_name(star, preference="right"):
    return day_series(star, preference)[star.weekday]


def shadow_label(star, preference="right"):
    return "Varjo oikealla · 7 revontulta" if shadow_side(star, preference) == "right" else "Varjo vasemmalla · 7 asteroidia"


def local_zone():
    """Read the system's time zone rules, including daylight saving transitions."""
    configured = os.environ.get("TZ", "").lstrip(":")
    if configured:
        try:
            return ZoneInfo(configured)
        except (KeyError, ValueError):
            pass
    try:
        with open("/etc/localtime", "rb") as stream:
            return ZoneInfo.from_file(stream, key="local")
    except OSError:
        return datetime.now().astimezone().tzinfo


@dataclass(frozen=True, order=True)
class StarDate:
    year: int
    month: int
    day: int

    def __post_init__(self):
        if (any(type(v) is not int for v in (self.year, self.month, self.day))
                or self.year < 1 or not 0 <= self.month < 17 or not 0 <= self.day < 30):
            raise ValueError("Tähtipäivä: kierto ≥ 1, kuu 0–16 ja päivä 0–29.")

    @property
    def key(self):
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    @property
    def ordinal(self):
        return (self.year - 1) * DAYS_PER_YEAR + self.month * 30 + self.day

    @property
    def weekday(self):
        return self.ordinal % 7

    @property
    def label(self):
        return f"{self.day}. {MONTHS[self.month]} · kierto {self.year}"

    @property
    def phase(self):
        if self.day == 0:
            return "Null-Piste · Uusikuu"
        if self.day <= 7:
            return "Flux-Kaari · Kasvava sirppi"
        if self.day <= 14:
            return "Kvantti-Divergenssi · Ensimmäinen neljännes"
        if self.day <= 22:
            return "Zenit-Valaisu · Täysikuu"
        if self.day <= 28:
            return "Impluusio-Kaari · Vähenevä kuu"
        return "Eklipsi · Viimeinen katoaminen"

    @classmethod
    def from_key(cls, key):
        if not isinstance(key, str) or not re.fullmatch(r"[0-9]+-[0-9]{2}-[0-9]{2}", key):
            raise ValueError("Virheellinen tähtipäivän tunniste.")
        return cls(*(int(part) for part in key.split("-")))

    @classmethod
    def from_ordinal(cls, ordinal):
        if type(ordinal) is not int or ordinal < 0:
            raise ValueError("Päivä on ennen ajanlaskun alkua.")
        year, within = divmod(ordinal, DAYS_PER_YEAR)
        month, day = divmod(within, 30)
        return cls(year + 1, month, day)

    def shift_month(self, delta):
        index = (self.year - 1) * 17 + self.month + delta
        if index < 0:
            raise ValueError("Kiertoja ennen ensimmäistä kiertoa ei ole.")
        year, month = divmod(index, 17)
        return StarDate(year + 1, month, self.day)


class CalendarClock:
    """The confirmed fixed cycle has 510 days and independent cycle numbering.

    solar is retained internally for interpreting older experimental data only;
    the application activates fixed on startup and exposes no solar mode choice.
    """
    def __init__(self, mode="fixed", epoch=date(2026, 7, 1), zone=None):
        if mode not in ("solar", "fixed"):
            raise ValueError("Tuntematon ajanlaskun muunnosmalli.")
        if not isinstance(epoch, date) or isinstance(epoch, datetime) or (epoch.month, epoch.day) != (7, 1):
            raise ValueError("Ensimmäinen kierto ankkuroidaan heinäkuun 1. päivään.")
        self.mode, self.epoch, self.zone = mode, epoch, zone or local_zone()

    def _midnight(self, day):
        return datetime(day.year, day.month, day.day, tzinfo=self.zone)

    def cycle_bounds(self, year):
        if self.mode == "solar":
            if not 1 <= year <= 9998:
                raise ValueError("Vuosittaisen muunnoksen kierto on 1–9998.")
            return self._midnight(date(year, 7, 1)), self._midnight(date(year + 1, 7, 1))
        start = self.epoch + timedelta(days=(year - 1) * DAYS_PER_YEAR)
        return self._midnight(start), self._midnight(start + timedelta(days=DAYS_PER_YEAR))

    def at(self, moment):
        if moment.tzinfo is None:
            raise ValueError("Aikaleiman pitää sisältää aikavyöhyke.")
        moment = moment.astimezone(self.zone)
        if self.mode == "fixed":
            return StarDate.from_ordinal((moment.date() - self.epoch).days)
        year = moment.year - ((moment.month, moment.day) < (7, 1))
        begin, end = self.cycle_bounds(year)
        # Integer microseconds avoid rounding a cycle's last instant into the next.
        elapsed = moment.astimezone(UTC) - begin.astimezone(UTC)
        length = end.astimezone(UTC) - begin.astimezone(UTC)
        elapsed_us = elapsed // timedelta(microseconds=1)
        length_us = length // timedelta(microseconds=1)
        day_index = elapsed_us * DAYS_PER_YEAR // length_us
        return StarDate(year, day_index // 30, day_index % 30)

    def day_bounds(self, star):
        if self.mode == "fixed":
            day = self.epoch + timedelta(days=star.ordinal)
            return self._midnight(day), self._midnight(day + timedelta(days=1))
        begin, end = self.cycle_bounds(star.year)
        base, total = begin.astimezone(UTC), end.astimezone(UTC) - begin.astimezone(UTC)
        total_us = total // timedelta(microseconds=1)
        index = star.month * 30 + star.day
        # Ceil is the first representable instant belonging to the given star day.
        a = (total_us * index + DAYS_PER_YEAR - 1) // DAYS_PER_YEAR
        b = (total_us * (index + 1) + DAYS_PER_YEAR - 1) // DAYS_PER_YEAR
        return (base + timedelta(microseconds=a)).astimezone(self.zone), (base + timedelta(microseconds=b)).astimezone(self.zone)

    def solar_marker(self, moment):
        local = moment.astimezone(self.zone)
        if self.mode == "solar":
            return (local.month, local.day) == (7, 1)
        try:
            star = self.at(moment)
            return star.month == 0 and star.day == 0
        except ValueError:
            return False

"""Clock composition and monotonic calendar rotation, independent of Qt/network."""
import math
import random
import time

SYSTEMS = ('shadow', 'star', 'civil')
PROFILE_KEYS = ('combined', 'shadow', 'star', 'civil')
CLOCK_TITLES = {'shadow': 'Varjoaika', 'star': 'Tähtiaika', 'civil': 'Gregoriaaninen'}
FIELD_LABELS = {
    'clock': 'Kello', 'date': 'Ajanlaskun päivämäärä', 'weekday': 'Päivän nimi',
    'phase': 'Kuunvaihe / kierronvaihe / ISO-viikko',
    'civil_date': 'Tavallinen päivämäärä', 'zone': 'Aikavyöhyke',
    'weather': 'Kolmen päivän sää', 'note': 'Päivän kalenterimerkintä',
    'reminder': 'Seuraava muistutus',
}


def default_profile(weather=False, civil_date=True):
    return {'clock': True, 'date': True, 'weekday': True, 'phase': True,
            'civil_date': civil_date, 'zone': True, 'weather': weather,
            'note': False, 'reminder': False}


DEFAULT_PROFILES = {
    'combined': default_profile(True), 'shadow': default_profile(True),
    'star': default_profile(), 'civil': default_profile(civil_date=False),
}


def clock_layout(profile, *, analog=False):
    """Stable slots; hidden fields collapse, changing calendars never changes size."""
    y = 56
    blocks = []
    for field, height in [('clock', 346 if analog else 90), ('date', 46), ('weekday', 34), ('phase', 34),
                          ('reference', 36), ('weather', 206), ('note', 66), ('reminder', 64)]:
        enabled = (profile['civil_date'] or profile['zone']) if field == 'reference' else profile[field]
        if enabled:
            blocks.append((field, y, height))
            y += height
    return blocks, max(150, y + 36)


class ClockRotation:
    def __init__(self, options, monotonic=time.monotonic, choose=random.choice):
        self.monotonic, self.choose = monotonic, choose
        self.current = options['time_system']
        self.signature = None
        self.configure(options)

    def configure(self, options):
        signature = (options['time_mode'], options['time_system'],
                     tuple(options['time_systems']), options['time_interval'])
        if signature == self.signature: return False
        self.signature = signature
        self.mode, manual, self.systems, self.interval = signature
        if self.mode == 'fixed': self.current = manual
        elif self.current not in self.systems: self.current = self.systems[0]
        self.deadline = self.monotonic() + self.interval
        return True

    def advance(self, direction=1):
        previous = self.current
        if self.mode == 'random':
            alternatives = [system for system in self.systems if system != self.current]
            if alternatives: self.current = self.choose(alternatives)
        else:
            pool = SYSTEMS if self.mode == 'fixed' else self.systems
            if self.current in pool:
                self.current = pool[(pool.index(self.current)+direction) % len(pool)]
            else: self.current = pool[0]
        self.deadline = self.monotonic() + self.interval
        return self.current != previous

    def poll(self):
        if self.mode == 'fixed' or self.monotonic() < self.deadline: return False
        return self.advance()

    def remaining(self):
        return max(0, math.ceil(self.deadline - self.monotonic()))

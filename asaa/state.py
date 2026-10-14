"""Private, atomic state for shared appearance, widgets, notes and reminders."""
import copy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from zoneinfo import ZoneInfo
from .clock_config import SYSTEMS, PROFILE_KEYS, FIELD_LABELS, DEFAULT_PROFILES
from .almanac import SPECS

DEFAULTS = {
    'theme': 'copper', 'font': 'Ubuntu', 'scale': 77, 'opacity': 77,
    'widget_text_scale': 130, 'widget_clock_scale': 100,
    'wallpaper_directory': '', 'wallpaper_mode': 'single',
    'wallpaper_interval': 77, 'wallpaper_shuffle': True,
    'wallpaper_follow_theme': True, 'wallpaper_theme_target': 'desktop',
    'icon_follow_theme': False,
    'time_mode': 'cycle', 'time_system': 'shadow', 'time_systems': list(SYSTEMS),
    'time_interval': 77, 'time_theme': 'shared', 'clock_profiles': copy.deepcopy(DEFAULT_PROFILES),
    'widget_themes': {}, 'widget_text_colors': {}, 'clock_displays': {},
    'calendar_extras_visible': True, 'calendar_extras': ['islamic', 'hebrew', 'persian'],
    'calendar_extras_scope': 'star', 'calendar_extra_cell': 'none',
    'seconds': True, 'locked': False, 'on_top': False, 'zone': 'Europe/Helsinki',
    'refresh_minutes': 77, 'provider': 'foreca', 'star_epoch': '2026-07-01',
    'weather_views': {'yr': 'graph', 'foreca': 'graph', 'fmi': 'graph', 'windy': 'map'},
    'star_side': 'left', 'clock_weather': True, 'sound': False,
    'windy_zoom': 9, 'windy_layer': 'temp', 'autostart': False,
    'place': {'name': 'Pöllönkangas, Oulu', 'latitude': 65.0701, 'longitude': 25.5071, 'timezone': 'Europe/Helsinki'},
    'widgets': {'combined': True, 'shadow': False, 'star': False, 'weather': True, 'daily': False, 'civil': False,
                'shadow_calendar': False, 'star_calendar': False},
}

def data_directory():
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'ajanlaskut-ja-saa'

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix='.state-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)

class State:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_directory() / 'state.json'
        self.data = {'version': 1, 'settings': copy.deepcopy(DEFAULTS), 'notes': {}, 'reminders': [], 'geometry': {}, 'imports': []}
        if self.path.exists():
            loaded = json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(loaded, dict) or loaded.get('version') != 1: raise ValueError('Tuntematon asetustiedosto')
            old_settings = loaded.get('settings', {})
            settings = {**copy.deepcopy(DEFAULTS), **old_settings}
            # Files written before clock-theme settings used calendar-specific palettes.
            if 'time_theme' not in old_settings: settings['time_theme'] = 'calendar'
            settings['widgets'] = {**DEFAULTS['widgets'], **settings.get('widgets', {})}
            old_views = old_settings.get('weather_views', {})
            if not isinstance(old_views, dict): raise ValueError('Virheelliset sään näyttötavat')
            settings['weather_views'] = {**DEFAULTS['weather_views'], **old_views}
            # Existing installations keep their selected windows until explicitly merged.
            if 'combined' not in old_settings.get('widgets', {}): settings['widgets']['combined'] = False
            profiles = copy.deepcopy(DEFAULT_PROFILES)
            old_profiles = old_settings.get('clock_profiles', {})
            if not isinstance(old_profiles, dict): raise ValueError('Virheelliset kellosisällöt')
            for key, values in old_profiles.items():
                if key not in profiles or not isinstance(values, dict): raise ValueError('Virheellinen kellowidget')
                profiles[key].update(values)
            if 'shadow' not in old_profiles: profiles['shadow']['weather'] = settings['clock_weather']
            settings['clock_profiles'] = profiles
            settings['clock_weather'] = profiles['shadow']['weather']
            loaded['settings'] = settings
            self.validate(loaded)
            self.data = loaded
        self.validate(self.data)

    @staticmethod
    def validate(data):
        if data.get('version') != 1: raise ValueError('Tuntematon asetustiedosto')
        settings = data['settings']
        ZoneInfo(settings['zone'])
        if settings['theme'] not in ('copper', 'frost', 'ubuntu', 'ubuntu2610_dark'): raise ValueError('Tuntematon teema')
        if settings['time_mode'] not in ('fixed', 'cycle', 'random'): raise ValueError('Tuntematon ajanlaskun vaihtotapa')
        if settings['time_system'] not in SYSTEMS: raise ValueError('Tuntematon ajanlasku')
        if settings['time_theme'] not in ('calendar', 'shared', 'ubuntu', 'ubuntu2610_dark'): raise ValueError('Tuntematon kelloteema')
        widget_themes = settings.get('widget_themes', {})
        if not isinstance(widget_themes, dict): raise ValueError('Virheelliset widgettiteemat')
        for key, selection in widget_themes.items():
            if (key not in DEFAULTS['widgets'] or not isinstance(selection, str)
                or selection not in ('shared', 'copper', 'frost', 'ubuntu', 'ubuntu2610_dark', 'calendar')
                or selection == 'calendar' and key not in PROFILE_KEYS):
                raise ValueError('Tuntematon widgettiteema')
        widget_text_colors = settings.get('widget_text_colors', {})
        if not isinstance(widget_text_colors, dict): raise ValueError('Virheelliset widgettien tekstivärit')
        for key, color in widget_text_colors.items():
            if (key not in DEFAULTS['widgets'] or not isinstance(color, str)
                or re.fullmatch(r'#[0-9a-fA-F]{6}', color) is None):
                raise ValueError('Virheellinen widgetin tekstiväri')
        clock_displays = settings.get('clock_displays', {})
        if not isinstance(clock_displays, dict): raise ValueError('Virheelliset kellon näyttötavat')
        for key, display in clock_displays.items():
            if (key not in PROFILE_KEYS or not isinstance(display, dict)
                or not set(display) <= {'mode', 'digit_scale', 'digit_color'}):
                raise ValueError('Virheellinen kellon näyttötapa')
            if 'mode' in display and (not isinstance(display['mode'], str)
                or display['mode'] not in ('theme', 'digital', 'analog', 'both')):
                raise ValueError('Tuntematon kellon näyttötapa')
            if 'digit_scale' in display and (type(display['digit_scale']) is not int
                or not 80 <= display['digit_scale'] <= 140):
                raise ValueError('Virheellinen digikellon koko')
            if 'digit_color' in display and (not isinstance(display['digit_color'], str)
                or re.fullmatch(r'#[0-9a-fA-F]{6}', display['digit_color']) is None):
                raise ValueError('Virheellinen digikellon väri')
        systems = settings['time_systems']
        if (not isinstance(systems, list) or not systems or any(s not in SYSTEMS for s in systems)
            or len(set(systems)) != len(systems)): raise ValueError('Valitse vähintään yksi eri ajanlasku.')
        extras = settings['calendar_extras']
        if (not isinstance(extras, list) or any(key not in SPECS for key in extras)
            or len(set(extras)) != len(extras)): raise ValueError('Tuntematon lisäkalenteri')
        if settings['calendar_extras_scope'] not in ('star', 'all'): raise ValueError('Virheellinen kalenterinäkymä')
        if settings['calendar_extra_cell'] not in ('none', *SPECS): raise ValueError('Tuntematon solupäiväys')
        profiles = settings['clock_profiles']
        if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_KEYS): raise ValueError('Virheelliset kellosisällöt')
        for profile in profiles.values():
            if (not isinstance(profile, dict) or set(profile) != set(FIELD_LABELS)
                or any(type(value) is not bool for value in profile.values()) or not any(profile.values())):
                raise ValueError('Valitse kellowidgettiin vähintään yksi sisältö.')
        if settings['wallpaper_mode'] not in ('single', 'slideshow'): raise ValueError('Tuntematon taustakuvatila')
        if settings['wallpaper_theme_target'] not in ('desktop', 'lock', 'both'):
            raise ValueError('Tuntematon teemataustan kohde')
        if not isinstance(settings['wallpaper_directory'], str) or len(settings['wallpaper_directory']) > 4096:
            raise ValueError('Virheellinen teemakansio')
        for key, lo, hi in [('scale', 60, 150), ('widget_text_scale', 80, 160), ('widget_clock_scale', 80, 140), ('opacity', 0, 100), ('refresh_minutes', 15, 180), ('windy_zoom', 3, 12), ('wallpaper_interval', 1, 77), ('time_interval', 1, 3600)]:
            if type(settings[key]) is not int or not lo <= settings[key] <= hi: raise ValueError('Virheellinen asetus: ' + key)
        for key in ('seconds', 'locked', 'on_top', 'clock_weather', 'sound', 'autostart', 'wallpaper_shuffle', 'wallpaper_follow_theme', 'icon_follow_theme', 'calendar_extras_visible'):
            if type(settings[key]) is not bool: raise ValueError('Virheellinen asetus: ' + key)
        if settings['provider'] not in ('yr', 'foreca', 'fmi', 'windy'): raise ValueError('Tuntematon sääpalvelu')
        views = settings['weather_views']
        if not isinstance(views, dict) or set(views) != set(DEFAULTS['weather_views']):
            raise ValueError('Virheelliset sään näyttötavat')
        for provider, mode in views.items():
            if not isinstance(mode, str) or mode not in (('graph',) if provider == 'yr' else ('graph', 'map')):
                raise ValueError('Tuntematon sään näyttötapa')
        if settings['star_side'] not in ('left', 'right', 'month'): raise ValueError('Virheellinen varjon puoli')
        if settings['windy_layer'] not in ('temp', 'wind', 'rain', 'clouds'): raise ValueError('Virheellinen karttakerros')
        from .weather.providers import Place
        from .models.star import CalendarClock
        Place(**settings['place'])
        CalendarClock('fixed', date.fromisoformat(settings['star_epoch']))
        if not isinstance(settings['font'], str) or len(settings['font']) > 120: raise ValueError('Virheellinen fontti')
        for key, value in settings['widgets'].items():
            if key not in DEFAULTS['widgets'] or type(value) is not bool: raise ValueError('Virheellinen widget')
        if not isinstance(data['notes'], dict): raise ValueError('Virheelliset merkinnät')
        for key, note in data['notes'].items():
            date.fromisoformat(key)
            if not isinstance(note, str): raise ValueError('Merkinnän pitää olla tekstiä')
        if not isinstance(data['reminders'], list): raise ValueError('Virheelliset muistutukset')
        identifiers = set()
        for reminder in data['reminders']:
            instant = datetime.fromisoformat(reminder['due'])
            if (instant.tzinfo is None or not isinstance(reminder['title'], str)
                or not reminder['title'].strip() or type(reminder['delivered']) is not bool
                or not isinstance(reminder['id'], str) or reminder['id'] in identifiers):
                raise ValueError('Virheellinen muistutus')
            identifiers.add(reminder['id'])
        if not isinstance(data.get('geometry', {}), dict): raise ValueError('Virheellinen sijainti')
        for key, values in data['geometry'].items():
            if (key not in (*DEFAULTS['widgets'], 'main') or not isinstance(values, list)
                or len(values) != (4 if key == 'main' else 2)
                or any(type(value) is not int for value in values)):
                raise ValueError('Virheellinen sijainti')
        sizes=data.get('widget_sizes',{})
        if not isinstance(sizes,dict):raise ValueError('Virheelliset widgetkoot')
        for key,values in sizes.items():
            if (key not in DEFAULTS['widgets'] or not isinstance(values,list) or len(values)!=2
                or any(type(value) is not int or not 1<=value<=16384 for value in values)):
                raise ValueError('Virheellinen widgetkoko')
        if not isinstance(data['imports'], list): raise ValueError('Virheelliset tuontitiedot')

    @property
    def settings(self): return copy.deepcopy(self.data['settings'])

    def commit(self, candidate):
        self.validate(candidate)
        atomic_json(self.path, candidate)
        self.data = candidate

    def configured_data(self, changes):
        candidate = copy.deepcopy(self.data)
        candidate['settings'].update(copy.deepcopy(changes))
        if 'clock_profiles' in changes:
            candidate['settings']['clock_weather'] = candidate['settings']['clock_profiles']['shadow']['weather']
        elif 'clock_weather' in changes:
            candidate['settings']['clock_profiles']['shadow']['weather'] = changes['clock_weather']
        self.validate(candidate)
        return candidate

    def configure(self, changes):
        candidate = self.configured_data(changes)
        self.commit(candidate)

    def geometry(self, key, value=None):
        if value is None: return copy.deepcopy(self.data['geometry'].get(key))
        candidate = copy.deepcopy(self.data)
        candidate['geometry'][key] = list(value)
        self.commit(candidate)

    def widget_size(self,key):return copy.deepcopy(self.data.get('widget_sizes',{}).get(key))

    def save_widget_geometry(self,key,position,size):
        candidate=copy.deepcopy(self.data)
        candidate['geometry'][key]=list(position)
        candidate.setdefault('widget_sizes',{})[key]=list(size)
        self.commit(candidate)

    def clear_widget_size(self,key):
        candidate=copy.deepcopy(self.data)
        candidate.get('widget_sizes',{}).pop(key,None)
        self.commit(candidate)

    def note(self, day): return self.data['notes'].get(day.isoformat(), '')

    def save_note(self, day, text, reminder=None):
        """Save a note and its optional reminder as one durable operation."""
        candidate = copy.deepcopy(self.data)
        if text.strip(): candidate['notes'][day.isoformat()] = text
        else: candidate['notes'].pop(day.isoformat(), None)
        if reminder is not None:
            candidate['reminders'].append(self.reminder(reminder, text))
        self.commit(candidate)

    @staticmethod
    def reminder(instant, title):
        if instant.tzinfo is None or not title.strip(): raise ValueError('Muistutukselle tarvitaan aika ja teksti')
        return {'id': uuid.uuid4().hex, 'due': instant.astimezone(timezone.utc).isoformat(), 'title': title.strip(), 'delivered': False}

    def add_reminder(self, instant, title):
        candidate = copy.deepcopy(self.data)
        candidate['reminders'].append(self.reminder(instant, title))
        self.commit(candidate)

    def take_due(self, now):
        candidate = copy.deepcopy(self.data)
        due = []
        for item in candidate['reminders']:
            if not item['delivered'] and datetime.fromisoformat(item['due']) <= now:
                item['delivered'] = True
                due.append(item.copy())
        if due: self.commit(candidate)
        return due

    def cancel_reminders(self, identifiers):
        candidate = copy.deepcopy(self.data)
        candidate['reminders'] = [r for r in candidate['reminders'] if r['id'] not in identifiers]
        self.commit(candidate)

    def import_legacy(self):
        """Copy local notes once. Existing applications' files are never changed."""
        if 'legacy-v1' in self.data['imports']: return
        from .calendar import Calendars
        from .models.shadow import CalendarDate, to_gregorian
        from .models.star import StarDate
        candidate = copy.deepcopy(self.data)
        root = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
        sources = [root / 'Goottikalenteri/events.json', root / 'tahtiaika/state.json']
        snapshots = {}
        for path in sources:
            if not path.is_file(): continue
            payload = json.loads(path.read_text(encoding='utf-8'))
            snapshots[str(path)] = payload
            for key, note in payload.get('events', {}).items():
                if not isinstance(note, str): continue
                if path.parent.name == 'Goottikalenteri':
                    civil = to_gregorian(CalendarDate.from_key(key))
                else:
                    namespace, star_key = key.split(':', 1)
                    if not namespace.startswith('fixed@'): continue
                    clock = Calendars(star_epoch=namespace[6:])
                    item = StarDate.from_key(star_key)
                    civil = clock.civil_date('star', item.year, item.month, item.day)
                previous = candidate['notes'].get(civil.isoformat(), '')
                if note not in previous:
                    candidate['notes'][civil.isoformat()] = (previous + '\n\n' + note).strip()
        candidate['imports'].append('legacy-v1')
        if snapshots: atomic_json(self.path.parent / 'alkuperaiset-kalenterit.json', snapshots)
        self.commit(candidate)

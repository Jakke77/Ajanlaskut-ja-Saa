"""Resolve shared appearance and sparse per-widget theme selections."""
from .clock_config import PROFILE_KEYS
from .theme import CALENDAR_THEMES, THEME_NAMES, THEMES


def widget_theme_selection(options, key):
    """An absent clock override preserves the legacy clock-theme preference."""
    fallback = options['time_theme'] if key in PROFILE_KEYS else 'shared'
    return options.get('widget_themes', {}).get(key, fallback)


def widget_theme(options, key, system=None, selection=None):
    """Resolve a saved selection, or a read-only preview's explicit selection."""
    if selection is None:
        selection = widget_theme_selection(options, key)
    if selection == 'shared':
        return THEMES[options['theme']]
    if selection == 'calendar':
        return CALENDAR_THEMES[system]
    return THEMES[selection]


def widget_theme_choices(key):
    """Return independent picker rows; calendar themes apply only to clocks."""
    choices = [('Sovelluksen yhteinen teema', 'shared')]
    if key in PROFILE_KEYS:
        choices.append(('Ajanlaskun oma teema', 'calendar'))
    for selection in ('copper', 'frost', 'ubuntu'):
        label = (('Ubuntu · analoginen kello' if key in PROFILE_KEYS
                  else 'Ubuntu · oranssi ja munakoiso') if selection == 'ubuntu'
                 else THEME_NAMES[selection])
        choices.append((label, selection))
    return choices

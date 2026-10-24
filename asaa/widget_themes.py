"""Resolve shared appearance and sparse per-widget theme selections."""
from dataclasses import replace
from .clock_config import PROFILE_KEYS
from .theme import CALENDAR_THEMES, THEME_NAMES, THEMES, available_themes
from .widget_colors import widget_text_color_selection


def widget_theme_selection(options, key):
    """An absent clock override preserves the legacy clock-theme preference."""
    fallback = options['time_theme'] if key in PROFILE_KEYS else 'shared'
    return options.get('widget_themes', {}).get(key, fallback)


def widget_theme(options, key, system=None, selection=None):
    """Resolve a saved selection, or a read-only preview's explicit selection."""
    if selection is None:
        selection = widget_theme_selection(options, key)
    if selection == 'shared':
        theme = THEMES[options['theme']]
    elif selection == 'calendar':
        theme = CALENDAR_THEMES[system]
    else:
        theme = THEMES[selection]
    color = widget_text_color_selection(options, key)
    return replace(theme, text=color, muted=color) if color is not None else theme


def widget_theme_choices(key):
    """Return independent picker rows; calendar themes apply only to clocks."""
    choices = [('Sovelluksen yhteinen teema', 'shared')]
    if key in PROFILE_KEYS:
        choices.append(('Ajanlaskun oma teema', 'calendar'))
    for selection in available_themes():
        label = ('Ubuntu · oranssi ja munakoiso' if selection == 'ubuntu'
                 else THEME_NAMES[selection])
        choices.append((label, selection))
    return choices

"""Resolve sparse clock display preferences without changing saved settings."""

CLOCK_DISPLAY_CHOICES = [
    ('Teeman oletus', 'theme'),
    ('Digitaalinen', 'digital'),
    ('Analoginen', 'analog'),
    ('Analoginen ja digitaalinen', 'both'),
]


def clock_display_selection(options, key):
    """Return a fresh draft; absent digit size continues to follow the global size."""
    return {'mode': 'theme', **options.get('clock_displays', {}).get(key, {})}


def clock_mode(options, key, theme, selection=None):
    """Resolve the effective palette's default, or a complete read-only draft."""
    if selection is None:
        selection = clock_display_selection(options, key)
    mode = selection.get('mode', 'theme')
    if mode == 'theme':
        return 'both' if theme.motif == 'ubuntu' else 'digital'
    return mode


def clock_digit_scale(options, key, selection=None):
    """A preview replaces the saved override; an absent size follows the global size."""
    if selection is None:
        selection = clock_display_selection(options, key)
    return selection.get('digit_scale', options['widget_clock_scale'])

"""Read sparse text-color preferences without changing themes or settings."""


def widget_text_color_selection(options, key):
    """Return a widget's saved RGB color, or None when it follows its theme."""
    return options.get('widget_text_colors', {}).get(key)

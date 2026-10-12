"""The dark Ubuntu theme's small foreground text remains readable on panels."""
import unittest

from asaa.theme import THEMES


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4
              for channel in channels]
    return sum(channel * weight for channel, weight in zip(linear, (.2126, .7152, .0722)))


class DarkUbuntuContrastTests(unittest.TestCase):
    def test_small_text_foregrounds_meet_aa_on_both_panel_surfaces(self):
        theme = THEMES['ubuntu2610_dark']
        for foreground in (theme.text, theme.muted, theme.accent):
            for background in (theme.background, theme.surface):
                with self.subTest(foreground=foreground, background=background):
                    low, high = sorted((luminance(foreground), luminance(background)))
                    self.assertGreaterEqual((high + .05) / (low + .05), 4.5)


if __name__ == '__main__': unittest.main()

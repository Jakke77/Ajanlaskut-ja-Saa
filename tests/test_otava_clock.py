"""Real Qt rendering of the seven-star symbolic seconds hand."""
from datetime import datetime
import math
import os
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

from asaa.clock_display import clock_mode
from asaa.otava import STARS
from asaa.theme import THEMES
from asaa.ubuntu_clock import otava_hand_shape, paint_clock


class OtavaClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        cls.app = QApplication.instance() or QApplication([])

    def render(self, second=0, *, seconds=True, style='otava', opacity=1):
        image = QImage(360, 360, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter(image)
        # Fix the larger hands to isolate the rotation of the constellation.
        with patch('asaa.ubuntu_clock.hand_angles', return_value=(305, 60, second*6)):
            digital = paint_clock(painter, QRectF(15, 15, 330, 330),
                datetime(2026, 10, 24, 10, 10, second), THEMES['copper'],
                'DejaVu Sans', opacity, seconds, style=style)
        painter.end()
        return image, digital

    def test_catalogue_pattern_has_seven_stars_and_fits_inside_dial(self):
        points = otava_hand_shape()
        self.assertEqual(len(points), 7)
        self.assertEqual(len(set(points)), 7)
        indices = {star.name: i for i, star in enumerate(STARS)}
        for point in points:
            self.assertTrue(all(math.isfinite(value) for value in point))
            self.assertLess(math.hypot(*point), .8)
        for name, expected_y in (('Alkaid', -.1), ('Dubhe', -.6)):
            point = points[indices[name]]
            self.assertAlmostEqual(point[0], 0)
            self.assertAlmostEqual(point[1], expected_y)

    def test_quarter_minute_moves_only_the_constellation_when_hands_are_fixed(self):
        noon, _ = self.render(0)
        right, _ = self.render(15)
        down, _ = self.render(30)
        self.assertNotEqual(noon, right)
        self.assertNotEqual(right, down)
        self.assertNotEqual(noon, down)
        hidden, _ = self.render(0, seconds=False)
        hidden_later, _ = self.render(15, seconds=False)
        self.assertEqual(hidden, hidden_later)

    def test_hiding_seconds_removes_constellation_and_retains_ordinary_hands(self):
        visible, _ = self.render()
        hidden, _ = self.render(seconds=False)
        standard, _ = self.render(seconds=False, style='standard')
        self.assertNotEqual(visible, hidden)
        self.assertEqual(hidden, standard)
        self.assertGreater(hidden.pixelColor(180, 180).alpha(), 0)

    def test_transparent_background_keeps_constellation_and_clock_content(self):
        visible, reserved = self.render(opacity=0)
        hidden, _ = self.render(opacity=0, seconds=False)
        self.assertEqual(visible.pixelColor(0, 0).alpha(), 0)
        self.assertNotEqual(visible, hidden)
        self.assertTrue(QRectF(15, 15, 330, 330).contains(reserved))

    def test_modes_are_explicit_and_independent_of_theme(self):
        options = {'clock_displays': {}}
        for theme in THEMES.values():
            for mode in ('otava', 'otava_both'):
                with self.subTest(mode=mode, theme=theme):
                    self.assertEqual(clock_mode(options, 'combined', theme,
                                                {'mode': mode}), mode)


if __name__ == '__main__':
    unittest.main()

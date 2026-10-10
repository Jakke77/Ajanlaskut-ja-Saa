"""Analogue time, optional layout and transparent dial rendering."""
import copy
from datetime import datetime
import os
import unittest
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication
from asaa.clock_config import DEFAULT_PROFILES, clock_layout
from asaa.theme import THEMES
from asaa.ubuntu_clock import hand_angles, paint_clock


class UbuntuClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
            cls.app = QApplication([])

    def test_hands_use_minutes_and_seconds_instead_of_only_whole_hours(self):
        self.assertEqual(hand_angles(datetime(2026, 10, 10, 3, 15, 30)), (97.75, 93, 180))
        self.assertEqual(hand_angles(datetime(2026, 10, 10, 15, 15, 30)), (97.75, 93, 180))
        self.assertEqual(hand_angles(datetime(2026, 10, 10, 0, 0)), (0, 0, 0))

    def test_analogue_slot_moves_following_content_without_overlap(self):
        profile = copy.deepcopy(DEFAULT_PROFILES['combined'])
        digital, digital_height = clock_layout(profile)
        analogue, analogue_height = clock_layout(profile, analog=True)
        self.assertEqual(analogue_height, digital_height + 256)
        self.assertEqual(analogue[0], ('clock', 56, 346))
        for old, new in zip(digital[1:], analogue[1:]):
            self.assertEqual(new, (old[0], old[1]+256, old[2]))
        for (_, y, height), (_, next_y, _) in zip(analogue, analogue[1:]):
            self.assertLessEqual(y+height, next_y)
        profile['clock'] = False
        self.assertEqual(clock_layout(profile, analog=True), clock_layout(profile))

    def render(self, opacity=1, seconds=True):
        image = QImage(360, 360, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter(image)
        digital = paint_clock(painter, QRectF(15, 15, 330, 330), datetime(2026, 10, 10, 10, 10, 30),
                              THEMES['ubuntu'], 'DejaVu Sans', opacity, seconds)
        painter.end()
        return image, digital

    def test_dial_keeps_transparent_corners_and_reserves_digital_time(self):
        image, digital = self.render()
        self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        self.assertGreater(image.pixelColor(180, 85).alpha(), 0)
        self.assertTrue(QRectF(15, 15, 330, 330).contains(digital))
        self.assertGreater(digital.width(), 170)

    def test_zero_opacity_keeps_hands_but_removes_background(self):
        image, _ = self.render(opacity=0)
        self.assertEqual(image.pixelColor(180, 85).alpha(), 0)
        self.assertGreater(image.pixelColor(180, 180).alpha(), 0)

    def test_seconds_setting_controls_the_second_hand(self):
        showing, _ = self.render(seconds=True)
        hidden, _ = self.render(seconds=False)
        self.assertNotEqual(showing, hidden)

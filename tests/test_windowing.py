"""Window hints and resize geometry must not mutate other desktop settings."""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from PyQt6.QtCore import QPoint, QPointF, QSize, QRect, Qt
from asaa.state import State
from asaa.windowing import resize_edges,resized_rect,apply_layer,skip_taskbar

class EdgeTests(unittest.TestCase):
    def test_all_eight_edges_and_inside(self):
        E=Qt.Edge
        for point,expected in [((1,1),E.LeftEdge|E.TopEdge),((298,1),E.RightEdge|E.TopEdge),
            ((1,198),E.LeftEdge|E.BottomEdge),((298,198),E.RightEdge|E.BottomEdge),
            ((1,99),E.LeftEdge),((298,99),E.RightEdge),((150,1),E.TopEdge),((150,198),E.BottomEdge),((150,99),E(0))]:
            self.assertEqual(resize_edges(QPointF(*point),QSize(300,200)),expected)
    def test_resize_anchors_opposite_corner_and_minimum(self):
        result=resized_rect(QRect(100,200,400,300),QPoint(500,500),Qt.Edge.LeftEdge|Qt.Edge.TopEdge,QSize(200,150),QSize(2000,2000))
        self.assertEqual(result,QRect(300,350,200,150))
    def test_resize_maximum_and_right_bottom_anchors(self):
        result=resized_rect(QRect(100,200,400,300),QPoint(2000,2000),Qt.Edge.RightEdge|Qt.Edge.BottomEdge,QSize(200,150),QSize(600,500))
        self.assertEqual(result,QRect(100,200,600,500))
    def test_resize_independent_single_dimensions(self):
        start=QRect(100,200,400,300)
        for edge,expected in [(Qt.Edge.LeftEdge,QRect(125,200,375,300)),(Qt.Edge.RightEdge,QRect(100,200,425,300)),
            (Qt.Edge.TopEdge,QRect(100,225,400,275)),(Qt.Edge.BottomEdge,QRect(100,200,400,325))]:
            self.assertEqual(resized_rect(start,QPoint(25,25),edge,QSize(200,150),QSize(2000,2000)),expected)

class SizeStateTests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory();self.path=Path(self.folder.name)/'state.json';self.state=State(self.path)
    def tearDown(self):self.folder.cleanup()
    def test_old_geometry_and_no_custom_size_are_unchanged(self):
        self.state.geometry('combined',(50,90));raw=self.path.read_bytes()
        fresh=State(self.path)
        self.assertEqual(fresh.geometry('combined'),[50,90]);self.assertIsNone(fresh.widget_size('combined'))
        self.assertEqual(self.path.read_bytes(),raw);self.assertNotIn('widget_sizes',fresh.data)
    def test_size_is_atomic_individual_and_copy(self):
        self.state.save_note(__import__('datetime').date(2026,10,8),'Säilytettävä merkintä')
        original=copy.deepcopy(self.state.data)
        self.state.save_widget_geometry('combined',(50,90),(420,520))
        fresh=State(self.path);self.assertEqual(fresh.widget_size('combined'),[420,520])
        value=fresh.widget_size('combined');value[0]=999
        self.assertEqual(fresh.widget_size('combined'),[420,520]);self.assertIsNone(fresh.widget_size('weather'))
        for key in ('notes','settings','reminders','imports'):self.assertEqual(fresh.data[key],original[key])
        self.assertEqual(fresh.geometry('combined'),[50,90]) # old versions accept this geometry
    def test_reset_only_one_size_keeps_positions(self):
        self.state.save_widget_geometry('combined',(50,90),(420,520));self.state.save_widget_geometry('weather',(10,20),(760,540))
        self.state.clear_widget_size('combined')
        self.assertIsNone(self.state.widget_size('combined'));self.assertEqual(self.state.widget_size('weather'),[760,540])
        self.assertEqual(self.state.geometry('combined'),[50,90])
    def test_invalid_sizes_never_commit(self):
        self.state.geometry('combined',(50,90));before=self.path.read_bytes()
        for key,value in [('main',[100,200]),('combined',[False,20]),('combined',[0,20]),('combined',[20000,20]),('combined',[20])]:
            with self.assertRaises(ValueError):self.state.save_widget_geometry(key,(50,90),value)
            self.assertEqual(self.path.read_bytes(),before)
    def test_failed_size_save_preserves_everything(self):
        original=copy.deepcopy(self.state.data)
        with patch('asaa.state.atomic_json',side_effect=OSError('Levy täynnä')):
            with self.assertRaises(OSError):self.state.save_widget_geometry('combined',(50,90),(420,520))
        self.assertEqual(self.state.data,original)

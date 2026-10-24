"""Display-mode transitions preserve user widget sizes and positions."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PyQt6.QtCore import QObject, QEvent, QPointF, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget
from asaa.state import State
from asaa.windowing import WidgetFrame


class Screen(QObject):
    geometryChanged=pyqtSignal(object)
    availableGeometryChanged=pyqtSignal(object)
    logicalDotsPerInchChanged=pyqtSignal(float)
    def __init__(self):
        super().__init__();self.area=QRect(0,0,1920,1040)


class Surface(QWidget):
    def __init__(self,screen):
        super().__init__(None,Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint)
        self.screen_model=screen;self.setGeometry(1500,740,300,200)
    def clamp(self):
        a=self.screen_model.area
        self.move(max(a.left(),min(self.x(),a.right()-self.width()+1)),
                  max(a.top(),min(self.y(),a.bottom()-self.height()+1)))
    def ensure_on_screen(self):self.clamp()


class DisplayGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.folder=TemporaryDirectory();self.state=State(Path(self.folder.name)/'state.json')
        self.state.configure({})
        self.screen=Screen();self.widget=Surface(self.screen)
        self.controller=SimpleNamespace(app=self.app,state=self.state,stopping=False,
            layers=SimpleNamespace(timer=Mock()),options={'locked':True},storage_error=Mock())
        with patch.object(self.app,'screens',return_value=[self.screen]):
            self.frame=WidgetFrame(self.widget,self.controller,'combined')
        self.frame.size(QSize(300,200));self.frame.remember_position()
        self.widget.show();self.app.processEvents();self.frame.display_timer.stop()
    def tearDown(self):
        self.controller.stopping=True;self.frame.display_timer.stop()
        self.widget.hide();self.widget.deleteLater()
        self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.app.processEvents()
        self.folder.cleanup()
    def restore(self):
        self.frame.display_timer.stop();self.frame.restore_display_geometry()
    def mode(self,rect):
        self.screen.area=rect;self.screen.geometryChanged.emit(rect)
        self.screen.availableGeometryChanged.emit(rect)
    def mouse(self,kind,local,global_point,button,buttons):
        event=QMouseEvent(kind,QPointF(*local),QPointF(*global_point),button,buttons,Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(self.widget,event)
    def test_game_resolution_round_trip_restores_size_and_original_position(self):
        original=self.widget.geometry();saved=self.state.path.read_bytes()
        for _ in range(3):
            self.mode(QRect(0,0,1280,680))
            self.widget.setGeometry(700,300,480,320)  # Native mode/DPI adjustment.
            self.restore()
            self.assertEqual(self.widget.size(),original.size())
            self.assertTrue(self.screen.area.contains(self.widget.geometry()))
            self.mode(QRect(0,0,1920,1040));self.restore()
            self.assertEqual(self.widget.geometry(),original)
            self.assertEqual(self.state.path.read_bytes(),saved)
    def test_dpi_event_restores_selected_custom_size_without_resaving_it(self):
        self.widget.setGeometry(1400,600,380,260);self.frame.persist()
        saved=self.state.path.read_bytes()
        self.widget.resize(608,416)
        QApplication.sendEvent(self.widget,QEvent(QEvent.Type.DevicePixelRatioChange))
        self.restore()
        self.assertEqual(self.widget.geometry(),QRect(1400,600,380,260))
        self.assertEqual(self.state.path.read_bytes(),saved)
    def test_display_restore_uses_latest_user_move_and_weather_clamp(self):
        self.frame.key='weather';self.state.geometry('weather',[1100,500])
        self.widget.setGeometry(600,300,480,320)
        self.screen.logicalDotsPerInchChanged.emit(144);self.restore()
        self.assertEqual(self.widget.geometry(),QRect(1100,500,300,200))
    def test_explicit_size_change_replaces_preferred_size(self):
        self.frame.size(QSize(330,220));self.widget.resize(500,400)
        self.frame.display_changed();self.restore()
        self.assertEqual(self.widget.size(),QSize(330,220))
    def test_interrupted_resize_cannot_follow_mouse_after_button_release(self):
        before=self.widget.geometry();saved=self.state.path.read_bytes()
        self.mouse(QEvent.Type.MouseButtonPress,(299,199),(1799,939),Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton)
        self.mouse(QEvent.Type.MouseMove,(399,299),(1899,1039),Qt.MouseButton.NoButton,Qt.MouseButton.NoButton)
        self.assertEqual(self.widget.geometry(),before);self.assertIsNone(self.frame.start)
        self.assertEqual(self.state.path.read_bytes(),saved)
    def test_game_activation_cancels_in_progress_resize_without_persisting(self):
        before=self.widget.geometry();saved=self.state.path.read_bytes()
        self.mouse(QEvent.Type.MouseButtonPress,(299,199),(1799,939),Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton)
        self.widget.resize(400,300)
        QApplication.sendEvent(self.widget,QEvent(QEvent.Type.WindowDeactivate))
        self.assertEqual(self.widget.geometry(),before);self.assertIsNone(self.frame.start)
        self.assertEqual(self.state.path.read_bytes(),saved)
    def test_real_held_button_resize_still_commits_user_size(self):
        self.mouse(QEvent.Type.MouseButtonPress,(299,199),(1799,939),Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton)
        self.mouse(QEvent.Type.MouseMove,(319,219),(1819,959),Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton)
        self.mouse(QEvent.Type.MouseButtonRelease,(319,219),(1819,959),Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton)
        self.assertEqual(self.state.widget_size('combined'),[320,220])
        self.assertEqual(self.frame.preferred.size(),QSize(320,220))


if __name__=='__main__':unittest.main()

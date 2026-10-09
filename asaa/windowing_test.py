"""Shared Qt acceptance for window priority and real edge mouse dispatch."""
import copy
from PyQt6.QtCore import Qt, QPoint, QPointF, QEvent
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtTest import QTest
from .state import State
from .windowing import layer_flags

def drag(widget,point,delta,cancel=False):
    origin=widget.mapToGlobal(point)
    for kind,global_point,button,buttons in [
        (QEvent.Type.MouseButtonPress,origin,Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseMove,origin+delta,Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton)]:
        event=QMouseEvent(kind,QPointF(widget.mapFromGlobal(global_point)),QPointF(global_point),button,buttons,Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(widget,event)
    if cancel:QTest.keyClick(widget,Qt.Key.Key_Escape)
    else:
        point=origin+delta
        QApplication.sendEvent(widget,QMouseEvent(QEvent.Type.MouseButtonRelease,QPointF(widget.mapFromGlobal(point)),
            QPointF(point),Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier))
    QApplication.processEvents()

def acceptance(controller,app):
    before=copy.deepcopy(controller.state.data)
    try:
        controller.configure({'on_top':True,'locked':True})
        controller.window.hide();app.processEvents();controller.layers.sync()
        for widget in controller.widgets.values():
            assert widget.windowType()==Qt.WindowType.Window
            assert layer_flags(widget)&Qt.WindowType.WindowStaysOnTopHint
        controller.window.showMaximized();app.processEvents()
        controller.open_calendar('star');app.processEvents()
        assert controller.window.isMaximized(),'Opening a page must not unmaximize the main window'
        for widget in controller.widgets.values():assert layer_flags(widget)&Qt.WindowType.WindowStaysOnBottomHint
        assert controller.options['on_top'],'Temporary priority must not overwrite the preference'
        controller.window.showMinimized();app.processEvents();controller.layers.sync()
        for widget in controller.widgets.values():assert layer_flags(widget)&Qt.WindowType.WindowStaysOnTopHint
        dialog=QDialog(controller.weather);dialog.show();app.processEvents();controller.layers.sync()
        assert dialog.isVisible(),'Changing the widget layer must not hide its popup'
        for widget in controller.widgets.values():assert layer_flags(widget)&Qt.WindowType.WindowStaysOnBottomHint
        dialog.hide();dialog.deleteLater();app.processEvents();controller.window.hide();controller.layers.sync()
        for key,widget in controller.widgets.items():
            widget.show();app.processEvents()
            others={other:item.size() for other,item in controller.widgets.items() if other!=key}
            settings=controller.options
            size=widget.size();drag(widget,QPoint(size.width()-2,size.height()-2),QPoint(36,28))
            assert widget.size().width()==size.width()+36 and widget.size().height()==size.height()+28,(key,size,widget.size())
            assert controller.state.widget_size(key)==[widget.width(),widget.height()]
            assert State(controller.state.path).widget_size(key)==controller.state.widget_size(key)
            assert controller.options==settings
            for other,expected in others.items():assert controller.widgets[other].size()==expected
            old_size=widget.size();widget.frame.reset();app.processEvents()
            assert controller.state.widget_size(key) is None and widget.size()!=old_size
        widget=controller.widgets['combined']
        for horizontal,vertical in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
            size=widget.size()
            point=QPoint(1 if horizontal<0 else size.width()-2 if horizontal>0 else size.width()//2,
                         1 if vertical<0 else size.height()-2 if vertical>0 else size.height()//2)
            drag(widget,point,QPoint(horizontal*18,vertical*14))
            assert widget.width()==size.width()+(18 if horizontal else 0)
            assert widget.height()==size.height()+(14 if vertical else 0)
        saved=copy.deepcopy(controller.state.data);rectangle=widget.geometry()
        drag(widget,QPoint(widget.width()-2,widget.height()-2),QPoint(35,25),cancel=True)
        assert widget.geometry()==rectangle and controller.state.data==saved
        widget.resize(widget.minimumSize());app.processEvents();assert not widget.grab().isNull()
        weather=controller.weather;weather.resize(820,560);app.processEvents();assert not weather.grab().isNull()
        weather.select_provider('windy');weather.load_windy();app.processEvents()
        assert weather.windy is not None and weather.rect().contains(weather.windy.geometry())
        assert before['notes']==controller.state.data['notes'] and before['reminders']==controller.state.data['reminders']
        print('PASS: independent windows, main/maximized/minimized/dialog priority; on-top preference preserved')
        print('PASS: all 8 widgets resize independently, all edges/corners, locked positions, persistence, reset and Escape')
    finally:
        controller.weather.select_provider(before['settings']['provider'])
        controller.state.commit(before)
        for key,widget in controller.widgets.items():
            if key=='weather':widget.apply_shared_options()
            else:widget.apply_options()
            widget.restore_position()
        controller.restore_widgets();controller.window.showNormal();controller.open_page('overview');app.processEvents()

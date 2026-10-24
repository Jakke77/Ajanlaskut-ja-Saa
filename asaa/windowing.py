"""Independent desktop windows, foreground priority and per-widget edge sizing."""
from functools import lru_cache
import ctypes as C
from PyQt6.QtCore import QObject, QEvent, QTimer, Qt, QRect, QSize, QPoint
from PyQt6.QtWidgets import QApplication, QDialog
from .platform_support import IS_WINDOWS

DESKTOP_FLAGS=(Qt.WindowType.Tool if IS_WINDOWS else Qt.WindowType.Window)|Qt.WindowType.FramelessWindowHint

class ClientData(C.Union):
    _fields_=[('b',C.c_char*20),('s',C.c_short*10),('l',C.c_long*5)]
class ClientMessage(C.Structure):
    _fields_=[('type',C.c_int),('serial',C.c_ulong),('send_event',C.c_int),('display',C.c_void_p),
              ('window',C.c_ulong),('message_type',C.c_ulong),('format',C.c_int),('data',ClientData)]
class XEvent(C.Union):
    _fields_=[('client',ClientMessage),('pad',C.c_long*24)]

@lru_cache(maxsize=1)
def x11():
    try:
        lib=C.CDLL('libX11.so.6')
        lib.XOpenDisplay.argtypes=[C.c_char_p];lib.XOpenDisplay.restype=C.c_void_p
        lib.XDefaultRootWindow.argtypes=[C.c_void_p];lib.XDefaultRootWindow.restype=C.c_ulong
        lib.XInternAtom.argtypes=[C.c_void_p,C.c_char_p,C.c_int];lib.XInternAtom.restype=C.c_ulong
        lib.XSendEvent.argtypes=[C.c_void_p,C.c_ulong,C.c_int,C.c_long,C.POINTER(XEvent)];lib.XSendEvent.restype=C.c_int
        lib.XFlush.argtypes=[C.c_void_p];lib.XFlush.restype=C.c_int
        display=lib.XOpenDisplay(None)
        return (lib,display) if display else None
    except OSError:return None

def skip_taskbar(widget):
    """Keep NORMAL windows out of the dock without the UTILITY stacking rule.

    EWMH client messages alter only the two skip states; Qt owns ABOVE/BELOW.
    Never used on offscreen/Wayland, or on an embedded preview.
    """
    try:
        if QApplication.platformName()!='xcb' or not widget.isVisible():return False
        connection=x11()
        if connection is None:return False
        lib,display=connection
        event=XEvent();event.client.type=33;event.client.send_event=1
        event.client.display=display;event.client.window=int(widget.winId())
        event.client.message_type=lib.XInternAtom(display,b'_NET_WM_STATE',0);event.client.format=32
        event.client.data.l[0]=1
        event.client.data.l[1]=lib.XInternAtom(display,b'_NET_WM_STATE_SKIP_TASKBAR',0)
        event.client.data.l[2]=lib.XInternAtom(display,b'_NET_WM_STATE_SKIP_PAGER',0)
        event.client.data.l[3]=1
        lib.XSendEvent(display,lib.XDefaultRootWindow(display),0,(1<<19)|(1<<20),C.byref(event));lib.XFlush(display)
        return True
    except RuntimeError:return False # a queued callback may outlive its QWidget

def apply_layer(widget,on_top):
    flags=DESKTOP_FLAGS|(Qt.WindowType.WindowStaysOnTopHint if on_top else Qt.WindowType.WindowStaysOnBottomHint)
    handle=widget.windowHandle()
    if layer_flags(widget)==flags:return
    if handle:
        # QWidget.setWindowFlags hides its dialogs and can recreate their parent.
        # QWindow changes the native stacking hints in place, preserving popups.
        handle.setFlags(flags)
        QTimer.singleShot(0,lambda:skip_taskbar(widget))
    else:widget.setWindowFlags(flags)

def layer_flags(widget):
    handle=widget.windowHandle()
    return handle.flags() if handle else widget.windowFlags()

class WindowLayers(QObject):
    """Own main/dialog windows outrank widgets without changing user settings."""
    def __init__(self,controller):
        super().__init__(controller);self.controller=controller
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.sync)
        controller.app.installEventFilter(self)
    def foreground_visible(self):
        main=self.controller.window
        return bool(main and main.isVisible() and not main.isMinimized()) or any(
            isinstance(window,QDialog) and window.isVisible() and not window.isMinimized()
            for window in QApplication.topLevelWidgets())
    def on_top(self):return self.controller.options['on_top'] and not self.foreground_visible()
    def sync(self):
        if self.controller.stopping:return
        for widget in self.controller.widgets.values():apply_layer(widget,self.on_top())
    def shutdown(self):
        self.timer.stop();self.controller.app.removeEventFilter(self)
    def eventFilter(self,watched,event):
        if (watched is self.controller.window or isinstance(watched,QDialog)) and event.type() in (
            QEvent.Type.Show,QEvent.Type.Hide,QEvent.Type.WindowStateChange):self.timer.start(0)
        return False

def resize_edges(point,size,margin=8):
    edges=Qt.Edge(0)
    if point.x()<margin:edges|=Qt.Edge.LeftEdge
    elif point.x()>=size.width()-margin:edges|=Qt.Edge.RightEdge
    if point.y()<margin:edges|=Qt.Edge.TopEdge
    elif point.y()>=size.height()-margin:edges|=Qt.Edge.BottomEdge
    return edges

def resized_rect(start,delta,edges,minimum,maximum):
    """Anchor the opposite edge, including at minimum/maximum size."""
    x,y,w,h=start.x(),start.y(),start.width(),start.height()
    if edges&Qt.Edge.LeftEdge:
        width=max(minimum.width(),min(maximum.width(),w-delta.x()));x+=w-width;w=width
    elif edges&Qt.Edge.RightEdge:w=max(minimum.width(),min(maximum.width(),w+delta.x()))
    if edges&Qt.Edge.TopEdge:
        height=max(minimum.height(),min(maximum.height(),h-delta.y()));y+=h-height;h=height
    elif edges&Qt.Edge.BottomEdge:h=max(minimum.height(),min(maximum.height(),h+delta.y()))
    return QRect(x,y,w,h)

class WidgetFrame(QObject):
    """Eight resize edges. Movement lock deliberately does not lock sizing.

    Manual pointer-grab resizing is deterministic on the supported XWayland
    desktop and also testable offscreen; only release writes the final geometry.
    """
    def __init__(self,widget,controller,key):
        super().__init__(widget);self.widget,self.controller,self.key=widget,controller,key
        self.edges=Qt.Edge(0);self.start=None;self.origin=None
        self.preferred=QRect(widget.geometry());self._handle=None
        self.display_timer=QTimer(self);self.display_timer.setSingleShot(True)
        self.display_timer.setInterval(350);self.display_timer.timeout.connect(self.restore_display_geometry)
        self._screens=set()
        app=controller.app
        for screen in app.screens():self.watch_screen(screen)
        app.screenAdded.connect(self.watch_screen);app.screenRemoved.connect(self.display_changed)
        widget.setMouseTracking(True);widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        widget.installEventFilter(self)
    def size(self,default):
        saved=self.controller.state.widget_size(self.key)
        result=QSize(*saved) if saved else default
        self.preferred.setSize(result)
        return result
    def remember_position(self):
        self.preferred.moveTopLeft(self.widget.pos())
    def watch_screen(self,screen):
        if screen in self._screens:return
        self._screens.add(screen)
        for signal in (screen.geometryChanged,screen.availableGeometryChanged,screen.logicalDotsPerInchChanged):
            signal.connect(self.display_changed)
        self.display_changed()
    def display_changed(self,*args):
        self.cancel_resize()
        for attribute in ('offset','drag_offset'):
            if hasattr(self.widget,attribute):setattr(self.widget,attribute,None)
        # Native display changes may arrive as a series during full-screen games.
        # They must never become a new user size or overwrite the saved position.
        self.display_timer.start()
    def restore_display_geometry(self):
        if self.controller.stopping or self.start is not None or not self.widget.isVisible():return
        position=self.controller.state.geometry(self.key)
        rect=QRect(self.preferred)
        if position:rect.moveTopLeft(QPoint(*position[:2]))
        self.widget.setGeometry(rect)
        if self.key=='weather':self.widget.ensure_on_screen()
        else:self.widget.clamp()
    def cancel_resize(self):
        if self.start is None:return
        rect=self.start;self.start=None;self.edges=Qt.Edge(0);self.origin=None
        self.widget.releaseMouse();self.widget.setGeometry(rect)
    def persist(self):
        widget=self.widget
        try:
            self.controller.state.save_widget_geometry(self.key,(widget.x(),widget.y()),(widget.width(),widget.height()))
            self.preferred=QRect(widget.geometry())
        except OSError as error:self.controller.storage_error(error)
    def reset(self):
        try:self.controller.state.clear_widget_size(self.key)
        except OSError as error:self.controller.storage_error(error);return
        if self.key=='weather':self.widget.apply_shared_options()
        else:self.widget.apply_options()
    def cursor(self,edges):
        horizontal=bool(edges&(Qt.Edge.LeftEdge|Qt.Edge.RightEdge));vertical=bool(edges&(Qt.Edge.TopEdge|Qt.Edge.BottomEdge))
        if horizontal and vertical:
            same=bool(edges&Qt.Edge.LeftEdge)==bool(edges&Qt.Edge.TopEdge)
            return Qt.CursorShape.SizeFDiagCursor if same else Qt.CursorShape.SizeBDiagCursor
        if horizontal:return Qt.CursorShape.SizeHorCursor
        if vertical:return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor if self.controller.options['locked'] else Qt.CursorShape.SizeAllCursor
    def eventFilter(self,watched,event):
        kind=event.type();widget=self.widget
        if kind==QEvent.Type.Show:
            handle=widget.windowHandle()
            if handle is not None and handle is not self._handle:
                self._handle=handle;handle.screenChanged.connect(self.display_changed)
            QTimer.singleShot(0,lambda:skip_taskbar(widget))
            self.controller.layers.timer.start(0)
            self.display_timer.start()
        elif kind==QEvent.Type.DevicePixelRatioChange:
            self.display_changed()
        elif kind==QEvent.Type.MouseButtonPress and event.button()==Qt.MouseButton.LeftButton:
            edges=resize_edges(event.position(),widget.size())
            if edges:
                self.edges=edges;self.start=widget.geometry();self.origin=event.globalPosition().toPoint()
                widget.setFocus(Qt.FocusReason.MouseFocusReason);widget.grabMouse();event.accept();return True
        elif kind==QEvent.Type.MouseMove:
            edges=self.edges or resize_edges(event.position(),widget.size());widget.setCursor(self.cursor(edges))
            if self.start is not None:
                if not event.buttons()&Qt.MouseButton.LeftButton:
                    self.cancel_resize();return False
                widget.setGeometry(resized_rect(self.start,event.globalPosition().toPoint()-self.origin,
                    self.edges,widget.minimumSize(),QSize(min(widget.maximumWidth(),16384),min(widget.maximumHeight(),16384))))
                event.accept();return True
        elif kind==QEvent.Type.MouseButtonRelease and self.start is not None:
            if event.button()!=Qt.MouseButton.LeftButton:return False
            self.start=None;self.edges=Qt.Edge(0);self.origin=None;widget.releaseMouse()
            if self.key=='weather':widget.ensure_on_screen()
            else:widget.clamp()
            self.persist();event.accept();return True
        elif kind==QEvent.Type.KeyPress and event.key()==Qt.Key.Key_Escape and self.start is not None:
            self.cancel_resize();return True
        elif kind in (QEvent.Type.Hide,QEvent.Type.UngrabMouse,QEvent.Type.WindowDeactivate):
            self.cancel_resize()
        return False

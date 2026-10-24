"""Read Windows personalization and accessibility colors without changing them."""
import ctypes
from ctypes import wintypes
from .platform_support import IS_WINDOWS


def apps_are_dark():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
            return winreg.QueryValueEx(key, 'AppsUseLightTheme')[0] == 0
    except (ImportError, OSError):
        return False


def high_contrast():
    if not IS_WINDOWS:
        return False
    class HighContrast(ctypes.Structure):
        _fields_ = [('size', wintypes.UINT), ('flags', wintypes.DWORD), ('scheme', wintypes.LPWSTR)]
    value = HighContrast(); value.size = ctypes.sizeof(value)
    return bool(ctypes.windll.user32.SystemParametersInfoW(0x0042, value.size,
                                                          ctypes.byref(value), 0) and value.flags & 1)


def system_color(index):
    value = ctypes.windll.user32.GetSysColor(index)
    return f'#{value & 255:02x}{(value >> 8) & 255:02x}{(value >> 16) & 255:02x}'


def accent_color():
    if IS_WINDOWS:
        color, opaque = wintypes.DWORD(), wintypes.BOOL()
        try:
            if ctypes.windll.dwmapi.DwmGetColorizationColor(ctypes.byref(color), ctypes.byref(opaque)) == 0:
                return f'#{color.value & 0xffffff:06x}'
        except (OSError, AttributeError):
            pass
    return '#0078d7'


def windows_colors(mode):
    if high_contrast():
        return dict(background=system_color(5), surface=system_color(15), border=system_color(6),
                    accent=system_color(13), text=system_color(8), muted=system_color(8), motif='windows')
    dark = mode == 'windows_dark' or mode == 'windows_system' and apps_are_dark()
    if dark:
        return dict(background='#202020', surface='#2b2b2b', border='#767676', accent=accent_color(),
                    text='#ffffff', muted='#d0d0d0', motif='windows')
    return dict(background='#ffffff', surface='#f0f0f0', border='#767676', accent=accent_color(),
                text='#000000', muted='#505050', motif='windows')


def titlebar_theme(widget, dark):
    if IS_WINDOWS:
        value = wintypes.BOOL(dark)
        try:
            api = ctypes.windll.dwmapi.DwmSetWindowAttribute
            api.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
            api.restype = ctypes.c_long
            # Attribute 20 is supported on recent Windows 10; 19 on older builds.
            if api(int(widget.winId()), 20, ctypes.byref(value), ctypes.sizeof(value)) != 0:
                api(int(widget.winId()), 19, ctypes.byref(value), ctypes.sizeof(value))
        except (OSError, AttributeError, RuntimeError):
            pass


from PyQt6.QtCore import QObject, QEvent, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication


class WindowsAppearanceWatcher(QObject):
    """Track OS changes, including while running only tray/desktop widgets."""
    def __init__(self, controller):
        super().__init__(controller); self.controller = controller
        self.timer = QTimer(self); self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh); self.timer.start()
        controller.app.installEventFilter(self)
        controller.settings_changed.connect(self.titlebars)

    def refresh(self):
        from .theme import refresh_windows_themes, apply_theme
        if self.controller.stopping or not refresh_windows_themes():
            return
        apply_theme(self.controller.app, self.controller.options)
        self.controller.weather.apply_widget_theme()
        self.controller.settings_changed.emit(); self.controller.clock_changed.emit()

    def titlebars(self):
        from .theme import THEMES
        theme = THEMES[self.controller.options['theme']]
        dark = QColor(theme.background).lightnessF() < .5
        for widget in QApplication.topLevelWidgets():
            if widget.isVisible(): titlebar_theme(widget, dark)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Show:
            QTimer.singleShot(0, self.titlebars)
        return False

    def shutdown(self):
        self.timer.stop(); self.controller.app.removeEventFilter(self)

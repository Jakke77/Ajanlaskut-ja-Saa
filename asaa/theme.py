"""Shared palette and artwork, based on the Pöllönkangas copper widget."""
from dataclasses import dataclass
from math import cos, radians, sin
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QPalette, QLinearGradient, QPen

@dataclass(frozen=True)
class Theme:
    background: str
    surface: str
    border: str
    accent: str
    text: str
    muted: str
    motif: str = 'orbits'

THEMES = {
    'copper': Theme('#100e15', '#1e1822', '#68483e', '#ef986e', '#f6e5db', '#c2aeb8'),
    'frost': Theme('#10151e', '#192330', '#405b72', '#a3cfe9', '#e9f4fb', '#a3bacb'),
    'ubuntu': Theme('#17121f', '#2b1b33', '#6e3c36', '#e95420', '#fff4ed', '#c6aebd', 'ubuntu'),
    'ubuntu2610_dark': Theme('#000000', '#2C001E', '#5E2750', '#E95420', '#FFFFFF', '#AEA79F', 'ubuntu'),
    'blood': Theme('#070508', '#160b12', '#56303c', '#f0788b', '#f5eaf0', '#bfa9b4', 'blood'),
}
THEME_NAMES = {'copper': 'Kupari', 'frost': 'Halla', 'ubuntu': 'Ubuntu',
               'ubuntu2610_dark': 'Ubuntu 26.10 Dark', 'blood': 'Veriyö'}
THEME_LABELS = {'copper': 'Kupari · Pöllönkankaan sää', 'frost': 'Halla · yön sininen',
                'ubuntu': 'Ubuntu · oranssi ja munakoiso',
                'ubuntu2610_dark': 'Ubuntu 26.10 Dark', 'blood': 'Veri Aika · Veriyö'}

# Clock-only tokens: never replace the shared palette of the standalone weather graph.
CALENDAR_THEMES = {
    'shadow': THEMES['copper'],
    'star': Theme('#0c191e', '#14292d', '#53605a', '#e6c37a', '#f5ead0', '#b4c4bd', 'stars'),
    'civil': Theme('#111c28', '#1d2b3b', '#4d657a', '#b8d9f0', '#eef5fc', '#b7c7d5', 'ledger'),
    'blood': THEMES['blood'],
}
CALENDAR_THEME_NAMES = {'shadow': 'Kupari', 'star': 'Astraali', 'civil': 'Aamunkajo', 'blood': 'Veriyö'}

def apply_theme(app, options):
    theme = THEMES[options['theme']]
    font=QFont(options['font']);font.setPixelSize(13);app.setFont(font)
    palette = QPalette()
    for role, value in [('Window', theme.background), ('WindowText', theme.text), ('Base', theme.surface),
                        ('Text', theme.text), ('Button', theme.surface), ('ButtonText', theme.text),
                        ('Highlight', theme.accent), ('HighlightedText', theme.background)]:
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(value))
    app.setPalette(palette)
    app.setStyleSheet(f'''
QMainWindow, QDialog {{ background: {theme.background}; }}
QWidget {{ color: {theme.text}; }}
QLabel {{ background: transparent; }}
QLabel#muted {{ color: {theme.muted}; }}
QLabel#eyebrow {{ color: {theme.accent}; font-size: 11px; font-weight: bold; letter-spacing: 2px; }}
QLabel#heading {{ font-size: 27px; font-weight: bold; }}
QLabel#clock {{ font-size: 48px; font-weight: bold; color: {theme.text}; }}
QFrame#card {{ background: {theme.surface}; border: 1px solid {theme.border}; border-radius: 16px; }}
QFrame#sidebar {{ background: {theme.surface}; border-right: 1px solid {theme.border}; }}
QPushButton, QToolButton {{ background: {theme.surface}; border: 1px solid {theme.border}; border-radius: 8px; padding: 8px 14px; }}
QPushButton:hover, QToolButton:hover {{ border-color: {theme.accent}; }}
QPushButton:focus, QToolButton:focus {{ border: 2px solid {theme.accent}; }}
QPushButton:checked, QPushButton#primary {{ background: {theme.accent}; color: {theme.background}; font-weight: bold; }}
QPushButton:disabled {{ color: {theme.muted}; }}
QPushButton#nav {{ border: 0; text-align: left; padding: 13px 18px; }}
QComboBox, QFontComboBox, QSpinBox, QLineEdit, QTextEdit, QTimeEdit, QDateEdit {{ background: {theme.surface}; color: {theme.text}; border: 1px solid {theme.border}; border-radius: 6px; padding: 7px; selection-background-color: {theme.accent}; selection-color: {theme.background}; }}
QHeaderView::section {{ background: {theme.surface}; color: {theme.text}; padding: 6px; border: 1px solid {theme.border}; }}
QComboBox QAbstractItemView, QMenu {{ background: {theme.surface}; color: {theme.text}; }}
QMenu::item {{ padding: 8px 18px; }} QMenu::item:selected {{ background: {theme.border}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {theme.border}; border-radius: 5px; }}
QCheckBox::indicator:checked {{ background: {theme.accent}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: 0; }}
QScrollBar:vertical {{ background: {theme.background}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {theme.border}; border-radius: 5px; min-height: 35px; }}
QToolTip {{ background: {theme.surface}; color: {theme.text}; border: 1px solid {theme.accent}; }}
QListWidget {{ background: {theme.surface}; border: 1px solid {theme.border}; border-radius: 8px; }}
QListWidget::item {{ padding: 8px; }}
''')

def paint_panel(p, rect, theme, opacity=1):
    p.save()
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    for at, value in [(0, theme.surface), (1, theme.background)]:
        color = QColor(value); color.setAlphaF(opacity); gradient.setColorAt(at, color)
    p.setBrush(gradient)
    border = QColor(theme.accent); border.setAlphaF(opacity * .5)
    p.setPen(QPen(border, 1))
    p.drawRoundedRect(rect.adjusted(.5, .5, -.5, -.5), 16, 16)
    p.setClipRect(rect)
    orbit = QColor(theme.accent); orbit.setAlphaF(opacity * .12)
    p.setPen(QPen(orbit, 1)); p.setBrush(Qt.BrushStyle.NoBrush)
    size = rect.width() * .75
    if theme.motif == 'ubuntu':
        center = QPointF(rect.right()-52, rect.top()+52)
        radius = 28
        ring = QRectF(center.x()-radius, center.y()-radius, radius*2, radius*2)
        p.setPen(QPen(orbit, 4))
        for angle in (30, 150, 270):
            p.drawArc(ring, (angle+18)*16, 84*16)
            direction = radians(angle)
            point = center + QPointF(cos(direction)*radius, -sin(direction)*radius)
            p.setBrush(orbit); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(point, 5, 5)
            p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(orbit, 4))
        p.setPen(QPen(orbit, 1))
    elif theme.motif == 'blood':
        # A static, faint decorative motif. Current Oulu sky positions are drawn
        # separately by the Otava views, never inferred from this panel artwork.
        origin = QPointF(rect.right()-148, rect.top()+22)
        points = [origin+QPointF(x, y) for x, y in
                  ((0, 4), (24, 12), (45, 29), (66, 46), (108, 42), (103, 72), (64, 75))]
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)):
            p.drawLine(points[a], points[b])
        p.setBrush(orbit); p.setPen(Qt.PenStyle.NoPen)
        for point in points:
            p.drawEllipse(point, 2, 2)
    elif theme.motif == 'ledger':
        for offset in range(5):
            x = rect.right()-122+offset*28
            p.drawLine(QPointF(x, rect.top()+16), QPointF(x, rect.top()+110))
            y = rect.top()+26+offset*18
            p.drawLine(QPointF(rect.right()-135, y), QPointF(rect.right()-8, y))
    else:
        for extra in [0, 18, 36]:
            p.drawEllipse(QRectF(rect.right()-size*.7-extra, rect.top()-size*.4-extra, size+extra*2, size+extra*2))
    for i in range(22):
        p.drawPoint(QPointF(rect.x()+(i*83+41) % max(1,int(rect.width())), rect.y()+(i*37+11) % max(1,int(rect.height()))))
    p.restore()

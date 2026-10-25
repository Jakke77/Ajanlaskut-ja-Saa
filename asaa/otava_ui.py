"""Seven real Otava stars, projected against Oulu's northern sky.

The sky picture follows sidereal time, independently of the decorative
second-hand constellation in the optional Otavakello clock face.
"""
from datetime import timezone
from math import hypot

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QWidget, QSizePolicy

from .otava import LINKS, sky_at, sampled_sky, tail_description
from .theme import THEMES


def _font(painter, pixels, bold=False):
    font = QFont(painter.font())
    font.setPixelSize(pixels)
    font.setBold(bold)
    painter.setFont(font)


def paint_otava(painter, rect, moment, theme, labels=False, stars=None):
    """Paint the actual north-facing sky; return seven screen star positions.

    The projection's origin is the north celestial pole, not the constellation's
    moving centre.  Up points towards the zenith and right towards east.  A
    fixed scale preserves both the true sidereal orientation and its movement.
    """
    stars = sky_at(moment) if stars is None else stars
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setClipRect(rect)
    center = rect.center()
    radius = max(1.0, min(rect.width(), rect.height()) * .36)
    accent = QColor(theme.accent)
    faint = QColor(theme.accent)
    faint.setAlpha(38)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(faint, 1))
    painter.drawEllipse(center, radius, radius)
    painter.drawEllipse(center, radius * .48, radius * .48)
    painter.drawLine(center + QPointF(-4, 0), center + QPointF(4, 0))
    painter.drawLine(center + QPointF(0, -4), center + QPointF(0, 4))
    # Reference directions are fixed while the seven stars move around them.
    _font(painter, 10)
    painter.setPen(QColor(theme.muted))
    painter.drawText(QRectF(rect.left(), rect.top(), rect.width(), 18),
                     Qt.AlignmentFlag.AlignHCenter, 'Zeniitti ↑')
    painter.drawText(QRectF(rect.left(), center.y()-8, 24, 16),
                     Qt.AlignmentFlag.AlignLeft, 'L ←')
    painter.drawText(QRectF(rect.right()-24, center.y()-8, 24, 16),
                     Qt.AlignmentFlag.AlignRight, '→ I')
    if labels:
        painter.drawText(QRectF(center.x() + 8, center.y() + 4, radius, 18),
                         Qt.AlignmentFlag.AlignLeft, 'Taivaannapa')
    points = tuple(QPointF(center.x() + star.x * radius,
                          center.y() + star.y * radius) for star in stars)
    line = QColor(theme.accent)
    line.setAlpha(180)
    painter.setPen(QPen(line, max(1.1, radius / 100)))
    for first, last in LINKS:
        painter.drawLine(points[first], points[last])
    occupied = []
    for index, (star, point) in enumerate(zip(stars, points)):
        size = max(1.8, 3.5 - star.magnitude * .35)
        glow = QRadialGradient(point, size * 5)
        middle = QColor(theme.accent)
        middle.setAlpha(95)
        clear = QColor(theme.accent)
        clear.setAlpha(0)
        glow.setColorAt(0, middle)
        glow.setColorAt(1, clear)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(point, size * 5, size * 5)
        painter.setBrush(QColor(theme.text))
        painter.drawEllipse(point, size, size)
        if star.name == 'Alkaid':
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(accent, 1.3))
            painter.drawEllipse(point, size+3, size+3)
        if labels:
            _font(painter, 11)
            metrics = QFontMetricsF(painter.font())
            width = metrics.horizontalAdvance(star.name) + 6
            dx, dy = point.x() - center.x(), point.y() - center.y()
            distance = max(1, hypot(dx, dy))
            left = point.x() + dx / distance * 12
            if dx < 0:
                left -= width
            top = point.y() + dy / distance * 12 - 8
            for offset in (0, 16, -16, 32, -32):
                area = QRectF(left, top + offset, width, 16)
                if rect.contains(area) and not any(area.intersects(other) for other in occupied):
                    break
            else:
                continue
            occupied.append(area)
            painter.setPen(QColor(theme.muted))
            painter.drawText(area, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             star.name)
    painter.restore()
    return points


class OtavaView(QWidget):
    """A live sky card shared by the Veri Aika page and dashboard."""

    def __init__(self, controller, compact=False, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.compact = compact
        self.moment = None
        self.sky = ()
        self.snapshot = None
        self.error = ''
        self.drawn_points = ()
        self.setMinimumSize(180 if compact else 320, 150 if compact else 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        controller.clock_changed.connect(self.tick)
        controller.settings_changed.connect(self.update)
        self.tick()

    def tick(self):
        self.set_moment(self.controller.calendars.now())

    def set_moment(self, moment):
        self.moment = moment
        try:
            self.snapshot = sampled_sky(self.controller, moment)
            self.sky = self.snapshot.stars
            self.error = ''
            lines = ['Otava Oulun pohjoistaivaalla',
                     'Tarkistettu: '+self.snapshot.moment.strftime('%d.%m.%Y %H:%M:%S UTC'),
                     'Seuraava tarkistus: '+self.snapshot.next_update.strftime('%H:%M:%S UTC'),
                     'Ylös: zeniitti · oikealle: itä · vasemmalle: länsi · keskus: pohjoinen taivaannapa',
                     'Ympyröity tähti: hännän pää Alkaid', tail_description(self.sky)]
            lines.extend(f'{star.name}: korkeus {star.altitude:.1f}°, suunta {star.azimuth:.1f}°'
                         for star in self.sky)
            description = '\n'.join(lines)
        except (TypeError, ValueError, OverflowError) as error:
            self.sky = ()
            self.error = str(error)
            description = 'Otavan asentoa ei voida laskea: ' + self.error
        self.setAccessibleName(description)
        self.setToolTip(description)
        self.update()

    def paintEvent(self, event):
        theme = THEMES[self.controller.options['theme']]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outer = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        gradient = QLinearGradient(outer.topLeft(), outer.bottomRight())
        gradient.setColorAt(0, QColor(theme.surface))
        gradient.setColorAt(1, QColor(theme.background))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(theme.border), 1))
        painter.drawRoundedRect(outer, 15, 15)
        chart = outer.adjusted(12, 24, -12, -53)
        if self.sky:
            self.drawn_points = paint_otava(painter, chart, self.snapshot.moment, theme,
                                           labels=not self.compact, stars=self.sky)
        else:
            self.drawn_points = ()
            painter.setPen(QColor(theme.muted))
            _font(painter, 12)
            painter.drawText(chart, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                             'Otavan asentoa ei voida laskea.\n' + self.error)
        painter.setPen(QColor(theme.accent))
        _font(painter, 10, True)
        painter.drawText(QRectF(14, 6, self.width() - 28, 18),
                         Qt.AlignmentFlag.AlignLeft, 'OTAVA · OULU')
        _font(painter, 10)
        painter.setPen(QColor(theme.muted))
        if self.moment is not None and not self.error:
            from .blood_time import ZONE
            stamp = self.snapshot.moment.astimezone(ZONE).strftime('%H:%M %Z')
            _font(painter, 9 if self.compact else 11)
            painter.drawText(QRectF(8, self.height()-48, self.width()-16, 20),
                             Qt.AlignmentFlag.AlignHCenter, '○ '+tail_description(self.sky))
            painter.drawText(QRectF(8, self.height()-27, self.width()-16, 20),
                             Qt.AlignmentFlag.AlignHCenter, f'Tarkistettu {stamp} · 26 min välein')
        painter.end()

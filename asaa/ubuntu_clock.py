"""Original Ubuntu-inspired analogue dial, drawn locally with Qt."""
import math
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QLinearGradient, QPen, QRadialGradient


def hand_angles(now):
    """Clockwise angles from twelve, using the same local time as the digital clock."""
    seconds = now.second
    minutes = now.minute + seconds / 60
    hours = now.hour % 12 + minutes / 60
    return hours * 30, minutes * 6, seconds * 6


def ubuntu_mark(painter, center, radius, color):
    """Three companions and a broken ring, in original vector geometry."""
    painter.save()
    painter.translate(center)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(color, radius * .25, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
    circle = QRectF(-radius, -radius, 2 * radius, 2 * radius)
    for angle in (0, 120, 240):
        painter.drawArc(circle, (angle + 22) * 16, 76 * 16)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    for angle in (0, 120, 240):
        radians = math.radians(angle)
        painter.drawEllipse(QPointF(math.cos(radians) * radius * 1.27,
                                   -math.sin(radians) * radius * 1.27), radius * .24, radius * .24)
    painter.restore()


def paint_clock(painter, rect, now, theme, font_family, opacity=1, seconds=True, clock_scale=1):
    """Paint the dial and return a reserved rectangle for the digital time."""
    painter.save()
    painter.setRenderHint(painter.RenderHint.Antialiasing)
    diameter = min(rect.width(), rect.height())
    center = rect.center()
    radius = diameter / 2
    circle = QRectF(center.x()-radius, center.y()-radius, diameter, diameter)
    accent, text = QColor(theme.accent), QColor(theme.text)
    muted = QColor(theme.muted)
    if opacity > 0:
        surface = QRadialGradient(center-QPointF(radius*.25, radius*.35), diameter)
        for at, value in ((0, theme.surface), (1, theme.background)):
            color = QColor(value);color.setAlphaF(opacity);surface.setColorAt(at, color)
        painter.setBrush(surface)
        border = QColor(theme.border);border.setAlphaF(opacity)
        painter.setPen(QPen(border, 2))
        painter.drawEllipse(circle)
        rim = QLinearGradient(circle.topLeft(), circle.bottomRight())
        for at, alpha in ((0, .9), (.45, .18), (1, .65)):
            color = QColor(theme.accent);color.setAlphaF(opacity*alpha);rim.setColorAt(at, color)
        painter.setPen(QPen(rim, 2.5));painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(circle.adjusted(7, 7, -7, -7))
        line = QColor(theme.accent);line.setAlphaF(opacity*.2)
        painter.setPen(QPen(line, 1))
        painter.drawEllipse(circle.adjusted(16, 16, -16, -16))
        if theme.motif == 'ubuntu':
            emblem = QColor(theme.accent);emblem.setAlphaF(opacity*.85)
            ubuntu_mark(painter, center-QPointF(0, radius*.37), radius*.075, emblem)

    # Marks and hands are clock content: they remain readable on a zero-opacity background.
    for tick in range(60):
        major = tick % 5 == 0
        color = QColor(theme.text if major else theme.muted)
        color.setAlphaF(.8 if major else .38)
        painter.save();painter.translate(center);painter.rotate(tick*6)
        painter.setPen(QPen(color, 2.5 if major else 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(0, -radius+23), QPointF(0, -radius+(34 if major else 27)))
        painter.restore()

    font = QFont(font_family);font.setPixelSize(round(14*clock_scale));font.setBold(True)
    painter.setFont(font);painter.setPen(muted)
    metrics = QFontMetricsF(font)
    for number, angle in ((12, 0), (3, 90), (6, 180), (9, 270)):
        radians = math.radians(angle)
        point = center + QPointF(math.sin(radians)*radius*.71, -math.cos(radians)*radius*.71)
        box = QRectF(point.x()-20, point.y()-metrics.height()/2, 40, metrics.height())
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, str(number))

    hour, minute, second = hand_angles(now)
    for angle, length, width, color in ((hour, .43, 6.5, text), (minute, .61, 4, text)):
        painter.save();painter.translate(center);painter.rotate(angle)
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(0, radius*.06), QPointF(0, -radius*length))
        painter.restore()
    if seconds:
        painter.save();painter.translate(center);painter.rotate(second)
        painter.setPen(QPen(accent, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(0, radius*.18), QPointF(0, -radius*.66))
        painter.setBrush(accent);painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, radius*.14), 3, 3)
        painter.restore()
    painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(text)
    painter.drawEllipse(center, 5, 5)
    painter.setBrush(accent);painter.drawEllipse(center, 2.5, 2.5)
    painter.restore()
    return QRectF(center.x()-radius*.54, center.y()+radius*.32, radius*1.08, radius*.25)

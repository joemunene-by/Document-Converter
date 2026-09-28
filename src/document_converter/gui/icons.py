"""Small line icons drawn with QPainter, so they stay sharp and match the theme."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_SCALE = 3  # draw at 3x so icons stay crisp on high-density screens


def _canvas(size: int):
    pm = QPixmap(size * _SCALE, size * _SCALE)
    pm.setDevicePixelRatio(_SCALE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p


def pixmap(name: str, color: QColor, size: int = 18, stroke: float = 1.6) -> QPixmap:
    pm, p = _canvas(size)
    pen = QPen(color, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    s = float(size)
    m = s * 0.18  # margin

    if name == "upload":
        p.drawLine(QPointF(s / 2, m), QPointF(s / 2, s * 0.62))
        p.drawPolyline([QPointF(s * 0.3, s * 0.36), QPointF(s / 2, m), QPointF(s * 0.7, s * 0.36)])
        p.drawPolyline([QPointF(m, s * 0.62), QPointF(m, s - m), QPointF(s - m, s - m), QPointF(s - m, s * 0.62)])
    elif name == "plus":
        p.drawLine(QPointF(s / 2, m), QPointF(s / 2, s - m))
        p.drawLine(QPointF(m, s / 2), QPointF(s - m, s / 2))
    elif name == "close":
        k = s * 0.3
        p.drawLine(QPointF(k, k), QPointF(s - k, s - k))
        p.drawLine(QPointF(s - k, k), QPointF(k, s - k))
    elif name == "chevron":
        p.drawPolyline([QPointF(s * 0.25, s * 0.38), QPointF(s / 2, s * 0.64), QPointF(s * 0.75, s * 0.38)])
    elif name == "check":
        p.drawPolyline([QPointF(s * 0.22, s * 0.52), QPointF(s * 0.42, s * 0.72), QPointF(s * 0.78, s * 0.3)])
    elif name == "alert":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawLine(QPointF(s / 2, s * 0.32), QPointF(s / 2, s * 0.55))
        p.drawPoint(QPointF(s / 2, s * 0.68))
    elif name == "folder":
        path = QPainterPath()
        path.moveTo(m, s * 0.28)
        path.lineTo(s * 0.4, s * 0.28)
        path.lineTo(s * 0.48, s * 0.38)
        path.lineTo(s - m, s * 0.38)
        path.lineTo(s - m, s - m * 1.1)
        path.lineTo(m, s - m * 1.1)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "theme":
        rect = QRectF(m, m, s - 2 * m, s - 2 * m)
        p.drawEllipse(rect)
        p.setBrush(color)
        p.drawPie(rect, 90 * 16, 180 * 16)
    elif name == "info":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawLine(QPointF(s / 2, s * 0.46), QPointF(s / 2, s * 0.68))
        p.drawPoint(QPointF(s / 2, s * 0.33))
    elif name == "arrow":
        p.drawLine(QPointF(m, s / 2), QPointF(s - m, s / 2))
        p.drawPolyline([QPointF(s * 0.56, s * 0.28), QPointF(s - m, s / 2), QPointF(s * 0.56, s * 0.72)])
    p.end()
    return pm


def icon(name: str, color: QColor, size: int = 18) -> QIcon:
    return QIcon(pixmap(name, color, size))

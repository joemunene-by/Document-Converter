"""Custom widgets for the main window."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QVBoxLayout,
                               QWidget)

from ..formats import Format
from . import icons, theme


def human_size(num: int) -> str:
    size = float(num)
    for unit in ("bytes", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} {unit}" if unit == "bytes" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num} bytes"


def repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class DropZone(QWidget):

    clicked = Signal()

    def __init__(self, compact: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.compact = compact
        self._hover = False
        self._drag = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover)

        self.glyph = QLabel()
        self.glyph.setAlignment(Qt.AlignCenter)
        self.title = QLabel("Drop files to convert" if not compact else "Drop more files here, or click to add")
        self.title.setObjectName("DropTitle" if not compact else "DropHint")
        self.title.setAlignment(Qt.AlignCenter)

        if compact:
            self.setFixedHeight(58)
            row = QHBoxLayout(self)
            row.setContentsMargins(18, 0, 18, 0)
            row.setSpacing(10)
            row.addStretch()
            row.addWidget(self.glyph)
            row.addWidget(self.title)
            row.addStretch()
        else:
            self.setMinimumHeight(300)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            hint = QLabel("or click to browse. Everything stays on your computer.")
            hint.setObjectName("DropHint")
            hint.setAlignment(Qt.AlignCenter)
            chips = QHBoxLayout()
            chips.setSpacing(6)
            chips.addStretch()
            for text in ("PDF", "DOCX", "XLSX", "PPTX", "ODT", "EPUB", "MD", "HTML", "CSV", "+ 25 MORE"):
                chip = QLabel(text)
                chip.setObjectName("Chip")
                chips.addWidget(chip)
            chips.addStretch()
            col = QVBoxLayout(self)
            col.setContentsMargins(24, 24, 24, 24)
            col.setSpacing(0)
            col.addStretch()
            col.addWidget(self.glyph)
            col.addSpacing(18)
            col.addWidget(self.title)
            col.addSpacing(6)
            col.addWidget(hint)
            col.addSpacing(22)
            col.addLayout(chips)
            col.addStretch()
        self.refresh_theme()

    def refresh_theme(self) -> None:
        size = 18 if self.compact else 26
        self.glyph.setPixmap(icons.pixmap("upload" if not self.compact else "plus", theme.color("text"), size))
        if not self.compact:
            self.glyph.setFixedHeight(64)
        self.update()

    def set_dragging(self, active: bool) -> None:
        self._drag = active
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = 12 if self.compact else 18
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0, theme.color("drop_top"))
        grad.setColorAt(1, theme.color("drop_bottom"))
        p.setBrush(grad)
        active = self._drag or self._hover
        pen = QPen(theme.color("text") if self._drag else theme.color("border_hi" if active else "border"), 1.2)
        if not self._drag:
            pen.setDashPattern([4, 4])
        p.setPen(pen)
        p.drawRoundedRect(rect, radius, radius)

        if not self.compact:
            center = self.glyph.geometry().center()
            circle = QRectF(center.x() - 32, center.y() - 32, 64, 64)
            p.setPen(QPen(theme.color("border_hi" if active else "border"), 1))
            p.setBrush(theme.color("surface"))
            p.drawEllipse(circle)
        p.end()


class Badge(QWidget):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.text = text.upper()[:4]
        self.setFixedSize(42, 42)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0, theme.color("surface_hi"))
        grad.setColorAt(1, theme.color("surface"))
        p.setBrush(grad)
        p.setPen(QPen(theme.color("border_hi"), 1))
        p.drawRoundedRect(rect, 10, 10)
        font = QFont(self.font())
        font.setPixelSize(10 if len(self.text) > 3 else 11)
        font.setBold(True)
        font.setLetterSpacing(QFont.PercentageSpacing, 104)
        p.setFont(font)
        p.setPen(theme.color("text"))
        p.drawText(rect, Qt.AlignCenter, self.text)
        p.end()


class Spinner(QWidget):
    def __init__(self, size: int = 16, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._timer.start()
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        p.setPen(QPen(theme.color("border_hi"), 2))
        p.drawEllipse(rect)
        pen = QPen(theme.color("text"), 2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, -self._angle * 16, 100 * 16)
        p.end()


class FileRow(QFrame):
    READY, UNAVAILABLE, SKIPPED, ACTIVE, DONE, FAILED = range(6)

    removed = Signal(object)
    open_requested = Signal(object)
    details_requested = Signal(object)

    def __init__(self, path: Path, fmt: Optional[Format], readable: bool, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Row")
        self.path = path
        self.fmt = fmt
        self.readable = readable
        self.outputs: List[Path] = []
        self.error = ""
        self.state = self.READY if readable else self.UNAVAILABLE

        self.badge = Badge(path.suffix.lstrip(".") or "?")
        self.name = QLabel()
        self.name.setObjectName("RowName")
        self.name.setMinimumWidth(80)
        self.name.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        try:
            size = human_size(path.stat().st_size)
        except OSError:
            size = ""
        label = fmt.label if fmt else "Unknown type"
        self.meta = QLabel(f"{label}  ·  {size}" if size else label)
        self.meta.setObjectName("RowMeta")

        text = QVBoxLayout()
        text.setSpacing(2)
        text.addStretch()
        text.addWidget(self.name)
        text.addWidget(self.meta)
        text.addStretch()

        self.spinner = Spinner()
        self.spinner.hide()
        self.status_icon = QLabel()
        self.status_icon.hide()
        self.status = QLabel()
        self.status.setObjectName("RowStatus")
        self.status.setCursor(Qt.ArrowCursor)
        self.remove = QToolButton()
        self.remove.setCursor(Qt.PointingHandCursor)
        self.remove.setToolTip("Remove from list")
        self.remove.setIconSize(QSize(14, 14))
        self.remove.clicked.connect(lambda: self.removed.emit(self))

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 10, 10)
        row.setSpacing(12)
        row.addWidget(self.badge)
        row.addLayout(text, 1)
        row.addWidget(self.spinner)
        row.addWidget(self.status_icon)
        row.addWidget(self.status)
        row.addWidget(self.remove)
        self.setFixedHeight(66)
        self.set_state(self.state)
        self.refresh_theme()

    def refresh_theme(self):
        self.remove.setIcon(icons.icon("close", theme.color("muted"), 14))
        self.set_state(self.state, self.error)
        self.badge.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = max(60, self.name.width())
        self.name.setText(self.name.fontMetrics().elidedText(self.path.name, Qt.ElideMiddle, width))
        self.name.setToolTip(str(self.path))

    def set_state(self, state: int, message: str = "") -> None:
        self.state = state
        self.spinner.stop()
        self.status_icon.hide()
        key = {self.ACTIVE: "active", self.DONE: "done", self.FAILED: "failed"}.get(state, "idle")
        self.status.setProperty("state", key)
        self.setProperty("state", key)
        self.status.setToolTip("")
        self.setToolTip("")
        if state == self.READY:
            self.status.setText("Ready")
        elif state == self.UNAVAILABLE:
            self.status.setText("Needs LibreOffice" if self.fmt else "Not supported")
        elif state == self.SKIPPED:
            self.status.setText(message or "Skipped")
        elif state == self.ACTIVE:
            self.status.setText("Converting")
            self.spinner.start()
        elif state == self.DONE:
            self.status.setText("Open")
            self.status_icon.setPixmap(icons.pixmap("check", theme.color("text"), 16))
            self.status_icon.show()
            self.status.setCursor(Qt.PointingHandCursor)
            names = ", ".join(p.name for p in self.outputs)
            self.setToolTip(f"Saved as {names}. Double-click to open.")
        elif state == self.FAILED:
            self.error = message
            self.status.setText("Failed, see why")
            self.status_icon.setPixmap(icons.pixmap("alert", theme.color("text"), 16))
            self.status_icon.show()
            self.status.setCursor(Qt.PointingHandCursor)
            self.status.setToolTip(message)
        repolish(self)
        repolish(self.status)

    def set_busy(self, busy: bool) -> None:
        self.remove.setVisible(not busy)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.status.geometry().contains(event.position().toPoint()):
            if self.state == self.DONE:
                self.open_requested.emit(self)
            elif self.state == self.FAILED:
                self.details_requested.emit(self)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.state == self.DONE:
            self.open_requested.emit(self)
        super().mouseDoubleClickEvent(event)


def divider() -> QFrame:
    line = QFrame()
    line.setObjectName("Divider")
    return line


def muted_color() -> QColor:
    return theme.color("muted")

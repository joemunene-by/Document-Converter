"""Monochrome light and dark themes."""

from __future__ import annotations

from string import Template
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

DARK: Dict[str, str] = {
    "name": "dark",
    "bg": "#0A0A0A",
    "bg_top": "#171717",
    "surface": "#111111",
    "surface_hi": "#191919",
    "border": "#242424",
    "border_hi": "#3A3A3A",
    "text": "#F5F5F5",
    "muted": "#8F8F8F",
    "faint": "#595959",
    "primary_top": "#FFFFFF",
    "primary_bottom": "#D6D6D6",
    "primary_text": "#0A0A0A",
    "selection": "#262626",
    "drop_top": "#161616",
    "drop_bottom": "#0C0C0C",
}

LIGHT: Dict[str, str] = {
    "name": "light",
    "bg": "#F6F6F6",
    "bg_top": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface_hi": "#F3F3F3",
    "border": "#E2E2E2",
    "border_hi": "#C4C4C4",
    "text": "#0A0A0A",
    "muted": "#6A6A6A",
    "faint": "#A6A6A6",
    "primary_top": "#2A2A2A",
    "primary_bottom": "#000000",
    "primary_text": "#FFFFFF",
    "selection": "#ECECEC",
    "drop_top": "#FFFFFF",
    "drop_bottom": "#F2F2F2",
}

_current: Dict[str, str] = DARK


def current() -> Dict[str, str]:
    return _current


def color(token: str) -> QColor:
    return QColor(_current[token])


def system_prefers_dark() -> bool:
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:  # Qt older than 6.5
        return QGuiApplication.palette().color(QPalette.Window).lightness() < 128


_QSS = Template("""
* { color: $text; font-size: 13px; }
QWidget#Root {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 $bg_top, stop:0.28 $bg, stop:1 $bg);
}
QLabel { background: transparent; }
QLabel#Title { font-size: 21px; font-weight: 600; }
QLabel#Subtitle { color: $muted; }
QLabel#Muted, QLabel#RowMeta, QLabel#Status { color: $muted; }
QLabel#Caption { color: $muted; font-size: 11px; font-weight: 600; letter-spacing: 1px; }
QLabel#DropTitle { font-size: 17px; font-weight: 600; }
QLabel#DropHint { color: $muted; }
QLabel#Chip {
    color: $muted; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;
    border: 1px solid $border; border-radius: 6px; padding: 3px 7px; background: $surface;
}
QLabel#SectionTitle { font-size: 14px; font-weight: 600; }
QLabel#RowName { font-weight: 500; }
QLabel#RowStatus { color: $muted; }
QLabel#RowStatus[state="done"] { color: $text; font-weight: 600; }
QLabel#RowStatus[state="failed"] { color: $text; font-weight: 600; }
QLabel#RowStatus[state="active"] { color: $text; }

QFrame#Card {
    background: $surface; border: 1px solid $border; border-radius: 16px;
}
QFrame#Row {
    background: $surface; border: 1px solid $border; border-radius: 12px;
}
QFrame#Row:hover { border-color: $border_hi; }
QFrame#Row[state="failed"] { border-color: $border_hi; }
QFrame#Divider { background: $border; max-height: 1px; min-height: 1px; border: none; }

QPushButton {
    background: $surface_hi; border: 1px solid $border; border-radius: 9px;
    padding: 8px 14px; font-weight: 500;
}
QPushButton:hover { border-color: $border_hi; }
QPushButton:pressed { background: $selection; }
QPushButton:disabled { color: $faint; }
QPushButton#Primary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 $primary_top, stop:1 $primary_bottom);
    color: $primary_text; border: 1px solid $primary_bottom; border-radius: 10px;
    padding: 11px 24px; font-weight: 600; font-size: 14px;
}
QPushButton#Primary:hover { border-color: $text; }
QPushButton#Primary:disabled {
    background: $surface_hi; color: $faint; border-color: $border;
}
QPushButton#Ghost, QPushButton#Link {
    background: transparent; border: none; color: $muted; padding: 6px 8px;
}
QPushButton#Ghost:hover, QPushButton#Link:hover { color: $text; }
QPushButton#Link { text-decoration: underline; padding: 2px 0; }
QPushButton#Pill {
    background: transparent; border: 1px solid $border; border-radius: 14px;
    padding: 5px 12px; font-size: 12px; color: $muted;
}
QPushButton#Pill:hover { color: $text; border-color: $border_hi; }
QPushButton#Field {
    text-align: left; padding: 8px 30px 8px 12px; min-width: 190px;
}
QPushButton#Field::menu-indicator {
    image: url("$chevron"); width: 12px; height: 12px;
    subcontrol-origin: padding; subcontrol-position: center right; right: 10px;
}

QToolButton { background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 5px; }
QToolButton:hover { background: $surface_hi; border-color: $border; }
QToolButton#IconButton { border: 1px solid $border; border-radius: 10px; padding: 7px; }
QToolButton#IconButton:hover { border-color: $border_hi; }

QComboBox {
    background: $surface_hi; border: 1px solid $border; border-radius: 9px;
    padding: 8px 12px; min-width: 230px;
}
QComboBox:hover { border-color: $border_hi; }
QComboBox:disabled { color: $faint; }
QComboBox::drop-down { border: none; width: 30px; }
QComboBox::down-arrow { image: url("$chevron"); width: 12px; height: 12px; }
QComboBox QAbstractItemView {
    background: $surface; border: 1px solid $border_hi; border-radius: 10px;
    padding: 6px; outline: 0; selection-background-color: $selection; selection-color: $text;
}
QComboBox QAbstractItemView::item { min-height: 28px; padding: 0 8px; border-radius: 6px; }

QListWidget#Queue { background: transparent; border: none; outline: 0; }
QListWidget#Queue::item, QListWidget#Queue::item:selected, QListWidget#Queue::item:hover {
    background: transparent; border: none;
}

QProgressBar#Progress {
    background: $border; border: none; border-radius: 1px;
    min-height: 3px; max-height: 3px;
}
QProgressBar#Progress::chunk { background: $text; border-radius: 1px; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border_hi; border-radius: 3px; min-height: 32px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QMenu { background: $surface; border: 1px solid $border_hi; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 7px 16px; border-radius: 6px; }
QMenu::item:selected { background: $selection; }
QMenu::separator { height: 1px; background: $border; margin: 5px 8px; }

QToolTip {
    background: $surface; color: $text; border: 1px solid $border_hi;
    padding: 6px 8px; border-radius: 6px;
}
QDialog, QMessageBox { background: $bg; }
QTextEdit, QPlainTextEdit {
    background: $surface; border: 1px solid $border; border-radius: 10px; padding: 8px;
}
""")


def stylesheet(tokens: Dict[str, str], chevron_path: str) -> str:
    return _QSS.substitute(tokens, chevron=chevron_path.replace("\\", "/"))


def palette(tokens: Dict[str, str]) -> QPalette:
    p = QPalette()
    c = lambda key: QColor(tokens[key])  # noqa: E731
    p.setColor(QPalette.Window, c("bg"))
    p.setColor(QPalette.WindowText, c("text"))
    p.setColor(QPalette.Base, c("surface"))
    p.setColor(QPalette.AlternateBase, c("surface_hi"))
    p.setColor(QPalette.Text, c("text"))
    p.setColor(QPalette.Button, c("surface_hi"))
    p.setColor(QPalette.ButtonText, c("text"))
    p.setColor(QPalette.ToolTipBase, c("surface"))
    p.setColor(QPalette.ToolTipText, c("text"))
    p.setColor(QPalette.Highlight, c("selection"))
    p.setColor(QPalette.HighlightedText, c("text"))
    p.setColor(QPalette.PlaceholderText, c("faint"))
    p.setColor(QPalette.Link, c("text"))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, c("faint"))
    return p


def activate(tokens: Dict[str, str]) -> None:
    global _current
    _current = tokens

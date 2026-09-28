"""The main application window."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QSettings, QSize, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu,
                               QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
                               QStackedWidget, QToolButton, QVBoxLayout, QWidget)

from .. import APP_NAME, __version__, engines
from ..converter import Converter
from ..formats import CATEGORIES, FORMATS, Format, detect
from . import icons, theme
from .widgets import DropZone, FileRow, divider

LIBREOFFICE_URL = "https://www.libreoffice.org/download/download-libreoffice/"


def reveal(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
            return
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(path)])
            return
    except OSError:
        pass
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))


def open_file(path: Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


class Worker(QThread):
    started_row = Signal(object)
    finished_row = Signal(object, list)
    failed_row = Signal(object, str)

    def __init__(self, jobs: List[FileRow], target: str, out_dir: Optional[Path]):
        super().__init__()
        self.jobs = jobs
        self.target = target
        self.out_dir = out_dir
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        converter = Converter()
        for row in self.jobs:
            if self._stop:
                break
            self.started_row.emit(row)
            try:
                outputs = converter.convert(row.path, self.target, self.out_dir)
                self.finished_row.emit(row, outputs)
            except Exception as exc:
                self.failed_row.emit(row, str(exc) or exc.__class__.__name__)


class EnginesDialog(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Conversion engines")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Conversion engines")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        pandoc = engines.pandoc_path()
        rows = [
            ("pandoc", "Included", "Word, OpenDocument, RTF, Markdown, HTML, EPUB, LaTeX and more."
             if pandoc else "Missing. Reinstall Document Converter."),
            ("Typst", "Included" if engines.typst_available() else "Missing",
             "Typesets clean, professional PDFs."),
        ]
        lo = engines.libreoffice_path()
        rows.append(("LibreOffice", "Installed" if lo else "Optional, not installed",
                     "Adds .doc, .xls, .ppt, Pages, Numbers, Keynote and Publisher files, "
                     "and pixel-exact Office to PDF."))
        for name, state, text in rows:
            layout.addWidget(divider())
            head = QHBoxLayout()
            label = QLabel(name)
            label.setObjectName("RowName")
            status = QLabel(state)
            status.setObjectName("Muted")
            head.addWidget(label)
            head.addStretch()
            head.addWidget(status)
            layout.addLayout(head)
            desc = QLabel(text)
            desc.setObjectName("Muted")
            desc.setWordWrap(True)
            layout.addWidget(desc)
        layout.addWidget(divider())

        buttons = QHBoxLayout()
        version = QLabel(f"{APP_NAME} {__version__}")
        version.setObjectName("Muted")
        buttons.addWidget(version)
        buttons.addStretch()
        if not lo:
            get = QPushButton("Get LibreOffice")
            get.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(LIBREOFFICE_URL)))
            buttons.addWidget(get)
        again = QPushButton("Check again")
        again.clicked.connect(self._check_again)
        buttons.addWidget(again)
        close = QPushButton("Done")
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        layout.addSpacing(4)
        layout.addLayout(buttons)

    def _check_again(self):
        engines.refresh()
        self.done(2)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("DocumentConverter", "Document Converter")
        self.converter = Converter()
        self.rows: List[FileRow] = []
        self.worker: Optional[Worker] = None
        self.out_dir: Optional[Path] = None
        saved = self.settings.value("out_dir", "", str)
        if saved and Path(saved).is_dir():
            self.out_dir = Path(saved)
        self._asset_dir = Path(tempfile.mkdtemp(prefix="docconv-ui-"))
        self._last_outputs: List[Path] = []
        self._done = self._failed = 0

        self.setWindowTitle(APP_NAME)
        self.setAcceptDrops(True)
        self.setMinimumSize(760, 600)
        self.resize(900, 680)
        self._build()
        mode = self.settings.value("theme", "", str)
        self.apply_theme(theme.DARK if (mode == "dark" or (not mode and theme.system_prefers_dark()))
                         else theme.LIGHT)
        self._refresh()


    def _build(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(32, 26, 32, 26)
        outer.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(14)
        self.mark = QLabel()
        self.mark.setFixedSize(40, 40)
        header.addWidget(self.mark)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        title = QLabel(APP_NAME)
        title.setObjectName("Title")
        subtitle = QLabel("Documents, spreadsheets, slides and eBooks. Offline and private.")
        subtitle.setObjectName("Subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        self.engine_pill = QPushButton()
        self.engine_pill.setObjectName("Pill")
        self.engine_pill.setCursor(Qt.PointingHandCursor)
        self.engine_pill.clicked.connect(self._show_engines)
        header.addWidget(self.engine_pill)
        self.theme_button = QToolButton()
        self.theme_button.setObjectName("IconButton")
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.setToolTip("Switch light or dark")
        self.theme_button.setIconSize(QSize(16, 16))
        self.theme_button.clicked.connect(self._toggle_theme)
        header.addWidget(self.theme_button)
        outer.addLayout(header)

        self.stack = QStackedWidget()
        self.drop = DropZone()
        self.drop.clicked.connect(self._browse)
        self.stack.addWidget(self.drop)

        queue_page = QWidget()
        queue = QVBoxLayout(queue_page)
        queue.setContentsMargins(0, 0, 0, 0)
        queue.setSpacing(12)
        bar = QHBoxLayout()
        self.count_label = QLabel()
        self.count_label.setObjectName("SectionTitle")
        bar.addWidget(self.count_label)
        bar.addStretch()
        self.clear_button = QPushButton("Clear list")
        self.clear_button.setObjectName("Ghost")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self._clear)
        bar.addWidget(self.clear_button)
        queue.addLayout(bar)
        self.list = QListWidget()
        self.list.setObjectName("Queue")
        self.list.setSpacing(3)
        self.list.setSelectionMode(QListWidget.NoSelection)
        self.list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.list.setFocusPolicy(Qt.NoFocus)
        queue.addWidget(self.list, 1)
        self.drop_small = DropZone(compact=True)
        self.drop_small.clicked.connect(self._browse)
        queue.addWidget(self.drop_small)
        self.stack.addWidget(queue_page)
        outer.addWidget(self.stack, 1)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        controls = QHBoxLayout()
        controls.setSpacing(16)

        to_col = QVBoxLayout()
        to_col.setSpacing(6)
        to_caption = QLabel("CONVERT TO")
        to_caption.setObjectName("Caption")
        self.format_combo = QComboBox()
        self.format_combo.setCursor(Qt.PointingHandCursor)
        self.format_combo.setMaxVisibleItems(18)
        self.format_combo.currentIndexChanged.connect(self._format_changed)
        to_col.addWidget(to_caption)
        to_col.addWidget(self.format_combo)
        controls.addLayout(to_col)

        save_col = QVBoxLayout()
        save_col.setSpacing(6)
        save_caption = QLabel("SAVE TO")
        save_caption.setObjectName("Caption")
        self.save_button = QPushButton()
        self.save_button.setObjectName("Field")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setIconSize(QSize(16, 16))
        self.save_menu = QMenu(self)
        self.save_button.setMenu(self.save_menu)
        save_col.addWidget(save_caption)
        save_col.addWidget(self.save_button)
        controls.addLayout(save_col)
        controls.addStretch()

        action_col = QVBoxLayout()
        action_col.setSpacing(6)
        action_col.addStretch()
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("Ghost")
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.clicked.connect(self._stop)
        self.stop_button.hide()
        self.convert_button = QPushButton("Convert")
        self.convert_button.setObjectName("Primary")
        self.convert_button.setCursor(Qt.PointingHandCursor)
        self.convert_button.clicked.connect(self._start)
        actions.addWidget(self.stop_button)
        actions.addWidget(self.convert_button)
        action_col.addLayout(actions)
        controls.addLayout(action_col)
        card_layout.addLayout(controls)

        self.progress = QProgressBar()
        self.progress.setObjectName("Progress")
        self.progress.setTextVisible(False)
        self.progress.hide()
        card_layout.addWidget(self.progress)

        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        self.status = QLabel()
        self.status.setObjectName("Status")
        status_row.addWidget(self.status)
        status_row.addStretch()
        self.reveal_button = QPushButton("Show in folder")
        self.reveal_button.setObjectName("Link")
        self.reveal_button.setCursor(Qt.PointingHandCursor)
        self.reveal_button.clicked.connect(lambda: self._last_outputs and reveal(self._last_outputs[-1]))
        self.reveal_button.hide()
        self.status.hide()
        status_row.addWidget(self.reveal_button)
        card_layout.addLayout(status_row)
        outer.addWidget(card)


    def apply_theme(self, tokens: Dict[str, str]):
        theme.activate(tokens)
        chevron = self._asset_dir / f"chevron-{tokens['name']}.png"
        icons.pixmap("chevron", theme.color("muted"), 12, 1.8).save(str(chevron))
        app = QApplication.instance()
        app.setPalette(theme.palette(tokens))
        app.setStyleSheet(theme.stylesheet(tokens, str(chevron)))
        self.theme_button.setIcon(icons.icon("theme", theme.color("text"), 16))
        self.save_button.setIcon(icons.icon("folder", theme.color("muted"), 16))
        self.mark.setPixmap(_app_mark(40))
        self.drop.refresh_theme()
        self.drop_small.refresh_theme()
        for row in self.rows:
            row.refresh_theme()
        self._refresh_engine_pill()

    def _toggle_theme(self):
        tokens = theme.LIGHT if theme.current()["name"] == "dark" else theme.DARK
        self.settings.setValue("theme", tokens["name"])
        self.apply_theme(tokens)


    def _browse(self):
        if self._busy():
            return
        exts = " ".join(f"*.{e}" for f in self.converter.readable_formats() for e in f.extensions)
        start = self.settings.value("browse_dir", str(Path.home()), str)
        files, _ = QFileDialog.getOpenFileNames(
            self, "Choose files to convert", start, f"Supported files ({exts});;All files (*)")
        if files:
            self.settings.setValue("browse_dir", str(Path(files[0]).parent))
            self.add_paths([Path(f) for f in files])

    def add_paths(self, paths: List[Path]):
        known = {row.path for row in self.rows}
        unsupported: List[str] = []
        added = 0
        for path in self._expand(paths):
            path = path.resolve()
            if path in known:
                continue
            fmt = detect(path)
            if fmt is None:
                unsupported.append(path.name)
                continue
            row = FileRow(path, fmt, self.converter.can_read(fmt))
            row.removed.connect(self._remove_row)
            row.open_requested.connect(lambda r: r.outputs and open_file(r.outputs[0]))
            row.details_requested.connect(self._show_error)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 70))
            self.list.addItem(item)
            self.list.setItemWidget(item, row)
            self.rows.append(row)
            known.add(path)
            added += 1
        if unsupported:
            names = ", ".join(unsupported[:3]) + (f" and {len(unsupported) - 3} more" if len(unsupported) > 3 else "")
            self._set_status(f"Skipped unsupported file{'s' if len(unsupported) > 1 else ''}: {names}")
        elif added:
            self._set_status("")
        self._refresh()

    @staticmethod
    def _expand(paths: List[Path]) -> List[Path]:
        out: List[Path] = []
        for path in paths:
            if path.is_dir():
                out += sorted(p for p in path.rglob("*")
                              if p.is_file() and not p.name.startswith(".") and detect(p))
            elif path.is_file():
                out.append(path)
        return out

    def _remove_row(self, row: FileRow):
        if self._busy():
            return
        index = self.rows.index(row)
        self.rows.pop(index)
        self.list.takeItem(index)
        row.deleteLater()
        self._refresh()

    def _clear(self):
        if self._busy():
            return
        self.rows.clear()
        self.list.clear()
        self._set_status("")
        self.reveal_button.hide()
        self._refresh()


    def _busy(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def _targets(self) -> List[Format]:
        keys = set()
        for row in self.rows:
            if row.readable:
                keys.update(t.key for t in self.converter.targets_for(row.fmt))
        return [f for f in FORMATS.values() if f.key in keys]

    def _refresh(self):
        has_rows = bool(self.rows)
        self.stack.setCurrentIndex(1 if has_rows else 0)
        n = len(self.rows)
        self.count_label.setText(f"{n} file{'s' if n != 1 else ''}")
        self._rebuild_formats()
        self._rebuild_save_menu()
        self._update_convert_button()

    def _rebuild_formats(self):
        previous = self.format_combo.currentData() or self.settings.value("target", "pdf", str)
        targets = self._targets()
        model = QStandardItemModel()
        select = -1
        for category in CATEGORIES:
            group = [f for f in targets if f.category == category]
            if not group:
                continue
            header = QStandardItem(category.upper())
            header.setFlags(Qt.NoItemFlags)
            font = header.font()
            font.setPixelSize(10)
            font.setBold(True)
            font.setLetterSpacing(QFont.PercentageSpacing, 110)
            header.setFont(font)
            model.appendRow(header)
            for fmt in group:
                item = QStandardItem(f"{fmt.label}   .{fmt.extension}")
                item.setData(fmt.key, Qt.UserRole)
                model.appendRow(item)
                if fmt.key == previous:
                    select = model.rowCount() - 1
        self.format_combo.blockSignals(True)
        self.format_combo.setModel(model)
        if select < 0:
            select = next((i for i in range(model.rowCount()) if model.item(i).isEnabled()), -1)
        if select < 0:
            placeholder = QStandardItem("Add files to choose a format")
            model.appendRow(placeholder)
            select = 0
        self.format_combo.setCurrentIndex(select)
        self.format_combo.setEnabled(bool(targets))
        self.format_combo.blockSignals(False)

    def _format_changed(self):
        key = self.format_combo.currentData()
        if key:
            self.settings.setValue("target", key)
        self._update_convert_button()

    def _rebuild_save_menu(self):
        self.save_menu.clear()
        same = self.save_menu.addAction("Same folder as each file")
        same.triggered.connect(lambda: self._set_out_dir(None))
        choose = self.save_menu.addAction("Choose folder")
        choose.triggered.connect(self._choose_out_dir)
        if self.out_dir:
            self.save_menu.addSeparator()
            show = self.save_menu.addAction("Open this folder")
            show.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.out_dir))))
        text = "Same folder as each file" if self.out_dir is None else self.out_dir.name or str(self.out_dir)
        metrics = self.save_button.fontMetrics()
        self.save_button.setText(metrics.elidedText(text, Qt.ElideMiddle, 200))
        self.save_button.setToolTip(str(self.out_dir) if self.out_dir else "")

    def _choose_out_dir(self):
        start = str(self.out_dir or Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Save converted files to", start)
        if folder:
            self._set_out_dir(Path(folder))

    def _set_out_dir(self, folder: Optional[Path]):
        self.out_dir = folder
        self.settings.setValue("out_dir", str(folder) if folder else "")
        self._rebuild_save_menu()

    def _eligible(self, key: Optional[str]) -> List[FileRow]:
        if not key:
            return []
        return [r for r in self.rows if r.readable and r.fmt.key != key
                and any(t.key == key for t in self.converter.targets_for(r.fmt))]

    def _update_convert_button(self):
        if self._busy():
            return
        key = self.format_combo.currentData()
        eligible = self._eligible(key)
        if eligible:
            n = len(eligible)
            label = FORMATS[key].extension.upper()
            self.convert_button.setText(f"Convert {n} file{'s' if n != 1 else ''} to {label}")
        else:
            self.convert_button.setText("Convert")
        self.convert_button.setEnabled(bool(eligible))

    def _refresh_engine_pill(self):
        if engines.libreoffice_path():
            self.engine_pill.setText("All engines ready")
        else:
            self.engine_pill.setText("LibreOffice not installed")
        self.engine_pill.setIcon(icons.icon("info", theme.color("muted"), 14))

    def _show_engines(self):
        result = EnginesDialog(self).exec()
        if result == 2:
            for row in self.rows:
                row.readable = self.converter.can_read(row.fmt)
                row.set_state(FileRow.READY if row.readable else FileRow.UNAVAILABLE)
            self._refresh_engine_pill()
            self._refresh()
            self._show_engines()

    def _set_status(self, text: str):
        self.status.setText(text)
        self.status.setVisible(bool(text) or self.reveal_button.isVisible())


    def _start(self):
        key = self.format_combo.currentData()
        jobs = self._eligible(key)
        if not jobs or self._busy():
            return
        target = FORMATS[key]
        for row in self.rows:
            if row in jobs:
                row.outputs = []
                row.set_state(FileRow.READY)
            elif row.readable:
                row.set_state(FileRow.SKIPPED, f"Already {target.extension.upper()}"
                              if row.fmt.key == key else "Not available")
            row.set_busy(True)
        self._done = self._failed = 0
        self._last_outputs = []
        self.progress.setRange(0, len(jobs))
        self.progress.setValue(0)
        self.progress.show()
        self.reveal_button.hide()
        self.stop_button.show()
        self.convert_button.setEnabled(False)
        self.convert_button.setText("Converting")
        self.format_combo.setEnabled(False)
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.drop_small.setEnabled(False)
        self._set_status(f"Converting to {target.label}")

        self.worker = Worker(jobs, key, self.out_dir)
        self.worker.started_row.connect(lambda r: r.set_state(FileRow.ACTIVE))
        self.worker.finished_row.connect(self._row_done)
        self.worker.failed_row.connect(self._row_failed)
        self.worker.finished.connect(self._finished)
        self.worker.start()

    def _row_done(self, row: FileRow, outputs: List[Path]):
        row.outputs = outputs
        row.set_state(FileRow.DONE)
        self._last_outputs += outputs
        self._done += 1
        self.progress.setValue(self._done + self._failed)

    def _row_failed(self, row: FileRow, message: str):
        row.set_state(FileRow.FAILED, message)
        self._failed += 1
        self.progress.setValue(self._done + self._failed)

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self.stop_button.setEnabled(False)
            self._set_status("Stopping after the current file")

    def _finished(self):
        stopped = self.worker is not None and self.worker._stop
        self.worker = None
        for row in self.rows:
            row.set_busy(False)
        self.progress.hide()
        self.stop_button.hide()
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.drop_small.setEnabled(True)
        self.format_combo.setEnabled(True)
        parts = [f"{self._done} converted"]
        if self._failed:
            parts.append(f"{self._failed} failed")
        if stopped:
            parts.append("stopped")
        self._set_status(", ".join(parts).capitalize())
        self.reveal_button.setVisible(bool(self._last_outputs))
        self._set_status(self.status.text())
        self._update_convert_button()
        QApplication.alert(self)

    def _show_error(self, row: FileRow):
        box = QDialog(self)
        box.setWindowTitle("Conversion failed")
        box.setMinimumSize(520, 300)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)
        title = QLabel(f"Could not convert {row.path.name}")
        title.setObjectName("SectionTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        detail = QPlainTextEdit(row.error)
        detail.setReadOnly(True)
        layout.addWidget(detail, 1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        copy = QPushButton("Copy details")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(row.error))
        close = QPushButton("Close")
        close.setObjectName("Primary")
        close.clicked.connect(box.accept)
        buttons.addWidget(copy)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        box.exec()


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self._busy():
            event.acceptProposedAction()
            self.drop.set_dragging(True)
            self.drop_small.set_dragging(True)

    def dragLeaveEvent(self, event):
        self.drop.set_dragging(False)
        self.drop_small.set_dragging(False)

    def dropEvent(self, event):
        self.drop.set_dragging(False)
        self.drop_small.set_dragging(False)
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            event.acceptProposedAction()
            self.add_paths(paths)

    def closeEvent(self, event):
        if self._busy():
            answer = QMessageBox.question(self, APP_NAME, "A conversion is still running. Quit anyway?")
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.worker.stop()
            self.worker.wait(10000)
        super().closeEvent(event)


def _app_mark(size: int):
    from PySide6.QtGui import QPixmap

    from . import asset_path

    pm = QPixmap(str(asset_path("icon.png")))
    if pm.isNull():
        return pm
    ratio = QApplication.instance().devicePixelRatio() if hasattr(QApplication.instance(), "devicePixelRatio") else 2
    scaled = pm.scaled(int(size * max(ratio, 2)), int(size * max(ratio, 2)),
                       Qt.KeepAspectRatio, Qt.SmoothTransformation)
    scaled.setDevicePixelRatio(max(ratio, 2))
    return scaled

"""Desktop app entry point."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def asset_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / name


def main() -> int:
    if os.name == "nt":
        # Without an explicit app id Windows groups the window under python.exe's taskbar icon.
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DocumentConverter.App")
        except Exception:
            pass

    from PySide6.QtCore import QEvent
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from .. import APP_NAME
    from .window import MainWindow

    class App(QApplication):
        window = None
        pending = []

        def event(self, e):
            # macOS delivers files opened from Finder or dropped on the Dock icon as events.
            if e.type() == QEvent.FileOpen:
                path = Path(e.file())
                if self.window:
                    self.window.add_paths([path])
                else:
                    self.pending.append(path)
                return True
            return super().event(e)

    app = QApplication.instance() or App(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName("DocumentConverter")
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(str(asset_path("icon.png"))))

    window = MainWindow()
    window.show()
    files = [Path(a) for a in sys.argv[1:] if not a.startswith("-") and Path(a).is_file()] + list(getattr(app, "pending", []))
    if isinstance(app, App):
        app.window = window
    if files:
        window.add_paths(files)
    return app.exec()

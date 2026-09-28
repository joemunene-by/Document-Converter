import os

import pytest

from document_converter.cli import main

from .conftest import make_md


def test_cli_converts_files(tmp_path, capsys):
    src = make_md(tmp_path / "notes.md")
    assert main([str(src), "-t", "docx", "-o", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "notes.docx").exists()


def test_cli_reports_failures(tmp_path):
    missing = tmp_path / "missing.md"
    assert main([str(missing), "-t", "pdf"]) == 1


def test_cli_lists_formats(capsys):
    assert main(["--formats"]) == 0
    assert "Word Document" in capsys.readouterr().out


def test_gui_builds_and_offers_formats(tmp_path, monkeypatch):
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    from PySide6.QtWidgets import QApplication

    from document_converter.gui.window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    src = make_md(tmp_path / "notes.md")
    window.add_paths([src, tmp_path / "ignored.xyz"])
    assert len(window.rows) == 1
    keys = [window.format_combo.itemData(i) for i in range(window.format_combo.count())]
    assert "pdf" in keys and "docx" in keys and "md" not in keys
    assert window.convert_button.isEnabled()
    window.close()
    app.processEvents()

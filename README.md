# Document Converter

Universal Document Converter — a small GUI application to convert between common document formats.

## Quick start

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install the project (editable) and dependencies:

```powershell
pip install -e .
# or if you prefer: pip install -r requirements.txt
```

3. Run the GUI:

```powershell
python -m document_converter.gui
```

## Build a Windows executable (single-file)

This repository includes a helper PowerShell script to build a single-file Windows executable using PyInstaller and place a shortcut on the desktop.

From the project root run:

```powershell
.\scripts\build_exe.ps1
```

The script will install PyInstaller (user scope), build `DocumentConverter.exe` under `dist/`, and create a `Document Converter.lnk` on the current user's Desktop pointing to the EXE.

If you only want a desktop shortcut that launches the Python UI (without building an EXE), run:

```powershell
.\scripts\create_shortcut.ps1
```

## Files added

- Build script: `scripts\build_exe.ps1`
- Shortcut helper: `scripts\create_shortcut.ps1`

## Notes

- The GUI entrypoint is `document_converter/gui.py` and can also be run with `python document_converter\gui.py`.
- The PowerShell scripts assume you run them from the project root on Windows and that PowerShell execution policy allows running local scripts.

## Additional format support

This converter now includes a fallback converter that attempts to handle many additional file formats (for example: `.odt`, `.rtf`, `.epub`, `.pub`, `.tex`, `.ods`, `.xls`, `.ppt`) by using either `pypandoc` (if installed) or a system LibreOffice installation.

To get the broadest format coverage, install LibreOffice on your system and ensure `soffice` is on your PATH. On Windows, the LibreOffice installer is available at https://www.libreoffice.org/

If you plan to use `pypandoc`, install it in your environment:

```powershell
pip install pypandoc
```

The fallback converter will attempt to convert unsupported inputs to an intermediate format (usually `docx` or `txt`) and then continue the conversion flow. This avoids adding heavy Python-only dependencies while providing wide format coverage.

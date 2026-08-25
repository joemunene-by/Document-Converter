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

This converter now attempts to handle many additional input formats (for example: `.odt`, `.rtf`, `.epub`, `.pub`, `.tex`, `.ods`, `.xls`, `.ppt`) using one of two fallbacks:

- pypandoc (Python wrapper for pandoc) if available in the current Python environment
- LibreOffice / `soffice` in headless mode if installed on the system

How it works:

- For formats that the project has native readers/writers for (plain text, `.docx`, `.pdf`, `.md`, `.html`, `.xlsx`, `.pptx`) the built-in code is used.
- If an input extension is not natively supported, the converter will try `pypandoc` first to convert the file to a sensible intermediate format (`docx` or `txt`). If `pypandoc` is not available, it will try LibreOffice's headless `soffice --convert-to` to produce an intermediate file that the converter can read.

Recommendations:

- To get the broadest format coverage, install LibreOffice and ensure `soffice` is on your PATH. Download from https://www.libreoffice.org/ and enable the program's installation path in your system PATH environment variable.
- Optionally install `pypandoc` in your Python environment for faster, dependency-light conversions from formats supported by pandoc:

```powershell
pip install pypandoc
```

Notes:

- The external fallback is best-effort: some complex formats (notably `.pub`/Publisher files) may not convert perfectly. When possible, prefer native file types.
- The converter will show in the GUI when it's falling back to an external tool and present common output options.

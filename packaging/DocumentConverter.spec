# PyInstaller spec: builds a windowed app for the current OS.
#   pyinstaller packaging/DocumentConverter.spec --noconfirm
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).parent
sys.path.insert(0, str(ROOT / "src"))
from document_converter import APP_NAME, __version__  # noqa: E402

datas, binaries, hiddenimports = [], [], []
# pypandoc-binary ships the pandoc executable as package data.
for package in ("pypandoc", "typst", "pptx"):
    try:
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass
hiddenimports += collect_submodules("odf") + collect_submodules("document_converter")
datas += [
    (str(ROOT / "src/document_converter/assets"), "document_converter/assets"),
    (str(ROOT / "src/document_converter/filters"), "document_converter/filters"),
]

a = Analysis(
    [str(ROOT / "packaging/launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtQml", "PySide6.QtQuick",
              "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtPdf"],
    noarchive=False,
)
pyz = PYZ(a.pure)

icon = str(ROOT / ("packaging/icon.icns" if sys.platform == "darwin" else "packaging/icon.ico"))

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DocumentConverter",
    console=False,
    icon=icon,
    upx=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name="DocumentConverter", upx=False)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=icon,
        bundle_identifier="io.github.joemunene.documentconverter",
        version=__version__,
        info_plist={
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": __version__,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSRequiresAquaSystemAppearance": False,
            "CFBundleDocumentTypes": [{
                "CFBundleTypeName": "Document",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": ["public.data"],
            }],
        },
    )

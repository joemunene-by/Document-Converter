"""Every supported file format and the routes by which it can be read and written."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# LibreOffice converts directly, keeping layout, between formats of the same family.
TEXT = "text"
SHEET = "sheet"
SLIDES = "slides"
DRAWING = "drawing"


@dataclass(frozen=True)
class Format:
    key: str
    label: str
    extensions: List[str]
    category: str
    pandoc_in: Optional[str] = None
    pandoc_out: Optional[str] = None
    native_in: bool = False
    native_out: bool = False
    office_family: Optional[str] = None
    lo_export: Optional[str] = None
    # Modern format LibreOffice converts this into before we read it.
    lo_import_as: Optional[str] = None

    @property
    def extension(self) -> str:
        return self.extensions[0]

    @property
    def display(self) -> str:
        return f"{self.label} (.{self.extension})"


CATEGORIES = ["Documents", "Spreadsheets", "Presentations", "Text & Markup", "eBooks", "Other"]

FORMATS: Dict[str, Format] = {
    f.key: f
    for f in [
        Format("pdf", "PDF", ["pdf"], "Documents", native_in=True, native_out=True),
        Format("docx", "Word Document", ["docx"], "Documents", "docx", "docx",
               office_family=TEXT, lo_export="docx:MS Word 2007 XML"),
        Format("doc", "Word 97-2003", ["doc", "dot"], "Documents",
               office_family=TEXT, lo_export="doc:MS Word 97", lo_import_as="docx"),
        Format("odt", "OpenDocument Text", ["odt"], "Documents", "odt", "odt",
               office_family=TEXT, lo_export="odt"),
        Format("rtf", "Rich Text", ["rtf"], "Documents", "rtf", "rtf",
               office_family=TEXT, lo_export="rtf"),
        Format("pages", "Apple Pages", ["pages"], "Documents",
               office_family=TEXT, lo_import_as="docx"),
        Format("wpd", "WordPerfect", ["wpd"], "Documents",
               office_family=TEXT, lo_import_as="docx"),
        Format("wps", "Microsoft Works", ["wps"], "Documents",
               office_family=TEXT, lo_import_as="docx"),
        Format("xlsx", "Excel Workbook", ["xlsx", "xlsm"], "Spreadsheets",
               native_in=True, native_out=True,
               office_family=SHEET, lo_export="xlsx:Calc MS Excel 2007 XML"),
        Format("xls", "Excel 97-2003", ["xls"], "Spreadsheets", native_in=True,
               office_family=SHEET, lo_export="xls:MS Excel 97"),
        Format("ods", "OpenDocument Spreadsheet", ["ods"], "Spreadsheets",
               native_in=True, native_out=True, office_family=SHEET, lo_export="ods"),
        Format("csv", "CSV", ["csv"], "Spreadsheets", native_in=True, native_out=True),
        Format("tsv", "Tab-Separated Values", ["tsv", "tab"], "Spreadsheets",
               native_in=True, native_out=True),
        Format("numbers", "Apple Numbers", ["numbers"], "Spreadsheets",
               office_family=SHEET, lo_import_as="xlsx"),
        Format("pptx", "PowerPoint", ["pptx"], "Presentations", pandoc_out="pptx",
               native_in=True, office_family=SLIDES,
               lo_export="pptx:Impress MS PowerPoint 2007 XML"),
        Format("ppt", "PowerPoint 97-2003", ["ppt", "pps"], "Presentations",
               office_family=SLIDES, lo_export="ppt:MS PowerPoint 97", lo_import_as="pptx"),
        Format("odp", "OpenDocument Presentation", ["odp"], "Presentations",
               office_family=SLIDES, lo_export="odp", lo_import_as="pptx"),
        Format("key", "Apple Keynote", ["key"], "Presentations",
               office_family=SLIDES, lo_import_as="pptx"),
        Format("md", "Markdown", ["md", "markdown", "mdown", "mkd"], "Text & Markup",
               "markdown", "gfm"),
        Format("txt", "Plain Text", ["txt", "text"], "Text & Markup",
               pandoc_out="plain", native_in=True),
        Format("html", "Web Page", ["html", "htm", "xhtml"], "Text & Markup", "html", "html5"),
        Format("tex", "LaTeX", ["tex", "latex"], "Text & Markup", "latex", "latex"),
        Format("rst", "reStructuredText", ["rst"], "Text & Markup", "rst", "rst"),
        Format("adoc", "AsciiDoc", ["adoc", "asciidoc"], "Text & Markup", "asciidoc", "asciidoc"),
        Format("org", "Org Mode", ["org"], "Text & Markup", "org", "org"),
        Format("typ", "Typst", ["typ"], "Text & Markup", "typst", "typst"),
        Format("textile", "Textile", ["textile"], "Text & Markup", "textile", "textile"),
        Format("wiki", "MediaWiki", ["wiki", "mediawiki"], "Text & Markup", "mediawiki", "mediawiki"),
        Format("ipynb", "Jupyter Notebook", ["ipynb"], "Text & Markup", "ipynb", "ipynb"),
        Format("epub", "EPUB eBook", ["epub"], "eBooks", "epub", "epub3"),
        Format("fb2", "FictionBook", ["fb2"], "eBooks", "fb2", "fb2"),
        # LibreOffice can only turn drawings into PDF.
        Format("pub", "Microsoft Publisher", ["pub"], "Other", office_family=DRAWING),
        Format("vsdx", "Visio Drawing", ["vsdx", "vsd"], "Other", office_family=DRAWING),
        Format("odg", "OpenDocument Drawing", ["odg"], "Other", office_family=DRAWING),
    ]
}

_BY_EXTENSION: Dict[str, Format] = {}
for _fmt in FORMATS.values():
    for _ext in _fmt.extensions:
        _BY_EXTENSION[_ext] = _fmt


def detect(path) -> Optional[Format]:
    return _BY_EXTENSION.get(Path(path).suffix.lower().lstrip("."))


def all_extensions() -> List[str]:
    return sorted(_BY_EXTENSION)

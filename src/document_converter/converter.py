"""Plans and runs conversions. Sources are loaded into a document hub (a file pandoc
can read) or a table hub (a list of sheets), and every target is written from a hub."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Union

from . import engines, extractors, tabular
from .engines import ConversionError
from .formats import DRAWING, FORMATS, SHEET, SLIDES, TEXT, Format, detect
from .textio import is_utf8, read_text, text_to_html

_STANDALONE = {"html5", "latex", "rtf", "typst", "epub3", "fb2", "docx", "odt", "pptx", "ipynb"}
# These writers reference images as separate files saved next to the output.
_EXTERNAL_MEDIA = {"gfm", "rst", "org", "textile", "mediawiki", "asciidoc", "latex", "typst"}
_BINARY_READERS = {"docx", "odt", "epub"}
_TABLE_TARGETS = {"xlsx", "ods", "csv", "tsv"}
_MODERN = {TEXT: "docx", SHEET: "xlsx", SLIDES: "pptx"}


@dataclass
class DocHub:
    path: Path
    fmt: str
    resource_dir: Path


@dataclass
class TableHub:
    sheets: List[tabular.Sheet]


Hub = Union[DocHub, TableHub]


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


class Converter:

    def can_read(self, fmt: Format) -> bool:
        if fmt.lo_import_as or fmt.office_family == DRAWING:
            return engines.libreoffice_path() is not None
        if fmt.native_in:
            return True
        return bool(fmt.pandoc_in) and fmt.pandoc_in in engines.pandoc_input_formats()

    def can_write(self, fmt: Format) -> bool:
        if fmt.key == "pdf":
            return engines.typst_available() or engines.libreoffice_path() is not None
        if fmt.native_out:
            return True
        if fmt.pandoc_out and fmt.pandoc_out in engines.pandoc_output_formats():
            return True
        return bool(fmt.lo_export) and engines.libreoffice_path() is not None

    def targets_for(self, source: Union[str, Path, Format]) -> List[Format]:
        fmt = source if isinstance(source, Format) else detect(source)
        if fmt is None or not self.can_read(fmt):
            return []
        if fmt.office_family == DRAWING:
            return [FORMATS["pdf"]]
        return [t for t in FORMATS.values() if t.key != fmt.key and self.can_write(t)]

    def readable_formats(self) -> List[Format]:
        return [f for f in FORMATS.values() if self.can_read(f)]


    def convert(self, source: Union[str, Path], target: str, out_dir: Union[str, Path, None] = None,
                overwrite: bool = False) -> List[Path]:
        """Convert `source` to the format keyed `target` (for example "pdf"). Returns the files written."""
        src = Path(source).expanduser().resolve()
        if not src.is_file():
            raise ConversionError(f"File not found: {src}")
        src_fmt = detect(src)
        if src_fmt is None:
            raise ConversionError(f"Unsupported file type: {src.suffix or src.name}")
        tgt = FORMATS.get(target.lower().lstrip("."))
        if tgt is None:
            raise ConversionError(f"Unknown output format: {target}")
        if tgt not in self.targets_for(src_fmt):
            hint = ""
            if (src_fmt.lo_import_as or tgt.lo_export or src_fmt.office_family == DRAWING) \
                    and engines.libreoffice_path() is None:
                hint = " Installing LibreOffice (free) enables it."
            raise ConversionError(f"{src_fmt.label} to {tgt.label} is not available.{hint}")

        out = Path(out_dir).expanduser().resolve() if out_dir else src.parent
        out.mkdir(parents=True, exist_ok=True)
        final = out / f"{src.stem}.{tgt.extension}"
        if not overwrite:
            final = unique_path(final)

        with tempfile.TemporaryDirectory(prefix="docconv-") as tmp_name:
            tmp = Path(tmp_name)
            stage = tmp / "out"
            stage.mkdir()
            self._convert(src, src_fmt, tgt, stage / final.name, tmp / "work")
            return self._publish(stage, out, final.name, overwrite)

    def _publish(self, stage: Path, out: Path, main_name: str, overwrite: bool) -> List[Path]:
        written: List[Path] = []
        items = sorted(stage.iterdir(), key=lambda p: (p.name != main_name, p.name))
        for item in items:
            dest = out / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
                continue
            if dest.exists() and not overwrite:
                dest = unique_path(dest)
            shutil.move(str(item), str(dest))
            written.append(dest)
        if not written:
            raise ConversionError("The conversion produced no output.")
        return written

    def _convert(self, src: Path, sf: Format, tf: Format, dst: Path, work: Path) -> None:
        work.mkdir(parents=True, exist_ok=True)
        lo = engines.libreoffice_path()

        # LibreOffice keeps page layout, so prefer it between office formats.
        if lo and sf.office_family and (
                tf.key == "pdf" or (tf.lo_export and tf.office_family == sf.office_family)):
            result = engines.libreoffice_convert(src, "pdf" if tf.key == "pdf" else tf.lo_export, work / "lo")
            shutil.move(str(result), str(dst))
            return
        if sf.office_family == DRAWING:
            raise ConversionError("LibreOffice is required to convert this file.")

        if tf.lo_export and not (tf.pandoc_out or tf.native_out):
            modern = FORMATS[_MODERN[tf.office_family]]
            middle = work / "mid" / f"{dst.stem}.{modern.extension}"
            middle.parent.mkdir(parents=True, exist_ok=True)
            self._convert(src, sf, modern, middle, work / "mid-work")
            result = engines.libreoffice_convert(middle, tf.lo_export, work / "lo")
            shutil.move(str(result), str(dst))
            return

        hub = self._load(src, sf, work)
        self._write(hub, tf, dst, work)


    def _load(self, src: Path, sf: Format, work: Path) -> Hub:
        if sf.lo_import_as:
            modern = FORMATS[sf.lo_import_as]
            imported = engines.libreoffice_convert(src, modern.lo_export, work / "import")
            return self._load(imported, modern, work)

        if sf.key == "xlsx":
            return TableHub(tabular.read_xlsx(src))
        if sf.key == "xls":
            return TableHub(tabular.read_xls(src))
        if sf.key == "ods":
            return TableHub(tabular.read_ods(src))
        if sf.key == "csv":
            return TableHub(tabular.read_delimited(src))
        if sf.key == "tsv":
            return TableHub(tabular.read_delimited(src, "\t"))
        if sf.key == "pdf":
            return self._html_hub(extractors.pdf_to_html(src), work, src.parent)
        if sf.key == "pptx":
            markup = extractors.pptx_to_html(src, work / "slides_media")
            return self._html_hub(markup, work, src.parent)
        if sf.key == "txt":
            return self._html_hub(text_to_html(read_text(src)), work, src.parent)
        if sf.pandoc_in:
            path = src
            if sf.pandoc_in not in _BINARY_READERS and not is_utf8(src):
                # pandoc only reads UTF-8; transcode legacy encodings first.
                path = work / f"source{src.suffix}"
                path.write_text(read_text(src), encoding="utf-8")
            return DocHub(path, sf.pandoc_in, src.parent)
        raise ConversionError(f"Cannot read {sf.label} files.")

    @staticmethod
    def _html_hub(markup: str, work: Path, resource_dir: Path) -> DocHub:
        path = work / "source.html"
        path.write_text(markup, encoding="utf-8")
        return DocHub(path, "html", resource_dir)


    def _pandoc(self, hub: DocHub, dst: Path, writer: str, args: Optional[List[str]] = None,
                cwd: Optional[Path] = None) -> Path:
        return engines.pandoc(hub.path, hub.fmt, dst, writer, cwd=cwd, args=args,
                              resource_dirs=[hub.resource_dir])

    def _write(self, hub: Hub, tf: Format, dst: Path, work: Path) -> None:
        if tf.key in _TABLE_TARGETS:
            self._write_table(hub, tf, dst, work)
            return
        columns = 0
        if isinstance(hub, TableHub):
            columns = max((len(r) for s in hub.sheets for r in s.rows), default=0)
            hub = self._html_hub(tabular.sheets_to_html(hub.sheets), work, work)
        if tf.key == "pdf":
            self._write_pdf(hub, dst, work, columns)
            return
        if not tf.pandoc_out:
            raise ConversionError(f"Cannot write {tf.label} files.")

        writer = tf.pandoc_out
        args: List[str] = []
        if writer in _STANDALONE:
            args.append("--standalone")
        if writer not in _STANDALONE:
            args += ["--lua-filter", engines.pandoc_filter("title_heading.lua")]
        if writer in _EXTERNAL_MEDIA:
            args += [f"--extract-media={dst.stem}_media", "--wrap=none"]
        if writer == "plain":
            args.append("--wrap=none")
        if writer in ("html5", "epub3", "fb2"):
            # Values in a metadata file never override the document's own title.
            meta = work / "meta.yaml"
            safe = dst.stem.replace('"', "'")
            meta.write_text(f'title: "{safe}"\npagetitle: "{safe}"\n', encoding="utf-8")
            args += ["--metadata-file", str(meta)]
            if writer == "html5":
                args.append("--embed-resources")
        self._pandoc(hub, dst, writer, args, cwd=dst.parent)

    def _write_pdf(self, hub: DocHub, dst: Path, work: Path, columns: int = 0) -> None:
        if not engines.typst_available():
            raise ConversionError("No PDF engine is available.")
        build = work / "pdf"
        build.mkdir(parents=True, exist_ok=True)
        source = build / "document.typ"
        self._pandoc(hub, source, "typst",
                     ["--standalone", "--extract-media=media", "--wrap=none",
                      "--lua-filter", engines.pandoc_filter("pdf_images.lua"),
                      "-V", "papersize=a4", *self._wide_table_layout(columns, build)],
                     cwd=build)
        # pandoc wraps tables in figures, which Typst never splits across pages, so long
        # tables would be cut off. The page rule must precede all content to avoid a blank page.
        preamble = "#show figure.where(kind: table): set block(breakable: true)\n"
        if columns > 8:
            preamble = "#set page(flipped: true)\n" + preamble
        source.write_text(preamble + source.read_text(encoding="utf-8"), encoding="utf-8")
        engines.typst_compile(source, dst)

    @staticmethod
    def _wide_table_layout(columns: int, build: Path) -> List[str]:
        if columns <= 8:
            return []
        meta = build / "layout.yaml"
        size = "9pt" if columns <= 14 else "7pt"
        meta.write_text(f"margin:\n  x: 1.5cm\n  y: 1.5cm\nfontsize: {size}\n", encoding="utf-8")
        return ["--metadata-file", str(meta)]

    def _write_table(self, hub: Hub, tf: Format, dst: Path, work: Path) -> None:
        if isinstance(hub, TableHub):
            sheets = hub.sheets
        else:
            fragment = work / "tables.html"
            self._pandoc(hub, fragment, "html5")
            # CSV holds a single table, so text around tables is only kept in workbooks.
            sheets = tabular.html_to_sheets(fragment.read_text(encoding="utf-8"), dst.stem,
                                            keep_text=tf.key in ("xlsx", "ods"))

        if tf.key == "xlsx":
            tabular.write_xlsx(sheets, dst)
        elif tf.key == "ods":
            tabular.write_ods(sheets, dst)
        else:
            delimiter = "," if tf.key == "csv" else "\t"
            if len(sheets) <= 1:
                tabular.write_delimited(sheets[0] if sheets else tabular.Sheet("", []), dst, delimiter)
            else:
                for sheet in sheets:
                    name = "".join(c if c.isalnum() or c in " -_" else "_" for c in sheet.name).strip()
                    tabular.write_delimited(sheet, dst.with_name(f"{dst.stem} - {name}{dst.suffix}"), delimiter)


def convert_many(paths: List[Path], target: str, out_dir: Optional[Path] = None,
                 on_result: Optional[Callable[[Path, Optional[List[Path]], Optional[str]], None]] = None) -> int:
    """Convert several files, reporting each result. Returns the number of failures."""
    converter = Converter()
    failures = 0
    for path in paths:
        try:
            outputs = converter.convert(path, target, out_dir)
            if on_result:
                on_result(path, outputs, None)
        except Exception as exc:  # report and keep going
            failures += 1
            if on_result:
                on_result(path, None, str(exc))
    return failures

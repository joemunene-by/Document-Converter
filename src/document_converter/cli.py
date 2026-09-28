"""Command-line interface: `docconv report.docx -t pdf`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__, engines
from .converter import Converter
from .formats import CATEGORIES, FORMATS, detect


def _list_formats(converter: Converter) -> None:
    readable = {f.key for f in converter.readable_formats()}
    writable = {f.key for f in FORMATS.values() if converter.can_write(f)}
    for category in CATEGORIES:
        print(category)
        for fmt in (f for f in FORMATS.values() if f.category == category):
            modes = ", ".join(m for m, ok in (("read", fmt.key in readable), ("write", fmt.key in writable)) if ok)
            exts = " ".join("." + e for e in fmt.extensions)
            print(f"  {fmt.key:<8} {fmt.label:<28} {exts:<28} {modes or 'needs LibreOffice'}")
    print()
    lo = engines.libreoffice_path()
    print(f"LibreOffice: {lo or 'not installed (legacy .doc/.xls/.ppt, Apple iWork and Publisher need it)'}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docconv",
        description="Convert documents, spreadsheets, presentations and markup files.",
    )
    parser.add_argument("files", nargs="*", type=Path, help="files to convert")
    parser.add_argument("-t", "--to", help="output format, for example pdf, docx, xlsx, md")
    parser.add_argument("-o", "--out-dir", type=Path, help="folder for the results (default: next to each file)")
    parser.add_argument("--overwrite", action="store_true", help="replace existing files instead of renaming")
    parser.add_argument("--formats", action="store_true", help="list supported formats and exit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    converter = Converter()
    if args.formats:
        _list_formats(converter)
        return 0
    if not args.files or not args.to:
        parser.print_usage()
        print("docconv: give one or more files and an output format with -t", file=sys.stderr)
        return 2

    failures = 0
    for path in args.files:
        try:
            outputs = converter.convert(path, args.to, args.out_dir, overwrite=args.overwrite)
            for out in outputs:
                print(f"{path}  to  {out}")
        except Exception as exc:
            failures += 1
            fmt = detect(path)
            label = fmt.label if fmt else path.suffix
            print(f"{path}: failed ({label} to {args.to}): {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

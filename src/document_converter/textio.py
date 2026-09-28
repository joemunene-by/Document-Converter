"""Text decoding helpers."""

from __future__ import annotations

import codecs
import html
import re
from pathlib import Path


def decode(data: bytes) -> str:
    for bom, encoding in ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF16_LE, "utf-16"),
                          (codecs.BOM_UTF16_BE, "utf-16")):
        if data.startswith(bom):
            return data.decode(encoding)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def read_text(path: Path) -> str:
    return decode(Path(path).read_bytes())


def is_utf8(path: Path) -> bool:
    try:
        Path(path).read_bytes().decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def text_to_html(text: str) -> str:
    """Plain text to HTML: blank lines separate paragraphs, line breaks are kept."""
    paragraphs = [p for p in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")) if p.strip()]
    body = "\n".join(
        "<p>" + "<br/>".join(html.escape(line) for line in p.strip("\n").split("\n")) + "</p>"
        for p in paragraphs
    )
    return f"<html><body>\n{body}\n</body></html>"

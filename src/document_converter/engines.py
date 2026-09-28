"""pandoc and Typst (bundled as wheels) and LibreOffice (optional, found on the system)."""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Set


class ConversionError(Exception):
    """A conversion failed with a message that is safe to show to users."""


# Hide console windows that would otherwise flash up on Windows.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _run(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            creationflags=_NO_WINDOW,
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionError(f"{Path(cmd[0]).name} timed out after {timeout} seconds") from exc



def _runs(exe: str) -> bool:
    # Only macOS ships a wrong-architecture binary. Elsewhere, running it here would only slow
    # startup, and a first launch can take a while while antivirus scans the executable.
    if sys.platform != "darwin":
        return True
    try:
        return _run([exe, "--version"], timeout=120).returncode == 0
    except (OSError, ConversionError):
        return False


@functools.lru_cache(maxsize=None)
def pandoc_path() -> Optional[str]:
    candidates = []
    try:
        import pypandoc

        candidates.append(str(pypandoc.get_pandoc_path()))
    except Exception:
        pass
    candidates.append(shutil.which("pandoc"))
    # The bundled binary can be the wrong architecture (Intel pandoc on an M-series Mac without Rosetta).
    for exe in candidates:
        if not exe:
            continue
        # pypandoc reports the Windows binary without its ".exe" suffix.
        for path in (Path(exe), Path(exe + ".exe")):
            if path.is_file() and _runs(str(path)):
                return str(path)
    return None


@functools.lru_cache(maxsize=None)
def _pandoc_list(flag: str) -> Set[str]:
    exe = pandoc_path()
    if not exe:
        return set()
    try:
        proc = _run([exe, flag], timeout=120)
    except (OSError, ConversionError):
        return set()
    return {line.strip() for line in proc.stdout.decode("utf-8", "replace").splitlines() if line.strip()}


def pandoc_input_formats() -> Set[str]:
    return _pandoc_list("--list-input-formats")


def pandoc_output_formats() -> Set[str]:
    return _pandoc_list("--list-output-formats")


_FILTER_DIR = Path(__file__).with_name("filters")


def pandoc(src: Path, src_fmt: str, dst: Path, dst_fmt: str, *, cwd: Optional[Path] = None,
           args: Optional[List[str]] = None, resource_dirs: Optional[List[Path]] = None) -> Path:
    exe = pandoc_path()
    if not exe:
        raise ConversionError("pandoc is not available. Reinstall Document Converter.")
    cmd = [exe, str(src), "-f", src_fmt, "-t", dst_fmt, "-o", str(dst),
           "--resource-path", os.pathsep.join([str(src.parent), *map(str, resource_dirs or []), "."])]
    cmd += args or []
    proc = _run(cmd, cwd=cwd)
    if proc.returncode != 0 or not dst.exists():
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise ConversionError(detail or f"pandoc could not convert to {dst_fmt}")
    return dst


def pandoc_filter(name: str) -> str:
    return str(_FILTER_DIR / name)



def typst_available() -> bool:
    try:
        import typst  # noqa: F401
        return True
    except Exception:
        return False


def typst_compile(source: Path, dst: Path) -> Path:
    try:
        import typst
    except Exception as exc:
        raise ConversionError("The Typst PDF engine is not available.") from exc
    try:
        typst.compile(str(source), output=str(dst), root=str(source.parent))
    except Exception as exc:
        raise ConversionError(f"PDF typesetting failed: {exc}") from exc
    return dst



def _libreoffice_candidates() -> List[str]:
    names = ["soffice", "libreoffice", "soffice.exe"]
    found = [p for p in (shutil.which(n) for n in names) if p]
    if sys.platform == "darwin":
        found += [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            str(Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice"),
        ]
    elif os.name == "nt":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                     os.environ.get("LOCALAPPDATA")):
            if base:
                found.append(str(Path(base) / "LibreOffice" / "program" / "soffice.exe"))
    else:
        found += ["/usr/bin/soffice", "/usr/lib/libreoffice/program/soffice",
                  "/snap/bin/libreoffice", "/var/lib/flatpak/exports/bin/org.libreoffice.LibreOffice"]
        found += [str(p) for p in sorted(Path("/opt").glob("libreoffice*/program/soffice"))]
    return found


@functools.lru_cache(maxsize=None)
def libreoffice_path() -> Optional[str]:
    override = os.environ.get("DOCCONV_SOFFICE")
    if override:
        return override if Path(override).exists() else None
    if os.environ.get("DOCCONV_NO_LIBREOFFICE"):
        return None
    for candidate in _libreoffice_candidates():
        if Path(candidate).is_file():
            return candidate
    return None


def refresh() -> None:
    """Forget the cached LibreOffice lookup, for example after the user installs it."""
    libreoffice_path.cache_clear()


def libreoffice_convert(src: Path, export: str, out_dir: Path) -> Path:
    """Convert `src` with LibreOffice. `export` is an extension or "ext:Filter Name"."""
    exe = libreoffice_path()
    if not exe:
        raise ConversionError("LibreOffice is required for this conversion but is not installed.")
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = export.split(":", 1)[0]
    # A private profile lets conversions run even while LibreOffice is open.
    with tempfile.TemporaryDirectory(prefix="docconv-lo-") as profile:
        cmd = [exe, f"-env:UserInstallation={Path(profile).as_uri()}", "--headless",
               "--norestore", "--nolockcheck", "--convert-to", export,
               "--outdir", str(out_dir), str(src)]
        proc = _run(cmd, timeout=300)
    result = out_dir / f"{src.stem}.{ext}"
    if not result.exists():
        detail = (proc.stderr or proc.stdout).decode("utf-8", "replace").strip()
        raise ConversionError(detail or f"LibreOffice could not convert {src.name} to .{ext}")
    return result

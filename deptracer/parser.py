from __future__ import annotations
from pathlib import Path
import os
import re
from .models import MissingDependency

# Runtime assets that commonly appear as late-bound PyInstaller dependencies.
EXTENSIONS = {
    ".so", ".so.1", ".dll", ".dylib", ".pt", ".pth", ".onnx", ".h5",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".npy", ".npz",
    ".csv", ".txt", ".wav", ".mp3", ".jpg", ".jpeg", ".png", ".gif",
    ".ttf", ".otf", ".model", ".bin",
}

SYSTEM_PREFIXES = (
    "/proc/", "/sys/", "/dev/", "/etc/ld.so.cache", "/etc/ld.so.preload",
    "/usr/share/zoneinfo/", "/usr/share/locale/", "/usr/lib/locale/",
)

IGNORE_NAMES = {
    "ld.so.cache", "ld.so.preload", "gconv-modules.cache",
}

PATH_RE = re.compile(r'"((?:\\.|[^"\\])*)"')

def _unescape(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape")

def classify(path: str) -> str | None:
    lower = path.lower()
    name = Path(lower).name
    if name in IGNORE_NAMES or any(lower.startswith(p) for p in SYSTEM_PREFIXES):
        return None
    if "/glibc-hwcaps/" in lower or "/tls/" in lower:
        return None
    suffix = Path(lower).suffix
    if ".so." in name or suffix in EXTENSIONS:
        if ".so" in name or suffix in {".dll", ".dylib"}:
            return "binary"
        return "data"
    return None

def parse_strace(trace_file: Path) -> list[MissingDependency]:
    found = {}
    for line in trace_file.read_text(encoding="utf-8", errors="replace").splitlines():
        # We only care about ENOENT/ENOTDIR failures: these are strong signals
        # that a runtime asset was requested but was absent at that location.
        if "ENOENT" not in line and "ENOTDIR" not in line:
            continue
        match = PATH_RE.search(line)
        if not match:
            continue
        path = os.path.normpath(_unescape(match.group(1)))
        kind = classify(path)
        if not kind:
            continue
        if not os.path.isabs(path):
            continue
        found[path] = MissingDependency(path=path, kind=kind, source_line=line)
    return [found[p] for p in sorted(found)]

def parse_missing_paths(trace_file: Path) -> list[str]:
    return [d.path for d in parse_strace(trace_file)]

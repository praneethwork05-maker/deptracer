from __future__ import annotations
from pathlib import Path
import ast
import json
import re
import shutil
from .models import ResolvedDependency

class SpecPatchError(RuntimeError):
    pass

def _quote(value: str) -> str:
    return repr(value)

def _entry(dep: ResolvedDependency) -> str:
    return f"({_quote(dep.source)}, {_quote(dep.destination)}, {_quote(dep.typecode)})"

def _list_literal(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"

def patch_spec(spec_path: Path, dependencies: list[ResolvedDependency], backup=True) -> bool:
    if not dependencies:
        return False
    original = spec_path.read_text(encoding="utf-8")
    if backup:
        backup_path = spec_path.with_suffix(spec_path.suffix + ".bak")
        if not backup_path.exists():
            shutil.copy2(spec_path, backup_path)

    binaries = [_entry(d) for d in dependencies if d.typecode == "BINARY"]
    datas = [_entry(d) for d in dependencies if d.typecode == "DATA"]
    existing_sources = set(re.findall(r"['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]+['\"]\s*,\s*['\"](?:BINARY|DATA)['\"]", original))

    binaries = [x for x in binaries if next((d.source for d in dependencies if _entry(d) == x), "") not in existing_sources]
    # Deduplicate by source path while retaining deterministic order.
    def unique_entries(entries):
        out, seen = [], set()
        for e in entries:
            if e not in seen:
                out.append(e); seen.add(e)
        return out

    binaries = unique_entries(binaries)
    datas = unique_entries(datas)
    if not binaries and not datas:
        return False

    lines = []
    if binaries:
        lines.append(f"a.binaries += {_list_literal(binaries)}")
    if datas:
        lines.append(f"a.datas += {_list_literal(datas)}")
    injection = "\n# deptracer injected runtime dependencies\n" + "\n".join(lines) + "\n"

    marker = "# deptracer injected runtime dependencies"
    if marker in original:
        return False

    # Insert before PYZ so the Analysis TOCs are finalized before packaging.
    match = re.search(r"(?m)^\s*pyz\s*=\s*PYZ\(", original)
    if match:
        patched = original[:match.start()] + injection + original[match.start():]
    else:
        # Some custom specs omit the standard variable names. In that case,
        # fail safely instead of silently corrupting the spec.
        raise SpecPatchError("Could not find 'pyz = PYZ(' in the spec; patch it manually or provide a standard PyInstaller spec.")

    spec_path.write_text(patched, encoding="utf-8")
    return True

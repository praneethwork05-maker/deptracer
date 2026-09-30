from __future__ import annotations
from pathlib import Path
import os
import time
from .models import MissingDependency, ResolvedDependency

class Resolver:
    def __init__(self, project_dir: Path, search_paths=None, deep_timeout=10.0, exclude_system=False):
        self.project_dir = project_dir.resolve()
        self.search_paths = [Path(p).resolve() for p in (search_paths or [])]
        self.deep_timeout = deep_timeout
        self.exclude_system = exclude_system

    def _candidates(self, name: str):
        roots = [
            self.project_dir,
            self.project_dir / "lib",
            self.project_dir / "libs",
            self.project_dir / "build",
            self.project_dir / "dist",
        ] + self.search_paths
        seen = set()
        for root in roots:
            if not root.exists():
                continue
            direct = root / name
            if direct.is_file() and str(direct) not in seen:
                seen.add(str(direct))
                yield direct
            try:
                for p in root.rglob(name):
                    if p.is_file() and str(p) not in seen:
                        seen.add(str(p))
                        yield p
            except (OSError, PermissionError):
                pass

    def resolve(self, dep: MissingDependency) -> Path | None:
        name = Path(dep.path).name
        # Prefer project-local assets over system copies.
        for p in self._candidates(name):
            return p

        if self.exclude_system:
            return None

        # A bounded scan avoids the unbounded 'find /' failure mode described
        # in the challenge statement.
        start = time.monotonic()
        system_roots = [Path("/usr/lib"), Path("/usr/lib64"), Path("/lib"), Path("/lib64"), Path("/usr/local/lib")]
        for root in system_roots:
            if time.monotonic() - start >= self.deep_timeout:
                break
            if not root.exists():
                continue
            try:
                for p in root.rglob(name):
                    if time.monotonic() - start >= self.deep_timeout:
                        break
                    if p.is_file():
                        return p
            except (OSError, PermissionError):
                continue
        return None

    def resolve_all(self, deps):
        results = []
        unresolved = []
        for dep in deps:
            source = self.resolve(dep)
            if source is None:
                unresolved.append(dep)
                continue
            destination = self.destination_for(dep, source)
            typecode = "BINARY" if dep.kind == "binary" else "DATA"
            results.append(ResolvedDependency(dep, str(source), destination, typecode))
        return results, unresolved

    def destination_for(self, dep: MissingDependency, source: Path) -> str:
        # Preserve the basename for runtime-opened absolute paths. For data
        # assets this is the least surprising PyInstaller runtime destination.
        return source.name

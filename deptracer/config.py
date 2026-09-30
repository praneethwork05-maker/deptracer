from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import os

@dataclass
class Config:
    project_dir: Path
    timeout: float = 30.0
    max_iterations: int = 8
    max_runtime: float = 600.0
    deep_search_timeout: float = 10.0
    use_sandbox: bool = False
    exclude_system: bool = False
    verbose: bool = False
    search_paths: list[Path] = field(default_factory=list)
    state_file: Path | None = None
    clean_build: bool = False

    def __post_init__(self):
        self.project_dir = self.project_dir.resolve()
        if self.state_file is None:
            self.state_file = self.project_dir / ".deptracer-state.json"
        self.search_paths = [Path(p).expanduser().resolve() for p in self.search_paths]

    @property
    def effective_search_paths(self) -> list[Path]:
        paths = [
            self.project_dir,
            self.project_dir / "lib",
            self.project_dir / "libs",
            self.project_dir / "build",
            self.project_dir / "dist",
            Path("/usr/local/lib"),
            Path("/usr/lib"),
            Path("/usr/lib64"),
            Path("/lib"),
            Path("/lib64"),
        ]
        paths.extend(self.search_paths)
        result, seen = [], set()
        for p in paths:
            if p.exists() and str(p) not in seen:
                result.append(p)
                seen.add(str(p))
        return result

def load_project_config(project_dir: Path) -> dict:
    cfg = project_dir / "deptracer_config.py"
    if not cfg.exists():
        return {}
    namespace = {}
    exec(compile(cfg.read_text(), str(cfg), "exec"), namespace, namespace)
    return {
        k: v for k, v in namespace.items()
        if k.isupper() and not k.startswith("__")
    }

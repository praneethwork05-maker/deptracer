from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time

@dataclass
class BuildState:
    project_dir: str
    spec_path: str
    app_name: str
    iteration: int = 0
    started_at: float = 0.0
    patched_sources: list[str] | None = None
    completed: bool = False
    last_error: str | None = None

    def save(self, path: Path):
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path):
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    @property
    def elapsed(self):
        return time.monotonic() - self.started_at if self.started_at else 0.0

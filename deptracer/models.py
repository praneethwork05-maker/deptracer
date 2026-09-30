from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class MissingDependency:
    path: str
    kind: str
    source_line: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class ResolvedDependency:
    missing: MissingDependency
    source: str
    destination: str
    typecode: str

    def to_dict(self):
        return {
            "missing": self.missing.to_dict(),
            "source": self.source,
            "destination": self.destination,
            "typecode": self.typecode,
        }

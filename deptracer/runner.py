from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

class CommandRunner:
    def __init__(self, timeout: float = 30.0, verbose: bool = False):
        self.timeout = timeout
        self.verbose = verbose

    def run(self, argv, cwd=None, env=None, output_file=None) -> CommandResult:
        if self.verbose:
            print("[RUN]", " ".join(map(str, argv)))
        try:
            with open(output_file, "w", encoding="utf-8", errors="replace") if output_file else open(os.devnull, "w") as sink:
                proc = subprocess.run(
                    [str(x) for x in argv],
                    cwd=str(cwd) if cwd else None,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self.timeout,
                )
            return CommandResult(proc.returncode, proc.stdout, proc.stderr, False)
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                -9,
                exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
                exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
                True,
            )

def command_exists(name: str) -> bool:
    return shutil.which(name) is not None

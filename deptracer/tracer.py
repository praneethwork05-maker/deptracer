from __future__ import annotations
from pathlib import Path
import os
import re
import tempfile
from .runner import CommandRunner, command_exists

class TraceError(RuntimeError):
    pass

class Tracer:
    """Trace runtime file access with strace; Bubblewrap is optional."""

    def __init__(self, timeout=30.0, sandbox=False, verbose=False):
        self.timeout = timeout
        self.sandbox = sandbox
        self.verbose = verbose

    def _sandbox_command(self, command: list[str], cwd: Path) -> list[str]:
        if not command_exists("bwrap"):
            raise TraceError("Sandbox requested but bubblewrap (bwrap) is not installed.")
        # The sandbox is deliberately read-only for the host filesystem and has a
        # private /tmp. This keeps the mission isolated while preserving normal
        # dynamic-loader visibility.
        return [
            "bwrap", "--die-with-parent",
            "--ro-bind", "/", "/",
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--chdir", str(cwd),
            "--unshare-pid",
            "--unshare-uts",
            "--unshare-ipc",
            "--",
            *command,
        ]

    def trace(self, executable: Path, cwd: Path, trace_file: Path) -> tuple[int, str, str]:
        if not command_exists("strace"):
            raise TraceError("strace is required on Linux. Install it with your distribution package manager.")
        cmd = ["strace", "-f", "-e", "trace=file", "-o", str(trace_file), str(executable)]
        if self.sandbox:
            cmd = ["strace", "-f", "-e", "trace=file", "-o", str(trace_file), *self._sandbox_command([str(executable)], cwd)]
        runner = CommandRunner(self.timeout, self.verbose)
        result = runner.run(cmd, cwd=cwd)
        return result.returncode, result.stdout, result.stderr

    def trace_command(self, command: list[str], cwd: Path, trace_file: Path) -> tuple[int, str, str]:
        if not command_exists("strace"):
            raise TraceError("strace is required on Linux.")
        actual = command
        if self.sandbox:
            actual = self._sandbox_command(command, cwd)
        cmd = ["strace", "-f", "-e", "trace=file", "-o", str(trace_file), *actual]
        result = CommandRunner(self.timeout, self.verbose).run(cmd, cwd=cwd)
        return result.returncode, result.stdout, result.stderr

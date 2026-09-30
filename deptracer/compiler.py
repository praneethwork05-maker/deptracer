from __future__ import annotations
from pathlib import Path
from .runner import CommandRunner, command_exists

class CompilerError(RuntimeError):
    pass

class Compiler:
    def __init__(self, timeout=300.0, verbose=False):
        self.timeout = timeout
        self.verbose = verbose

    def build(self, spec_path: Path, project_dir: Path, clean=False):
        if not command_exists("pyinstaller"):
            raise CompilerError("PyInstaller is not installed or not on PATH.")
        cmd = ["pyinstaller"]
        if clean:
            cmd.append("--clean")
        cmd.extend(["--noconfirm", str(spec_path)])
        result = CommandRunner(self.timeout, self.verbose).run(cmd, cwd=project_dir)
        if result.returncode != 0:
            raise CompilerError(
                "PyInstaller build failed.\nSTDOUT:\n%s\nSTDERR:\n%s"
                % (result.stdout, result.stderr)
            )
        return result

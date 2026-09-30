from __future__ import annotations
from pathlib import Path
import time
import tempfile
from .compiler import Compiler
from .config import Config
from .parser import parse_strace
from .resolver import Resolver
from .spec import patch_spec
from .state import BuildState
from .tracer import Tracer, TraceError

class BuildError(RuntimeError):
    pass

class BuildEngine:
    def __init__(self, config: Config):
        self.config = config
        self.compiler = Compiler(timeout=max(config.timeout, 300.0), verbose=config.verbose)
        self.tracer = Tracer(timeout=config.timeout, sandbox=config.use_sandbox, verbose=config.verbose)
        self.resolver = Resolver(
            config.project_dir,
            config.effective_search_paths,
            config.deep_search_timeout,
            config.exclude_system,
        )

    def _find_executable(self, app_name: str) -> Path:
        candidates = [
            self.config.project_dir / "dist" / app_name,
            self.config.project_dir / "dist" / (app_name + ".bin"),
            self.config.project_dir / app_name,
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                return p
        raise BuildError(f"Could not find built executable for '{app_name}' in dist/.")

    def run(self, app_name: str, spec_path: Path, resume=False, dry_run=False):
        state_path = self.config.state_file
        if resume and state_path.exists():
            state = BuildState.load(state_path)
            if state.completed:
                print("[CORE] Previous run is already complete.")
                return 0
            iteration = state.iteration
            started_at = state.started_at or time.monotonic()
            state.started_at = started_at
            print(f"[CORE] Resuming from iteration {iteration + 1}")
        else:
            state = BuildState(
                project_dir=str(self.config.project_dir),
                spec_path=str(spec_path),
                app_name=app_name,
                started_at=time.monotonic(),
            )
            iteration = 0

        while iteration < self.config.max_iterations:
            if time.monotonic() - state.started_at > self.config.max_runtime:
                state.last_error = "overall time budget exceeded"
                state.save(state_path)
                raise BuildError("Overall time/iteration budget exceeded.")

            iteration += 1
            state.iteration = iteration
            state.save(state_path)
            print(f"\n[CORE] INITIATING SWEEP ITERATION: {iteration}")

            if not dry_run:
                self.compiler.build(spec_path, self.config.project_dir, clean=self.config.clean_build)

            executable = self._find_executable(app_name)
            with tempfile.TemporaryDirectory(prefix="deptracer-") as td:
                trace_file = Path(td) / "trace.log"
                print("[TRACER] Tracing runtime file accesses...")
                rc, out, err = self.tracer.trace(executable, self.config.project_dir, trace_file)
                deps = parse_strace(trace_file)

            print(f"[PARSER] Candidate missing runtime dependencies: {len(deps)}")
            if not deps:
                state.completed = True
                state.last_error = None
                state.save(state_path)
                print("[CORE] EXECUTABLE IS FULLY SELF-CONTAINED.")
                return 0

            resolved, unresolved = self.resolver.resolve_all(deps)
            for dep in resolved:
                print(f"[RESOLVER] Located: {dep.missing.path} -> {dep.source}")
            for dep in unresolved:
                print(f"[RESOLVER] Unresolved: {dep.path}")

            if dry_run:
                print("[DRY-RUN] No files or spec were modified.")
                return 0

            if not resolved:
                state.last_error = "No missing dependencies could be resolved."
                state.save(state_path)
                raise BuildError("No missing dependencies could be resolved.")

            changed = patch_spec(spec_path, resolved)
            if not changed:
                state.last_error = "No new spec entries were added."
                state.save(state_path)
                raise BuildError("Dependencies were found but the spec was not changed; stopping to avoid an infinite loop.")

            state.patched_sources = sorted(set((state.patched_sources or []) + [d.source for d in resolved]))
            state.save(state_path)
            print(f"[FIXER] Patched spec with {len(resolved)} dependency entries.")

        state.last_error = f"maximum iterations ({self.config.max_iterations}) reached"
        state.save(state_path)
        raise BuildError("Maximum iteration count reached before a clean build was verified.")

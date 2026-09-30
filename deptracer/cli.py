from __future__ import annotations
import argparse
from pathlib import Path
import sys
from . import __version__
from .config import Config, load_project_config
from .core import BuildEngine, BuildError
from .tracer import TraceError

def build_parser():
    p = argparse.ArgumentParser(
        prog="deptracer",
        description="Discover runtime dependencies and automatically patch PyInstaller specs.",
    )
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="Build, trace, resolve, patch and repeat.")
    b.add_argument("project", type=Path)
    b.add_argument("app_name")
    b.add_argument("spec", type=Path)
    b.add_argument("--max-iterations", type=int, default=8)
    b.add_argument("--max-runtime", type=float, default=600.0)
    b.add_argument("--timeout", type=float, default=30.0)
    b.add_argument("--deep-search-timeout", type=float, default=10.0)
    b.add_argument("--search-path", action="append", default=[])
    b.add_argument("--exclude-system", action="store_true")
    b.add_argument("--sandbox", action="store_true")
    b.add_argument("--dry-run", action="store_true")
    b.add_argument("--resume", action="store_true")
    b.add_argument("--clean", action="store_true")
    b.add_argument("-v", "--verbose", action="store_true")

    c = sub.add_parser("clean-state", help="Remove a previous resume state.")
    c.add_argument("project", type=Path)

    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "clean-state":
        state = args.project.resolve() / ".deptracer-state.json"
        if state.exists():
            state.unlink()
            print(f"Removed {state}")
        else:
            print("No state file exists.")
        return 0

    project = args.project.resolve()
    spec = args.spec.resolve() if args.spec.is_absolute() else (project / args.spec).resolve()
    if not project.exists():
        print(f"error: project does not exist: {project}", file=sys.stderr)
        return 2
    if not spec.exists():
        print(f"error: spec does not exist: {spec}", file=sys.stderr)
        return 2

    user_cfg = load_project_config(project)
    config = Config(
        project_dir=project,
        timeout=args.timeout,
        max_iterations=args.max_iterations,
        max_runtime=args.max_runtime,
        deep_search_timeout=args.deep_search_timeout,
        use_sandbox=args.sandbox,
        exclude_system=args.exclude_system,
        verbose=args.verbose,
        search_paths=args.search_path or user_cfg.get("SEARCH_PATHS", []),
        clean_build=args.clean,
    )
    try:
        return BuildEngine(config).run(args.app_name, spec, resume=args.resume, dry_run=args.dry_run)
    except (BuildError, TraceError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

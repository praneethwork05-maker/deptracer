# deptracer — TathHack PS5 implementation

A competition-ready implementation of the PS5 concept: automatically discover runtime
dependencies of a PyInstaller executable, resolve them, patch the PyInstaller spec, rebuild,
and repeat until the executable is clean or a bounded failure condition is reached.

The challenge asks for a real end-to-end tool rather than a program that merely prints
success. This implementation therefore includes bounded tracing/build operations, persistent
resume state, dry-run mode, and regression tests.

## Features

### Core
- PyInstaller build orchestration.
- `strace -f -e trace=file` runtime tracing.
- Missing file parsing for shared libraries, models, configs, media and other assets.
- Project-first dependency resolution.
- PyInstaller `.spec` patching.
- Iterative rebuild/trace/patch loop.
- Final clean verification.

### PS5 extension features
- **Resume, not restart**: `--resume` uses `.deptracer-state.json`.
- **Dry run**: `--dry-run` reports candidates and resolutions without modifying the spec.
- **Timeouts**: subprocess and deep-search timeouts.
- **Iteration budget**: `--max-iterations`.
- **Overall time budget**: `--max-runtime`.
- Custom dependency search paths.
- Optional Bubblewrap sandbox.
- Automated regression tests.

## Requirements

Linux is the primary target, matching the original project architecture.

- Python 3.8+
- PyInstaller
- `strace`
- optional `bubblewrap` (`bwrap`) for sandbox mode

Example Ubuntu/Debian setup:

```bash
sudo apt update
sudo apt install python3 python3-pip strace bubblewrap
python3 -m pip install pyinstaller pytest
```

## Install this project

```bash
python3 -m pip install -e .
```

## Usage

A normal run:

```bash
deptracer build /path/to/project my_app my_app.spec
```

Verbose:

```bash
deptracer build /path/to/project my_app my_app.spec -v
```

Dry run:

```bash
deptracer build /path/to/project my_app my_app.spec --dry-run
```

Resume an interrupted run:

```bash
deptracer build /path/to/project my_app my_app.spec --resume
```

Bounded run:

```bash
deptracer build /path/to/project my_app my_app.spec   --max-iterations 6   --max-runtime 300   --timeout 30   --deep-search-timeout 8
```

Custom dependency roots:

```bash
deptracer build /path/to/project my_app my_app.spec   --search-path /opt/vendor/lib   --search-path /home/me/vendor
```

Sandbox mode:

```bash
deptracer build /path/to/project my_app my_app.spec --sandbox
```

Clear resume state:

```bash
deptracer clean-state /path/to/project
```

## Development test suite

```bash
pytest -q
```

The tests cover:
- strace parsing,
- project dependency resolution,
- spec patching,
- state persistence.

## Demo

The `examples/` directory contains a tiny runtime-data example. A real PyInstaller project
should first generate its own `.spec`:

```bash
cd examples
pyinstaller --onefile demo_app.py
deptracer build . demo_app demo_app.spec
```

## How the loop works

1. Build the application with PyInstaller.
2. Execute the resulting binary under `strace`.
3. Parse failed file accesses (`ENOENT` / `ENOTDIR`).
4. Filter OS/runtime noise.
5. Resolve candidates in the project and configured library roots.
6. Patch the spec with `BINARY` or `DATA` entries.
7. Rebuild.
8. Repeat until no candidate dependency remains.
9. Stop on a clear success, unresolved dependency, no-op patch, iteration limit, or time budget.

## Important limitations

- Runtime discovery is only as complete as the application's executed code paths.
- A dependency that is never exercised during tracing cannot be discovered dynamically.
- The primary target is Linux/PyInstaller, consistent with the supplied PS5 specification.
- Windows/macOS support is not claimed by this version.

## Presentation/demo points

For a hackathon demo, show:
1. A Python app that loads a runtime asset.
2. A normal PyInstaller build.
3. The first deptracer sweep finding the missing asset.
4. Resolver output.
5. Spec patch.
6. Automatic rebuild.
7. A clean final sweep.
8. `--resume`, `--dry-run`, and the bounded-time options as engineering features.

## License

MIT

# deptracer architecture

```text
CLI
 |
 v
BuildEngine
 |------ Compiler ------> PyInstaller
 |
 |------ Tracer --------> strace (+ optional bwrap)
 |
 |------ Parser --------> MissingDependency[]
 |
 |------ Resolver ------> ResolvedDependency[]
 |
 `------ Spec Patcher --> *.spec
             |
             `------ next iteration
```

## Safety and bounded execution

The tool uses explicit timeouts for subprocesses and deep searches. The build loop has both
an iteration limit and an overall wall-clock budget. Resume state is stored in JSON so an
interrupted sweep can continue without pretending it completed.

## Feature mapping

- Runtime dependency discovery: tracer + parser.
- Dependency resolution: project-first and bounded system search.
- Spec automation: AST-safe-ish insertion at the standard `pyz = PYZ(...)` boundary.
- Resume: `.deptracer-state.json`.
- Dry run: resolves and reports without changing the project.
- Timeouts: command and deep-search limits.
- Iteration budget: `--max-iterations`.
- Overall budget: `--max-runtime`.
- Custom paths: `--search-path` or `deptracer_config.py`.

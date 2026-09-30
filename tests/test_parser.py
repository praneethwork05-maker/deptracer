from pathlib import Path
from deptracer.parser import parse_strace

def test_parse_missing_assets(tmp_path: Path):
    trace = tmp_path / "trace.log"
    trace.write_text(
        'openat(AT_FDCWD, "/opt/app/model.pt", O_RDONLY) = -1 ENOENT (No such file or directory)\n'
        'openat(AT_FDCWD, "/usr/lib/libdemo.so.1", O_RDONLY) = -1 ENOENT (No such file or directory)\n'
        'openat(AT_FDCWD, "/proc/cpuinfo", O_RDONLY) = -1 ENOENT (No such file or directory)\n',
        encoding="utf-8",
    )
    deps = parse_strace(trace)
    assert {d.path for d in deps} == {"/opt/app/model.pt", "/usr/lib/libdemo.so.1"}
    assert {d.kind for d in deps} == {"binary", "data"}

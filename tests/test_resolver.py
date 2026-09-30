from pathlib import Path
from deptracer.resolver import Resolver
from deptracer.models import MissingDependency

def test_project_resolution(tmp_path: Path):
    lib = tmp_path / "lib"
    lib.mkdir()
    target = lib / "libdemo.so.1"
    target.write_text("x")
    resolver = Resolver(tmp_path, deep_timeout=0.1)
    dep = MissingDependency("/usr/lib/libdemo.so.1", "binary")
    result = resolver.resolve(dep)
    assert result == target

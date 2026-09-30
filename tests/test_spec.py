from pathlib import Path
from deptracer.models import MissingDependency, ResolvedDependency
from deptracer.spec import patch_spec

def test_patch_spec(tmp_path: Path):
    spec = tmp_path / "app.spec"
    spec.write_text(
        "a = Analysis(['app.py'])\n"
        "pyz = PYZ(a.pure)\n"
        "exe = EXE(pyz)\n",
        encoding="utf-8",
    )
    src = tmp_path / "libdemo.so"
    src.write_text("x")
    dep = ResolvedDependency(
        MissingDependency("/missing/libdemo.so", "binary"),
        str(src),
        "libdemo.so",
        "BINARY",
    )
    assert patch_spec(spec, [dep])
    text = spec.read_text()
    assert "libdemo.so" in text
    assert "BINARY" in text

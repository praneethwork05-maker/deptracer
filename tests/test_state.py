from pathlib import Path
from deptracer.state import BuildState

def test_state_roundtrip(tmp_path: Path):
    p = tmp_path / "state.json"
    s = BuildState("/p", "/p/a.spec", "app", iteration=2, started_at=1.0)
    s.save(p)
    loaded = BuildState.load(p)
    assert loaded.iteration == 2
    assert loaded.app_name == "app"

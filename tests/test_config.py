from pathlib import Path
from cookbook.config import ensure_output_dirs

def test_ensure_output_dirs(tmp_path: Path):
    base_dir = tmp_path / "output"
    dirs = ensure_output_dirs(base_dir)
    
    assert dirs["splits"] == base_dir / "splits"
    assert dirs["recipes"] == base_dir / "recipes"
    assert dirs["splits"].exists()
    assert dirs["recipes"].exists()

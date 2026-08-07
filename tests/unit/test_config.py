import json

import pytest
from pydantic import ValidationError

from puzzle_pipeline.config.loader import load_config
from puzzle_pipeline.config.models import PuzzleConfig


def test_default_config_has_safe_ranges() -> None:
    config = PuzzleConfig(puzzle_id="demo")
    assert config.grid.columns == 3
    assert config.grid.rows == 2
    assert config.board.thickness > 0
    assert config.atlas.size >= 256


def test_invalid_grid_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PuzzleConfig(puzzle_id="bad", grid={"columns": 1, "rows": 2})


def test_loader_applies_explicit_overrides(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"puzzle_id": "demo", "seed": 1}), encoding="utf-8")
    config = load_config(path, {"seed": 42, "grid": "4x3"})
    assert config.seed == 42
    assert (config.grid.columns, config.grid.rows) == (4, 3)

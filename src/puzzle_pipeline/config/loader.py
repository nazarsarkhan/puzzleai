"""Load and override JSON configuration."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .models import PuzzleConfig


def _parse_grid(value: object) -> dict[str, int]:
    if not isinstance(value, str) or "x" not in value.lower():
        raise ValueError("grid override must use the form CxR, for example 4x3")
    columns_text, rows_text = value.lower().split("x", 1)
    try:
        return {"columns": int(columns_text), "rows": int(rows_text)}
    except ValueError as exc:
        raise ValueError("grid override must use integer dimensions, for example 4x3") from exc


def load_config(path: Path, overrides: Mapping[str, Any] | None = None) -> PuzzleConfig:
    """Read JSON and apply explicit CLI-style overrides."""
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be a JSON object")
    data: dict[str, Any] = dict(raw)
    for key, value in (overrides or {}).items():
        if value is None:
            continue
        if key == "grid":
            data["grid"] = _parse_grid(value)
        else:
            data[key] = value
    return PuzzleConfig.model_validate(data)

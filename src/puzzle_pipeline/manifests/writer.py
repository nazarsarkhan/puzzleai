"""Stable JSON manifest writing."""

from __future__ import annotations

import json
from pathlib import Path

from .models import PuzzleManifest


def write_manifest(manifest: PuzzleManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path

"""Read-only inspection of the supplied golden puzzle archive."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, cast

from PIL import Image


def _json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(zf.read(name).decode("utf-8")))


def inspect_reference(archive: Path) -> dict[str, Any]:
    """Return stable structural facts from a reference ZIP archive."""
    if not archive.is_file():
        raise FileNotFoundError(f"Reference archive not found: {archive}")
    with zipfile.ZipFile(archive) as zf:
        members = [
            name.removeprefix("puzzle_019/")
            for name in zf.namelist()
            if name.startswith("puzzle_019/") and not name.endswith("/")
        ]
        config = _json(zf, "puzzle_019/config/puzzle_019.json")
        manifest = _json(zf, "puzzle_019/manifest.json")
        generator_manifest = _json(zf, "puzzle_019/reports/generator_manifest.json")
        atlas_name = "puzzle_019/export/puzzle_019_atlas.png"
        with zf.open(atlas_name) as atlas_file:
            atlas_size = Image.open(atlas_file).size[0]

        return {
            "files": sorted(members),
            "grid": {"columns": config["columns"], "rows": config["rows"]},
            "seed": config["randomSeed"],
            "piece_count": config["expectedPieceCount"],
            "atlas_size": atlas_size,
            "thickness": config["pieceThickness"],
            "material_names": [manifest["material"]["name"]],
            "front_axis": manifest["frontAxis"],
            "pivot_policy": manifest["assemblyConvention"]["pivotPolicy"],
            "triangle_total": generator_manifest["expectedPieceCount"]
            and sum(piece["triangleCount"] for piece in generator_manifest["pieces"]),
            "blender_available": False,
        }

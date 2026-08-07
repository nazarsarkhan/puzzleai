import json

from puzzle_pipeline.artwork.atlas import AtlasLayout, PixelRect
from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.geometry.outlines import generate_puzzle_geometry
from puzzle_pipeline.manifests.models import build_manifest
from puzzle_pipeline.manifests.writer import write_manifest


def test_manifest_contains_machine_readable_neighbors_and_seams(tmp_path) -> None:
    config = PuzzleConfig(puzzle_id="demo", seed=42)
    geometry = generate_puzzle_geometry(config)
    layout = AtlasLayout(256, PixelRect(10, 80, 236, 157), PixelRect(4, 4, 100, 32), PixelRect(112, 4, 100, 32), 4)
    manifest = build_manifest(config, geometry, layout)
    first = manifest.pieces[0]
    assert first.id == "piece_r00_c00"
    assert first.neighbors["right"] == "piece_r00_c01"
    assert first.seam_ids["right"].startswith("seam_v_")
    path = write_manifest(manifest, tmp_path / "puzzle.json")
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1

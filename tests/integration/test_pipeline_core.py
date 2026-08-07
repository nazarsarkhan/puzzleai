import json

from PIL import Image

from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.pipeline import run_core_pipeline


def test_core_pipeline_writes_reproducible_package(tmp_path) -> None:
    image_path = tmp_path / "artwork.png"
    Image.new("RGB", (8, 4), (25, 50, 75)).save(image_path)
    config = PuzzleConfig(puzzle_id="demo", seed=42, atlas={"size": 256})

    first = run_core_pipeline(config, image_path, tmp_path / "dist-a")
    second = run_core_pipeline(config, image_path, tmp_path / "dist-b")

    assert first.validation.status == "passed"
    assert first.manifest_path.read_bytes() == second.manifest_path.read_bytes()
    assert (first.package_dir / "textures" / "demo_atlas.png").is_file()
    assert (first.package_dir / "manifests" / "validation.json").is_file()
    assert len(json.loads(first.manifest_path.read_text(encoding="utf-8"))["pieces"]) == 6

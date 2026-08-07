import json

from PIL import Image

from puzzle_pipeline.roblox import batch_images


def test_batch_images_assigns_stable_numbered_packages(tmp_path) -> None:
    input_dir = tmp_path / "images"
    input_dir.mkdir()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(input_dir / "black.png")
    Image.new("RGB", (8, 12), (4, 5, 6)).save(input_dir / "portrait.jpg")

    results = batch_images(input_dir, tmp_path / "assets" / "puzzles", start_number=7, atlas_size=256)

    assert [result.package_dir.name for result in results] == ["puzzle_007", "puzzle_008"]
    assert (
        json.loads((results[0].package_dir / "roblox-overrides.json").read_text(encoding="utf-8"))["orientation"]
        == "square"
    )
    assert (
        json.loads((results[1].package_dir / "roblox-overrides.json").read_text(encoding="utf-8"))["orientation"]
        == "portrait"
    )

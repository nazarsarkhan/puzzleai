import json

from PIL import Image

from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.pipeline import run_core_pipeline


def test_reference_configuration_preserves_structural_invariants(tmp_path) -> None:
    image = tmp_path / "reference-art.png"
    Image.new("RGB", (2990, 2009), (30, 40, 50)).save(image)
    config = PuzzleConfig(
        puzzle_id="puzzle_019_regression",
        seed=119,
        grid={"columns": 3, "rows": 2},
        board={"width": 4.8, "height": 3.2251505016722404, "thickness": 0.07},
        atlas={"size": 2048},
    )
    result = run_core_pipeline(config, image, tmp_path / "dist")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert result.validation.status == "passed"
    assert manifest["grid"] == {"columns": 3, "rows": 2}
    assert manifest["seed"] == 119
    assert len(manifest["pieces"]) == 6
    assert manifest["board"]["thickness"] == 0.07
    assert manifest["atlas"]["size"] == 2048
    assert manifest["material"] == {"name": "PuzzleAtlas", "shared": True}
    assert sum(piece["triangle_count"] for piece in manifest["pieces"]) > 0

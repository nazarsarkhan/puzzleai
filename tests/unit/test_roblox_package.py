import json

from PIL import Image

from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.pipeline import run_core_pipeline
from puzzle_pipeline.roblox import RobloxPuzzleSpec, write_roblox_package


def test_roblox_package_has_exact_contract_and_completion_copy(tmp_path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(source)
    config = PuzzleConfig(
        puzzle_id="puzzle_007", grid={"columns": 3, "rows": 3}, board={"width": 4, "height": 4}, atlas={"size": 256}
    )
    core = run_core_pipeline(config, source, tmp_path / "core")
    spec = RobloxPuzzleSpec(
        number=7,
        source=source,
        display_name="Black Square",
        artist="Kazimir Malevich",
        year="1915",
        orientation="square",
        columns=3,
        rows=3,
        ui_sort_order=7,
        frame_label="Black Square — Kazimir Malevich",
        notes="Preserve the full square composition.",
    )

    result = write_roblox_package(spec, config, core, tmp_path / "assets" / "puzzles", blender_status="unavailable")
    assert result.package_dir.name == "puzzle_007"
    expected = {
        "manifest.json",
        "manifest.validation.json",
        "puzzle_007_atlas.png",
        "puzzle_007_completion.png",
        "fbx_export_report.json",
        "fbx_reimport_report.json",
        "roblox-overrides.json",
    }
    assert {path.name for path in result.package_dir.iterdir()} == expected
    assert (result.package_dir / "puzzle_007_completion.png").read_bytes() == source.read_bytes()
    overrides = json.loads((result.package_dir / "roblox-overrides.json").read_text(encoding="utf-8"))
    assert overrides["displayName"] == "Black Square"
    assert overrides["columns"] == 3
    export_report = json.loads((result.package_dir / "fbx_export_report.json").read_text(encoding="utf-8"))
    assert export_report["status"] == "unavailable"
    assert not (result.package_dir / "puzzle_007.fbx").exists()

import json
from pathlib import Path

import pytest

from puzzle_pipeline.blender.bootstrap import find_blender, run_blender_generation


def test_missing_blender_is_actionable(tmp_path) -> None:
    missing = tmp_path / "does-not-exist" / "blender.exe"
    assert find_blender(missing) is None
    result = run_blender_generation(tmp_path / "scene-input.json", tmp_path, executable=missing)
    assert result.status == "unavailable"
    assert "Blender executable not found" in result.message


@pytest.mark.blender
def test_installed_blender_generates_an_fbx_smoke_artifact(tmp_path) -> None:
    blender = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe")
    if find_blender(blender) is None:
        pytest.skip("known Blender installation is not present")
    scene_input = tmp_path / "scene-input.json"
    scene_input.write_text(
        json.dumps(
            {
                "puzzle_id": "smoke",
                "collection_name": "Puzzle_smoke",
                "atlas_path": None,
                "positions": {"piece_r00_c00": [0.0, 0.0, 0.0]},
                "meshes": [
                    {
                        "piece_id": "piece_r00_c00",
                        "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                        "faces": [[0, 1, 2]],
                        "corner_uvs": [[[0, 0], [1, 0], [0, 1]]],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = run_blender_generation(scene_input, tmp_path, executable=blender)
    assert result.status == "passed", result.stderr
    assert (tmp_path / "models" / "puzzle.fbx").is_file()
    assert (tmp_path / "reports" / "fbx-reimport-report.json").is_file()

from puzzle_pipeline.blender.bootstrap import find_blender, run_blender_generation


def test_missing_blender_is_actionable(tmp_path) -> None:
    missing = tmp_path / "does-not-exist" / "blender.exe"
    assert find_blender(missing) is None
    result = run_blender_generation(tmp_path / "scene-input.json", tmp_path, executable=missing)
    assert result.status == "unavailable"
    assert "Blender executable not found" in result.message

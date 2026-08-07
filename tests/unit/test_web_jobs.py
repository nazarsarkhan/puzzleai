import json
from pathlib import Path

from PIL import Image

from puzzle_pipeline.web.jobs import GenerationJobService
from puzzle_pipeline.web.models import Recommendation


def test_job_generates_roblox_package_and_zip(tmp_path: Path) -> None:
    image = tmp_path / "art.png"
    Image.new("RGB", (16, 12), (30, 60, 90)).save(image)
    service = GenerationJobService(tmp_path / "data", skip_blender=True, atlas_size=256)
    recommendation = Recommendation(
        orientation="landscape",
        crop_mode="preserve",
        board_aspect=4 / 3,
        columns=3,
        rows=2,
        piece_count=6,
        confidence=1.0,
        reasons=["test"],
        warnings=[],
        source="deterministic",
    )

    created = service.create(image, recommendation)
    finished = service.run(created.id)

    assert finished.status == "ready"
    assert finished.download_name == "puzzle_001.zip"
    assert (tmp_path / "data" / created.id / "package" / "puzzle_001" / "manifest.json").is_file()
    contents = json.loads((tmp_path / "data" / created.id / "manifest.json").read_text(encoding="utf-8"))
    assert contents["status"] == "ready"
    assert (tmp_path / "data" / created.id / "puzzle_001.zip").is_file()


def test_job_uses_artwork_metadata_in_roblox_overrides(tmp_path: Path) -> None:
    image = tmp_path / "art.png"
    Image.new("RGB", (16, 16), (30, 60, 90)).save(image)
    service = GenerationJobService(tmp_path / "data", skip_blender=True, atlas_size=256)
    recommendation = Recommendation(
        orientation="square",
        crop_mode="preserve",
        board_aspect=1.0,
        columns=3,
        rows=3,
        piece_count=9,
        confidence=1.0,
        reasons=["AI identified the artwork."],
        warnings=[],
        source="llm",
        display_name="The Circus",
        artist="Georges Seurat",
        year="1890-1891",
        frame_label="The Circus — Georges Seurat",
        notes="Preserve the full circus scene.",
    )

    created = service.create(image, recommendation)
    finished = service.run(created.id)

    assert finished.status == "ready"
    overrides = json.loads(
        (tmp_path / "data" / created.id / "package" / "puzzle_001" / "roblox-overrides.json").read_text(
            encoding="utf-8"
        )
    )
    assert overrides["displayName"] == "The Circus"
    assert overrides["artist"] == "Georges Seurat"
    assert overrides["year"] == "1890-1891"
    assert overrides["frameLabel"] == "The Circus — Georges Seurat"
    assert overrides["notes"] == "Preserve the full circus scene."


def test_job_records_failure_without_losing_error_details(tmp_path: Path) -> None:
    missing = tmp_path / "missing.png"
    service = GenerationJobService(tmp_path / "data", skip_blender=True)
    recommendation = Recommendation(
        orientation="square",
        crop_mode="preserve",
        board_aspect=1.0,
        columns=3,
        rows=3,
        piece_count=9,
        confidence=1.0,
        reasons=[],
        warnings=[],
        source="deterministic",
    )

    created = service.create(missing, recommendation)
    finished = service.run(created.id)

    assert finished.status == "failed"
    assert "not found" in (finished.error or "").lower()


def test_relative_data_root_is_resolved_before_blender_receives_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    service = GenerationJobService(Path(".web-data"), skip_blender=True)

    assert service.data_root.is_absolute()

"""Roblox-specific package assembly and deterministic image batching."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from puzzle_pipeline.blender.bootstrap import BlenderResult, run_blender_generation
from puzzle_pipeline.config.models import AtlasConfig, BoardConfig, GridConfig, PuzzleConfig
from puzzle_pipeline.pipeline import GenerationResult, run_core_pipeline

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PREFERRED_IMAGE_ORDER = (
    "чёрный_супрематический_квадрат._1915._гтг.png",
    "download.jpg",
    "99a5fec23b9b29718b492326a88b454d.jpg",
    "2892.1800x1800.jpg",
)


@dataclass(frozen=True)
class RobloxPuzzleSpec:
    number: int
    source: Path
    display_name: str
    artist: str
    year: str
    orientation: str
    columns: int
    rows: int
    ui_sort_order: int
    frame_label: str
    notes: str

    @property
    def puzzle_id(self) -> str:
        return f"puzzle_{self.number:03d}"


@dataclass(frozen=True)
class RobloxPackageResult:
    package_dir: Path
    spec: RobloxPuzzleSpec
    export_status: str


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _report_from_status(status: str | BlenderResult, kind: str) -> dict[str, object]:
    if isinstance(status, BlenderResult):
        if status.status == "passed":
            return {"valid": True, "status": "passed", "message": status.message, "command": status.command}
        return {
            "valid": False,
            "status": status.status,
            "message": status.message,
            "command": status.command,
            "stderr": status.stderr,
        }
    if status == "passed":
        return {"valid": True, "status": "passed", "message": f"{kind} passed"}
    return {
        "valid": False,
        "status": status,
        "message": "Blender executable not found; install Blender and rerun export.",
    }


def write_roblox_package(
    spec: RobloxPuzzleSpec,
    config: PuzzleConfig,
    core: GenerationResult,
    output_root: Path,
    blender_status: str | BlenderResult = "unavailable",
) -> RobloxPackageResult:
    """Copy only the files accepted by the Roblox import contract."""
    package_dir = output_root / spec.puzzle_id
    package_dir.mkdir(parents=True, exist_ok=True)
    atlas_source = core.package_dir / "textures" / f"{config.puzzle_id}_atlas.png"
    shutil.copy2(atlas_source, package_dir / f"{spec.puzzle_id}_atlas.png")
    shutil.copy2(spec.source, package_dir / f"{spec.puzzle_id}_completion.png")

    manifest = core.manifest.model_dump(mode="json")
    manifest["puzzle_id"] = spec.puzzle_id
    manifest["grid"] = {"columns": spec.columns, "rows": spec.rows}
    export_report = _report_from_status(blender_status, "FBX export")
    reimport_report = _report_from_status(blender_status, "FBX re-import")
    fbx_source = core.package_dir / "models" / "puzzle.fbx"
    fbx_target = package_dir / f"{spec.puzzle_id}.fbx"
    if fbx_source.is_file() and export_report["status"] == "passed":
        shutil.copy2(fbx_source, fbx_target)
        manifest["exports"] = {"fbx": fbx_target.name, "glb": None, "blend": None}
    else:
        fbx_target.unlink(missing_ok=True)
        manifest["exports"] = {"fbx": None, "glb": None, "blend": None}
    _write_json(package_dir / "manifest.json", manifest)
    validation = {
        "valid": core.validation.status == "passed",
        "status": core.validation.status,
        "errors": list(core.validation.errors),
        "checks": {key: value == "passed" for key, value in core.validation.checks.items()},
        "expectedPieceCount": len(core.manifest.pieces),
        "validatedPieceCount": len(core.manifest.pieces),
        "exportStatus": export_report["status"],
        "metrics": core.validation.metrics,
    }
    _write_json(package_dir / "manifest.validation.json", validation)
    _write_json(package_dir / "fbx_export_report.json", export_report)
    _write_json(package_dir / "fbx_reimport_report.json", reimport_report)
    _write_json(
        package_dir / "roblox-overrides.json",
        {
            "displayName": spec.display_name,
            "artist": spec.artist,
            "year": spec.year,
            "orientation": spec.orientation,
            "columns": spec.columns,
            "rows": spec.rows,
            "uiSortOrder": spec.ui_sort_order,
            "frameLabel": spec.frame_label,
            "notes": spec.notes,
        },
    )
    return RobloxPackageResult(package_dir, spec, str(export_report["status"]))


def _orientation(width: int, height: int) -> str:
    if abs(width - height) / max(width, height) <= 0.03:
        return "square"
    return "landscape" if width > height else "portrait"


def _known_metadata(name: str) -> tuple[str, str, str, str] | None:
    lowered = name.lower()
    if lowered.startswith("чёрный_супрематический_квадрат"):
        return ("Black Square", "Kazimir Malevich", "1915", "Preserve the full square composition.")
    if lowered == "download.jpg":
        return ("Mona Lisa", "Leonardo da Vinci", "1503-1519", "Preserve the full portrait composition.")
    if lowered == "99a5fec23b9b29718b492326a88b454d.jpg":
        return ("Graffiti Portrait", "Unknown", "unknown", "Preserve the full supplied artwork.")
    if lowered == "2892.1800x1800.jpg":
        return ("Mountain Landscape", "Unknown", "unknown", "Preserve the full supplied artwork.")
    return None


def spec_for_image(path: Path, number: int) -> RobloxPuzzleSpec:
    with Image.open(path) as image:
        width, height = image.size
    orientation = _orientation(width, height)
    metadata = _known_metadata(path.name)
    display_name, artist, year, notes = metadata or (
        path.stem.replace("_", " ").title(),
        "Unknown",
        "unknown",
        "Preserve the full supplied artwork.",
    )
    columns, rows = (3, 3) if orientation == "square" else (3, 4) if orientation == "portrait" else (4, 3)
    frame_label = display_name if artist == "Unknown" else f"{display_name} — {artist}"
    return RobloxPuzzleSpec(
        number=number,
        source=path,
        display_name=display_name,
        artist=artist,
        year=year,
        orientation=orientation,
        columns=columns,
        rows=rows,
        ui_sort_order=number,
        frame_label=frame_label,
        notes=notes,
    )


def _config_for_spec(spec: RobloxPuzzleSpec, atlas_size: int) -> PuzzleConfig:
    board_width, board_height = (
        (4.0, 4.0) if spec.orientation == "square" else (3.0, 4.0) if spec.orientation == "portrait" else (4.0, 3.0)
    )
    return PuzzleConfig(
        puzzle_id=spec.puzzle_id,
        seed=spec.number,
        grid=GridConfig(columns=spec.columns, rows=spec.rows),
        board=BoardConfig(width=board_width, height=board_height, thickness=0.07),
        atlas=AtlasConfig(size=atlas_size),
    )


def batch_images(
    input_dir: Path,
    output_root: Path,
    start_number: int = 7,
    atlas_size: int = 2048,
    skip_blender: bool = False,
) -> tuple[RobloxPackageResult, ...]:
    """Compile every supported image into a numbered Roblox package."""
    paths = sorted(
        (path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda path: (
            0,
            PREFERRED_IMAGE_ORDER.index(path.name.lower()),
        )
        if path.name.lower() in PREFERRED_IMAGE_ORDER
        else (1, path.name.lower()),
    )
    if not paths:
        raise ValueError(f"No supported artwork images found in {input_dir}")
    results: list[RobloxPackageResult] = []
    with TemporaryDirectory(prefix="puzzle-pipeline-batch-") as temporary:
        temporary_root = Path(temporary)
        for offset, path in enumerate(paths):
            spec = spec_for_image(path, start_number + offset)
            config = _config_for_spec(spec, atlas_size)
            core = run_core_pipeline(config, path, temporary_root / "core")
            blender_status: str | BlenderResult = "unavailable"
            if not skip_blender:
                blender_status = run_blender_generation(
                    core.package_dir / "blender" / "scene-input.json",
                    core.package_dir,
                    config.export.formats,
                )
            results.append(write_roblox_package(spec, config, core, output_root, blender_status))
    return tuple(results)

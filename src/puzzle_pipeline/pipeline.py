"""Core pipeline orchestration independent of Blender."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from puzzle_pipeline import __version__
from puzzle_pipeline.artwork.atlas import AtlasArtifact
from puzzle_pipeline.artwork.loader import load_artwork
from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.coordinates import board_coordinates
from puzzle_pipeline.core.geometry.mesh import MeshData, extrude_piece
from puzzle_pipeline.core.geometry.outlines import PuzzleGeometry, generate_puzzle_geometry
from puzzle_pipeline.manifests.models import PuzzleManifest, build_manifest
from puzzle_pipeline.manifests.writer import write_manifest
from puzzle_pipeline.uv.front import map_mesh_uvs
from puzzle_pipeline.validation.geometry import validate_outlines
from puzzle_pipeline.validation.mesh import validate_mesh
from puzzle_pipeline.validation.seams import validate_topology
from puzzle_pipeline.validation.uv import validate_uv

from .artwork.atlas import build_atlas


@dataclass(frozen=True)
class ValidationSummary:
    status: str
    checks: dict[str, str]
    metrics: dict[str, float]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class GenerationResult:
    package_dir: Path
    manifest_path: Path
    validation_path: Path
    manifest: PuzzleManifest
    validation: ValidationSummary
    meshes: tuple[MeshData, ...]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mesh_json(mesh: MeshData) -> dict[str, object]:
    return {
        "piece_id": mesh.piece_id,
        "vertices": mesh.vertices,
        "faces": mesh.faces,
        "regions": [region.value for region in mesh.regions],
        "uvs": mesh.uvs,
        "corner_uvs": mesh.corner_uvs,
        "thickness": mesh.thickness,
    }


def _validation_summary(
    geometry: PuzzleGeometry,
    meshes: tuple[MeshData, ...],
    atlas: AtlasArtifact,
    config: PuzzleConfig,
) -> ValidationSummary:
    results = {
        "topology": validate_topology(geometry),
        "outlines": validate_outlines(geometry),
        "geometry": validate_outlines(geometry),
    }
    for mesh in meshes:
        results[f"mesh:{mesh.piece_id}"] = validate_mesh(mesh, config.piece)
    for mesh in meshes:
        results[f"uv:{mesh.piece_id}"] = validate_uv(mesh, atlas.layout)
    errors = tuple(error for result in results.values() for error in result.errors)
    metrics: dict[str, float] = {key: value for result in results.values() for key, value in result.metrics}
    return ValidationSummary(
        "passed" if not errors else "failed",
        {key: "passed" if result.valid else "failed" for key, result in results.items()},
        metrics,
        errors,
    )


def run_core_pipeline(config: PuzzleConfig, image: Path, output_root: Path) -> GenerationResult:
    """Generate all non-Blender artifacts and fail with structured validation output."""
    package_dir = output_root / config.puzzle_id
    for directory in ("source", "textures", "models", "blender", "manifests", "reports", "debug"):
        (package_dir / directory).mkdir(parents=True, exist_ok=True)
    artwork = load_artwork(image)
    source_target = package_dir / "source" / image.name
    if image.resolve() != source_target.resolve():
        shutil.copy2(image, source_target)
    board = board_coordinates(config)
    atlas = build_atlas(artwork, config.atlas, board, package_dir / "textures" / f"{config.puzzle_id}_atlas.png")
    geometry = generate_puzzle_geometry(config)
    meshes = tuple(
        map_mesh_uvs(extrude_piece(piece, config.board, config.piece), piece, board, atlas.layout)
        for piece in geometry.pieces
    )
    validation = _validation_summary(geometry, meshes, atlas, config)
    manifest = build_manifest(config, geometry, atlas.layout)
    manifest = manifest.model_copy(
        update={
            "pieces": [
                piece.model_copy(update={"triangle_count": mesh.triangle_count})
                for piece, mesh in zip(manifest.pieces, meshes, strict=True)
            ]
        }
    )
    manifest_path = write_manifest(manifest, package_dir / "manifests" / "puzzle.json")
    validation_path = package_dir / "manifests" / "validation.json"
    _write_json(
        validation_path,
        {
            "status": validation.status,
            "checks": validation.checks,
            "metrics": validation.metrics,
            "errors": validation.errors,
        },
    )
    _write_json(
        package_dir / "debug" / "seam-map.json",
        {
            seam.id: {"orientation": seam.orientation, "points": seam.boundary_points, "center_t": seam.center_t}
            for seam in geometry.seams
        },
    )
    _write_json(
        package_dir / "blender" / "scene-input.json",
        {
            "puzzle_id": config.puzzle_id,
            "atlas_path": str(package_dir / "textures" / f"{config.puzzle_id}_atlas.png"),
            "collection_name": f"Puzzle_{config.puzzle_id}",
            "positions": {
                piece.id: [piece.center[0], piece.center[1], 0.0]
                for piece in geometry.pieces
            },
            "meshes": [_mesh_json(mesh) for mesh in meshes],
        },
    )
    _write_json(
        package_dir / "reports" / "generation-report.json",
        {
            "status": validation.status,
            "generator_version": __version__,
            "puzzle_id": config.puzzle_id,
            "pieces": len(meshes),
            "triangles": sum(mesh.triangle_count for mesh in meshes),
            "blender": {"status": "not_run", "reason": "core pipeline does not require Blender"},
            "errors": validation.errors,
        },
    )
    return GenerationResult(package_dir, manifest_path, validation_path, manifest, validation, meshes)

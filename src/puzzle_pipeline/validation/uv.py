"""Atlas bounds and front UV continuity validation."""

from __future__ import annotations

from puzzle_pipeline.artwork.atlas import AtlasLayout
from puzzle_pipeline.core.geometry.mesh import MeshData, SurfaceRegion
from puzzle_pipeline.core.types import ValidationResult


def validate_uv(mesh: MeshData, layout: AtlasLayout) -> ValidationResult:
    errors: list[str] = []
    for uv in mesh.uvs:
        if not all(0.0 <= value <= 1.0 for value in uv):
            errors.append(f"{mesh.piece_id}: UV outside normalized atlas bounds: {uv}")
    for _face, region, corners in zip(mesh.faces, mesh.regions, mesh.corner_uvs, strict=True):
        for uv in corners:
            if not all(0.0 <= value <= 1.0 for value in uv):
                errors.append(f"{mesh.piece_id}: corner UV outside normalized atlas bounds: {uv}")
            if region is SurfaceRegion.FRONT:
                min_u = layout.artwork.x / layout.size
                max_u = (layout.artwork.x + layout.artwork.width) / layout.size
                min_v = layout.artwork.y / layout.size
                max_v = (layout.artwork.y + layout.artwork.height) / layout.size
                if not min_u - 1e-12 <= uv[0] <= max_u + 1e-12 or not min_v - 1e-12 <= uv[1] <= max_v + 1e-12:
                    errors.append(f"{mesh.piece_id}: front UV is outside artwork region")
    return ValidationResult(not errors, tuple(errors), (("uv_count", float(len(mesh.uvs))),))

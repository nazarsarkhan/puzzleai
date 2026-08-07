"""Puzzle topology validation."""

from __future__ import annotations

from puzzle_pipeline.core.geometry.outlines import PuzzleGeometry
from puzzle_pipeline.core.types import EdgeKind, Side, ValidationResult


def validate_topology(geometry: PuzzleGeometry) -> ValidationResult:
    errors: list[str] = []
    for seam in geometry.seams:
        if seam.owner_a[2] is not EdgeKind.TAB or seam.owner_b[2] is not EdgeKind.HOLE:
            errors.append(f"{seam.id}: owners are not TAB/HOLE complementary")
        if geometry.piece(seam.owner_a[0]).seam_id(seam.owner_a[1]) != seam.id:
            errors.append(f"{seam.id}: owner A does not reference seam")
        if geometry.piece(seam.owner_b[0]).seam_id(seam.owner_b[1]) != seam.id:
            errors.append(f"{seam.id}: owner B does not reference seam")
    for piece in geometry.pieces:
        for side in Side:
            expected = geometry.piece(piece.id).connector(side)
            if side in {Side.TOP, Side.RIGHT} and piece.row == 0 and side is Side.TOP:
                pass
            if expected is not EdgeKind.FLAT and piece.seam_id(side) is None:
                errors.append(f"{piece.id}.{side.value}: internal connector has no seam id")
    return ValidationResult(not errors, tuple(errors), (("seams", float(len(geometry.seams))),))

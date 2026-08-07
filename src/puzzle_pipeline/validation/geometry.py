"""2D outline validation."""

from __future__ import annotations

import math

from puzzle_pipeline.core.geometry.outlines import PieceOutline, PuzzleGeometry
from puzzle_pipeline.core.types import Point2, ValidationResult


def _cross(a: Point2, b: Point2, c: Point2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(a: Point2, b: Point2, c: Point2, d: Point2) -> bool:
    ab_c = _cross(a, b, c)
    ab_d = _cross(a, b, d)
    cd_a = _cross(c, d, a)
    cd_b = _cross(c, d, b)
    return (ab_c * ab_d < -1e-12) and (cd_a * cd_b < -1e-12)


def _signed_area(points: tuple[Point2, ...]) -> float:
    return 0.5 * sum(
        points[index][0] * points[index + 1][1] - points[index + 1][0] * points[index][1]
        for index in range(len(points) - 1)
    )


def _valid_piece(piece: PieceOutline) -> list[str]:
    errors: list[str] = []
    if len(piece.points) < 4 or piece.points[0] != piece.points[-1]:
        errors.append(f"{piece.id}: outline is not closed")
        return errors
    if _signed_area(piece.points) <= 0:
        errors.append(f"{piece.id}: outline winding is not counter-clockwise")
    for point in piece.points:
        if not all(math.isfinite(value) for value in point):
            errors.append(f"{piece.id}: outline contains a non-finite coordinate")
    segments = list(zip(piece.points, piece.points[1:], strict=False))
    for first, (a, b) in enumerate(segments):
        for second, (c, d) in enumerate(segments):
            if second <= first + 1 or (first == 0 and second == len(segments) - 1):
                continue
            if _segments_intersect(a, b, c, d):
                errors.append(f"{piece.id}: outline self-intersects between segments {first} and {second}")
    return errors


def validate_outlines(geometry: PuzzleGeometry) -> ValidationResult:
    errors = [error for piece in geometry.pieces for error in _valid_piece(piece)]
    return ValidationResult(not errors, tuple(errors), (("pieces", float(len(geometry.pieces))),))

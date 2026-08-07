"""Mesh topology and metric validation."""

from __future__ import annotations

import math
from collections import Counter

from puzzle_pipeline.config.models import PieceConfig
from puzzle_pipeline.core.geometry.mesh import MeshData
from puzzle_pipeline.core.types import ValidationResult


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def validate_mesh(mesh: MeshData, config: PieceConfig) -> ValidationResult:
    errors: list[str] = []
    degenerate = 0
    volume = 0.0
    edges: Counter[tuple[int, int]] = Counter()
    for face in mesh.faces:
        a, b, c = (mesh.vertices[index] for index in face)
        ab = _sub(b, a)
        ac = _sub(c, a)
        if math.sqrt(_dot(_cross(ab, ac), _cross(ab, ac))) <= 1e-12:
            degenerate += 1
        volume += _dot(a, _cross(b, c)) / 6.0
        for first, second in zip(face, (*face[1:], face[0]), strict=True):
            edge = (min(first, second), max(first, second))
            edges[edge] += 1
    non_manifold = sum(1 for count in edges.values() if count != 2)
    if len(mesh.vertices) != len(mesh.uvs):
        errors.append(f"{mesh.piece_id}: vertex/UV count mismatch")
    if degenerate:
        errors.append(f"{mesh.piece_id}: {degenerate} degenerate triangles")
    if non_manifold:
        errors.append(f"{mesh.piece_id}: {non_manifold} non-manifold edges")
    if volume <= 0:
        errors.append(f"{mesh.piece_id}: signed volume is not positive")
    if mesh.triangle_count > 1000:
        errors.append(f"{mesh.piece_id}: triangle count exceeds 1000")
    if abs(mesh.thickness - mesh.vertices[0][2] * 2) > 1e-9:
        errors.append(f"{mesh.piece_id}: thickness metadata does not match vertices")
    return ValidationResult(
        not errors,
        tuple(errors),
        (
            ("triangles", float(mesh.triangle_count)),
            ("degenerate_triangles", float(degenerate)),
            ("non_manifold_edges", float(non_manifold)),
            ("signed_volume", volume),
            ("bevel_width", config.bevel_width),
        ),
    )

"""Deterministic ear-clipping triangulation for simple polygons."""

from __future__ import annotations

from collections.abc import Sequence

from puzzle_pipeline.core.types import Point2


class TriangulationError(ValueError):
    """Raised when a polygon cannot be triangulated safely."""


def _cross(a: Point2, b: Point2, c: Point2) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _area(polygon: Sequence[Point2]) -> float:
    return 0.5 * sum(
        polygon[index][0] * polygon[(index + 1) % len(polygon)][1]
        - polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
        for index in range(len(polygon))
    )


def _inside(point: Point2, a: Point2, b: Point2, c: Point2) -> bool:
    signs = (_cross(a, b, point), _cross(b, c, point), _cross(c, a, point))
    return all(value >= -1e-12 for value in signs) or all(value <= 1e-12 for value in signs)


def triangulate_polygon(polygon: Sequence[Point2]) -> tuple[tuple[int, int, int], ...]:
    """Triangulate a counter-clockwise simple polygon without changing its order."""
    if len(polygon) < 3 or abs(_area(polygon)) <= 1e-12:
        raise TriangulationError("degenerate polygon cannot be triangulated")
    if _area(polygon) < 0:
        raise TriangulationError("polygon must be counter-clockwise")
    remaining = list(range(len(polygon)))
    triangles: list[tuple[int, int, int]] = []
    guard = 0
    while len(remaining) > 3:
        ear_found = False
        for position, current in enumerate(remaining):
            previous = remaining[position - 1]
            following = remaining[(position + 1) % len(remaining)]
            if _cross(polygon[previous], polygon[current], polygon[following]) <= 1e-12:
                continue
            if any(
                _inside(polygon[index], polygon[previous], polygon[current], polygon[following])
                for index in remaining
                if index not in {previous, current, following}
            ):
                continue
            triangles.append((previous, current, following))
            del remaining[position]
            ear_found = True
            break
        guard += 1
        if not ear_found or guard > len(polygon) * len(polygon):
            raise TriangulationError("polygon is self-intersecting or has no stable ear")
    triangles.append((remaining[0], remaining[1], remaining[2]))
    return tuple(triangles)

import pytest

from puzzle_pipeline.core.geometry.triangulation import TriangulationError, triangulate_polygon


def test_triangulates_concave_polygon_deterministically() -> None:
    polygon = ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (1.0, 1.0), (0.0, 2.0))
    first = triangulate_polygon(polygon)
    assert first == triangulate_polygon(polygon)
    assert len(first) == 3


def test_rejects_degenerate_polygon() -> None:
    with pytest.raises(TriangulationError, match="degenerate"):
        triangulate_polygon(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)))

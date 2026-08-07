"""Predictable closed triangle meshes for puzzle pieces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from puzzle_pipeline.config.models import BoardConfig, PieceConfig
from puzzle_pipeline.core.geometry.outlines import PieceOutline
from puzzle_pipeline.core.geometry.triangulation import triangulate_polygon
from puzzle_pipeline.core.types import Point2


class SurfaceRegion(StrEnum):
    FRONT = "front"
    BACK = "back"
    SIDE = "side"


Point3 = tuple[float, float, float]
UV = tuple[float, float]


@dataclass(frozen=True)
class MeshData:
    piece_id: str
    vertices: tuple[Point3, ...]
    faces: tuple[tuple[int, int, int], ...]
    regions: tuple[SurfaceRegion, ...]
    uvs: tuple[UV, ...]
    thickness: float

    @property
    def triangle_count(self) -> int:
        return len(self.faces)


def _local(point: Point2, center: Point2) -> Point2:
    return (point[0] - center[0], point[1] - center[1])


def extrude_piece(piece: PieceOutline, board: BoardConfig, _piece: PieceConfig | None = None) -> MeshData:
    """Extrude a closed outline into a watertight triangle mesh."""
    outline = tuple(_local(point, piece.center) for point in piece.points[:-1])
    triangles_2d = triangulate_polygon(outline)
    half_thickness = board.thickness / 2
    vertices: list[Point3] = [(*point, half_thickness) for point in outline]
    vertices.extend((*point, -half_thickness) for point in outline)
    faces: list[tuple[int, int, int]] = []
    regions: list[SurfaceRegion] = []
    count = len(outline)
    for first, second, third in triangles_2d:
        faces.append((first, second, third))
        regions.append(SurfaceRegion.FRONT)
        faces.append((count + third, count + second, count + first))
        regions.append(SurfaceRegion.BACK)
    for index in range(count):
        following = (index + 1) % count
        faces.append((count + index, count + following, following))
        regions.append(SurfaceRegion.SIDE)
        faces.append((count + index, following, index))
        regions.append(SurfaceRegion.SIDE)
    return MeshData(
        piece_id=piece.id,
        vertices=tuple(vertices),
        faces=tuple(faces),
        regions=tuple(regions),
        uvs=tuple((0.0, 0.0) for _ in vertices),
        thickness=board.thickness,
    )

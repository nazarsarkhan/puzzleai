"""Mathematical front and per-surface mesh UV mapping."""

from __future__ import annotations

from dataclasses import replace

from puzzle_pipeline.artwork.atlas import AtlasLayout
from puzzle_pipeline.core.coordinates import BoardCoordinates
from puzzle_pipeline.core.geometry.mesh import UV, MeshData, SurfaceRegion
from puzzle_pipeline.core.geometry.outlines import PieceOutline
from puzzle_pipeline.core.types import Point2


def front_uv_for_point(point: Point2, board: BoardCoordinates, atlas: AtlasLayout) -> UV:
    return atlas.front_uv(board.world_to_front_uv(point[0], point[1]))


def map_mesh_uvs(
    mesh: MeshData,
    piece: PieceOutline,
    board: BoardCoordinates,
    atlas: AtlasLayout,
) -> MeshData:
    vertex_count = len(mesh.vertices) // 2
    uvs: list[UV] = []
    for index, vertex in enumerate(mesh.vertices):
        if index < vertex_count:
            uvs.append(front_uv_for_point((vertex[0] + piece.center[0], vertex[1] + piece.center[1]), board, atlas))
        else:
            uvs.append(atlas.back_uv())
    corner_uvs: list[tuple[UV, UV, UV]] = []
    for face, region in zip(mesh.faces, mesh.regions, strict=True):
        if region is SurfaceRegion.FRONT:
            corner_uvs.append(tuple(uvs[index] for index in face))  # type: ignore[arg-type]
        elif region is SurfaceRegion.BACK:
            corner_uvs.append(tuple(atlas.back_uv() for _ in face))  # type: ignore[arg-type]
        else:
            corner_uvs.append(tuple(atlas.sides_uv() for _ in face))  # type: ignore[arg-type]
    return replace(mesh, uvs=tuple(uvs), corner_uvs=tuple(corner_uvs))

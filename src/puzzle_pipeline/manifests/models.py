"""Roblox-facing manifest models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from puzzle_pipeline import __version__
from puzzle_pipeline.artwork.atlas import AtlasLayout
from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.geometry.outlines import PieceOutline, PuzzleGeometry


class ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TransformModel(ManifestModel):
    position: tuple[float, float, float]
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)


class PieceManifest(ManifestModel):
    id: str
    row: int
    column: int
    solved_transform: TransformModel
    neighbors: dict[str, str | None]
    seam_ids: dict[str, str | None]
    connectors: dict[str, str]
    visual_bounds: dict[str, tuple[float, float]]
    triangle_count: int


class PuzzleManifest(ManifestModel):
    schema_version: int = 1
    generator_version: str = __version__
    puzzle_id: str
    seed: int
    grid: dict[str, int]
    board: dict[str, float]
    atlas: dict[str, object]
    material: dict[str, object]
    exports: dict[str, str | None]
    pieces: list[PieceManifest] = Field(default_factory=list)


def _piece_bounds(piece: PieceOutline) -> dict[str, tuple[float, float]]:
    xs = [point[0] for point in piece.points]
    ys = [point[1] for point in piece.points]
    return {"min": (min(xs), min(ys)), "max": (max(xs), max(ys))}


def _neighbors(piece: PieceOutline, geometry: PuzzleGeometry) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for side, delta in (("top", (0, 1)), ("right", (1, 0)), ("bottom", (0, -1)), ("left", (-1, 0))):
        row = piece.row + delta[1]
        column = piece.column + delta[0]
        result[side] = next(
            (candidate.id for candidate in geometry.pieces if candidate.row == row and candidate.column == column),
            None,
        )
    return result


def build_manifest(config: PuzzleConfig, geometry: PuzzleGeometry, layout: AtlasLayout) -> PuzzleManifest:
    pieces: list[PieceManifest] = []
    for piece in geometry.pieces:
        connectors = {side.value: kind.value for side, kind in piece.connectors}
        seam_ids = {side.value: piece.seam_id(side) for side, _kind in piece.connectors}
        pieces.append(
            PieceManifest(
                id=piece.id,
                row=piece.row,
                column=piece.column,
                solved_transform=TransformModel(position=(piece.center[0], piece.center[1], 0.0)),
                neighbors=_neighbors(piece, geometry),
                seam_ids=seam_ids,
                connectors=connectors,
                visual_bounds=_piece_bounds(piece),
                triangle_count=0,
            )
        )
    return PuzzleManifest(
        puzzle_id=config.puzzle_id,
        seed=config.seed,
        grid={"columns": config.grid.columns, "rows": config.grid.rows},
        board={"width": config.board.width, "height": config.board.height, "thickness": config.board.thickness},
        atlas={
            "filename": f"{config.puzzle_id}_atlas.png",
            "size": layout.size,
            "artwork_pixels": [layout.artwork.x, layout.artwork.y, layout.artwork.width, layout.artwork.height],
            "back_pixels": [layout.back.x, layout.back.y, layout.back.width, layout.back.height],
            "sides_pixels": [layout.sides.x, layout.sides.y, layout.sides.width, layout.sides.height],
        },
        material={"name": "PuzzleAtlas", "shared": True},
        exports={"blend": None, "fbx": None, "glb": None},
        pieces=pieces,
    )

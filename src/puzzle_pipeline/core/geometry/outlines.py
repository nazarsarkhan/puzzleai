"""Assemble piece outlines from shared global seam boundaries."""

from __future__ import annotations

from dataclasses import dataclass

from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.coordinates import board_coordinates
from puzzle_pipeline.core.geometry.seams import Seam, SeamGraph, piece_id
from puzzle_pipeline.core.random import SeededRng
from puzzle_pipeline.core.types import EdgeKind, Point2, Side


@dataclass(frozen=True)
class PieceOutline:
    id: str
    row: int
    column: int
    center: Point2
    points: tuple[Point2, ...]
    edges: tuple[tuple[Side, tuple[Point2, ...]], ...]
    connectors: tuple[tuple[Side, EdgeKind], ...]
    seam_ids: tuple[tuple[Side, str], ...]

    def edge_points(self, side: Side) -> tuple[Point2, ...]:
        return dict(self.edges)[side]

    def connector(self, side: Side) -> EdgeKind:
        return dict(self.connectors)[side]

    def seam_id(self, side: Side) -> str | None:
        return dict(self.seam_ids).get(side)


@dataclass(frozen=True)
class PuzzleGeometry:
    seams: tuple[Seam, ...]
    pieces: tuple[PieceOutline, ...]
    width: float
    height: float

    def piece(self, piece_id_value: str) -> PieceOutline:
        for piece in self.pieces:
            if piece.id == piece_id_value:
                return piece
        raise KeyError(piece_id_value)


def _flat_edge(side: Side, min_x: float, max_x: float, min_y: float, max_y: float) -> tuple[Point2, Point2]:
    if side is Side.BOTTOM:
        return ((min_x, min_y), (max_x, min_y))
    if side is Side.RIGHT:
        return ((max_x, min_y), (max_x, max_y))
    if side is Side.TOP:
        return ((max_x, max_y), (min_x, max_y))
    return ((min_x, max_y), (min_x, min_y))


def _edge_from_seam(side: Side, seam_points: tuple[Point2, ...]) -> tuple[Point2, ...]:
    if side in {Side.RIGHT, Side.BOTTOM}:
        return seam_points
    return tuple(reversed(seam_points))


def generate_puzzle_geometry(config: PuzzleConfig) -> PuzzleGeometry:
    board = board_coordinates(config)
    graph = SeamGraph.generate(config.grid, config.seams, SeededRng(config.seed), board.width, board.height)
    pieces: list[PieceOutline] = []
    for row in range(config.grid.rows):
        for column in range(config.grid.columns):
            center = board.cell_center(column, row)
            min_x = board.min_x + column * board.cell_width
            max_x = min_x + board.cell_width
            min_y = board.min_y + row * board.cell_height
            max_y = min_y + board.cell_height
            edge_map: dict[Side, tuple[Point2, ...]] = {}
            connector_map: dict[Side, EdgeKind] = {}
            seam_map: dict[Side, str] = {}
            for side in Side:
                seam = graph.for_piece(piece_id(row, column), side)
                if seam is None:
                    edge_map[side] = _flat_edge(side, min_x, max_x, min_y, max_y)
                    connector_map[side] = EdgeKind.FLAT
                else:
                    edge_map[side] = _edge_from_seam(side, seam.boundary_points)
                    owner = (
                        seam.owner_a
                        if seam.owner_a[0] == piece_id(row, column) and seam.owner_a[1] is side
                        else seam.owner_b
                    )
                    connector_map[side] = owner[2]
                    seam_map[side] = seam.id

            bottom, right, top, left = (edge_map[side] for side in (Side.BOTTOM, Side.RIGHT, Side.TOP, Side.LEFT))
            points = tuple((*bottom[:-1], *right[:-1], *top[:-1], *left[:-1], bottom[0]))
            pieces.append(
                PieceOutline(
                    id=piece_id(row, column),
                    row=row,
                    column=column,
                    center=center,
                    points=points,
                    edges=tuple(edge_map.items()),
                    connectors=tuple(connector_map.items()),
                    seam_ids=tuple(seam_map.items()),
                )
            )
    return PuzzleGeometry(tuple(graph.seams), tuple(pieces), board.width, board.height)

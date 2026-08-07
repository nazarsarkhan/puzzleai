"""Board coordinate conventions and UV projection."""

from __future__ import annotations

from dataclasses import dataclass

from puzzle_pipeline.config.models import PuzzleConfig


@dataclass(frozen=True)
class BoardCoordinates:
    width: float
    height: float
    columns: int
    rows: int

    @property
    def min_x(self) -> float:
        return -self.width / 2

    @property
    def min_y(self) -> float:
        return -self.height / 2

    @property
    def cell_width(self) -> float:
        return self.width / self.columns

    @property
    def cell_height(self) -> float:
        return self.height / self.rows

    def cell_center(self, column: int, row: int) -> tuple[float, float]:
        if not 0 <= column < self.columns or not 0 <= row < self.rows:
            raise IndexError("cell is outside the configured grid")
        return (
            self.min_x + (column + 0.5) * self.cell_width,
            self.min_y + (row + 0.5) * self.cell_height,
        )

    def world_to_front_uv(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self.min_x) / self.width, (y - self.min_y) / self.height)


def board_coordinates(config: PuzzleConfig) -> BoardCoordinates:
    return BoardCoordinates(
        width=config.board.width,
        height=config.board.height,
        columns=config.grid.columns,
        rows=config.grid.rows,
    )

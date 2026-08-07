"""Shared seeded seam graph generation."""

from __future__ import annotations

from dataclasses import dataclass

from puzzle_pipeline.config.models import GridConfig, SeamConfig
from puzzle_pipeline.core.random import SeededRng
from puzzle_pipeline.core.types import EdgeKind, Point2, Side

from .curves import classic_semicircle_samples

Owner = tuple[str, Side, EdgeKind]


@dataclass(frozen=True)
class Seam:
    id: str
    orientation: str
    owner_a: Owner
    owner_b: Owner
    boundary_points: tuple[Point2, ...]
    center_t: float

    @property
    def kind(self) -> EdgeKind:
        return EdgeKind.TAB

    def boundary_points_for(self, _side: Side, _kind: EdgeKind) -> tuple[Point2, ...]:
        return self.boundary_points


@dataclass(frozen=True)
class SeamGraph:
    seams: tuple[Seam, ...]

    @classmethod
    def generate(
        cls,
        grid: GridConfig,
        config: SeamConfig,
        rng: SeededRng,
        width: float = 4.8,
        height: float = 3.2,
    ) -> SeamGraph:
        cell_width = width / grid.columns
        cell_height = height / grid.rows
        min_x = -width / 2
        min_y = -height / 2
        seams: list[Seam] = []
        vertical_rng = rng.fork("vertical")
        horizontal_rng = rng.fork("horizontal")

        for row in range(grid.rows):
            for column in range(1, grid.columns):
                center = max(
                    0.22,
                    min(
                        0.78,
                        0.5 + vertical_rng.uniform(-config.position_jitter, config.position_jitter),
                    ),
                )
                depth = cell_width * config.tab_depth_ratio * (
                    1.0 + vertical_rng.uniform(-config.shape_jitter, config.shape_jitter)
                )
                head_radius_ratio = config.tab_head_radius_ratio * (
                    1.0 + vertical_rng.uniform(-config.shape_jitter, config.shape_jitter)
                )
                x = min_x + column * cell_width
                y0 = min_y + row * cell_height
                points = tuple(
                    (x + offset, y0 + t * cell_height)
                    for t, offset in classic_semicircle_samples(
                        center,
                        cell_height,
                        depth,
                        head_radius_ratio,
                        config.edge_resolution,
                    )
                )
                left_id = piece_id(row, column - 1)
                right_id = piece_id(row, column)
                seams.append(
                    Seam(
                        id=f"seam_v_r{row:02}_c{column:02}",
                        orientation="vertical",
                        owner_a=(left_id, Side.RIGHT, EdgeKind.TAB),
                        owner_b=(right_id, Side.LEFT, EdgeKind.HOLE),
                        boundary_points=points,
                        center_t=center,
                    )
                )

        for row in range(1, grid.rows):
            for column in range(grid.columns):
                center = max(
                    0.22,
                    min(
                        0.78,
                        0.5 + horizontal_rng.uniform(-config.position_jitter, config.position_jitter),
                    ),
                )
                depth = cell_height * config.tab_depth_ratio * (
                    1.0 + horizontal_rng.uniform(-config.shape_jitter, config.shape_jitter)
                )
                head_radius_ratio = config.tab_head_radius_ratio * (
                    1.0 + horizontal_rng.uniform(-config.shape_jitter, config.shape_jitter)
                )
                x0 = min_x + column * cell_width
                y = min_y + row * cell_height
                points = tuple(
                    (x0 + t * cell_width, y + offset)
                    for t, offset in classic_semicircle_samples(
                        center,
                        cell_width,
                        depth,
                        head_radius_ratio,
                        config.edge_resolution,
                    )
                )
                lower_id = piece_id(row - 1, column)
                upper_id = piece_id(row, column)
                seams.append(
                    Seam(
                        id=f"seam_h_r{row:02}_c{column:02}",
                        orientation="horizontal",
                        owner_a=(lower_id, Side.TOP, EdgeKind.TAB),
                        owner_b=(upper_id, Side.BOTTOM, EdgeKind.HOLE),
                        boundary_points=points,
                        center_t=center,
                    )
                )
        return cls(tuple(seams))

    def for_piece(self, piece_id_value: str, side: Side) -> Seam | None:
        for seam in self.seams:
            if (seam.owner_a[0], seam.owner_a[1]) == (piece_id_value, side):
                return seam
            if (seam.owner_b[0], seam.owner_b[1]) == (piece_id_value, side):
                return seam
        return None


def piece_id(row: int, column: int) -> str:
    return f"piece_r{row:02}_c{column:02}"

from puzzle_pipeline.config.models import BoardConfig, GridConfig, PuzzleConfig
from puzzle_pipeline.core.coordinates import board_coordinates


def test_board_coordinates_center_and_front_projection() -> None:
    config = PuzzleConfig(
        puzzle_id="demo",
        grid=GridConfig(columns=4, rows=3),
        board=BoardConfig(width=8, height=6, thickness=0.07),
    )
    coords = board_coordinates(config)
    assert coords.cell_center(0, 0) == (-3.0, -2.0)
    assert coords.cell_center(3, 2) == (3.0, 2.0)
    assert coords.world_to_front_uv(0.0, 0.0) == (0.5, 0.5)

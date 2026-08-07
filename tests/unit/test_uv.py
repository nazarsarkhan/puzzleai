from PIL import Image

from puzzle_pipeline.artwork.atlas import build_atlas
from puzzle_pipeline.artwork.loader import load_artwork
from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.coordinates import board_coordinates
from puzzle_pipeline.core.geometry.mesh import extrude_piece
from puzzle_pipeline.core.geometry.outlines import generate_puzzle_geometry
from puzzle_pipeline.uv.front import front_uv_for_point, map_mesh_uvs
from puzzle_pipeline.validation.uv import validate_uv


def test_front_uv_projects_board_corners_into_artwork_region(tmp_path) -> None:
    image_path = tmp_path / "art.png"
    Image.new("RGB", (4, 2), (1, 2, 3)).save(image_path)
    config = PuzzleConfig(
        puzzle_id="demo",
        board={"width": 4, "height": 2},
        atlas={"size": 256},
    )
    atlas = build_atlas(load_artwork(image_path), config.atlas, board_coordinates(config), tmp_path / "atlas.png")
    low = front_uv_for_point((-2.0, -1.0), board_coordinates(config), atlas.layout)
    high = front_uv_for_point((2.0, 1.0), board_coordinates(config), atlas.layout)
    assert low == (atlas.layout.artwork.x / 256, atlas.layout.artwork.y / 256)
    assert high == (
        (atlas.layout.artwork.x + atlas.layout.artwork.width) / 256,
        (atlas.layout.artwork.y + atlas.layout.artwork.height) / 256,
    )


def test_generated_piece_uvs_validate(tmp_path) -> None:
    image_path = tmp_path / "art.png"
    Image.new("RGB", (4, 2), (1, 2, 3)).save(image_path)
    config = PuzzleConfig(puzzle_id="demo", board={"width": 4, "height": 2})
    board = board_coordinates(config)
    atlas = build_atlas(load_artwork(image_path), config.atlas, board, tmp_path / "atlas.png")
    geometry = generate_puzzle_geometry(config)
    mesh = map_mesh_uvs(extrude_piece(geometry.pieces[0], config.board), geometry.pieces[0], board, atlas.layout)
    assert validate_uv(mesh, atlas.layout).valid

from collections import Counter

from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.geometry.mesh import SurfaceRegion, extrude_piece
from puzzle_pipeline.core.geometry.outlines import generate_puzzle_geometry
from puzzle_pipeline.validation.mesh import validate_mesh


def test_extrusion_is_watertight_with_consistent_thickness() -> None:
    config = PuzzleConfig(puzzle_id="demo", seed=42)
    piece = generate_puzzle_geometry(config).pieces[0]
    mesh = extrude_piece(piece, config.board)

    assert mesh.triangle_count > 20
    assert len(mesh.vertices) == len(mesh.uvs)
    assert Counter(mesh.regions)[SurfaceRegion.FRONT] > 0
    assert Counter(mesh.regions)[SurfaceRegion.BACK] > 0
    assert validate_mesh(mesh, config.piece).valid


def test_mesh_contains_no_degenerate_triangles() -> None:
    config = PuzzleConfig(puzzle_id="demo", seed=43)
    mesh = extrude_piece(generate_puzzle_geometry(config).pieces[1], config.board)
    assert validate_mesh(mesh, config.piece).metrics_dict["degenerate_triangles"] == 0

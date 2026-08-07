from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.geometry.outlines import generate_puzzle_geometry
from puzzle_pipeline.validation.geometry import validate_outlines
from puzzle_pipeline.validation.seams import validate_topology


def test_piece_outlines_are_closed_valid_and_topology_is_complete() -> None:
    geometry = generate_puzzle_geometry(PuzzleConfig(puzzle_id="demo", seed=42))
    assert len(geometry.pieces) == 6
    assert all(piece.points[0] == piece.points[-1] for piece in geometry.pieces)
    assert validate_outlines(geometry).valid
    assert validate_topology(geometry).valid


def test_assembled_piece_boundaries_match_exactly() -> None:
    geometry = generate_puzzle_geometry(PuzzleConfig(puzzle_id="demo", seed=42))
    for seam in geometry.seams:
        first = geometry.piece(seam.owner_a[0]).edge_points(seam.owner_a[1])
        second = geometry.piece(seam.owner_b[0]).edge_points(seam.owner_b[1])
        assert first == tuple(reversed(second))

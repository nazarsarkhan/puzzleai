from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.core.geometry.seams import EdgeKind, SeamGraph, Side
from puzzle_pipeline.core.random import SeededRng


def test_internal_seams_are_shared_and_complementary() -> None:
    graph = SeamGraph.generate(PuzzleConfig(puzzle_id="demo").grid, PuzzleConfig(puzzle_id="demo").seams, SeededRng(42))
    assert len(graph.seams) == 7
    for seam in graph.seams:
        assert seam.kind == EdgeKind.TAB
        assert seam.owner_a[1] in {Side.RIGHT, Side.TOP}
        assert seam.owner_b[1] in {Side.LEFT, Side.BOTTOM}
        assert seam.owner_a[2] == EdgeKind.TAB
        assert seam.owner_b[2] == EdgeKind.HOLE
        assert seam.boundary_points == seam.boundary_points_for(seam.owner_b[1], EdgeKind.HOLE)


def test_same_seed_is_equal_and_different_seed_changes_seams() -> None:
    config = PuzzleConfig(puzzle_id="demo")
    a = SeamGraph.generate(config.grid, config.seams, SeededRng(42))
    b = SeamGraph.generate(config.grid, config.seams, SeededRng(42))
    c = SeamGraph.generate(config.grid, config.seams, SeededRng(43))
    assert a == b
    assert a != c

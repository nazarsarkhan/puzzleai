from puzzle_pipeline.core.random import SeededRng


def test_seeded_rng_is_reproducible_without_global_state() -> None:
    a = SeededRng(123)
    b = SeededRng(123)
    assert [a.uniform(-1, 1) for _ in range(8)] == [b.uniform(-1, 1) for _ in range(8)]


def test_fork_labels_produce_stable_independent_streams() -> None:
    a = SeededRng(123).fork("vertical")
    b = SeededRng(123).fork("vertical")
    c = SeededRng(123).fork("horizontal")
    assert [a.uniform(0, 1) for _ in range(4)] == [b.uniform(0, 1) for _ in range(4)]
    assert [SeededRng(123).fork("vertical").uniform(0, 1)] != [c.uniform(0, 1)]

"""Side-surface UV helpers."""

from puzzle_pipeline.artwork.atlas import AtlasLayout


def side_uv(layout: AtlasLayout) -> tuple[float, float]:
    return layout.sides_uv()

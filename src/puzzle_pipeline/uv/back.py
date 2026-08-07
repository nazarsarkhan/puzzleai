"""Back-surface UV helpers."""

from puzzle_pipeline.artwork.atlas import AtlasLayout


def back_uv(layout: AtlasLayout) -> tuple[float, float]:
    return layout.back_uv()

from PIL import Image

from puzzle_pipeline.artwork.atlas import build_atlas
from puzzle_pipeline.artwork.loader import load_artwork
from puzzle_pipeline.config.models import AtlasConfig
from puzzle_pipeline.core.coordinates import BoardCoordinates


def test_atlas_is_deterministic_and_has_explicit_regions(tmp_path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (4, 2), (200, 30, 10)).save(source)
    artwork = load_artwork(source)
    board = BoardCoordinates(4.0, 2.0, 2, 2)
    first = build_atlas(artwork, AtlasConfig(size=256, padding=4), board, tmp_path / "one.png")
    second = build_atlas(artwork, AtlasConfig(size=256, padding=4), board, tmp_path / "two.png")
    assert first.layout == second.layout
    assert first.image_bytes == second.image_bytes
    assert first.layout.artwork.width > 0
    assert first.layout.back.width > 0
    assert first.layout.sides.width > 0

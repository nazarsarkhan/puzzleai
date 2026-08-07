import pytest
from PIL import Image

from puzzle_pipeline.artwork.loader import load_artwork
from puzzle_pipeline.artwork.preprocess import fit_artwork


def test_load_artwork_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="Artwork image not found"):
        load_artwork(tmp_path / "missing.png")


def test_fit_artwork_accepts_portrait_and_landscape_inputs(tmp_path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (2, 4), (20, 40, 60)).save(source)
    artwork = load_artwork(source)
    fitted = fit_artwork(artwork, (200, 100))
    assert fitted.image.size == (200, 100)
    assert fitted.source_size == (2, 4)

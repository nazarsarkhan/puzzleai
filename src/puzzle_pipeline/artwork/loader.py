"""Safe artwork image loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class ArtworkImage:
    path: Path
    image: Image.Image
    source_size: tuple[int, int]
    mode: str


def load_artwork(path: Path) -> ArtworkImage:
    if not path.is_file():
        raise FileNotFoundError(f"Artwork image not found: {path}")
    try:
        with Image.open(path) as source:
            image = source.convert("RGBA" if "A" in source.getbands() else "RGB")
            source_size = source.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Unable to read artwork image: {path}") from exc
    if min(source_size) < 2:
        raise ValueError(f"Artwork image must be at least 2×2 pixels: {path}")
    return ArtworkImage(path, image, source_size, image.mode)

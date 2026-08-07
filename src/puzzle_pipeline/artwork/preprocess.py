"""Deterministic artwork fitting."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageOps

from .loader import ArtworkImage


@dataclass(frozen=True)
class FittedArtwork:
    image: Image.Image
    source_size: tuple[int, int]
    crop_mode: str


def fit_artwork(artwork: ArtworkImage, target_size: tuple[int, int]) -> FittedArtwork:
    """Fill an atlas rectangle without stretching; crop symmetrically if needed."""
    if min(target_size) < 1:
        raise ValueError("target artwork size must be positive")
    fitted = ImageOps.fit(
        artwork.image,
        target_size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    return FittedArtwork(fitted, artwork.source_size, "cover")

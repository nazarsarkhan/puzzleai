"""Deterministic single-texture atlas construction."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from puzzle_pipeline.config.models import AtlasConfig
from puzzle_pipeline.core.coordinates import BoardCoordinates

from .loader import ArtworkImage
from .preprocess import fit_artwork


@dataclass(frozen=True)
class PixelRect:
    x: int
    y: int
    width: int
    height: int

    def center_uv(self, size: int) -> tuple[float, float]:
        return ((self.x + self.width / 2) / size, (self.y + self.height / 2) / size)


@dataclass(frozen=True)
class AtlasLayout:
    size: int
    artwork: PixelRect
    back: PixelRect
    sides: PixelRect
    padding: int

    def front_uv(self, normalized: tuple[float, float]) -> tuple[float, float]:
        return (
            (self.artwork.x + normalized[0] * self.artwork.width) / self.size,
            (self.artwork.y + normalized[1] * self.artwork.height) / self.size,
        )

    def back_uv(self) -> tuple[float, float]:
        return self.back.center_uv(self.size)

    def sides_uv(self) -> tuple[float, float]:
        return self.sides.center_uv(self.size)


@dataclass(frozen=True)
class AtlasArtifact:
    path: Path
    layout: AtlasLayout
    image_bytes: bytes


def _layout(config: AtlasConfig, board: BoardCoordinates) -> AtlasLayout:
    size = config.size
    footer_height = max(32, min(256, size // 8))
    footer_y = config.padding
    half_width = (size - 3 * config.padding) // 2
    back = PixelRect(config.padding, footer_y, half_width, footer_height - 2 * config.padding)
    sides = PixelRect(2 * config.padding + half_width, footer_y, half_width, footer_height - 2 * config.padding)
    box_width = size - 2 * config.padding
    box_height = size - footer_height - 2 * config.padding
    target_aspect = board.width / board.height
    box_aspect = box_width / box_height
    if target_aspect >= box_aspect:
        artwork_width = box_width
        artwork_height = max(1, round(box_width / target_aspect))
    else:
        artwork_height = box_height
        artwork_width = max(1, round(box_height * target_aspect))
    artwork = PixelRect(
        (size - artwork_width) // 2,
        footer_height + config.padding + (box_height - artwork_height) // 2,
        artwork_width,
        artwork_height,
    )
    return AtlasLayout(size, artwork, back, sides, config.padding)


def build_atlas(
    artwork: ArtworkImage,
    config: AtlasConfig,
    board: BoardCoordinates,
    output: Path,
) -> AtlasArtifact:
    """Build a deterministic atlas and return its serialized bytes and layout."""
    layout = _layout(config, board)
    image = Image.new("RGB", (config.size, config.size), (32, 24, 18))
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        [
            layout.back.x,
            config.size - layout.back.y - layout.back.height,
            layout.back.x + layout.back.width - 1,
            config.size - layout.back.y - 1,
        ],
        fill=(248, 248, 248),
    )
    draw.rectangle(
        [
            layout.sides.x,
            config.size - layout.sides.y - layout.sides.height,
            layout.sides.x + layout.sides.width - 1,
            config.size - layout.sides.y - 1,
        ],
        fill=(150, 100, 55),
    )
    fitted = fit_artwork(artwork, (layout.artwork.width, layout.artwork.height)).image.convert("RGB")
    pillow_y = config.size - layout.artwork.y - layout.artwork.height
    image.paste(fitted, (layout.artwork.x, pillow_y))
    output.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    image.save(buffer, format=config.format, optimize=False)
    image_bytes = buffer.getvalue()
    output.write_bytes(image_bytes)
    return AtlasArtifact(output, layout, image_bytes)

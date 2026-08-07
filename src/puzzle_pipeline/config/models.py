"""Typed and validated puzzle configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class GridConfig(StrictModel):
    columns: int = Field(default=3, ge=2, le=64)
    rows: int = Field(default=2, ge=2, le=64)


class BoardConfig(StrictModel):
    width: float = Field(default=4.8, gt=0)
    height: float = Field(default=3.2, gt=0)
    thickness: float = Field(default=0.07, gt=0, le=1)


class PieceConfig(StrictModel):
    bevel_width: float = Field(default=0.012, ge=0, le=0.25)
    bevel_segments: int = Field(default=2, ge=0, le=8)


class SeamConfig(StrictModel):
    tab_radius_ratio: float = Field(default=0.18, gt=0.01, lt=0.45)
    position_jitter: float = Field(default=0.08, ge=0, le=0.4)
    shape_jitter: float = Field(default=0.12, ge=0, le=0.4)
    edge_resolution: int = Field(default=10, ge=4, le=32)


class AtlasConfig(StrictModel):
    size: int = Field(default=2048, ge=256, le=8192)
    padding: int = Field(default=8, ge=0, le=256)
    format: Literal["PNG"] = "PNG"

    @field_validator("size")
    @classmethod
    def size_is_power_of_two(cls, value: int) -> int:
        if value & (value - 1):
            raise ValueError("atlas size must be a power of two")
        return value


class ExportConfig(StrictModel):
    formats: tuple[Literal["fbx", "glb"], ...] = ("fbx",)
    apply_transforms: bool = True
    embed_textures: bool = True


class PuzzleConfig(StrictModel):
    schema_version: int = Field(default=1, ge=1)
    puzzle_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    seed: int = 42
    grid: GridConfig = Field(default_factory=GridConfig)
    board: BoardConfig = Field(default_factory=BoardConfig)
    piece: PieceConfig = Field(default_factory=PieceConfig)
    seams: SeamConfig = Field(default_factory=SeamConfig)
    atlas: AtlasConfig = Field(default_factory=AtlasConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)

    @field_validator("seed")
    @classmethod
    def seed_is_int32(cls, value: int) -> int:
        if not -(2**31) <= value <= 2**31 - 1:
            raise ValueError("seed must fit a signed 32-bit integer")
        return value

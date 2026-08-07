"""Schema for optional upstream artwork analysis."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ArtworkAnalysis(BaseModel):
    orientation: Literal["portrait", "landscape", "square"]
    crop_mode: Literal["preserve", "cover", "contain"] = "preserve"
    recommended_grid: dict[str, int] | None = None
    decorative_border: bool = False
    notes: str | None = Field(default=None, max_length=1000)
    display_name: str | None = Field(default=None, max_length=160)
    artist: str | None = Field(default=None, max_length=160)
    year: str | None = Field(default=None, max_length=80)
    frame_label: str | None = Field(default=None, max_length=240)

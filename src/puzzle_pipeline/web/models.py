"""Typed contracts shared by the web API and future MCP adapter."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    orientation: Literal["portrait", "landscape", "square"]
    crop_mode: Literal["preserve", "cover", "contain"]
    board_aspect: float = Field(gt=0)
    columns: int = Field(ge=2, le=12)
    rows: int = Field(ge=2, le=12)
    piece_count: int = Field(ge=4, le=144)
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source: Literal["deterministic", "llm", "fallback"]
    display_name: str = Field(default="Untitled Artwork", max_length=160)
    artist: str = Field(default="Unknown", max_length=160)
    year: str = Field(default="unknown", max_length=80)
    frame_label: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=1000)


class JobRecord(BaseModel):
    id: str
    status: Literal[
        "uploaded",
        "recommendation_ready",
        "generating",
        "validating",
        "ready",
        "failed",
    ]
    image_name: str
    recommendation: Recommendation
    package_dir: str | None = None
    download_name: str | None = None
    preview_url: str | None = None
    error: str | None = None

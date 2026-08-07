"""Deterministic layout recommendations with an optional advisory provider."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol

from PIL import Image

from puzzle_pipeline.ai.schema import ArtworkAnalysis

from .models import Recommendation


class ArtworkAdvisor(Protocol):
    def analyze(self, image: Path) -> ArtworkAnalysis:
        """Analyze artwork without mutating the puzzle generator."""


def _source_name(image: Path) -> str:
    stem = image.stem
    prefix, separator, original = stem.partition("_")
    if separator and len(prefix) == 32 and all(character in "0123456789abcdef" for character in prefix.lower()):
        return original
    return stem


def _meaningful(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip().casefold() not in {"null", "none", "unknown", "untitled"})


def _filename_metadata(name: str) -> tuple[str, str, str]:
    lowered = name.casefold()
    if ("супремат" in lowered and "квадрат" in lowered) or "black square" in lowered:
        return "Black Square", "Kazimir Malevich", "1915"
    return name.replace("_", " ").title(), "Unknown", "unknown"


def _orientation(width: int, height: int) -> str:
    if abs(width - height) / max(width, height) <= 0.03:
        return "square"
    return "landscape" if width > height else "portrait"


def _default_grid(orientation: str) -> tuple[int, int]:
    return {"square": (3, 3), "portrait": (3, 4), "landscape": (4, 3)}[orientation]


def _bounded_grid(value: dict[str, int] | None, fallback: tuple[int, int]) -> tuple[int, int]:
    if not value:
        return fallback
    columns = min(12, max(2, int(value.get("columns", fallback[0]))))
    rows = min(12, max(2, int(value.get("rows", fallback[1]))))
    return columns, rows


def recommend_image(image: Path, advisor: ArtworkAdvisor | None = None) -> Recommendation:
    """Return a safe recommendation; AI provider errors never block generation."""
    with Image.open(image) as source:
        width, height = source.size
    orientation = _orientation(width, height)
    default_columns, default_rows = _default_grid(orientation)
    source_kind = "deterministic"
    crop_mode: Literal["preserve", "cover", "contain"] = "preserve"
    reasons = [f"Source image is {width}x{height} and is {orientation}-oriented."]
    warnings: list[str] = []
    filename_name = _source_name(image)
    display_name, artist, year = _filename_metadata(filename_name)
    frame_label: str | None = None
    notes: str | None = None
    if min(width, height) < 300:
        warnings.append("Source image is small; use fewer pieces or a larger artwork image.")
    columns, rows = default_columns, default_rows

    if advisor is not None:
        try:
            analysis = advisor.analyze(image)
            columns, rows = _bounded_grid(analysis.recommended_grid, (default_columns, default_rows))
            crop_mode = analysis.crop_mode
            source_kind = "llm"
            if analysis.notes:
                reasons.append(analysis.notes)
                notes = analysis.notes
            if _meaningful(analysis.display_name):
                display_name = analysis.display_name or display_name
            if _meaningful(analysis.artist):
                artist = analysis.artist or artist
            if _meaningful(analysis.year):
                year = analysis.year or year
            if _meaningful(analysis.frame_label):
                frame_label = analysis.frame_label
        except Exception:
            source_kind = "fallback"
            warnings.append("AI analysis unavailable; deterministic recommendation used.")

    if frame_label is None:
        frame_label = display_name if artist == "Unknown" else f"{display_name} — {artist}"

    board_aspect = {"square": 1.0, "portrait": 3 / 4, "landscape": 4 / 3}[orientation]
    return Recommendation(
        orientation=orientation,  # type: ignore[arg-type]
        crop_mode=crop_mode,
        board_aspect=board_aspect,
        columns=columns,
        rows=rows,
        piece_count=columns * rows,
        confidence=0.86 if source_kind == "llm" else 0.9,
        reasons=reasons,
        warnings=warnings,
        source=source_kind,  # type: ignore[arg-type]
        display_name=display_name,
        artist=artist,
        year=year,
        frame_label=frame_label,
        notes=notes,
    )

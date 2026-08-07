"""Shared typed geometry data structures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

Point2 = tuple[float, float]


class Side(StrEnum):
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"


class EdgeKind(StrEnum):
    FLAT = "flat"
    TAB = "tab"
    HOLE = "hole"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    metrics: tuple[tuple[str, float], ...] = ()

    @classmethod
    def pass_(cls, **metrics: float) -> ValidationResult:
        return cls(True, (), tuple(metrics.items()))

    @classmethod
    def fail(cls, *errors: str, **metrics: float) -> ValidationResult:
        return cls(False, tuple(errors), tuple(metrics.items()))

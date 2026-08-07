"""Aspect-ratio helpers for artwork diagnostics."""

from __future__ import annotations


def aspect_ratio(size: tuple[int, int]) -> float:
    if size[1] <= 0:
        raise ValueError("image height must be positive")
    return size[0] / size[1]

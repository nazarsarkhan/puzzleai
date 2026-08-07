"""Smooth deterministic jigsaw connector curves."""

from __future__ import annotations


def smoothstep(value: float) -> float:
    clamped = max(0.0, min(1.0, value))
    return clamped * clamped * (3.0 - 2.0 * clamped)


def connector_offset(
    t: float,
    center: float,
    half_width: float,
    depth: float,
    neck_ratio: float = 0.42,
) -> float:
    """Return an outward offset with a rounded head and narrowed shoulders."""
    distance = abs(t - center)
    if distance >= half_width:
        return 0.0
    normalized = distance / half_width
    if normalized <= neck_ratio:
        head_progress = normalized / neck_ratio
        return depth * (0.72 + 0.28 * (1.0 - smoothstep(head_progress)))
    shoulder_progress = (normalized - neck_ratio) / (1.0 - neck_ratio)
    return depth * 0.72 * (1.0 - smoothstep(shoulder_progress))


def curve_samples(
    center: float,
    half_width: float,
    depth: float,
    resolution: int,
) -> tuple[tuple[float, float], ...]:
    """Return `(t, offset)` pairs for the connector profile."""
    count = max(4, resolution)
    start = max(0.0, center - half_width)
    end = min(1.0, center + half_width)
    points = [(0.0, 0.0)]
    for index in range(count + 1):
        t = start + (end - start) * index / count
        points.append((t, connector_offset(t, center, half_width, depth)))
    points.append((1.0, 0.0))
    return tuple(points)

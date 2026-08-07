"""Owned deterministic random streams."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class SeededRng:
    """A reproducible RNG that never mutates Python's global random state."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._random = random.Random(seed)

    def uniform(self, lower: float, upper: float) -> float:
        return self._random.uniform(lower, upper)

    def choice(self, values: Sequence[T]) -> T:
        if not values:
            raise ValueError("cannot choose from an empty sequence")
        return values[self._random.randrange(len(values))]

    def fork(self, label: str) -> SeededRng:
        digest = hashlib.sha256(f"{self.seed}:{label}".encode()).digest()
        return SeededRng(int.from_bytes(digest[:8], "big", signed=False))

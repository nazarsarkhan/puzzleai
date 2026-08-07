"""Local protocol for optional artwork analysis providers."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .schema import ArtworkAnalysis


class ArtworkAnalyzer(Protocol):
    def analyze(self, image: Path) -> ArtworkAnalysis:
        """Return analysis without mutating the deterministic pipeline."""

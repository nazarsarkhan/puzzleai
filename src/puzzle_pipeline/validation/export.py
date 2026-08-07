"""Read and validate Blender export reports."""

from __future__ import annotations

import json
from pathlib import Path

from puzzle_pipeline.core.types import ValidationResult


def validate_export_report(path: Path) -> ValidationResult:
    if not path.is_file():
        return ValidationResult.fail(f"export re-import report not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("valid"):
        return ValidationResult.fail(f"export re-import validation failed: {path}")
    return ValidationResult.pass_(object_count=float(data.get("object_count", 0)))

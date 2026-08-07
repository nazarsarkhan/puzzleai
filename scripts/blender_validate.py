"""Validate an exported FBX in a clean Blender scene."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from puzzle_pipeline.blender.export import validate_reimport


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fbx", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = validate_reimport(args.fbx)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()

"""Validate an exported FBX in a clean Blender scene."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> None:
    from puzzle_pipeline.blender.export import validate_reimport

    parser = argparse.ArgumentParser()
    parser.add_argument("fbx", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    blender_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(blender_args)
    result = validate_reimport(args.fbx)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()

"""Headless Blender entry point for puzzle scene creation and export."""

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
    from puzzle_pipeline.blender.export import export_models, validate_reimport
    from puzzle_pipeline.blender.scene import build_scene

    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--formats", default="fbx")
    blender_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(blender_args)
    data = json.loads(args.scene_input.read_text(encoding="utf-8"))
    blend_path = args.output / "blender" / f"{data.get('puzzle_id', 'puzzle')}.blend"
    build_scene(args.scene_input, blend_path)
    exports = export_models(args.output / "models", tuple(args.formats.split(",")))
    reimport = validate_reimport(Path(exports["fbx"])) if "fbx" in exports else {"valid": True}
    (args.output / "reports").mkdir(parents=True, exist_ok=True)
    (args.output / "reports" / "fbx-reimport-report.json").write_text(
        json.dumps(reimport, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"blend": str(blend_path), "exports": exports, "reimport": reimport}, sort_keys=True))


if __name__ == "__main__":
    main()

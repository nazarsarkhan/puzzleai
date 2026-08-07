"""Public command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from puzzle_pipeline.blender.bootstrap import run_blender_generation
from puzzle_pipeline.config.loader import load_config
from puzzle_pipeline.config.models import PuzzleConfig
from puzzle_pipeline.pipeline import run_core_pipeline
from puzzle_pipeline.reference import inspect_reference
from puzzle_pipeline.roblox import batch_images


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="puzzle", description="Compile deterministic Roblox puzzle assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reference = subparsers.add_parser("inspect-reference", help="inspect a puzzle reference ZIP")
    reference.add_argument("archive", type=Path)

    generate = subparsers.add_parser("generate", help="generate a puzzle package")
    generate.add_argument("image_pos", nargs="?", type=Path)
    generate.add_argument("--image", dest="image_opt", type=Path)
    generate.add_argument("--config", type=Path)
    generate.add_argument("--id", dest="puzzle_id")
    generate.add_argument("--grid")
    generate.add_argument("--seed", type=int)
    generate.add_argument("--output", type=Path, default=Path("dist"))
    generate.add_argument("--formats", default="fbx")
    generate.add_argument("--skip-blender", action="store_true")
    generate.add_argument("--debug", action="store_true")

    validate = subparsers.add_parser("validate", help="validate a generated package")
    validate.add_argument("package", type=Path)

    inspect = subparsers.add_parser("inspect", help="inspect a generated package")
    inspect.add_argument("package", type=Path)

    batch = subparsers.add_parser("batch", help="batch artworks into Roblox import packages")
    batch.add_argument("--input", type=Path, required=True)
    batch.add_argument("--output", type=Path, default=Path("assets/puzzles"))
    batch.add_argument("--start-number", type=int, default=7)
    batch.add_argument("--atlas-size", type=int, default=2048)
    batch.add_argument("--skip-blender", action="store_true")
    return parser


def _generate(args: argparse.Namespace) -> int:
    image = args.image_opt or args.image_pos
    if image is None:
        raise ValueError("generate requires --image IMAGE or a positional image path")
    if args.config is not None:
        config = load_config(args.config, {"puzzle_id": args.puzzle_id, "grid": args.grid, "seed": args.seed})
    else:
        if not args.puzzle_id:
            raise ValueError("generate without --config requires --id")
        data: dict[str, object] = {"puzzle_id": args.puzzle_id}
        if args.grid:
            columns, rows = args.grid.lower().split("x", 1)
            data["grid"] = {"columns": int(columns), "rows": int(rows)}
        if args.seed is not None:
            data["seed"] = args.seed
        config = PuzzleConfig.model_validate(data)
    print("[1/9] Loading artwork")
    print("[2/9] Generating deterministic seams and outlines")
    result = run_core_pipeline(config, image, args.output)
    print("[3/9] Building meshes")
    print("[4/9] Creating atlas and UVs")
    print("[5/9] Running core validation")
    if not args.skip_blender:
        print("[6/9] Building Blender scene")
        blender = run_blender_generation(
            result.package_dir / "blender" / "scene-input.json",
            result.package_dir,
            tuple(args.formats.split(",")),
        )
        print(f"Blender: {blender.status} — {blender.message}")
    else:
        print("[6/9] Blender skipped")
    print("[7/9] Export stage complete")
    print("[8/9] Re-import stage complete")
    print("[9/9] Writing manifest")
    print(f"{'PASS' if result.validation.status == 'passed' else 'FAIL'} puzzle {config.puzzle_id}")
    print(f"Pieces: {len(result.meshes)}")
    print(f"Triangles: {sum(mesh.triangle_count for mesh in result.meshes)}")
    if result.validation.errors:
        for error in result.validation.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.validation.status == "passed" else 1


def _validate(package: Path) -> int:
    report_path = package / "manifests" / "validation.json"
    if not report_path.is_file():
        print(f"Validation report not found: {report_path}", file=sys.stderr)
        return 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    status = report.get("status")
    print(f"{status.upper()} {package}")
    for error in report.get("errors", []):
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if status == "passed" else 1


def _inspect(package: Path) -> int:
    manifest_path = package / "manifests" / "puzzle.json"
    if not manifest_path.is_file():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(json.dumps({key: manifest[key] for key in ("puzzle_id", "seed", "grid", "board", "pieces")}, indent=2))
    return 0


def _batch(args: argparse.Namespace) -> int:
    results = batch_images(
        args.input,
        args.output,
        start_number=args.start_number,
        atlas_size=args.atlas_size,
        skip_blender=args.skip_blender,
    )
    for result in results:
        suffix = "" if result.export_status == "passed" else " (FBX unavailable)"
        print(f"PASS {result.package_dir.name}{suffix}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect-reference":
            print(json.dumps(inspect_reference(args.archive), indent=2, sort_keys=True))
            return 0
        if args.command == "generate":
            return _generate(args)
        if args.command == "validate":
            return _validate(args.package)
        if args.command == "batch":
            return _batch(args)
        return _inspect(args.package)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

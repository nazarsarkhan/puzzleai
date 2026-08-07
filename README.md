# Roblox puzzle asset pipeline

This repository is a deterministic asset compiler for physical jigsaw-puzzle
artwork in Roblox. The core geometry is pure Python: a seed creates one shared
seam graph, the graph creates all piece outlines, and the same solved coordinates
drive extrusion, UVs, the atlas, and the Roblox manifest.

## Requirements

- Python 3.12 or newer
- Pillow and Pydantic (installed by the package)
- Blender 3.6 LTS or newer for `.blend`, FBX, and optional GLB export
- Blender must be available on `PATH` as `blender`/`blender.exe`, or invoked with
  `--skip-blender` when only the core package is needed

## Installation

```bash
python -m pip install -e ".[dev]"
```

## Generate a puzzle

With a JSON config:

```bash
python -m puzzle_pipeline generate \
  --image ./artworks/starry_night.png \
  --config ./configs/examples/3x2.json \
  --output ./dist
```

For a config-free run:

```bash
puzzle generate ./artworks/starry_night.png \
  --id starry_night \
  --grid 4x3 \
  --seed 42 \
  --skip-blender
```

Use `--skip-blender` only when Blender is not installed. A normal production run
invokes Blender headlessly and writes the `.blend`, FBX, optional GLB, and clean
scene re-import report.

## Validate and inspect

```bash
puzzle validate ./dist/starry_night
puzzle inspect ./dist/starry_night
puzzle inspect-reference ./puzzle_019.zip
```

## Tests and quality checks

```bash
python -m pytest -q
ruff check .
mypy src
```

Blender tests are marked separately:

```bash
python -m pytest -m blender -q
```

## Output format

Each package is written to `dist/<puzzle_id>/`:

```text
source/       copied artwork
textures/     <id>_atlas.png
models/       FBX/GLB when Blender is available
blender/      scene-input.json and <id>.blend
manifests/    puzzle.json and validation.json
reports/      generation-report.json and export reports
debug/        seam-map.json and optional debug drawings
```

## Architecture

```text
artwork + config
      → deterministic core geometry
      → UV projection + atlas
      → core validation + manifest
      → optional Blender scene/export adapter
      → export/re-import validation
```

See [architecture](docs/architecture.md), [geometry](docs/puzzle-geometry.md),
[UV and atlas](docs/uv-and-atlas.md), [Roblox import](docs/roblox-import.md), and
the [puzzle_019 reference analysis](docs/reference-puzzle-019.md).

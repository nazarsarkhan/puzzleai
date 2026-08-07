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

To run the browser interface, install the web extras:

```bash
python -m pip install -e ".[dev,web]"
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

To batch the supplied artwork directory into the Roblox repository contract:

```bash
puzzle batch --input ./images --output ./assets/puzzles
```

The initial image mapping is stable: Black Square → `puzzle_007`, Mona Lisa →
`puzzle_008`, graffiti portrait → `puzzle_009`, and mountain landscape →
`puzzle_010`. Unknown attribution is recorded as `Unknown`.

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

## Browser interface

Start the local web application:

```bash
puzzle-web
```

Open `http://127.0.0.1:8000`, upload an artwork image, review the recommended
orientation and grid, then generate and download the Roblox ZIP package. The
application works without an AI key using deterministic image-dimension rules.

To enable optional artwork-aware recommendations and richer
`roblox-overrides.json` metadata, edit the local `.env` file:

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY=your-key
puzzle-web
```

The web layer uses `gpt-4o-mini` for typed artwork recommendations and metadata
such as `displayName`, `artist`, `year`, `frameLabel`, and curator `notes`. The
deterministic generator remains responsible for geometry, UVs, FBX export, and
validation. `.env` is ignored by Git; never commit the key. Set `PUZZLE_WEB_DATA`
to choose the local job/artifact directory; the default is `.web-data`.

The API boundary is independent of the browser so a future MCP server can call
the same analyze, generate, status, preview, and download operations before
adding a local Roblox Studio import bridge.

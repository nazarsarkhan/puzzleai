# Roblox import package design

## Goal

Turn a directory of artwork images into numbered Roblox puzzle packages that match
the existing import contract, while keeping deterministic geometry and artwork
generation in the existing core pipeline.

## Input mapping

The initial batch uses stable sorted filename order:

| ID | Source | Metadata policy |
|---|---|---|
| puzzle_007 | Black Suprematist Square PNG | Black Square; Kazimir Malevich; 1915; square; 3×3 |
| puzzle_008 | `download.jpg` | Mona Lisa; Leonardo da Vinci; 1503–1519; portrait; 3×4 |
| puzzle_009 | `99a5fec23b9b29718b492326a88b454d.jpg` | Graffiti Portrait; Unknown; unknown; portrait; 3×4 |
| puzzle_010 | `2892.1800x1800.jpg` | Mountain Landscape; Unknown; unknown; portrait; 3×4 |

Unknown attribution is explicit in `roblox-overrides.json`; it is never inferred
from an image filename or visual similarity.

## Output contract

Each package is written directly under the configured Roblox root:

```text
assets/puzzles/puzzle_NNN/
├── manifest.json
├── manifest.validation.json
├── puzzle_NNN.fbx                 # only when Blender export succeeds
├── puzzle_NNN_atlas.png
├── puzzle_NNN_completion.png
├── fbx_export_report.json
├── fbx_reimport_report.json
└── roblox-overrides.json
```

The existing core package remains available for debugging and intermediate files;
the Roblox packager copies only the contract files above. `completion.png` is a
pixel-faithful copy of the processed artwork. Export reports always exist and
contain `status: unavailable` plus an actionable Blender message when Blender is
missing. No fake FBX is created.

## Manual Roblox import documentation

Generated FBX files are staged manually under:

```text
Workspace.ImportStaging/Puzzle_NNN_Raw
```

The package manifest and overrides remain the source of truth for display metadata,
grid dimensions, piece IDs, and solved transforms.

## Verification

Tests cover input ordering, orientation, metadata serialization, exact filenames,
completion-image byte identity, package validation, and missing-Blender reports.
The batch command is verified against all four supplied images.

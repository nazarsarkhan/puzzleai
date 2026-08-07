# Reference analysis: `puzzle_019`

This document records facts read from `puzzle_019.zip`. It intentionally separates
what the fixture proves from choices made for the generalized pipeline.

## Observed behavior

- The archive contains a generated 3×2 puzzle with six mesh pieces.
- The reference configuration uses seed `119`, logical cell dimensions `1.6 ×
  1.6125752508361202`, total assembled bounds `4.8 × 3.225150502 × 0.07`, and
  bevel depth `0.012` with two segments.
- The front axis is `+Z`; the planar axes are `+X` and `+Y`.
- Piece origins use the `logicalCellCenter` policy. Objects have zero rotation and
  unit scale before FBX conversion.
- Piece names are stable machine-readable names: `p019_piece_001` through
  `p019_piece_006`.
- The exported scene uses one shared material named `PuzzleAtlas` and one atlas
  image named `puzzle_019_atlas.png`.
- The atlas is 2048×2048. Its artwork rectangle is `[132, 1022, 1527, 1026]`;
  white back pixels occupy `[0, 0, 896, 256]`, and cardboard side pixels occupy
  `[896, 0, 896, 256]`.
- The manifest reports six pieces, seven unique internal seams, flat external
  edges, and complementary `Tab`/`Hole` connectors.
- The generated validation reports a maximum internal seam mismatch of about
  `8.86e-08`, a maximum front UV mismatch of about `3.97e-08`, positive signed
  volume, manifold pieces, and a total of 1024 triangles.
- FBX export embeds the atlas texture and the clean-scene re-import report checks
  names, dimensions, origins, rotations, scales, triangles, materials, UVs, and
  the embedded PNG payload.
- No GLB file is present in the archive. The archive contains `.blend`, `.blend1`,
  FBX, PNG, JSON manifests, and reports.

## Assumptions / design decisions

- The generalized generator keeps `+Z` as the front axis and uses `+X` right,
  `+Y` up, which matches the reference and makes UV projection direct.
- The core uses a shared seam graph as the source of truth; adjacent pieces never
  independently sample their common boundary.
- The generalized default origin is the logical cell center, while the manifest
  also records the visual bounds so Roblox code can reason about tabs extending
  outside a nominal cell.
- The MVP keeps FBX first-class and makes GLB optional. Blender-specific output is
  skipped with an actionable report when no Blender executable is installed.
- Golden tests compare structural invariants and numeric tolerances rather than
  binary files, because Blender and FBX serialization are not byte-stable.

## Inspection limitation

Blender was not installed in the execution environment, so the `.blend` database
was not opened with Blender Python. Scene-level facts above come from the supplied
manifests and export/re-import reports. When Blender is available, the inspector
and integration suite can add direct datablock checks.

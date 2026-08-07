# Architecture

The project is split into a deterministic compiler core and an optional Blender
adapter.

## Core

`config` validates versioned input. `core.geometry` creates shared seeded seams,
outlines, triangulated solids, transforms, and mesh metrics. `artwork` loads and
fits the source image and writes one deterministic atlas. `uv` projects solved
board coordinates into the atlas. `validation` proves topology, outlines, mesh
manifoldness, triangle budgets, and UV bounds. `manifests` serializes the
machine-readable Roblox contract.

The core never imports Blender and can run in CI, batch jobs, or a future geometry
cache. Geometry and artwork are separate inputs, so one seam template can be
reused with many paintings.

## Blender adapter

`blender/bootstrap.py` locates Blender and invokes it with `--background`. The
serializable `blender/scene-input.json` is the boundary between the two layers.
The Blender script resets the scene, creates predictable piece names and one
`PuzzleAtlas` material, assigns loop UVs, writes `.blend`, exports FBX/GLB, and
re-imports FBX into a clean scene for validation.

When Blender is missing, the core still produces a valid non-Blender package and
the adapter returns an explicit `unavailable` status.

## Determinism

Randomness is owned by `SeededRng`. Each seam orientation uses a labeled fork, so
global Python random state cannot affect output. Stable JSON writers sort keys and
golden tests compare structural invariants rather than Blender byte streams.

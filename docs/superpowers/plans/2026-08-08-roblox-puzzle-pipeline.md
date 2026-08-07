# Roblox Puzzle Asset Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic Python asset compiler that converts artwork and typed puzzle configuration into validated Roblox-ready puzzle geometry, atlas textures, manifests, debug artifacts, and optional Blender/FBX exports.

**Architecture:** The pure-Python core owns configuration, seeded shared seam topology, outlines, triangulated solids, UVs, atlas generation, manifests, and validators. A subprocess-isolated Blender adapter consumes a serializable intermediate scene description and is optional when Blender is unavailable. The CLI orchestrates stages and writes a stable `dist/<puzzle_id>` package.

**Tech Stack:** Python 3.12+, Pydantic v2, Pillow, pytest, Ruff, mypy, setuptools package entry point, optional Blender Python API, GitHub Actions.

## Global Constraints

- Geometry is deterministic, mathematical, seed-based, and independent of any LLM or external AI API.
- Shared seams are generated once and referenced by adjacent pieces with complementary polarity.
- Front UVs are projected from solved board coordinates and must be continuous across shared seams.
- One shared atlas material is used whenever Blender is available.
- Blender is optional for core tests; Blender-dependent tests are marked `blender` and fail actionably when the executable is missing.
- Reference comparisons use structural invariants, never byte-identical FBX/Blend output.
- No generated output contains nondeterministic timestamps unless explicitly placed in a non-golden report field.
- Every new behavior is introduced with a failing pytest test before production code.

---

### Task 1: Repository foundation and developer tooling

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `Makefile`
- Create: `.github/workflows/ci.yml`
- Create: `src/puzzle_pipeline/__init__.py`
- Create: `tests/conftest.py`
- Test: `tests/unit/test_package_smoke.py`

**Interfaces:**
- Produces an installable package named `puzzle-pipeline` with module entry point `python -m puzzle_pipeline` and console command `puzzle`.
- Provides `puzzle_pipeline.__version__` as a string.

- [ ] **Step 1: Write the failing package smoke test** asserting the version exists and is a semantic version string.
- [ ] **Step 2: Run `rtk python -m pytest tests/unit/test_package_smoke.py -q` and verify it fails because the package is absent.**
- [ ] **Step 3: Add packaging metadata, source package, test configuration, lint/typecheck settings, CI, and standard ignore/editor files.**
- [ ] **Step 4: Run `rtk python -m pytest tests/unit/test_package_smoke.py -q`, `rtk ruff check .`, and `rtk mypy src`; verify all pass.**
- [ ] **Step 5: Initialize Git if needed, review `git diff --check`, and commit `chore: establish puzzle pipeline foundation`.**

### Task 2: Reference inspection and documentation contract

**Files:**
- Create: `scripts/inspect_reference.py`
- Create: `docs/reference-puzzle-019.md`
- Create: `tests/golden/test_reference_contract.py`
- Create: `tests/fixtures/reference/puzzle_019_contract.json`

**Interfaces:**
- `inspect_reference(path: Path) -> dict[str, object]` reads the ZIP without requiring Blender and reports files, JSON metadata, images, and structural invariants.
- `puzzle inspect-reference <zip>` prints a readable summary and optionally writes JSON.

- [ ] **Step 1: Write failing tests for the observed 3×2 grid, seed 119, 6 pieces, 2048 atlas, 0.07 thickness, one shared material, +Z front axis, and reference package filenames.**
- [ ] **Step 2: Run the targeted golden test and verify it fails because the inspector and fixture are missing.**
- [ ] **Step 3: Implement the ZIP inspector and fixture extraction/contract loader; record Blender as unavailable in the report when no executable is found.**
- [ ] **Step 4: Write `docs/reference-puzzle-019.md` with explicit `Observed behavior` and `Assumptions / design decisions` sections, including the reference’s logical-cell-center pivot policy, atlas regions, naming, triangle metrics, and FBX re-import properties.**
- [ ] **Step 5: Run the golden contract test and commit `docs: document puzzle 019 reference contract`.**

### Task 3: Typed configuration, coordinates, and deterministic RNG

**Files:**
- Create: `src/puzzle_pipeline/config/models.py`
- Create: `src/puzzle_pipeline/config/defaults.py`
- Create: `src/puzzle_pipeline/config/loader.py`
- Create: `src/puzzle_pipeline/core/random.py`
- Create: `src/puzzle_pipeline/core/coordinates.py`
- Test: `tests/unit/test_config.py`
- Test: `tests/unit/test_coordinates.py`
- Test: `tests/unit/test_random.py`

**Interfaces:**
- `PuzzleConfig`, `GridConfig`, `BoardConfig`, `PieceConfig`, `SeamConfig`, `AtlasConfig`, and `ExportConfig` are Pydantic models.
- `load_config(path: Path, overrides: Mapping[str, object] | None = None) -> PuzzleConfig` validates JSON and applies explicit CLI overrides.
- `SeededRng(seed: int)` exposes deterministic `uniform`, `choice`, and `fork(label)` methods without touching global random state.
- `board_coordinates(config: PuzzleConfig) -> BoardCoordinates` exposes board bounds, cell centers, and `world_to_front_uv(x, y)`.

- [ ] **Step 1: Write failing tests for valid defaults, rejected grids/ranges, deterministic config loading, coordinate projection, and distinct fork streams.**
- [ ] **Step 2: Run the targeted tests and confirm feature-missing failures.**
- [ ] **Step 3: Implement Pydantic models with documented defaults and ranges, JSON loading, explicit override parsing for `--grid` and `--seed`, and coordinate math matching the reference +X/+Y/+Z convention.**
- [ ] **Step 4: Run targeted tests, then `rtk ruff check .` and `rtk mypy src`.**
- [ ] **Step 5: Commit `feat: add typed puzzle configuration and deterministic coordinates`.**

### Task 4: Shared seam topology and parametric outlines

**Files:**
- Create: `src/puzzle_pipeline/core/types.py`
- Create: `src/puzzle_pipeline/core/geometry/curves.py`
- Create: `src/puzzle_pipeline/core/geometry/seams.py`
- Create: `src/puzzle_pipeline/core/geometry/outlines.py`
- Create: `src/puzzle_pipeline/core/puzzle.py`
- Create: `src/puzzle_pipeline/validation/seams.py`
- Create: `src/puzzle_pipeline/validation/geometry.py`
- Create: `scripts/render_outlines.py`
- Test: `tests/unit/test_seams.py`
- Test: `tests/unit/test_outlines.py`
- Test: `tests/unit/test_puzzle_topology.py`

**Interfaces:**
- `SeamGraph.generate(grid: GridConfig, seams: SeamConfig, rng: SeededRng) -> SeamGraph` creates every internal seam exactly once.
- `Seam.edge_points(side: Side, polarity: int, cell_width: float, cell_height: float) -> tuple[Point2, ...]` returns complementary sampled points.
- `generate_puzzle_geometry(config: PuzzleConfig) -> PuzzleGeometry` returns seam graph, piece outlines, piece metadata, and solved transforms.
- `validate_topology(geometry: PuzzleGeometry) -> ValidationResult` and `validate_outlines(geometry: PuzzleGeometry) -> ValidationResult` provide structured errors and metrics.

- [ ] **Step 1: Write failing tests asserting shared seam identity, TAB/HOLE complementarity, flat borders, deterministic same-seed output, changed-seed variation, closed outlines, and no self-intersections.**
- [ ] **Step 2: Run tests and verify failures before implementation.**
- [ ] **Step 3: Implement cubic/parametric classic jigsaw seams with bounded jitter, canonical seam orientation, reverse traversal for opposing pieces, and outline assembly from four edges.**
- [ ] **Step 4: Implement topology and outline validators with piece/seam-specific actionable messages.**
- [ ] **Step 5: Add deterministic SVG outline rendering and run the full core geometry test set.**
- [ ] **Step 6: Commit `feat: generate deterministic shared puzzle seams and outlines`.**

### Task 5: Triangulated watertight mesh core

**Files:**
- Create: `src/puzzle_pipeline/core/geometry/triangulation.py`
- Create: `src/puzzle_pipeline/core/geometry/mesh.py`
- Create: `src/puzzle_pipeline/validation/transforms.py`
- Test: `tests/unit/test_mesh.py`
- Test: `tests/unit/test_triangulation.py`

**Interfaces:**
- `triangulate_polygon(outline: Sequence[Point2]) -> tuple[Triangle2, ...]` uses deterministic ear clipping and rejects degenerate/self-intersecting input.
- `extrude_piece(piece: PieceOutline, board: BoardConfig, atlas: AtlasLayout) -> MeshData` produces front, back, side faces, positions, normals, UVs, material slot, and triangle metrics.
- `validate_mesh(mesh: MeshData, budget: tuple[int, int]) -> ValidationResult` checks finite coordinates, nonzero area, winding, degeneracy, manifold edge counts, volume sign, and triangle budget.

- [ ] **Step 1: Write failing tests for simple polygon triangulation, concave jigsaw outlines, watertight extrusion, positive volume, consistent front/back normals, thickness, and triangle limits.**
- [ ] **Step 2: Run the targeted tests and verify expected failures.**
- [ ] **Step 3: Implement deterministic triangulation, indexed extrusion, side winding, optional lightweight bevel treatment without Blender booleans, and logical-cell-center transforms.**
- [ ] **Step 4: Run mesh and geometry tests, inspect triangle counts against the reference budget, and commit `feat: add deterministic puzzle mesh generation`.**

### Task 6: Artwork preprocessing, UV mapping, and atlas generation

**Files:**
- Create: `src/puzzle_pipeline/artwork/loader.py`
- Create: `src/puzzle_pipeline/artwork/preprocess.py`
- Create: `src/puzzle_pipeline/artwork/crop.py`
- Create: `src/puzzle_pipeline/artwork/atlas.py`
- Create: `src/puzzle_pipeline/uv/front.py`
- Create: `src/puzzle_pipeline/uv/back.py`
- Create: `src/puzzle_pipeline/uv/sides.py`
- Create: `src/puzzle_pipeline/validation/uv.py`
- Test: `tests/unit/test_artwork.py`
- Test: `tests/unit/test_atlas.py`
- Test: `tests/unit/test_uv.py`

**Interfaces:**
- `load_artwork(path: Path) -> ArtworkImage` validates image readability, dimensions, mode, and aspect ratio.
- `build_atlas(artwork: ArtworkImage, config: AtlasConfig, board: BoardCoordinates) -> AtlasArtifact` writes atlas PNG and JSON layout metadata.
- `front_uv_for_point(point: Point2, board: BoardCoordinates, atlas: AtlasLayout) -> UV` projects +X/+Y into the artwork rectangle.
- `validate_uv(geometry: PuzzleGeometry, atlas: AtlasLayout) -> ValidationResult` checks bounds, front-region membership, and shared-edge continuity.

- [ ] **Step 1: Write failing tests for missing/corrupt image errors, portrait/landscape/square aspect handling, deterministic atlas layout, exact coordinate projection, back/cardboard regions, and UV seam continuity.**
- [ ] **Step 2: Run targeted tests and confirm failures.**
- [ ] **Step 3: Implement Pillow loading/preprocess fit modes, deterministic atlas regions with padding/dilation, front/back/side UV functions, and structured errors.**
- [ ] **Step 4: Run targeted tests plus image round-trip checks and commit `feat: add artwork atlas and projected puzzle UVs`.**

### Task 7: Manifests, reports, and package layout

**Files:**
- Create: `src/puzzle_pipeline/manifests/models.py`
- Create: `src/puzzle_pipeline/manifests/writer.py`
- Create: `src/puzzle_pipeline/validation/report.py`
- Create: `src/puzzle_pipeline/pipeline.py`
- Test: `tests/unit/test_manifest.py`
- Test: `tests/integration/test_pipeline_core.py`

**Interfaces:**
- `build_manifest(config, geometry, atlas, exports) -> PuzzleManifest` returns stable schema-versioned metadata with neighbors, seam IDs, solved transforms, and paths.
- `write_package(result: GenerationResult, output_root: Path) -> Path` creates `source/`, `textures/`, `models/`, `blender/`, `manifests/`, `reports/`, and `debug/` as needed.
- `run_core_pipeline(config: PuzzleConfig, image: Path, output: Path) -> GenerationResult` runs artwork, geometry, mesh, atlas, UV, and core validation without Blender.

- [ ] **Step 1: Write failing tests for manifest serialization, stable ordering, neighbor references, omission of timestamps from golden fields, and 2×2/3×2 core package generation.**
- [ ] **Step 2: Run tests and verify missing implementation failures.**
- [ ] **Step 3: Implement models, deterministic JSON writers, stage timing, validation report schema, and core package layout.**
- [ ] **Step 4: Run integration tests across 2×2, 3×2, portrait, landscape, square, and multiple seeds; commit `feat: package validated puzzle manifests and reports`.**

### Task 8: Blender headless adapter and export/re-import validation

**Files:**
- Create: `src/puzzle_pipeline/blender/bootstrap.py`
- Create: `src/puzzle_pipeline/blender/scene.py`
- Create: `src/puzzle_pipeline/blender/mesh.py`
- Create: `src/puzzle_pipeline/blender/materials.py`
- Create: `src/puzzle_pipeline/blender/export.py`
- Create: `src/puzzle_pipeline/validation/export.py`
- Create: `scripts/blender_generate.py`
- Create: `scripts/blender_validate.py`
- Test: `tests/blender/test_blender_integration.py`

**Interfaces:**
- `find_blender(executable: str | None = None) -> Path | None` searches explicit path and platform PATH.
- `run_blender_generation(scene_path: Path, output_dir: Path, formats: Sequence[str]) -> BlenderResult` invokes Blender with `--background --python` and reports stdout/stderr on failure.
- `build_scene(scene_input: SceneInput) -> None` creates named collections, piece meshes, one shared atlas material, transforms, and a saved `.blend`.
- `export_and_reimport(blend_path: Path, output_dir: Path, formats: Sequence[str]) -> ExportValidationResult` exports FBX first, optional GLB, imports FBX into a clean scene, and revalidates names, transforms, dimensions, triangles, materials, UVs, and embedded atlas payload.

- [ ] **Step 1: Write marked tests for missing executable messaging and, when Blender exists, named objects, one shared material, `.blend` save, FBX export, and clean re-import invariants.**
- [ ] **Step 2: Run tests in this environment and verify the missing-executable test fails until the actionable fallback is implemented; record Blender integration as skipped/unavailable, not mocked.**
- [ ] **Step 3: Implement serializable scene input, Blender scene creation, material nodes, mesh/UV assignment, explicit origins/transforms, export settings matching the reference, and re-import validation.**
- [ ] **Step 4: Run all marked tests; if Blender remains unavailable, report the exact blocked command while keeping core tests green.**
- [ ] **Step 5: Commit `feat: add optional headless Blender export adapter`.**

### Task 9: CLI, debug artifacts, and user-facing errors

**Files:**
- Create: `src/puzzle_pipeline/cli/main.py`
- Create: `src/puzzle_pipeline/cli/__init__.py`
- Create: `src/puzzle_pipeline/ai/interface.py`
- Create: `src/puzzle_pipeline/ai/schema.py`
- Test: `tests/integration/test_cli.py`

**Interfaces:**
- Commands: `puzzle inspect-reference`, `puzzle generate`, `puzzle validate`, and `puzzle inspect`.
- `generate --image IMAGE --config CONFIG [--id ID] [--grid CxR] [--seed N] [--output DIR] [--formats ...] [--skip-blender] [--debug]` uses the core pipeline and optional Blender adapter.
- Optional AI interface is a typed local protocol only; no network call is required.

- [ ] **Step 1: Write failing CLI tests for help, generate, validate, inspect, overrides, missing image/config, invalid grid, and `--skip-blender`.**
- [ ] **Step 2: Run targeted CLI tests and verify failures.**
- [ ] **Step 3: Implement thin command handlers, readable nine-stage progress logs, nonzero exit codes, actionable errors, debug seam-map JSON/SVG/atlas preview output, and optional AI schema.**
- [ ] **Step 4: Run CLI integration tests and commit `feat: add puzzle generation and validation CLI`.**

### Task 10: Documentation, CI completion, and golden regression suite

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/puzzle-geometry.md`
- Create: `docs/uv-and-atlas.md`
- Create: `docs/roblox-import.md`
- Modify: `.github/workflows/ci.yml`
- Create: `tests/golden/test_puzzle_019.py`
- Create: `tests/fixtures/artwork.png`

**Interfaces:**
- Documentation includes Python/Blender requirements, installation, exact CLI commands, output layout, architecture, geometry, UV/atlas, Roblox import conventions, and Lua manifest usage example.
- Golden test compares 3×2 topology, piece count, dimensions, thickness, shared seams, material count, atlas dimensions, UV continuity, triangle budget, and manifest structure.

- [ ] **Step 1: Write failing golden tests and documentation link checks for the final workflow.**
- [ ] **Step 2: Run the golden tests and verify failures before wiring the final fixture and docs.**
- [ ] **Step 3: Add a small deterministic fixture artwork, implement structural comparison against `puzzle_019`, and complete README/reference links.**
- [ ] **Step 4: Run the full verification suite: `rtk python -m pytest -q`, `rtk ruff check .`, `rtk mypy src`, and `rtk git diff --check`.**
- [ ] **Step 5: Review the complete diff and commit `feat: complete Roblox puzzle asset pipeline MVP`.**


# Puzzle Web Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser interface that accepts an artwork image, recommends a puzzle layout, generates a validated Roblox package, and exposes a stable API boundary for a future MCP/Roblox Studio bridge.

**Architecture:** FastAPI serves a small static browser client and JSON API. The backend stores uploaded images and job artifacts under a configured data directory, uses deterministic image dimensions and allowed-grid rules as the baseline recommendation, optionally calls `gpt-4o-mini` through a server-side adapter, and delegates generation to the existing pipeline. A job service isolates long-running generation so the later MCP server can call the same operations without depending on the browser.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Pillow, Pydantic, existing puzzle pipeline and optional OpenAI SDK.

## Global Constraints

- The OpenAI key is read only from `OPENAI_API_KEY` and is never sent to the browser.
- The deterministic pipeline remains the source of truth for grids, geometry, UVs, manifests, FBX output, and validation.
- A missing or failing LLM provider must fall back to deterministic recommendations.
- Generated packages must preserve the Roblox package contract already used by `puzzle batch`.
- Uploaded files are copied into an application-owned data directory; client-provided paths are never executed.
- Generation jobs are explicit state machines and return structured failure details.

---

### Task 1: Recommendation service and provider boundary

**Files:**
- Create: `src/puzzle_pipeline/web/recommendations.py`
- Create: `src/puzzle_pipeline/web/models.py`
- Modify: `src/puzzle_pipeline/ai/schema.py`
- Test: `tests/unit/test_web_recommendations.py`

**Interfaces:**
- `recommend_image(image: Path, advisor: ArtworkAdvisor | None = None) -> Recommendation`
- `Recommendation` contains orientation, crop mode, board aspect, columns, rows, piece count, confidence, reasons, and warnings.
- `ArtworkAdvisor.analyze(image: Path) -> ArtworkAnalysis` remains optional and cannot directly create geometry.

- [ ] Write tests for square/portrait/landscape grid recommendations, small-image warnings, and fallback when the advisor raises.
- [ ] Run the focused test file and confirm it fails because the web recommendation module does not exist.
- [ ] Implement dimension-based recommendations and Pydantic validation for advisor output.
- [ ] Run the focused tests and confirm they pass.
- [ ] Refactor only after green; keep the recommendation policy deterministic and bounded.

### Task 2: Optional OpenAI vision advisor

**Files:**
- Create: `src/puzzle_pipeline/web/openai_advisor.py`
- Modify: `src/puzzle_pipeline/ai/schema.py`
- Modify: `pyproject.toml`
- Test: `tests/unit/test_openai_advisor.py`

**Interfaces:**
- `OpenAIArtworkAdvisor(api_key: str, model: str = "gpt-4o-mini")` implements the local advisor protocol.
- The adapter returns only the typed `ArtworkAnalysis` fields and raises a provider-specific error on invalid responses.

- [ ] Write tests using an injected fake client for valid structured output and provider failure.
- [ ] Run the focused tests and confirm they fail before the adapter exists.
- [ ] Implement the adapter with server-side credentials, image input, and strict schema parsing.
- [ ] Run the focused tests and confirm they pass without requiring a real API key.

### Task 3: Job service and Roblox export

**Files:**
- Create: `src/puzzle_pipeline/web/jobs.py`
- Test: `tests/unit/test_web_jobs.py`

**Interfaces:**
- `JobStore` persists `JobRecord` JSON and artifacts beneath one configured data directory.
- `GenerationJobService.create(image, recommendation) -> JobRecord`
- `GenerationJobService.run(job_id) -> JobRecord`
- Job states are `uploaded`, `recommendation_ready`, `generating`, `validating`, `ready`, and `failed`.

- [ ] Write tests for job state transitions, failure capture, and ZIP contents.
- [ ] Run them and confirm failure before implementation.
- [ ] Implement isolated job directories and call `write_roblox_package` with a generated `RobloxPuzzleSpec`.
- [ ] Implement ZIP creation containing exactly the accepted package files.
- [ ] Run focused tests and confirm they pass.

### Task 4: FastAPI API and static browser UI

**Files:**
- Create: `src/puzzle_pipeline/web/app.py`
- Create: `src/puzzle_pipeline/web/static/index.html`
- Create: `src/puzzle_pipeline/web/static/app.js`
- Create: `src/puzzle_pipeline/web/static/styles.css`
- Modify: `pyproject.toml`
- Test: `tests/integration/test_web_api.py`

**Interfaces:**
- `GET /` serves the upload UI.
- `POST /api/analyze` accepts an image upload and returns a recommendation.
- `POST /api/generate` accepts an image plus approved settings and returns a job ID.
- `GET /api/jobs/{job_id}` returns job state and previews.
- `GET /api/jobs/{job_id}/download` streams the Roblox ZIP after readiness.

- [ ] Write API tests for upload validation, recommendation response, generation status, and download response.
- [ ] Run them and confirm failure before implementation.
- [ ] Implement dependency-injected app creation so tests use a temporary data directory and no external API calls.
- [ ] Implement the browser flow: upload, recommendation review/edit, generate, poll, preview, download.
- [ ] Run focused API tests and confirm they pass.

### Task 5: Verification and documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Test: `tests/integration/test_web_api.py`

- [ ] Add no-key fallback and optional-key setup instructions.
- [ ] Add a local launch command and future MCP boundary notes.
- [ ] Run the full test, lint, type-check, and diff checks.
- [ ] Run a real local HTTP smoke test against the static UI and API.

"""Persistent generation jobs shared by the web API and future MCP tools."""

from __future__ import annotations

import json
import os
import shutil
import uuid
import zipfile
from pathlib import Path

from puzzle_pipeline.blender.bootstrap import BlenderResult, run_blender_generation
from puzzle_pipeline.config.models import AtlasConfig, BoardConfig, GridConfig, PuzzleConfig
from puzzle_pipeline.pipeline import run_core_pipeline
from puzzle_pipeline.roblox import RobloxPuzzleSpec, write_roblox_package

from .models import JobRecord, Recommendation


class GenerationJobService:
    def __init__(
        self,
        data_root: Path,
        *,
        skip_blender: bool = False,
        atlas_size: int = 2048,
        blender_executable: Path | None = None,
    ) -> None:
        self.data_root = data_root.resolve()
        self.skip_blender = skip_blender
        self.atlas_size = atlas_size
        self.blender_executable = blender_executable or self._configured_blender()
        self.data_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _configured_blender() -> Path | None:
        configured = os.environ.get("BLENDER_EXECUTABLE")
        return Path(configured) if configured else None

    def _job_dir(self, job_id: str) -> Path:
        candidate = self.data_root / job_id
        if candidate.parent != self.data_root or candidate.name != job_id:
            raise ValueError("invalid job id")
        return candidate

    def _record_path(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def _save(self, record: JobRecord) -> JobRecord:
        path = self._record_path(record.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def get(self, job_id: str) -> JobRecord:
        path = self._record_path(job_id)
        if not path.is_file():
            raise FileNotFoundError(f"Job not found: {job_id}")
        return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def create(self, image: Path, recommendation: Recommendation) -> JobRecord:
        job_id = uuid.uuid4().hex[:12]
        job_dir = self._job_dir(job_id)
        source_dir = job_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        if image.is_file():
            target = source_dir / image.name
            shutil.copy2(image, target)
        record = JobRecord(
            id=job_id,
            status="recommendation_ready",
            image_name=image.name,
            recommendation=recommendation,
        )
        return self._save(record)

    def _config(self, recommendation: Recommendation) -> PuzzleConfig:
        puzzle_id = "puzzle_001"
        width, height = float(recommendation.columns), float(recommendation.rows)
        return PuzzleConfig(
            puzzle_id=puzzle_id,
            seed=42,
            grid=GridConfig(columns=recommendation.columns, rows=recommendation.rows),
            board=BoardConfig(width=width, height=height, thickness=0.07),
            atlas=AtlasConfig(size=self.atlas_size),
        )

    def _zip_package(self, package_dir: Path, destination: Path) -> None:
        accepted = {
            "manifest.json",
            "manifest.validation.json",
            "puzzle_001.fbx",
            "puzzle_001_atlas.png",
            "puzzle_001_completion.png",
            "fbx_export_report.json",
            "fbx_reimport_report.json",
            "roblox-overrides.json",
        }
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(package_dir.iterdir()):
                if path.name in accepted and path.is_file():
                    archive.write(path, f"puzzle_001/{path.name}")

    def run(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record.status == "ready" or record.status == "failed":
            return record
        job_dir = self._job_dir(job_id)
        try:
            record = self._save(record.model_copy(update={"status": "generating", "error": None}))
            source = job_dir / "source" / record.image_name
            if not source.is_file():
                raise FileNotFoundError(f"Source image not found: {record.image_name}")
            config = self._config(record.recommendation)
            core = run_core_pipeline(config, source, job_dir / "core")
            blender_status: str | BlenderResult = "unavailable"
            if not self.skip_blender:
                blender_status = run_blender_generation(
                    core.package_dir / "blender" / "scene-input.json",
                    core.package_dir,
                    config.export.formats,
                    executable=self.blender_executable,
                )
                if not isinstance(blender_status, BlenderResult) or blender_status.status != "passed":
                    raise RuntimeError(getattr(blender_status, "message", "Blender export failed"))
            record = self._save(record.model_copy(update={"status": "validating"}))
            package_result = write_roblox_package(
                RobloxPuzzleSpec(
                    number=1,
                    source=source,
                    display_name=record.recommendation.display_name,
                    artist=record.recommendation.artist,
                    year=record.recommendation.year,
                    orientation=record.recommendation.orientation,
                    columns=record.recommendation.columns,
                    rows=record.recommendation.rows,
                    ui_sort_order=1,
                    frame_label=record.recommendation.frame_label or record.recommendation.display_name,
                    notes=record.recommendation.notes or "Preserve the full supplied artwork.",
                ),
                config,
                core,
                job_dir / "package",
                blender_status,
            )
            archive_path = job_dir / "puzzle_001.zip"
            self._zip_package(package_result.package_dir, archive_path)
            final = record.model_copy(
                update={
                    "status": "ready",
                    "package_dir": str(package_result.package_dir),
                    "download_name": archive_path.name,
                    "preview_url": f"/api/jobs/{job_id}/preview",
                }
            )
            self._save(final)
            (job_dir / "manifest.json").write_text(
                json.dumps({"id": job_id, "status": final.status, "download": archive_path.name}, indent=2) + "\n",
                encoding="utf-8",
            )
            return final
        except Exception as exc:
            failed = record.model_copy(update={"status": "failed", "error": str(exc)})
            self._save(failed)
            return failed

    def download_path(self, job_id: str) -> Path:
        record = self.get(job_id)
        if record.status != "ready":
            raise FileNotFoundError("Job is not ready")
        path = self._job_dir(job_id) / (record.download_name or "puzzle_001.zip")
        if not path.is_file():
            raise FileNotFoundError("Job download is missing")
        return path

    def preview_path(self, job_id: str) -> Path:
        record = self.get(job_id)
        if not record.package_dir:
            raise FileNotFoundError("Job preview is not ready")
        path = Path(record.package_dir) / "puzzle_001_completion.png"
        if not path.is_file():
            raise FileNotFoundError("Job preview is missing")
        return path

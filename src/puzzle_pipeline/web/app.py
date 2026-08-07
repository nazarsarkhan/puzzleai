"""FastAPI application for uploading, configuring, and exporting puzzles."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from .jobs import GenerationJobService
from .models import JobRecord, Recommendation
from .openai_advisor import OpenAIArtworkAdvisor
from .recommendations import ArtworkAdvisor, recommend_image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
STATIC_DIR = Path(__file__).with_name("static")
load_dotenv()


def _advisor_from_environment() -> ArtworkAdvisor | None:
    key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAIArtworkAdvisor(key, model=model) if key else None


def _board_aspect(orientation: str) -> float:
    return {"square": 1.0, "portrait": 3 / 4, "landscape": 4 / 3}[orientation]


class WebApplication:
    def __init__(self, data_root: Path, advisor: ArtworkAdvisor | None, service: GenerationJobService) -> None:
        self.data_root = data_root
        self.advisor = advisor
        self.service = service

    async def save_upload(self, upload: UploadFile) -> Path:
        filename = Path(upload.filename or "upload.png").name
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Please upload a supported image (PNG, JPG, or WEBP).")
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")
        upload_dir = self.data_root / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        target = upload_dir / f"{uuid.uuid4().hex}_{filename}"
        target.write_bytes(content)
        try:
            with Image.open(target) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            target.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from exc
        return target


def create_app(
    data_root: Path | None = None,
    *,
    skip_blender: bool | None = None,
    atlas_size: int = 2048,
    advisor: ArtworkAdvisor | None = None,
) -> FastAPI:
    root = (data_root or Path(os.environ.get("PUZZLE_WEB_DATA", ".web-data"))).resolve()
    blender_disabled = skip_blender if skip_blender is not None else os.environ.get("PUZZLE_WEB_SKIP_BLENDER") == "1"
    service = GenerationJobService(root, skip_blender=blender_disabled, atlas_size=atlas_size)
    application = WebApplication(root, advisor if advisor is not None else _advisor_from_environment(), service)
    app = FastAPI(title="Roblox Puzzle Asset Studio", version="0.1.0")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=FileResponse)
    async def index() -> str:
        return str(STATIC_DIR / "index.html")

    @app.post("/api/analyze", response_model=Recommendation)
    async def analyze(file: Annotated[UploadFile, File(...)]) -> Recommendation:
        image = await application.save_upload(file)
        return recommend_image(image, application.advisor)

    @app.post("/api/generate", response_model=JobRecord, status_code=202)
    async def generate(
        background_tasks: BackgroundTasks,
        file: Annotated[UploadFile, File(...)],
        columns: Annotated[int | None, Form()] = None,
        rows: Annotated[int | None, Form()] = None,
        crop_mode: Annotated[str | None, Form()] = None,
    ) -> JobRecord:
        image = await application.save_upload(file)
        recommendation = recommend_image(image, application.advisor)
        if columns is not None or rows is not None or crop_mode is not None:
            selected_columns = columns if columns is not None else recommendation.columns
            selected_rows = rows if rows is not None else recommendation.rows
            selected_crop = crop_mode or recommendation.crop_mode
            try:
                recommendation = Recommendation(
                    orientation=recommendation.orientation,
                    crop_mode=selected_crop,  # type: ignore[arg-type]
                    board_aspect=_board_aspect(recommendation.orientation),
                    columns=selected_columns,
                    rows=selected_rows,
                    piece_count=selected_columns * selected_rows,
                    confidence=1.0,
                    reasons=["User-approved layout."],
                    warnings=recommendation.warnings,
                    source="deterministic",
                    display_name=recommendation.display_name,
                    artist=recommendation.artist,
                    year=recommendation.year,
                    frame_label=recommendation.frame_label,
                    notes=recommendation.notes,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid puzzle layout: {exc}") from exc
        record = application.service.create(image, recommendation)
        background_tasks.add_task(application.service.run, record.id)
        return record

    @app.get("/api/jobs/{job_id}", response_model=JobRecord)
    async def get_job(job_id: str) -> JobRecord:
        try:
            return application.service.get(job_id)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/jobs/{job_id}/download", response_class=FileResponse)
    async def download(job_id: str) -> FileResponse:
        try:
            path = application.service.download_path(job_id)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileResponse(path, media_type="application/zip", filename=path.name)

    @app.get("/api/jobs/{job_id}/preview", response_class=FileResponse)
    async def preview(job_id: str) -> FileResponse:
        try:
            path = application.service.preview_path(job_id)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileResponse(path, media_type="image/png", filename=path.name)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "puzzle_pipeline.web.app:app",
        host=os.environ.get("PUZZLE_WEB_HOST", "127.0.0.1"),
        port=int(os.environ.get("PUZZLE_WEB_PORT", "8000")),
        reload=False,
    )

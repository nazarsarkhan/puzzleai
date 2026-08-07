from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from puzzle_pipeline.web.app import create_app


def test_web_upload_recommend_generate_and_download(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = create_app(tmp_path / "data", skip_blender=True, atlas_size=256)
    client = TestClient(app)
    image = tmp_path / "portrait.png"
    Image.new("RGB", (16, 20), (10, 20, 30)).save(image)

    with image.open("rb") as handle:
        analysis = client.post("/api/analyze", files={"file": ("portrait.png", handle, "image/png")})
    assert analysis.status_code == 200
    recommendation = analysis.json()
    assert recommendation["orientation"] == "portrait"
    assert recommendation["piece_count"] == 12

    with image.open("rb") as handle:
        generated = client.post(
            "/api/generate",
            files={"file": ("portrait.png", handle, "image/png")},
            data={"columns": "3", "rows": "2", "crop_mode": "preserve"},
        )
    assert generated.status_code == 202
    job_id = generated.json()["id"]

    status = client.get(f"/api/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "ready"

    download = client.get(f"/api/jobs/{job_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"


def test_web_rejects_unsupported_upload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client = TestClient(create_app(tmp_path / "data", skip_blender=True))

    response = client.post("/api/analyze", files={"file": ("notes.txt", b"hello", "text/plain")})

    assert response.status_code == 400
    assert "supported image" in response.json()["detail"]

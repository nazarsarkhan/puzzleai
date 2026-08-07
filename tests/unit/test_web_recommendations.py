from pathlib import Path

from PIL import Image

from puzzle_pipeline.ai.schema import ArtworkAnalysis
from puzzle_pipeline.web.recommendations import recommend_image


def test_recommends_portrait_grid_from_image_dimensions(tmp_path: Path) -> None:
    image = tmp_path / "portrait.png"
    Image.new("RGB", (300, 400)).save(image)

    result = recommend_image(image)

    assert result.orientation == "portrait"
    assert (result.columns, result.rows) == (3, 4)
    assert result.piece_count == 12
    assert result.source == "deterministic"


def test_advisor_grid_is_bounded_and_explained(tmp_path: Path) -> None:
    image = tmp_path / "square.png"
    Image.new("RGB", (1000, 1000)).save(image)

    class Advisor:
        def analyze(self, image: Path) -> ArtworkAnalysis:
            return ArtworkAnalysis(
                orientation="square",
                crop_mode="preserve",
                recommended_grid={"columns": 5, "rows": 5},
                notes="Centered composition.",
                display_name="The Circus",
                artist="Georges Seurat",
                year="1890-1891",
            )

    result = recommend_image(image, Advisor())

    assert (result.columns, result.rows) == (5, 5)
    assert result.piece_count == 25
    assert result.source == "llm"
    assert "Centered composition." in result.reasons
    assert result.display_name == "The Circus"
    assert result.artist == "Georges Seurat"
    assert result.year == "1890-1891"


def test_provider_failure_falls_back_without_failing_upload(tmp_path: Path) -> None:
    image = tmp_path / "landscape.png"
    Image.new("RGB", (800, 500)).save(image)

    class BrokenAdvisor:
        def analyze(self, image: Path) -> ArtworkAnalysis:
            raise RuntimeError("provider unavailable")

    result = recommend_image(image, BrokenAdvisor())

    assert result.source == "fallback"
    assert (result.columns, result.rows) == (4, 3)
    assert result.warnings == ["AI analysis unavailable; deterministic recommendation used."]


def test_small_image_warns_about_piece_texture_resolution(tmp_path: Path) -> None:
    image = tmp_path / "tiny.png"
    Image.new("RGB", (64, 64)).save(image)

    result = recommend_image(image)

    assert result.warnings == ["Source image is small; use fewer pieces or a larger artwork image."]


def test_malevich_filename_fills_placeholder_ai_metadata(tmp_path: Path) -> None:
    image = tmp_path / "417ea94e84e24a4c836abed1593ae7de5_Чёрный_супрематический_квадрат._1915._ГТГ.png"
    Image.new("RGB", (1000, 1000)).save(image)

    class PlaceholderAdvisor:
        def analyze(self, image: Path) -> ArtworkAnalysis:
            return ArtworkAnalysis(
                orientation="square",
                display_name="Untitled",
                artist="null",
                year="null",
                frame_label="null",
                notes="Explores themes of abstraction, texture, and darkness within a minimalist framework.",
            )

    result = recommend_image(image, PlaceholderAdvisor())

    assert result.display_name == "Black Square"
    assert result.artist == "Kazimir Malevich"
    assert result.year == "1915"
    assert result.frame_label == "Black Square — Kazimir Malevich"

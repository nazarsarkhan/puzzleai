from pathlib import Path

from PIL import Image

from puzzle_pipeline.web import app as web_app
from puzzle_pipeline.web.openai_advisor import OpenAIArtworkAdvisor


def test_openai_advisor_parses_structured_analysis(tmp_path: Path) -> None:
    image = tmp_path / "art.png"
    Image.new("RGB", (32, 48)).save(image)

    class FakeResponses:
        def create(self, **kwargs: object) -> object:
            assert kwargs["model"] == "gpt-4o-mini"
            output = (
                '{"orientation":"portrait","crop_mode":"preserve",'
                '"recommended_grid":{"columns":3,"rows":4},'
                '"decorative_border":false,"notes":"Keep the full frame.",'
                '"display_name":"The Circus","artist":"Georges Seurat",'
                '"year":"1890-1891","frame_label":"The Circus — Georges Seurat"}'
            )
            return type("Response", (), {"output_text": output})()

    class FakeClient:
        responses = FakeResponses()

    result = OpenAIArtworkAdvisor("test-key", client=FakeClient()).analyze(image)

    assert result.orientation == "portrait"
    assert result.recommended_grid == {"columns": 3, "rows": 4}
    assert result.display_name == "The Circus"


def test_openai_advisor_rejects_invalid_provider_json(tmp_path: Path) -> None:
    image = tmp_path / "art.png"
    Image.new("RGB", (32, 48)).save(image)

    class FakeResponses:
        def create(self, **kwargs: object) -> object:
            return type("Response", (), {"output_text": "not json"})()

    class FakeClient:
        responses = FakeResponses()

    try:
        OpenAIArtworkAdvisor("test-key", client=FakeClient()).analyze(image)
    except ValueError as exc:
        assert "invalid artwork analysis" in str(exc)
    else:
        raise AssertionError("invalid provider JSON must be rejected")


def test_environment_selects_model_for_server_side_advisor(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class FakeAdvisor:
        def __init__(self, api_key: str, model: str) -> None:
            captured["api_key"] = api_key
            captured["model"] = model

    monkeypatch.setenv("OPENAI_API_KEY", "server-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(web_app, "OpenAIArtworkAdvisor", FakeAdvisor)

    web_app._advisor_from_environment()

    assert captured == {"api_key": "server-key", "model": "gpt-4o-mini"}

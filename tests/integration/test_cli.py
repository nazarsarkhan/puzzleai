import json

from PIL import Image

from puzzle_pipeline.cli.main import main


def test_cli_generates_validates_and_inspects_package(tmp_path, capsys) -> None:
    image = tmp_path / "art.png"
    config = tmp_path / "config.json"
    output = tmp_path / "dist"
    Image.new("RGB", (8, 4), (1, 2, 3)).save(image)
    config.write_text(
        json.dumps({"puzzle_id": "cli_demo", "seed": 9, "atlas": {"size": 256}}),
        encoding="utf-8",
    )

    assert (
        main(["generate", "--image", str(image), "--config", str(config), "--output", str(output), "--skip-blender"])
        == 0
    )
    assert main(["validate", str(output / "cli_demo")]) == 0
    assert main(["inspect", str(output / "cli_demo")]) == 0
    assert "PASS puzzle cli_demo" in capsys.readouterr().out


def test_cli_reports_missing_artwork(tmp_path, capsys) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"puzzle_id": "bad"}), encoding="utf-8")
    assert main(["generate", "--image", str(tmp_path / "missing.png"), "--config", str(config), "--skip-blender"]) == 2
    assert "Artwork image not found" in capsys.readouterr().err

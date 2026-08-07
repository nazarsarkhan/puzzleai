from pathlib import Path


def test_required_documentation_files_exist_and_link_core_commands() -> None:
    root = Path(__file__).resolve().parents[2]
    required = (
        "README.md",
        "docs/architecture.md",
        "docs/puzzle-geometry.md",
        "docs/uv-and-atlas.md",
        "docs/roblox-import.md",
        "docs/reference-puzzle-019.md",
    )
    for relative in required:
        assert (root / relative).is_file(), relative
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "puzzle generate" in readme
    assert "puzzle validate" in readme
    assert "Blender" in readme

"""Render a generated outline pattern to a lightweight SVG debug artifact."""

from __future__ import annotations

import argparse
from pathlib import Path

from puzzle_pipeline.config.loader import load_config
from puzzle_pipeline.core.geometry.outlines import generate_puzzle_geometry


def render_outlines(config_path: Path, output: Path) -> Path:
    config = load_config(config_path)
    geometry = generate_puzzle_geometry(config)
    margin = 0.2
    width = geometry.width + 2 * margin
    height = geometry.height + 2 * margin

    def point(value: tuple[float, float]) -> str:
        x = value[0] + geometry.width / 2 + margin
        y = height - (value[1] + geometry.height / 2 + margin)
        return f"{x:.6f},{y:.6f}"

    paths = []
    for piece in geometry.pieces:
        paths.append(f'<polyline points="{" ".join(point(p) for p in piece.points)}" />')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.6f} {height:.6f}">'
        '<g fill="none" stroke="#1b2733" stroke-width="0.01">'
        + "".join(paths)
        + "</g></svg>\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render_outlines(args.config, args.output)


if __name__ == "__main__":
    main()

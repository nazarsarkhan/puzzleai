"""Locate and invoke Blender without GUI automation."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BlenderResult:
    status: str
    message: str
    command: tuple[str, ...] = ()
    stdout: str = ""
    stderr: str = ""


def find_blender(executable: Path | None = None) -> Path | None:
    if executable is not None:
        return executable if executable.is_file() else None
    found = shutil.which("blender") or shutil.which("blender.exe")
    return Path(found) if found else None


def run_blender_generation(
    scene_input: Path,
    output_dir: Path,
    formats: tuple[str, ...] = ("fbx",),
    executable: Path | None = None,
) -> BlenderResult:
    blender = find_blender(executable)
    if blender is None:
        return BlenderResult("unavailable", "Blender executable not found; core artifacts remain valid.")
    script = Path(__file__).resolve().parents[3] / "scripts" / "blender_generate.py"
    command = (
        str(blender),
        "--background",
        "--python",
        str(script),
        "--",
        "--scene-input",
        str(scene_input),
        "--output",
        str(output_dir),
        "--formats",
        ",".join(formats),
    )
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BlenderResult("failed", f"Blender subprocess failed: {exc}", command)
    if completed.returncode != 0:
        return BlenderResult("failed", "Blender generation failed.", command, completed.stdout, completed.stderr)
    if "fbx" in formats and not (output_dir / "models" / "puzzle.fbx").is_file():
        return BlenderResult(
            "failed",
            "Blender exited without producing models/puzzle.fbx.",
            command,
            completed.stdout,
            completed.stderr,
        )
    if "fbx" in formats and not (output_dir / "reports" / "fbx-reimport-report.json").is_file():
        return BlenderResult(
            "failed",
            "Blender exited without producing reports/fbx-reimport-report.json.",
            command,
            completed.stdout,
            completed.stderr,
        )
    return BlenderResult("passed", "Blender scene and exports generated.", command, completed.stdout, completed.stderr)

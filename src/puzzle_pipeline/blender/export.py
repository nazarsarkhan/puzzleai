"""Blender export and re-import operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_models(output_dir: Path, formats: tuple[str, ...]) -> dict[str, str]:
    import bpy  # type: ignore[import-not-found]

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    if "fbx" in formats:
        path = output_dir / "puzzle.fbx"
        bpy.ops.export_scene.fbx(
            filepath=str(path),
            use_selection=True,
            object_types={"MESH"},
            path_mode="COPY",
            embed_textures=True,
            axis_forward="Z",
            axis_up="Y",
            apply_unit_scale=True,
            use_space_transform=True,
            bake_space_transform=True,
            add_leaf_bones=False,
            bake_anim=False,
        )
        paths["fbx"] = str(path)
    if "glb" in formats:
        path = output_dir / "puzzle.glb"
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True)
        paths["glb"] = str(path)
    return paths


def validate_reimport(path: Path) -> dict[str, Any]:
    import bpy

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(path))
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    return {
        "valid": bool(objects),
        "object_count": len(objects),
        "names": sorted(obj.name for obj in objects),
        "triangles": sum(len(obj.data.loop_triangles) for obj in objects),
    }

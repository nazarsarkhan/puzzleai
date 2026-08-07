"""Blender scene construction helpers, imported only inside Blender."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_scene(scene_input: Path, blend_path: Path) -> None:
    """Create a clean named scene from the serializable core scene input."""
    import bpy  # type: ignore[import-not-found]

    data: dict[str, Any] = json.loads(scene_input.read_text(encoding="utf-8"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)
    root = bpy.data.collections.get(data.get("collection_name", "Puzzle")) or bpy.data.collections.new(
        data.get("collection_name", "Puzzle")
    )
    if root.name not in [child.name for child in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(root)
    pieces_collection = bpy.data.collections.new(f"{root.name}_Pieces")
    root.children.link(pieces_collection)
    material = _material(bpy, data.get("atlas_path"))
    positions = data.get("positions", {})
    for raw_mesh in data["meshes"]:
        mesh_data = bpy.data.meshes.new(raw_mesh["piece_id"] + "_Mesh")
        mesh_data.from_pydata(raw_mesh["vertices"], [], raw_mesh["faces"])
        mesh_data.update()
        uv_layer = mesh_data.uv_layers.new(name="UVMap")
        for polygon in mesh_data.polygons:
            corners = raw_mesh["corner_uvs"][polygon.index]
            for loop_index, uv in zip(polygon.loop_indices, corners, strict=True):
                uv_layer.data[loop_index].uv = uv
        mesh_data.materials.append(material)
        obj = bpy.data.objects.new(raw_mesh["piece_id"], mesh_data)
        obj.location = positions.get(raw_mesh["piece_id"], [0.0, 0.0, 0.0])
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.scale = (1.0, 1.0, 1.0)
        pieces_collection.objects.link(obj)
    bpy.context.view_layer.objects.active = None
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))


def _material(bpy: Any, atlas_path: str | None) -> Any:
    material = bpy.data.materials.new("PuzzleAtlas")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    if atlas_path:
        texture.image = bpy.data.images.load(atlas_path, check_existing=True)
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material

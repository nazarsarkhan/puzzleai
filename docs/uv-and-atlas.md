# UVs and atlas

The front UV for a solved-world point is computed as:

```text
u_board = (x - board_min_x) / board_width
v_board = (y - board_min_y) / board_height
```

Those normalized coordinates are mapped into the atlas artwork rectangle. Because
the same solved seam points are used by adjacent pieces, front UVs are continuous
when the puzzle is assembled.

The atlas is a single PNG. It contains an artwork region, a white back region, and
a cardboard side region. Padding keeps filtering from sampling unrelated regions.
Back and side surfaces use dedicated region centers, while front loops use the
mathematical artwork projection. `atlas` metadata in `manifests/puzzle.json`
records pixel rectangles and atlas size.

Pillow stores pixels top-to-bottom; the atlas builder converts the lower-left
manifest rectangles to Pillow coordinates when pasting artwork. UV metadata stays
in the lower-left convention used by Blender and the Roblox import contract.

# Roblox import

Import the generated FBX as a static mesh asset. Keep the imported object names and
the shared `PuzzleAtlas` material. The reference and generator use one stud as
one Blender scene unit, with the front face on local `+Z` before FBX axis
conversion. Imported FBX may report the host application's axis conversion in
its transform display; use the manifest's solved transforms as the source of truth.

Each piece has a stable ID such as `piece_r00_c00`. The manifest contains:

- `solved_transform.position`, rotation, and scale;
- row/column coordinates;
- neighbor IDs;
- seam IDs and connector polarity;
- atlas and export metadata.

Example Luau lookup:

```lua
local manifest = require(script.PuzzleManifest)
local pieces = workspace.PuzzlePieces

for _, pieceInfo in ipairs(manifest.pieces) do
    local piece = pieces:FindFirstChild(pieceInfo.id)
    assert(piece, "Missing imported puzzle piece: " .. pieceInfo.id)
    local p = pieceInfo.solved_transform.position
    piece:SetAttribute("PuzzleRow", pieceInfo.row)
    piece:SetAttribute("PuzzleColumn", pieceInfo.column)
    piece:SetAttribute("SolvedX", p[1])
    piece:SetAttribute("SolvedY", p[2])
end
```

Use `neighbors` and `seam_ids` for game logic instead of inferring topology from
mesh geometry. Preserve the atlas texture assignment when uploading the model;
the atlas is intentionally shared by every piece.

## Batch package contract

Run:

```bash
puzzle batch --input ./images --output ./assets/puzzles
```

Each numbered folder contains `manifest.json`, `manifest.validation.json`, the
atlas and completion PNGs, `fbx_export_report.json`, `fbx_reimport_report.json`,
and `roblox-overrides.json`. A real FBX is included only after Blender export
succeeds; missing Blender is reported explicitly and never replaced by a fake
file. Stage a successful FBX manually as `Workspace.ImportStaging/Puzzle_NNN_Raw`.

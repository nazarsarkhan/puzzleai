# Puzzle geometry

The board uses `+X` right, `+Y` up, and `+Z` front. The assembled board is centered
at the origin. Each piece mesh is generated around its logical cell center, and
the object transform places that local mesh at the solved cell center.

For every internal boundary, `SeamGraph` creates exactly one `Seam`. The left or
lower owner receives a `TAB`; the right or upper owner receives the complementary
`HOLE`. Both outlines reference the same sampled global boundary points, reversed
only for polygon winding. Borders are always flat.

Outlines use a smooth parametric classic-jigsaw connector with bounded center,
shape, and depth jitter. Ear-clipping triangulation converts each counter-clockwise
outline into a front face and reversed back face. Two triangles per outline edge
close the side walls, producing a watertight solid with positive signed volume.

The default pivot policy is `logicalCellCenter`, matching the reference fixture.
This makes Roblox movement and rotation natural while the manifest retains visual
bounds for tabs extending beyond the nominal cell.

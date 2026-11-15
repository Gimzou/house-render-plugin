# House data schema (`<project>/house/*.json`)

Units are metres and degrees. **Axes:** +X = right of the plan sheet, +Y = top of the sheet, z = 0 at the finished floor of the level. Any scalar can be wrapped as `{"value": x, "placeholder": "<why guessed>"}` or `{"value": x, "source": "<sheet/date>"}`. The build lists every placeholder.

## levels.json
`{"<level>": {"wall_height", "slab_below", "ceiling": {"enabled", "clear_height", "thickness"}}}`. The engine builds the first level that has a matching `<level>.json` (or `--level NAME`). Keys starting with `_` and entries without `wall_height` (datums, elevations) are ignored.

## <level>.json
| key | meaning |
|---|---|
| `orientation.plan_up_bearing_deg` | compass bearing of the sheet's top (read the north arrow). Drives the sun. |
| `footprint` | outer polygon, counter-clockwise, `[[x, y], ...]` |
| `plan_total_area` | title-block area, checked against the footprint |
| `wall_thickness` | one thickness for the outer wall ring (inset with mitred corners, any angle) |
| `facades` | `{"name": {"from": [x, y], "to": [x, y]}}`, one per edge that has openings. The inward side is found automatically. Legacy: `{"axis": "x"/"y", "line", "inward": ±1}`, where `pos` is then a coordinate |
| `openings` | `{"id", "facade", "pos" (distance from the facade's 'from' to the opening centre), "width", "height", "sill", "kind": "window" or "door"}` |
| `frame_inset`, `glass_pane_thickness` | pane/door leaf inset in the opening |
| `partition_thickness`, `partitions` | interior walls, axis-aligned: `{"id", "from", "to", "doors": [{"id", "center" (x or y along the wall), "width", "height", "type": "opening", "sliding_pocket" or "swing", ...}]}` |
| `rooms` | `{"id", "name", "polygon", "finish": <surface>, "plan_area"?}`: floor finish and area check |
| `outdoor` | terraces and balconies: `{"id", "polygon", "thickness", "material", "plan_area"?, "railing": {"edges": [[i, j], ...] or "all", "height", "thickness", "material"}}`. Railings sit on the listed polygon edges. |
| `blocks` | free boxes `{"id", "center": [x, y, z], "size": [w, d, h], "rot_z", "material"}` (joinery, columns...) |
| `stairs`, `chimney_breast` | optional; see `build_stairs` / `build_partitions` in `engine/lib/geom.py` for the fields |
| `site` | `{"enabled", "ground_z" (e.g. -9.5 for a 3rd-floor flat), "ground_plane_size", "ground_plane_center"}` |

## materials.json
`library` holds named materials: `{"color": [r, g, b] (0-1 linear), "roughness", "metallic"?, "type": "glass"?, "emission"?}`. `surfaces` maps the engine's surface names to library entries. Required surfaces: `exterior_wall, partition, glazing, door, door_leaf, slab, ceiling, ground`, plus every `finish`, outdoor `material` and furniture `material` you use (e.g. `floor_wood, terrace, railing, furniture.block, people`). Swapping a finish means changing one name here.

## furniture.json
`items`: `{"id", "room", "tier": "block", "proxy" or "asset", "size": [W, D, H], "center": [x, y], "base_z", "rot_z", "material", "proxy"?: "sofa", "person_standing" or "person_seated", "variant"?: "group:option"}`. `variants`: `{"group": {"options": [...], "default": "..."}}`; pick one with `--variant group=option`.

## cameras.json
`{"name", "location", "target", "lens" (mm), "resolution"?, "clip_start"?, "type"?: "ortho", "ortho_scale"?, "plan_up"?: true (top-down with +Y up), "hide"?: ["ceiling", ...], "hero"?}`. Collections you can hide: `structure, ceiling, glazing, doors, outdoor, furniture, people, site, floors, blocks`.

## lighting.json
`site: {lat, lon}`, `default`, and `presets: {"name": {"type": "solar", "date", "time", "utc_offset_h", "sun_strength", "sky_strength", "exposure", "view_transform": "AgX"}}`. Keep exposure fixed per preset so images compare across versions.

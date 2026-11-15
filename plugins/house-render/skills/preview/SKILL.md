---
name: preview
description: Rebuild house.blend from house/*.json and render fast EEVEE previews of all or named cameras. Use after any data change, or when the owner says "show me".
---

# Preview

Run from the project folder, with `B` = `blender` from `~/.config/house-render/machine.json` (run `setup` if that file is missing) and `E=${CLAUDE_PLUGIN_ROOT}/engine`.

1. Build: `$B -b -P $E/build.py -- --house .`. Fix any `DATA ERROR` or traceback first. Show the user the placeholder count and the AREAS block (footprint against plan total).
2. Render: `$B -b build/house.blend -P $E/render.py -- --house . --engine eevee --cameras <all|a,b> [--preset NAME] [--scale 0.5]`. Output goes to `renders/preview/<date>_<camera>_<preset>_<gitsha>.png`. The sha is `-dirty` if `house/` has uncommitted changes, so commit before renders you send.
   - Expect about 5 to 60 s per view. With more than 4 views, or on a slow machine, run in the background.
3. **Look at every PNG yourself** (Read). Check for missing walls, black rooms, wrong scale, z-fighting, objects in walls, and openings on the wrong side.
4. Send the user the images (SendUserFile), one line per image on what changed. For a design-option change, show a before/after pair.

New cameras: add them to `house/cameras.json`. Use eye height 1.6 m and lens 18 to 24 mm for interiors. A `plan_top` ortho camera with `"hide": ["ceiling"]` is the geometry check.

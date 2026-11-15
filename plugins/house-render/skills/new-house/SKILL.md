---
name: new-house
description: Start a new house/apartment render project from the plugin template: folder, brief, data skeleton, git. Use when someone says "render my house/flat", shares plans for a new place, or wants to start a project for a friend.
---

# New house project

1. **Ask for the essentials** (one short message, skip what's already known):
   - folder name (short, e.g. `rue-x-12`), and where the plan PDFs/images are;
   - address or at least city (for the sun position; a street-level address isn't needed: lat/lon to 2 decimals is fine);
   - house or apartment, which floor(s) to model first;
   - what they want to see (rooms, terrace, before/after of a choice) and what's already decided (finishes, furniture). If nothing is decided, that's fine.
2. **Create the project:** `cp -R ${CLAUDE_PLUGIN_ROOT}/templates/house/. <folder>/`, unless the folder already exists with plans in it. In that case copy the template around them without overwriting anything. Put the plans in `<folder>/data/plans/`. `git init` and make a first commit.
3. **Fill in `brief.md`** from the answers. It is the record of what the owners decided. **The project depicts decisions and never makes them.** Anything not in the brief is drawn as a neutral placeholder and tagged `placeholder`.
4. **Fill in `house/lighting.json` → `site`** (lat/lon) and rename the level in `house/levels.json` and `house/<level>.json` (e.g. `ground`, `apartment`).
5. Hand over to **`update-from-plans`** to trace the geometry, then **`preview`**.
6. Make sure `CLAUDE.md` in the new folder names the project and points to this plugin's skills (the template does that).

# house-render

A Claude Code plugin that turns a home's floor plans into a Blender model, fast EEVEE previews and photoreal Cycles stills. You talk to Claude; Claude traces the plans into JSON data, builds the model headless and shows you the renders.

## Install (once)
1. Install **Blender 4.2 LTS or newer** from blender.org (Intel Macs: 4.5 LTS).
2. In Claude Code:
   ```
   /plugin marketplace add <git URL or local path of this repo>
   /plugin install house-render@house-render
   ```
3. Ask Claude: "run house-render setup". It finds Blender, detects your GPU and writes `~/.config/house-render/machine.json`.

## Use
- "Start a house-render project for my flat, plans are in ~/Downloads/plans" (`new-house`, then `update-from-plans`, then `preview`)
- "Show me the living room", "add our 240 cm sofa", "make the real picture of the kitchen tonight"

Each home is its own folder (and git repo): `brief.md` (the owners' decisions), `house/*.json` (geometry and choices), `data/plans/`, `renders/`. The project only **depicts** decisions; anything undecided stays a neutral placeholder.

## Contents
- `plugins/house-render/engine/`: `build.py`, `render.py`, `lib/` (Blender, headless), `tools/plan_trace.py` (measure PDFs at 1 px = 1 cm), `SCHEMA.md`
- `plugins/house-render/skills/`: setup, new-house, update-from-plans, preview, furnish, hero-render, review-render
- `plugins/house-render/agents/render-reviewer.md`
- `plugins/house-render/templates/house/`: new project skeleton
- `plugins/house-render/examples/box-house/`: tiny test house (diagonal wall, terrace)

Smoke test: `blender -b -P plugins/house-render/engine/build.py -- --house plugins/house-render/examples/box-house` builds it.

Origin: abstracted from a single-house project (Montgolfier render), then proven on an apartment (wo58).

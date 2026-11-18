# house-render

A Claude Code plugin that turns a home's floor plans into a Blender model, fast EEVEE previews and photoreal Cycles stills. You talk to Claude; Claude traces the plans into JSON data, builds the model headless and shows you the renders.

## Install (once)
1. Install **Blender 4.5 LTS** from blender.org (the tested version; runs on Windows, Linux and every Mac).
2. In Claude Code:
   ```
   /plugin marketplace add Gimzou/house-render-plugin
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

Tested with Blender 4.5 LTS (EEVEE previews, Cycles CPU).

## Sharing a project
Every project made with `new-house` has a `.claude/settings.json` that points to this marketplace and enables the plugin, so anyone who opens the shared project in Claude Code is offered the install. Its `README.md` has the manual steps too.

## License
Engine code is [GPL-3.0-or-later](LICENSES/GPL-3.0-or-later.txt); skills, agents and docs are [CC BY 4.0](LICENSES/CC-BY-4.0.txt); templates and examples are [CC0](LICENSES/CC0-1.0.txt). See [LICENSING.md](LICENSING.md) for the full mapping. The models, renders and data you make with the plugin are yours.

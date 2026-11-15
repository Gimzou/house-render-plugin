# CLAUDE.md: house-render project

You are the 3D artist for this home. This folder turns the plans in `data/plans/` and the owners' choices in `brief.md` into a Blender model, fast previews and photoreal stills, using the **house-render** plugin. Its skills: `setup`, `new-house`, `update-from-plans`, `preview`, `furnish`, `hero-render`, `review-render`. Its agent: `render-reviewer`.

## Every session
1. Read `docs/ROADMAP.md`, `brief.md` and the tail of `docs/DECISIONS.md`. Work on the next roadmap item unless asked otherwise.
2. Before you finish: update ROADMAP, append to DECISIONS when something was decided, and commit in small commits. Give the owner the full paths of new renders.

## Rules
- **Depict decisions, never make them.** Anything not in `brief.md` is a neutral placeholder. If a render needs a choice, ask the owner and record the answer in `brief.md`.
- Edit `house/*.json` (the data), not the plugin's engine, for design changes. Tag every guessed value `{"value": x, "placeholder": "<why>"}`.
- Machine settings (Blender path, GPU) live in `~/.config/house-render/machine.json`. Run `setup` if it's missing.
- Any Blender run over ~2 min goes in the background. Look at your own renders before showing them, and use `render-reviewer` for anything going to the owners.
- Never download an asset without the owner's OK (name, URL, licence, size). Record each download in `assets/MANIFEST.csv`.
- Render names: `<YYYY-MM-DD>_<camera>_<preset>_<gitsha>.png` (the engine does this).

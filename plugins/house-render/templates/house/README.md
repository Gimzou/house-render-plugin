# House render project

A 3D model of this home, built from the plans in `data/plans/` with the [house-render](https://github.com/Gimzou/house-render-plugin) plugin for Claude Code.

## Getting started (once per computer)

1. Install **Blender 4.5 LTS** (free): https://www.blender.org/download/lts/4-5/
2. Install **Claude Code**: https://claude.com/claude-code
3. Clone this repo and open the folder in Claude Code. It reads `.claude/settings.json` and asks to install the **house-render** plugin: say yes (trust the folder if asked).
   If it does not ask, install the plugin by hand, inside Claude Code:
   ```
   /plugin marketplace add Gimzou/house-render-plugin
   /plugin install house-render@house-render
   ```
   then run `/reload-plugins` (or restart Claude Code).
4. Ask Claude: **"run house-render setup"**. It finds Blender, checks your graphics card and saves `~/.config/house-render/machine.json`.
5. Ask for what you want to see: "show me the living room", "add our sofa (240 x 95 cm, grey)", "make the real picture of the terrace tonight".

Plugin skills show up as `/house-render:preview`, `/house-render:furnish`, etc., but plain sentences work too.

## What is where
- `brief.md`: your decisions (finishes, furniture, views). Claude only draws what is written here; everything else stays a neutral placeholder.
- `data/plans/`: the plans the model is traced from.
- `house/*.json`: the model as data (walls, openings, materials, furniture, cameras, sun).
- `renders/`: images, named `<date>_<camera>_<lighting>_<version>.png`.
- `docs/ROADMAP.md`, `docs/DECISIONS.md`: what is next and what was decided or measured.

Updates to the plugin: `/plugin marketplace update house-render`.

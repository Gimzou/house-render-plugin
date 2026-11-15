---
name: update-from-plans
description: Trace or update house/<level>.json (footprint, facades, openings, partitions, rooms, terraces) from floor-plan PDFs or images. Use for a new project, new or revised plans, or adding a level.
---

# Update from plans

Read `${CLAUDE_PLUGIN_ROOT}/engine/SCHEMA.md` first: it defines every field and the model axes.

1. **Read the plans** (Read the PDF). List the sheets: level, date, scale, the north arrow, the written dimensions, and the title-block areas. When sheets disagree, use the **latest** and note it.
2. **Prefer written dimensions** over tracing. To trace, use `${CLAUDE_PLUGIN_ROOT}/engine/tools/plan_trace.py` (its docstring gives the steps):
   - `scale`: get pt per metre from the graphic scale (vector PDFs). For scans, rasterise and measure the scale bar.
   - `raster`: renders the sheet at 1 px = 1 cm.
   - `map` and `scan`: give wall faces, door gaps and window gaps in cm.
   - `probe`: finds glazing lines and thin frames.
   - Check one long traced run against a written dimension (e.g. a written chain of three dimensions against the traced length of the same wall) and record it.
3. **Read the north arrow** on a 600 dpi crop and set `orientation.plan_up_bearing_deg`, the compass bearing of the sheet's top. Record the source.
4. **Write the data.** For anything non-trivial, keep a small generator script in the project (`tools/trace_<level>.py`, pixel coordinates in, JSON out) so a re-trace is a one-line edit. Pattern: a `P(px, py)` helper that converts traced pixels to model metres (`x = (px - x0)/100, y = (y0 - py)/100`), then the footprint, facades, openings and partitions as lists, dumped to `house/<level>.json`.
   - Footprint: counter-clockwise outer polygon. Façades: one `{from, to}` segment per glazed or windowed edge; diagonal façades are fine.
   - Openings sit on a façade (`pos` = distance along it). Interior walls are `partitions`, with door gaps.
   - `rooms` are for floor finishes and area checks. `outdoor` is for terraces and balconies (slab plus railing edges).
   - Tag every guess `{"value": x, "placeholder": "<why>"}`, add `src` to traced items, and set `plan_total_area` and `plan_area` where the plan gives them.
5. **Build, then compare:** run `preview` with the `plan_top` ortho camera (ceiling hidden) and compare it with the PDF side by side. The build prints the footprint and room areas against the plan: aim for within 2%. Fix the data, not the engine.
6. Log the change in `docs/DECISIONS.md` (sources, scale, checks) and tick `docs/ROADMAP.md`.

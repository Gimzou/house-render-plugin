---
name: hero-render
description: Queue photoreal Cycles renders of chosen cameras as a background (or overnight) batch. Use when the owner wants "the real picture" of a room after previews are approved.
---

# Hero render

1. **Preconditions:** the owner approved a preview of the same camera, and the project is committed (the git sha goes in the file name).
2. **Estimate the time** from `machine.json` (`cycles_device`, `cycles_sec_per_view_720p_128spp`). For a 1080p furnished view, multiply the benchmark by about 10 on the CPU and about 4 on a GPU. On the CPU, plan 20 to 60 min per view. Tell the owner the estimate. For long batches, ask them to keep the computer plugged in and awake, and request keep-awake if available.
3. Run in the background:
   `$B -b build/house.blend -P ${CLAUDE_PLUGIN_ROOT}/engine/render.py -- --house . --engine cycles --cameras a,b [--samples 256]`
   - The device comes from `machine.json`, and the log prints `CYCLES DEVICE`.
   - One process renders the views in sequence and writes each file as it finishes, so a crash keeps the finished ones.
   - Output: `renders/hero/`.
4. Interior daylight: the engine hides glass and turns on window **portals** in Cycles. Fix noise with portals and per-view samples, not with global brute force.
5. When it's done: Read every image, run `review-render`, log the minutes per view in `docs/DECISIONS.md`, then send the images.

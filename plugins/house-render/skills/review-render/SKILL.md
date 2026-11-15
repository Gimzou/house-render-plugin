---
name: review-render
description: Critically check renders against the plans, the house data and photoreal quality before showing them to the owner. Use after preview/hero renders, or when the owner says something looks off.
---

# Review render

Launch the `house-render:render-reviewer` agent with the render paths, the camera names, the project folder and what changed. Then:
- Fix the **geometry/data defects** it reports before you show anything.
- Pass on the **open doubts** (things only the plans or the owners can settle) to the owner in a short list, and suggest they record the answers in `brief.md`.
- Treat **quality notes** (noise, exposure, scale cues) as tuning for the next run.

---
name: furnish
description: Add, move or swap furniture/fixtures in house/furniture.json, including sourcing a real 3D asset. Use when the owner mentions a piece of furniture, a product they chose, or a layout to try.
---

# Furnish

1. **Find the decision in `brief.md`.** Look for the product, dimensions and colour. If it's not there, ask the owner, then record their answer in `brief.md` (with the date) before modelling. Furniture drawn on developer or architect plans is usually illustrative only: don't treat it as chosen.
2. **Add a `block`-tier entry first:** room, true W × D × H in metres, centre, `rot_z` and material. Always do this, so the scene is right before it is pretty.
3. **Upgrade the tier when it's worth it:**
   - `proxy`: a simple modelled shape from `engine/lib/proxies.py` (`sofa`, `person_standing`, `person_seated`). Add new proxies to the plugin, not the project.
   - `asset`: a free model from the manufacturer, Poly Haven or ambientCG. **Ask the owner before downloading** and give the name, URL, licence and size. Store it under `assets/models/<id>/`, add a row to `assets/MANIFEST.csv`, and check its dimensions against the block.
4. Use `variants` (`"variant": "group:option"`) to compare alternatives, for example a sofa against two armchairs. Pick one with `--variant group=option` at build time.
5. Run `preview` on the cameras that see the item.

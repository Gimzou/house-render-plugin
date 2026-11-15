"""Load <house>/house/*.json, unwrap tagged scalars, report placeholders. Pure Python (no bpy).

The house folder comes from `--house <dir>` after Blender's `--`, else the current directory.
"""
import json
import os
import sys
from pathlib import Path


def _house_root():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--house" in argv:
        return Path(argv[argv.index("--house") + 1]).expanduser().resolve()
    return Path(os.environ.get("HOUSE_DIR", os.getcwd())).resolve()


ROOT = _house_root()
HOUSE = ROOT / "house"
MACHINE = Path(os.environ.get("HOUSE_RENDER_CONFIG", "~/.config/house-render/machine.json")).expanduser()


def load(name):
    with open(HOUSE / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def load_all():
    if not HOUSE.is_dir():
        sys.exit(f"no house data at {HOUSE} (pass --house <dir>)")
    return {p.stem: load(p.stem) for p in sorted(HOUSE.glob("*.json"))}


def machine():
    """Per-user machine settings written by the setup skill (Cycles device etc.)."""
    try:
        return json.loads(MACHINE.read_text())
    except (OSError, ValueError):
        return {}


def level_names(d):
    """Levels that have a geometry file <name>.json, in levels.json order (or --level)."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--level" in argv:
        return [argv[argv.index("--level") + 1]]
    return [k for k in d["levels"] if not k.startswith("_") and k in d and isinstance(d["levels"][k], dict)
            and "wall_height" in d["levels"][k]]


def v(x):
    """Unwrap {"value": ..., "placeholder"/"source": ...} to its value."""
    return x["value"] if isinstance(x, dict) and "value" in x else x


def placeholders(data, path=""):
    """Yield (path, value, reason) for every dict carrying a 'placeholder' key."""
    if isinstance(data, dict):
        if "placeholder" in data:
            yield path, data.get("value"), data["placeholder"]
        for k, val in data.items():
            if k != "placeholder":
                yield from placeholders(val, f"{path}.{k}" if path else k)
    elif isinstance(data, list):
        for i, val in enumerate(data):
            label = val.get("id") or val.get("name") if isinstance(val, dict) else None
            yield from placeholders(val, f"{path}[{label or i}]")


def polygon_area(poly):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def point_in_polygon(x, y, poly):
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def facade_frame(fac, footprint):
    """Normalise a facade to (origin, unit direction, inward normal). Two forms:
    - segment: {"from": [x, y], "to": [x, y]}; 'pos' is the distance from 'from'; inward is found from the footprint.
    - legacy axis-aligned: {"axis": "x"|"y", "line": L, "inward": ±1}; 'pos' is the x (or y) coordinate."""
    if "from" in fac:
        (x0, y0), (x1, y1) = fac["from"], fac["to"]
        L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        u = ((x1 - x0) / L, (y1 - y0) / L)
        n = (-u[1], u[0])
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if not point_in_polygon(mx + n[0] * 0.05, my + n[1] * 0.05, footprint):
            n = (-n[0], -n[1])
        return (x0, y0), u, n
    line, inward = fac["line"], fac["inward"]
    if fac["axis"] == "x":
        return (0.0, line), (1.0, 0.0), (0.0, float(inward))
    return (line, 0.0), (0.0, 1.0), (float(inward), 0.0)

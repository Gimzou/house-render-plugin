"""Build <house>/build/house.blend from <house>/house/*.json.

    Blender -b -P <plugin>/engine/build.py -- --house <dir> [--out <file>] [--level NAME] [--variant G=O]

Deterministic: starts from factory settings and builds everything from data. Prints a placeholder
report and an area check against the plan (rooms with 'plan_area', and the level's 'plan_total_area').
One level is built per run (the first level in levels.json that has a <name>.json geometry file).
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
from lib import data, geom, materials, cameras, lighting, furniture  # noqa: E402
from lib.data import v  # noqa: E402


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--house", default=None, help="house project folder (default: cwd)")
    ap.add_argument("--level", default=None)
    ap.add_argument("--out", default=str(data.ROOT / "build" / "house.blend"))
    ap.add_argument("--variant", action="append", default=[], metavar="GROUP=OPTION",
                    help="pick a furniture variant, e.g. seating=armchairs")
    return ap.parse_args(argv)


def check(cond, msg):
    if not cond:
        sys.exit(f"DATA ERROR: {msg}")


def report(d, name):
    print("\n=== PLACEHOLDERS ===")
    n = 0
    for doc_name, doc in d.items():
        for path, value, reason in data.placeholders(doc):
            n += 1
            val = "" if value is None else f" = {value}"
            print(f"  {doc_name}:{path}{val}  <- {reason}")
    print(f"  ({n} placeholders)")
    g = d[name]
    print("\n=== AREAS (model vs plan) ===")
    for r in g.get("rooms", []):
        a = data.polygon_area(r["polygon"])
        pa = v(r.get("plan_area"))
        if pa:
            diff = (a - pa) / pa * 100
            flag = "  <-- CHECK" if abs(diff) > 5 else ""
            print(f"  {r['id']:12s} {a:6.2f} m2 vs {pa:6.2f}  ({diff:+.0f}%){flag}")
        else:
            print(f"  {r['id']:12s} {a:6.2f} m2 (no plan area)")
    tot = v(g.get("plan_total_area"))
    if tot:
        fa = data.polygon_area(g["footprint"])
        print(f"  {'FOOTPRINT':12s} {fa:6.2f} m2 vs plan total {tot:6.2f}  ({(fa - tot) / tot * 100:+.0f}%)")
    for s in g.get("outdoor", []):
        a, pa = data.polygon_area(s["polygon"]), v(s.get("plan_area"))
        print(f"  {s['id']:12s} {a:6.2f} m2" + (f" vs {pa:6.2f}  ({(a - pa) / pa * 100:+.0f}%)" if pa else ""))


def main():
    a = args()
    d = data.load_all()
    for key in ("levels", "materials", "cameras", "lighting"):
        check(key in d, f"missing house/{key}.json")
    names = data.level_names(d)
    check(names, "no level in levels.json has a matching <name>.json with wall_height")
    name = a.level or names[0]
    lvl, g = d["levels"][name], d[name]
    for key in ("footprint", "wall_thickness", "facades", "openings", "partition_thickness", "orientation"):
        check(key in g, f"{name}.json lacks '{key}'")
    for op in g["openings"]:
        check(op["facade"] in g["facades"], f"opening {op['id']} uses unknown facade {op['facade']}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    cols = {n: geom.collection(n) for n in ("structure", "glazing", "doors", "portals", "site", "cameras")}
    mats = materials.build(d["materials"])

    slab_below = v(lvl.get("slab_below", 0.2))
    slab = geom.prism("slab", [tuple(p) for p in g["footprint"]], -slab_below, 0, mats["slab"], cols["structure"])
    geom.build_walls(g, lvl, mats, cols)
    geom.build_partitions(g, lvl, mats, cols)
    site = g.get("site", {})
    if site.get("enabled", True):
        s = site.get("ground_plane_size", 60)
        cx, cy = site.get("ground_plane_center", [0, 0])
        gz = v(site.get("ground_z", -slab_below))
        geom.box("ground", (cx, cy, gz - 0.0005), (s, s, 0.001), mats["ground"], cols["site"]).name = "ground"
    geom.build_floors(g, mats, cols)
    geom.build_outdoor(g, mats, cols)
    geom.build_stairs(g, lvl, mats, cols, slab)
    geom.build_blocks(g, mats, cols)
    ceil = geom.build_ceiling(g, lvl, mats, cols)
    sw = g.get("stairs", {}).get("stairwell")
    if ceil and sw:
        (x0, y0), (x1, y1) = sw["from"], sw["to"]
        cut = geom.box("cut_stairwell", ((x0 + x1) / 2, (y0 + y1) / 2, 3.0), (abs(x1 - x0), abs(y1 - y0), 2.0), None, cols["structure"])
        geom.boolean(ceil, cut)
        bpy.data.objects.remove(cut)
    geom.build_portals(g, cols)

    furniture.build(d.get("furniture", {}), mats, dict(x.split("=", 1) for x in a.variant))
    cameras.build(d["cameras"], cols["cameras"])
    lighting.apply(scene, d["lighting"], g, d["lighting"]["default"])
    scene.render.image_settings.file_format = 'PNG'
    lighting.set_engine(scene, "eevee")

    report(d, name)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=False)
    print(f"\nBUILT {out}")


main()

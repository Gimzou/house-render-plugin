"""Render named cameras from <house>/build/house.blend.

    Blender -b <house>/build/house.blend -P <plugin>/engine/render.py -- --house <dir> --engine eevee|cycles \
        [--cameras all|name,name] [--preset autumn_afternoon] [--out renders/preview] \
        [--samples N] [--scale 1.0]

Output: <out>/<YYYY-MM-DD>_<camera>_<preset>_<gitsha>[-dirty].png
"""
import sys
import time
import argparse
import subprocess
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
from lib import data, lighting  # noqa: E402


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--house", default=None)
    ap.add_argument("--engine", choices=["eevee", "cycles"], default="eevee")
    ap.add_argument("--cameras", default="all")
    ap.add_argument("--preset", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--scale", type=float, default=1.0, help="resolution scale (e.g. 0.5 for tests)")
    return ap.parse_args(argv)


def git_sha():
    root = str(data.ROOT)
    sha = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip() or "nogit"
    dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--untracked-files=no",
                            "--", "house"], capture_output=True, text=True).stdout.strip()
    return sha + ("-dirty" if dirty else "")


def setup_engine(scene, engine, samples, factory=False):
    portals = bpy.data.collections.get("portals")
    glazing = bpy.data.collections.get("glazing")
    if engine == "eevee":
        lighting.set_engine(scene, "eevee")
        if portals:  # portals are Cycles-only; EEVEE would light the scene with them
            portals.hide_render = True
        if factory:  # legacy regression: keep factory EEVEE settings
            return
        ee = scene.eevee
        ee.taa_render_samples = samples or 64
        ee.use_shadows = True
        ee.use_raytracing = True
        ee.ray_tracing_options.resolution_scale = '1'
        ee.fast_gi_method = 'GLOBAL_ILLUMINATION'
    else:
        lighting.set_engine(scene, "cycles")
        print("CYCLES DEVICE", lighting.setup_cycles_device(scene, data.machine().get("cycles_device")))
        scene.cycles.samples = samples or 256
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        if portals:
            portals.hide_render = False
        if glazing:  # interior daylight rule: no panes in Cycles
            glazing.hide_render = True


def main():
    a = args()
    d = data.load_all()
    scene = bpy.context.scene
    preset = a.preset or d["lighting"]["default"]
    info = lighting.apply(scene, d["lighting"], d[data.level_names(d)[0]], preset)
    print("LIGHTING", info)
    setup_engine(scene, a.engine, a.samples,
                 factory=d["lighting"]["presets"][preset].get("factory_engine", False))

    cams = sorted([o for o in scene.objects if o.type == 'CAMERA'], key=lambda o: o.name)
    if a.cameras != "all":
        want = {"cam_" + n for n in a.cameras.split(",")}
        cams = [c for c in cams if c.name in want]
        missing = want - {c.name for c in cams}
        if missing:
            sys.exit(f"unknown cameras: {sorted(missing)}")

    out = Path(a.out or data.ROOT / "renders" / ("preview" if a.engine == "eevee" else "hero"))
    out.mkdir(parents=True, exist_ok=True)
    sha, today = git_sha(), date.today().isoformat()
    orig_hide = {col.name: col.hide_render for col in bpy.data.collections}
    for cam in cams:
        rx, ry = cam["resolution"]
        scene.render.resolution_x, scene.render.resolution_y = int(rx * a.scale), int(ry * a.scale)
        scene.render.resolution_percentage = 100
        scene.camera = cam
        hidden = {n for n in cam.get("hide", "").split(",") if n}
        for col in bpy.data.collections:
            col.hide_render = orig_hide[col.name] or col.name in hidden
        name = cam.name[4:]
        path = out / f"{today}_{name}_{preset}_{sha}.png"
        scene.render.filepath = str(path)
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"RENDERED {path}  ({time.time() - t0:.1f} s)")


main()

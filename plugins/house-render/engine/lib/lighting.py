"""Apply a lighting preset (sun, sky, exposure) to the scene. Idempotent: replaces previous sun/world."""
import math
import bpy
from mathutils import Euler, Vector

from .data import v
from .sun import sun_position, local_to_utc, model_vector


def _clear():
    for ob in [o for o in bpy.data.objects if o.name == "sun"]:
        bpy.data.objects.remove(ob)
    for w in list(bpy.data.worlds):
        bpy.data.worlds.remove(w)


def _sun(strength, angle_deg=0.526):
    sd = bpy.data.lights.new("sun", 'SUN')
    sd.energy = strength
    sd.angle = math.radians(angle_deg)
    ob = bpy.data.objects.new("sun", sd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (10, 10, 20)
    return ob


def apply(scene, lighting, ground, name):
    p = lighting["presets"][name]
    _clear()
    w = bpy.data.worlds.new("world")
    w.use_nodes = True
    scene.world = w
    bg = w.node_tree.nodes["Background"]
    info = {"preset": name}

    if p["type"] == "fixed":
        sun = _sun(p["sun_strength"])
        sun.data.angle = math.radians(0.526)  # factory default
        sun.rotation_euler = Euler([math.radians(a) for a in p["sun_euler_deg"]])
        bg.inputs["Color"].default_value = (*p["world_color"], 1)
        return info

    site = lighting["site"]
    dt = local_to_utc(p["date"], p["time"], p["utc_offset_h"])
    az, el = sun_position(site["lat"], site["lon"], dt)
    o = ground["orientation"]
    bearing = v(o["plan_up_bearing_deg"] if "plan_up_bearing_deg" in o else o["garden_bearing_deg"])
    to_sun = Vector(model_vector(az, el, bearing))
    sun = _sun(p["sun_strength"], p.get("sun_angle_deg", 0.526))
    sun.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()

    sky = w.node_tree.nodes.new("ShaderNodeTexSky")
    types = [e.identifier for e in sky.bl_rna.properties["sky_type"].enum_items]
    sky.sky_type = next((t for t in ("NISHITA", "MULTIPLE_SCATTERING", "SINGLE_SCATTERING") if t in types), types[-1])
    sky.sun_disc = False
    sky.sun_elevation = math.radians(max(el, 0.0))
    sky.sun_rotation = math.atan2(to_sun.x, to_sun.y) % (2 * math.pi)
    sky.altitude = 80
    sky.air_density = p.get("air_density", 1.0)
    sky.dust_density = p.get("dust_density", 1.0)
    w.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = p["sky_strength"]

    vs = scene.view_settings
    vs.view_transform = p.get("view_transform", "AgX")
    vs.look = p.get("look", "None")
    vs.exposure = p["exposure"]
    vs.gamma = 1.0
    info.update(azimuth=round(az, 1), elevation=round(el, 1), utc=dt.isoformat())
    return info


def set_engine(scene, engine):
    """Pick the EEVEE identifier this Blender exposes (EEVEE Next in 4.2-4.x, plain EEVEE elsewhere)."""
    if engine == "cycles":
        scene.render.engine = 'CYCLES'
        return 'CYCLES'
    for ident in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = ident
            return ident
        except TypeError:
            continue
    raise RuntimeError("no EEVEE engine in this Blender")


def setup_cycles_device(scene, wanted=None):
    """Use the GPU backend named in the machine config (METAL, OPTIX, CUDA, HIP, ONEAPI) if Blender sees
    a device for it; otherwise CPU. Returns the device type actually used."""
    import bpy
    scene.cycles.device = 'CPU'
    if not wanted or wanted == "CPU":
        return "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = wanted
        prefs.refresh_devices()
        devs = [dv for dv in prefs.devices if dv.type == wanted]
        if not devs:
            return "CPU"
        for dv in prefs.devices:
            dv.use = dv.type == wanted
        scene.cycles.device = 'GPU'
        return wanted
    except Exception as e:  # noqa: BLE001 - fall back to CPU on any backend failure
        print("GPU setup failed, using CPU:", e)
        return "CPU"

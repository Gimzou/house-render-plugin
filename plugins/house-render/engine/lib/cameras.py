"""Named cameras from cameras.json."""
import bpy
from mathutils import Vector


def build(cameras, col):
    for c in cameras["cameras"]:
        name = "cam_" + c["name"]
        cd = bpy.data.cameras.new(name)
        cd.lens = c.get("lens", 35)
        if c.get("type") == "ortho":
            cd.type = 'ORTHO'
            cd.ortho_scale = c.get("ortho_scale", 20)
        cd.clip_start = c.get("clip_start", 0.1)
        ob = bpy.data.objects.new(name, cd)
        col.objects.link(ob)
        ob.location = c["location"]
        d = Vector(c["target"]) - ob.location
        up = 'Y' if abs(d.normalized().z) < 0.999 else 'X'  # straight-down plan cameras need another up axis
        ob.rotation_euler = d.to_track_quat('-Z', up).to_euler()
        if c.get("plan_up"):  # top-down: keep plan +Y at the top of the image
            ob.rotation_euler = (0, 0, 0)
        ob["resolution"] = c.get("resolution", [1280, 720])
        ob["note"] = c.get("note", "")
        ob["hero"] = bool(c.get("hero", False))
        ob["hide"] = ",".join(c.get("hide", []))  # collections hidden for this camera (e.g. ceiling)

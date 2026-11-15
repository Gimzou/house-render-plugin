"""Furniture from house/furniture.json. Block tier only for now (proxy/asset fall back to block)."""
import math
from . import geom
from .data import v
from . import proxies


def _variant_col(parent, group, option, shown):
    """Child collection 'var <group> = <option>'; hidden unless it is the chosen option.
    Toggle it with the eye icon in the Outliner (or the camera icon for renders)."""
    import bpy
    name = f"var {group} = {option}"
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    col.hide_render = not shown

    def find(lc):
        if lc.collection == col:
            return lc
        for c in lc.children:
            r = find(c)
            if r:
                return r
    lc = find(bpy.context.view_layer.layer_collection)
    if lc:
        lc.hide_viewport = not shown
    return col


def build(furn, mats, choices=None):
    """choices: {group: option} overrides the defaults in furn['variants']."""
    col = geom.collection("furniture")
    people = geom.collection("people")
    chosen = {g: (choices or {}).get(g, spec["default"]) for g, spec in furn.get("variants", {}).items()}
    for g, o in chosen.items():
        print(f"  variant {g} = {o}  (options: {', '.join(furn['variants'][g]['options'])})")
    for it in furn.get("items", []):
        var = it.get("variant")
        if var:
            g, o = var.split(":")
            vparent = people if it.get("proxy", "").startswith("person") else col
            target_col = _variant_col(vparent, g, o, chosen.get(g) == o)
        else:
            target_col = None
        w, d, h = (v(x) for x in it["size"])
        x, y = (v(c) for c in it["center"])
        z0 = v(it.get("base_z", 0.0))
        kind = it.get("proxy")
        if kind:
            target = target_col or (people if kind.startswith("person") else col)
            ob = proxies.build(it["id"], kind, (w, d, h), mats[it["material"]], target)
            ob.location = (x, y, z0)
        else:
            ob = geom.box(it["id"], (x, y, z0 + h / 2), (w, d, h), mats[it["material"]], target_col or col)
        ob.rotation_euler[2] = math.radians(it.get("rot_z", 0))
        ob["tier"] = "proxy" if kind else "block"
        ob["room"] = it.get("room", "")
        if var:
            ob["variant"] = var

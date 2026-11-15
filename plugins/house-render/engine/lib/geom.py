"""Geometry helpers: prisms, boxes, booleans, walls with openings, partitions."""
import bpy
import bmesh

import math

from .data import v, facade_frame


def collection(name, scene=None):
    scene = scene or bpy.context.scene
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    return col


def _link(ob, col):
    col.objects.link(ob)
    return ob


def prism(name, poly, z0, z1, mat, col):
    me = bpy.data.meshes.new(name)
    ob = _link(bpy.data.objects.new(name, me), col)
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z0)) for x, y in poly])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)],
                        vec=(0, 0, z1 - z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    return ob


def box(name, center, size, mat, col):
    """Axis-aligned box built from data (no operators, so it is deterministic)."""
    me = bpy.data.meshes.new(name)
    ob = _link(bpy.data.objects.new(name, me), col)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    ob.location = center
    ob.scale = size
    if mat:
        me.materials.append(mat)
    return ob


def boolean(target, cutter):
    md = target.modifiers.new("cut", 'BOOLEAN')
    md.operation, md.object, md.solver = 'DIFFERENCE', cutter, 'EXACT'
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="cut")


def edge_thicknesses(ground):
    """Per-footprint-edge wall thickness: 'wall_thickness' is one value or a list (edge i = vertex i -> i+1)."""
    t = v(ground["wall_thickness"])
    n = len(ground["footprint"])
    if isinstance(t, list):
        assert len(t) == n, f"wall_thickness list has {len(t)} values for {n} footprint edges"
        return [float(v(x)) for x in t]
    return [float(t)] * n


def facade_thickness(fr, ground):
    """Thickness of the footprint edge the facade lies on (default: the thickest wall)."""
    (ox, oy), u, _ = fr
    fp = ground["footprint"]
    ts = edge_thicknesses(ground)
    for i, (a, b) in enumerate(zip(fp, fp[1:] + fp[:1])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        cross = abs(dx * u[1] - dy * u[0]) / L
        off = abs((ox - a[0]) * dy - (oy - a[1]) * dx) / L
        if cross < 1e-6 and off < 0.02:
            return ts[i]
    return max(ts)


def inset_polygon(poly, t):
    """Inset a simple polygon with mitred corners (any corner angle). t = one thickness or one per edge."""
    n = len(poly)
    ts = t if isinstance(t, (list, tuple)) else [t] * n
    area2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1 if area2 > 0 else -1  # counter-clockwise -> interior on the left of each edge

    def offset_line(a, b, t):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = s * -dy / L, s * dx / L
        return (a[0] + nx * t, a[1] + ny * t), (dx, dy)

    lines = [offset_line(poly[i], poly[(i + 1) % n], ts[i]) for i in range(n)]
    res = []
    for i in range(n):
        (p, d), (q, e) = lines[i - 1], lines[i]
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-12:  # collinear edges
            res.append((round(q[0], 6), round(q[1], 6)))
            continue
        k = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        res.append((round(p[0] + d[0] * k, 6), round(p[1] + d[1] * k, 6)))
    return res


def opening_box(frame, pos, width, height, sill, depth, t, offset=None):
    """Centre, size and z-rotation of a box on a facade. offset = distance in from the outer face (default t/2)."""
    (ox, oy), u, n = frame
    zc = sill + height / 2
    o = t / 2 if offset is None else offset
    c = (ox + u[0] * pos + n[0] * o, oy + u[1] * pos + n[1] * o, zc)
    return c, (width, depth, height), math.atan2(u[1], u[0])


def oriented_box(name, center, size, rot, mat, col):
    ob = box(name, center, size, mat, col)
    ob.rotation_euler[2] = rot
    return ob


def build_walls(ground, level, mats, cols):
    h = v(level["wall_height"])
    outer = [tuple(p) for p in ground["footprint"]]
    inner = inset_polygon(outer, edge_thicknesses(ground))
    walls = prism("walls", outer, 0, h, mats["exterior_wall"], cols["structure"])
    core = prism("core", inner, -0.01, h + 0.1, mats["exterior_wall"], cols["structure"])
    boolean(walls, core)
    bpy.data.objects.remove(core)

    inset = ground["frame_inset"]
    for op in ground["openings"]:
        fr = facade_frame(ground["facades"][op["facade"]], outer)
        t = facade_thickness(fr, ground)
        w, hh, sill = v(op["width"]), v(op["height"]), v(op["sill"])
        c, s, rot = opening_box(fr, v(op["pos"]), w, hh, sill, t * 3, t)
        cutter = oriented_box("cut_" + op["id"], c, s, rot, None, cols["structure"])
        boolean(walls, cutter)
        bpy.data.objects.remove(cutter)
        if op["kind"] == "door":
            c2, s2, r2 = opening_box(fr, v(op["pos"]), w - 2 * inset, hh - 2 * inset, sill + inset, 0.05, t)
            oriented_box(op["id"], c2, s2, r2, mats["door"], cols["doors"])
        else:
            pane = v(ground.get("glass_pane_thickness", 0.05))
            c2, s2, r2 = opening_box(fr, v(op["pos"]), w - 2 * inset, hh - 2 * inset, sill + inset, pane, t)
            oriented_box(op["id"], c2, s2, r2, mats["glazing"], cols["glazing"])
    return walls


def build_partitions(ground, level, mats, cols):
    """Straight partitions, optionally with door openings. A door splits the wall into solid runs plus
    a lintel; an open sliding-pocket leaf sits inside the wall on the side with more room."""
    ti = v(ground["partition_thickness"])
    h = v(level["wall_height"])
    if level.get("ceiling", {}).get("enabled"):
        h -= 0.005  # top hidden inside the ceiling slab: no coplanar faces (roof seams) and no gap at the stairwell
    for p in ground["partitions"]:
        (x0, y0), (x1, y1) = p["from"], p["to"]
        along_x = abs(x1 - x0) >= abs(y1 - y0)
        a0, a1 = sorted((x0, x1) if along_x else (y0, y1))
        fixed = y0 if along_x else x0

        def seg(name, b0, b1, z0, z1, mat, thick=ti):
            c_al, c_z = (b0 + b1) / 2, (z0 + z1) / 2
            size_al = max(b1 - b0, 0.001)
            if along_x:
                box(name, (c_al, fixed, c_z), (size_al, thick, z1 - z0), mat, cols["structure"])
            else:
                box(name, (fixed, c_al, c_z), (thick, size_al, z1 - z0), mat, cols["structure"])

        cuts = []
        for d in p.get("doors", []):
            c, w, dh = v(d["center"]), d["width"], v(d["height"])
            cuts.append((c - w / 2, c + w / 2, dh, d))
        cuts.sort(key=lambda t: t[0])
        pos, i = a0, 0
        for b0, b1, dh, d in cuts:
            if b0 > pos:
                seg(f"{p['id']}_{i}", pos, b0, 0, h, mats["partition"]); i += 1
            seg(f"{d['id']}_lintel", b0, b1, dh, h, mats["partition"])
            if d.get("type") == "sliding_pocket":
                w = b1 - b0
                left_room, right_room = b0 - a0, a1 - b1
                if d.get("leaf_open", True):
                    l0 = b0 - w if left_room >= right_room else b1
                else:
                    l0 = b0
                seg(d["id"] + "_leaf", l0, l0 + w, 0, dh - 0.01, mats["door_leaf"], thick=0.04)
            if d.get("type") == "swing":
                leaf, sw = d.get("leaf", b1 - b0), v(d["swing"])
                hx = b1 - 0.02 if d.get("hinge", "end") == "end" else b0 + 0.02
                perp0, perp1 = sorted((fixed, fixed + sw * (leaf + ti / 2)))
                zc = (dh - 0.01) / 2
                if along_x:
                    box(d["id"] + "_leaf", (hx, (perp0 + perp1) / 2, zc), (0.04, perp1 - perp0, dh - 0.01),
                        mats["door_leaf"], cols["doors"])
                else:
                    box(d["id"] + "_leaf", ((perp0 + perp1) / 2, hx, zc), (perp1 - perp0, 0.04, dh - 0.01),
                        mats["door_leaf"], cols["doors"])
            pos = b1
        if pos < a1:
            seg(f"{p['id']}_{i}", pos, a1, 0, h, mats["partition"])
    cb = ground.get("chimney_breast")
    if cb and cb.get("enabled"):
        cx, cy = v(cb["center"][0]), v(cb["center"][1])
        box("chimney_breast", (cx, cy, h / 2), (cb["depth"], cb["width"], h), mats["chimney"], cols["structure"])


def build_ceiling(ground, level, mats, cols):
    c = level.get("ceiling", {})
    if not c.get("enabled"):
        return None
    z0 = v(c["clear_height"])
    # inner polygon: the wall ring keeps its own top face, so no overlapping coplanar faces (roof seams)
    poly = inset_polygon([tuple(p) for p in ground["footprint"]], edge_thicknesses(ground))
    return prism("ceiling", poly, z0, z0 + v(c["thickness"]), mats["ceiling"], collection("ceiling"))


def build_portals(ground, cols):
    """One area light per exterior window, flagged as a Cycles light portal, facing into the house.
    render.py hides this collection in EEVEE (which would treat them as real lights)."""
    from mathutils import Vector
    outer = [tuple(p) for p in ground["footprint"]]
    for op in ground["openings"]:
        if op["kind"] == "door":
            continue
        (ox, oy), u, n = facade_frame(ground["facades"][op["facade"]], outer)
        w, h, sill = v(op["width"]), v(op["height"]), v(op["sill"])
        ld = bpy.data.lights.new("portal_" + op["id"], 'AREA')
        ld.shape = 'RECTANGLE'
        ld.cycles.is_portal = True
        ob = bpy.data.objects.new("portal_" + op["id"], ld)
        cols["portals"].objects.link(ob)
        pos = v(op["pos"])
        ob.location = (ox + u[0] * pos - n[0] * 0.01, oy + u[1] * pos - n[1] * 0.01, sill + h / 2)
        ob.rotation_euler = Vector((n[0], n[1], 0)).to_track_quat('-Z', 'Y').to_euler()
        # local X/Y of the light after tracking: Y is world up, X is horizontal
        ld.size, ld.size_y = w, h


def build_blocks(ground, mats, cols):
    """Generic block-tier items: {id, center, size, rot_z (deg), material}."""
    import math
    col = collection("blocks")
    for b in ground.get("blocks", []):
        c = tuple(v(x) for x in b["center"])
        ob = box(b["id"], c, tuple(v(x) for x in b["size"]), mats[b["material"]], col)
        ob.rotation_euler[2] = math.radians(b.get("rot_z", 0))


def build_stairs(ground, level, mats, cols, slab):
    """Block-tier stairs. Up-flight: flight 1 solid to the floor, winders and flight 2 as treads with a
    soffit (waist). Cellar: floor opening cut in the slab plus the visible top run of steps."""
    st = ground.get("stairs")
    if not st:
        return
    col = collection("stairs")
    m = mats["stair"]
    up = st["up"]
    r = v(up["rise_total"]) / up["risers"]
    waist = v(up["waist"])

    def tread(n, x0, x1, y0, y1, solid):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
        top = n * r
        bot = 0 if solid else max(top - r - waist, 0)
        box(f"stair_{n:02d}", ((x0 + x1) / 2, (y0 + y1) / 2, (top + bot) / 2), (x1 - x0, y1 - y0, top - bot), m, col)

    f1 = up["flight1"]; a, b = f1["treads"]; k = b - a + 1
    step = (f1["from_x"] - f1["to_x"]) / k
    for i in range(k):
        tread(a + i, f1["from_x"] - step * i, f1["from_x"] - step * (i + 1), f1["y0"], f1["y1"], True)
    w = up["winders"]; a, b = w["treads"]; k = b - a + 1
    dy = (w["y1"] - w["y0"]) / k
    for i in range(k):
        tread(a + i, w["x0"], w["x1"], w["y0"] + dy * i, w["y0"] + dy * (i + 1), False)
    f2 = up["flight2"]; a, b = f2["treads"]; k = b - a + 1
    step = (f2["to_x"] - f2["from_x"]) / k
    for i in range(k):
        tread(a + i, f2["from_x"] + step * i, f2["from_x"] + step * (i + 1), f2["y0"], f2["y1"], False)

    c = st.get("cellar")
    if c:
        (ox0, oy0), (ox1, oy1) = c["opening"]["from"], c["opening"]["to"]
        ox0, ox1 = sorted((ox0, ox1)); oy0, oy1 = sorted((oy0, oy1))
        cut = box("cut_cellar", ((ox0 + ox1) / 2, (oy0 + oy1) / 2, -0.5), (ox1 - ox0, oy1 - oy0, 2.0), None, col)
        for target in [slab, bpy.data.objects.get("ground")] + [o for o in bpy.data.objects if o.name.startswith("floor_")]:
            if target:
                boolean(target, cut)
        bpy.data.objects.remove(cut)
        rr, zb = c["rise_total"] / v(c["risers"]), c["bottom_z"]

        def ctread(n, x0, x1, y0, y1):
            x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
            top = zb + n * rr
            box(f"cellar_{n:02d}", ((x0 + x1) / 2, (y0 + y1) / 2, (top + zb) / 2), (x1 - x0, y1 - y0, top - zb), m, col)

        f1 = c["flight1"]; a, b = f1["treads"]; k = b - a + 1
        step = (f1["from_x"] - f1["to_x"]) / k
        for i in range(k):
            ctread(a + i, f1["from_x"] - step * i, f1["from_x"] - step * (i + 1), f1["y0"], f1["y1"])
        w = c["winders"]; a, b = w["treads"]; k = b - a + 1
        dy = (w["y1"] - w["y0"]) / k
        for i in range(k):
            ctread(a + i, w["x0"], w["x1"], w["y0"] + dy * i, w["y0"] + dy * (i + 1))


def build_floors(ground, mats, cols, thickness=0.005):
    """One thin finish layer per room polygon, material from the room's 'finish' surface key."""
    col = collection("floors")
    for r in ground["rooms"]:
        f = r.get("finish")
        if f:
            prism("floor_" + r["id"], [tuple(p) for p in r["polygon"]], 0.0, thickness, mats[v(f)], col)


def build_outdoor(ground, mats, cols):
    """Terraces and balconies: {id, polygon, thickness, material, railing: {edges: [[i, j], ...] | "all",
    height, thickness, material}}. Railing runs along the listed polygon edges (vertex index pairs)."""
    col = collection("outdoor")
    for s in ground.get("outdoor", []):
        poly = [tuple(p) for p in s["polygon"]]
        th = v(s.get("thickness", 0.2))
        prism("slab_" + s["id"], poly, -th, 0.0, mats[s.get("material", "terrace")], col)
        r = s.get("railing")
        if not r:
            continue
        edges = r["edges"] if r["edges"] != "all" else [[i, (i + 1) % len(poly)] for i in range(len(poly))]
        h, rt = v(r["height"]), v(r["thickness"])
        for k, (i, j) in enumerate(edges):
            (x0, y0), (x1, y1) = poly[i], poly[j]
            L = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2  # centred on the slab edge
            oriented_box(f"rail_{s['id']}_{k}", (cx, cy, h / 2), (L + rt, rt, h), math.atan2(uy, ux),
                         mats[r.get("material", "railing")], col)

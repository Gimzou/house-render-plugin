"""Proxy-tier shapes built from boxes/spheres in local coords (W along X, D along Y, front = -Y, z up from 0).
The item's centre/rot_z place them. Sizes come from the item; people use typical adult dimensions."""
import bmesh
import bpy


def _box(bm, cx, cy, cz, sx, sy, sz):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for vert in r["verts"]:
        vert.co.x = cx + vert.co.x * sx
        vert.co.y = cy + vert.co.y * sy
        vert.co.z = cz + vert.co.z * sz


def _sphere(bm, cx, cy, cz, rad):
    r = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=rad)
    for vert in r["verts"]:
        vert.co.x += cx; vert.co.y += cy; vert.co.z += cz


def sofa(bm, w, d, h, seat_h=0.44, arm_w=0.18, arm_h=0.62, back_d=0.22):
    _box(bm, 0, 0, 0.09, w, d, 0.18)                                   # plinth/frame
    for s in (-1, 1):                                                  # arms
        _box(bm, s * (w / 2 - arm_w / 2), 0, arm_h / 2, arm_w, d, arm_h)
    _box(bm, 0, d / 2 - back_d / 2, h / 2, w - 2 * arm_w, back_d, h)  # back
    inner = w - 2 * arm_w
    n = 2 if inner < 2.0 else 3
    cw = inner / n
    for i in range(n):                                                 # seat cushions
        x = -inner / 2 + cw * (i + 0.5)
        _box(bm, x, -back_d / 2, (0.18 + seat_h) / 2, cw - 0.01, d - back_d, seat_h - 0.18)
        _box(bm, x, d / 2 - back_d - 0.08, seat_h + 0.2, cw - 0.01, 0.16, 0.4)  # back cushions


def person_standing(bm, height=1.75):
    k = height / 1.75
    for s in (-1, 1):
        _box(bm, s * 0.1 * k, 0, 0.43 * k, 0.14 * k, 0.16 * k, 0.86 * k)       # legs
        _box(bm, s * 0.25 * k, 0, 1.15 * k, 0.09 * k, 0.1 * k, 0.6 * k)        # arms
    _box(bm, 0, 0, 1.16 * k, 0.4 * k, 0.24 * k, 0.6 * k)                       # torso (shoulders 46 cm incl. arms)
    _box(bm, 0, 0, 1.5 * k, 0.1 * k, 0.1 * k, 0.1 * k)                         # neck
    _sphere(bm, 0, 0, 1.64 * k, 0.11 * k)                                      # head


def person_seated(bm, seat_h=0.44, height=1.75):
    k = height / 1.75
    hip_y = 0.05                                                                # pelvis toward the back
    for s in (-1, 1):
        _box(bm, s * 0.1 * k, hip_y - 0.25 * k, seat_h + 0.08, 0.14 * k, 0.5 * k, 0.15 * k)       # thighs
        _box(bm, s * 0.1 * k, hip_y - 0.5 * k, (seat_h + 0.08) / 2, 0.12 * k, 0.12 * k, seat_h + 0.08)  # shins
        _box(bm, s * 0.1 * k, hip_y - 0.57 * k, 0.04, 0.1 * k, 0.24 * k, 0.08)                 # feet
        _box(bm, s * 0.25 * k, hip_y - 0.05, seat_h + 0.45 * k, 0.09 * k, 0.1 * k, 0.55 * k)   # arms
    _box(bm, 0, hip_y + 0.02, seat_h + 0.4 * k, 0.4 * k, 0.24 * k, 0.6 * k)    # torso
    _sphere(bm, 0, hip_y + 0.02, seat_h + 0.88 * k, 0.11 * k)                  # head


BUILDERS = {"sofa": sofa, "person_standing": person_standing, "person_seated": person_seated}


def build(name, kind, size, mat, col):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    bm = bmesh.new()
    if kind == "sofa":
        sofa(bm, *size)
    else:
        BUILDERS[kind](bm)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    return ob

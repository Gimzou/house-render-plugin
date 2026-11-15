"""Material library -> bpy materials, and surface -> material mapping."""
import bpy


def _principled(name, spec):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*spec["color"], 1)
    b.inputs["Roughness"].default_value = spec.get("roughness", 0.8)
    b.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    if spec.get("emission"):
        b.inputs["Emission Color"].default_value = (*spec["emission"], 1)
        b.inputs["Emission Strength"].default_value = spec.get("emission_strength", 1.0)
    return m


def _glass(name, spec):
    """Thin architectural glass: transparent + Fresnel reflection. Shadow-transparent in Cycles and EEVEE.
    Back faces are fully transparent: Fresnel on a back face goes to total internal reflection at grazing
    angles, which made panes seen from inside look fogged or mirrored (glass tuning 2026-11-14)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    fres = nt.nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = 1.5
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*spec["color"], 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = spec.get("roughness", 0.05)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    front = nt.nodes.new("ShaderNodeMath")
    front.operation = 'SUBTRACT'
    front.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs["Backfacing"], front.inputs[1])
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = 'MULTIPLY'
    nt.links.new(fres.outputs[0], fac.inputs[0])
    nt.links.new(front.outputs[0], fac.inputs[1])
    nt.links.new(fac.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    # BLENDED: the dithered + ray-traced path speckled the interior seen through the panes in EEVEE
    # (glass tuning 2026-11-14). Panes are single sheets, so blended sorting is not an issue.
    m.surface_render_method = 'BLENDED'
    m.use_transparent_shadow = True
    return m


def build(materials):
    lib = {}
    for name, spec in materials["library"].items():
        lib[name] = _glass(name, spec) if spec.get("type") == "glass" else _principled(name, spec)
    return {surface: lib[name] for surface, name in materials["surfaces"].items()}

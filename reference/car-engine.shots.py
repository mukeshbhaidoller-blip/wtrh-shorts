# Shots for "Your Engine Explodes Thousands of Times a Minute" (how a car engine works). One function per line.
# Z up, metres. Cars drive along +Y; wheel axles along X. Person faces -Y at rot_z=0 (his right hand is on -X).
def dur(a, b): return (b - a) / FPS

_cyl = cyl
def cyl(*args, **kw):
    o = _cyl(*args, **kw)
    try: o.data.set_sharp_from_angle(angle=math.radians(35))
    except Exception:
        for p in o.data.polygons: p.use_smooth = False
    return o

# ---------------------------------------------------------------- materials
def mats():
    M = {}
    M['asphalt'] = mat_textured('Asphalt', ['asphalt_02', 'asphalt_04'], 0.35, (0.16, 0.16, 0.165))[0]
    M['floor'] = mat_textured('GarageFloor', ['concrete_floor_02'], 0.45, (0.45, 0.45, 0.44), rough=(0.35, 0.75), tint=(0.85, 0.85, 0.84))[0]
    M['brick'] = mat_textured('Brick', ['painted_brick'], 0.5, (0.7, 0.7, 0.68), rough=(0.8, 0.95))[0]
    M['rubber'] = tire_mat()
    M['rim'] = mat_simple('Rim', (0.62, 0.63, 0.65), 0.22, 1.0)[0]
    M['dark'] = mat_simple('DarkMetal', (0.03, 0.03, 0.032), 0.45, 0.6)[0]
    M['red'] = mat_simple('CaliperRed', (0.42, 0.025, 0.018), 0.42, 0.1, coat=0.25)[0]
    M['pad'] = mat_simple('PadFriction', (0.09, 0.08, 0.07), 0.9)[0]
    M['steel'] = mat_simple('Steel', (0.55, 0.56, 0.58), 0.3, 1.0)[0]
    M['glass'] = mat_glass('Glass', (0.96, 0.98, 1.0), 0.02)[0]
    M['fluid'] = mat_simple('BrakeFluid', (0.85, 0.5, 0.1), 0.05, trans=0.85, ior=1.45)[0]
    M['studio'] = mat_simple('StudioFloor', (0.04, 0.04, 0.045), 0.5)[0]
    M['cabglass'] = mat_simple('CarGlass', (0.015, 0.017, 0.02), 0.04, coat=1.0)[0]
    M['grass'] = mat_textured('Grass', ['aerial_grass_rock'], 0.12, (0.18, 0.26, 0.09), rough=(0.85, 1.0), bump=0.8, tint=(0.55, 0.85, 0.45))[0]
    return M

def tire_mat():
    m, nt, p = nodes_mat('Tire')
    p.inputs['Base Color'].default_value = (0.025, 0.025, 0.027, 1); p.inputs['Roughness'].default_value = 0.78
    tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 300
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def disc_mat(name='Disc', glow=0.0):
    """Cast-iron rotor with concentric machining rings; returns (material, emission-strength socket) for the heat glow."""
    m, nt, p = nodes_mat(name)
    p.inputs['Metallic'].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sx.inputs[0])
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(sx.outputs['Y'], cb.inputs['Y']); nt.links.new(sx.outputs['Z'], cb.inputs['Z'])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(cb.outputs[0], ln.inputs[0])
    # rings: sin of radius
    mr = nt.nodes.new('ShaderNodeMath'); mr.operation = 'MULTIPLY'; mr.inputs[1].default_value = 2400.0; nt.links.new(ln.outputs['Value'], mr.inputs[0])
    sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(mr.outputs[0], sn.inputs[0])
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 18; n.inputs['Detail'].default_value = 4
    nt.links.new(ln.outputs['Value'], n.inputs['W']) if 'W' in n.inputs else None
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.08; ad.inputs[2].default_value = 0.3
    nt.links.new(sn.outputs[0], ad.inputs[0]); nt.links.new(ad.outputs[0], p.inputs['Roughness'])
    hat = nt.nodes.new('ShaderNodeMapRange'); hat.inputs['From Min'].default_value = 0.068; hat.inputs['From Max'].default_value = 0.072
    nt.links.new(ln.outputs['Value'], hat.inputs['Value'])
    cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; nt.links.new(hat.outputs['Result'], cm.inputs['Factor'])
    cm.inputs[6].default_value = (0.12, 0.11, 0.1, 1); cm.inputs[7].default_value = (0.36, 0.36, 0.37, 1)
    nt.links.new(cm.outputs[2], p.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08; bp.inputs['Distance'].default_value = 0.0005
    nt.links.new(sn.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    rm = nt.nodes.new('ShaderNodeMapRange'); rm.inputs['From Min'].default_value = 0.08; rm.inputs['From Max'].default_value = 0.11
    nt.links.new(ln.outputs['Value'], rm.inputs['Value'])
    gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'; nt.links.new(rm.outputs['Result'], gm.inputs[0]); nt.links.new(n.outputs['Fac'], gm.inputs[1])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(gm.outputs[0], mx.inputs['Factor'])
    mx.inputs[6].default_value = (0, 0, 0, 1); mx.inputs[7].default_value = (1.0, 0.16, 0.01, 1)
    nt.links.new(mx.outputs[2], inp(p, 'Emission Color', 'Emission'))
    es = inp(p, 'Emission Strength'); es.default_value = glow
    return m, es

def key_glow(es, pts): key_socket(es, pts)

# ---------------------------------------------------------------- brake / wheel kit
def tube(name, pts, r, mat, verts=12):
    out = []
    for p0, p1 in zip(pts[:-1], pts[1:]):
        p0 = Vector(p0); p1 = Vector(p1); L = (p1 - p0).length
        c = cyl(name, r, L, (0, 0, 0), mat, verts=verts)
        c.location = (p0 + p1) / 2; c.rotation_euler = (p1 - p0).to_track_quat('Z', 'Y').to_euler(); out.append(c)
        out.append(sphere(name + 'J', r, tuple(p1), mat, sub=1))
    return out

def rotor(M, dm, r=0.165, th=0.028, vented=True, cut=False):
    """Vented disc, axle along X, centred at the origin of the returned rig."""
    rig = bpy.data.objects.new('Rotor', None); link(rig); P = []
    pt = th * 0.3
    for s in (-1, 1):
        P.append(cyl('Plate', r, pt, (s * (th / 2 - pt / 2), 0, 0), dm, rot=(0, math.radians(90), 0), verts=96))
    P.append(cyl('Hat', r * 0.48, th * 1.6, (0.02, 0, 0), dm, rot=(0, math.radians(90), 0), verts=64))
    if vented:
        n = 36
        for k in range(n):
            a = 2 * math.pi * k / n
            v = box('Vane', (th - 2 * pt, r * 0.42, 0.006), (0, 0, 0), M['dark'])
            rr = r * 0.74; v.location = (0, rr * math.cos(a), rr * math.sin(a)); v.rotation_euler = (a + math.radians(90 + 18), 0, 0)
            P.append(v)
    for k in range(5):
        a = 2 * math.pi * k / 5
        P.append(cyl('Stud', 0.007, 0.07, (0.05, 0.055 * math.cos(a), 0.055 * math.sin(a)), M['steel'], rot=(0, math.radians(90), 0), verts=12))
    for o in P: o.parent = rig
    return rig

def caliper(M, side=1, r=0.165, ang=120, pads=True):
    """Red floating caliper straddling the rotor rim at angle ang (deg, 90 = top). Returns (rig, [pad objects])."""
    rig = bpy.data.objects.new('Caliper', None); link(rig)
    a = math.radians(ang); rc = r - 0.035
    rig.location = (0, rc * math.cos(a), rc * math.sin(a)); rig.rotation_euler = (a - math.radians(90), 0, 0)
    P = []
    P.append(box('CalBody', (0.035, 0.13, 0.075), (side * 0.035, 0, 0.012), M['red'], bevel=0.012))
    P.append(box('CalBack', (0.03, 0.12, 0.07), (-side * 0.032, 0, 0.012), M['red'], bevel=0.01))
    P.append(box('CalBridge', (0.1, 0.1, 0.03), (0, 0, 0.055), M['red'], bevel=0.01))
    P.append(cyl('Bleeder', 0.005, 0.03, (side * 0.03, 0.05, 0.06), M['steel'], verts=8))
    pl = []
    if pads:
        for s in (-1, 1):
            pd = box('Pad', (0.012, 0.11, 0.05), (s * 0.022, 0, 0.0), M['pad'], bevel=0.003); pl.append((pd, s)); P.append(pd)
    for o in P: o.parent = rig
    return rig, pl

def squeeze(pads, t0, t1, gap=0.022, closed=0.0155, pulses=None):
    for pd, s in pads:
        if pulses:
            pts = [(0, Vector((s * gap, 0, 0)))]
            for (ta, tb) in pulses: pts += [(ta, Vector((s * gap, 0, 0))), (ta + 0.04, Vector((s * closed, 0, 0))), (tb, Vector((s * closed, 0, 0))), (tb + 0.04, Vector((s * gap, 0, 0)))]
            key(pd, 'location', pts, interp='LINEAR')
        else:
            key(pd, 'location', [(0, Vector((s * gap, 0, 0))), (t0, Vector((s * gap, 0, 0))), (t1, Vector((s * closed, 0, 0)))])

def wheel(M, loc, side=1, r=0.33, w=0.22, dm=None, cal_ang=110, name='Wheel'):
    """Road wheel; outer face towards side*X. Returns (rig, spin) — rotate spin about X (negative = rolling +Y)."""
    rig = bpy.data.objects.new(name, None); link(rig); rig.location = loc
    spin = bpy.data.objects.new('Spin', None); link(spin); spin.parent = rig
    tr = 0.075
    bpy.ops.mesh.primitive_torus_add(major_radius=r - tr, minor_radius=tr, major_segments=96, minor_segments=24)
    t = bpy.context.active_object; t.name = 'Tire'; t.rotation_euler = (0, math.radians(90), 0); t.scale = (1, 1, w / (2 * tr))
    bpy.ops.object.shade_smooth(); t.data.materials.append(M['rubber']); t.parent = spin
    bpy.ops.mesh.primitive_torus_add(major_radius=r - 2 * tr + 0.01, minor_radius=0.012, major_segments=96, minor_segments=12)
    lip = bpy.context.active_object; lip.rotation_euler = (0, math.radians(90), 0); lip.location = (side * w * 0.3, 0, 0)
    bpy.ops.object.shade_smooth(); lip.data.materials.append(M['rim']); lip.parent = spin
    rb = cyl('Barrel', r - 2 * tr + 0.005, w * 0.85, (0, 0, 0), M['rim'], rot=(0, math.radians(90), 0), verts=96)
    rb.parent = spin
    for o in [rb]:
        # hollow out the barrel so the rotor shows between the spokes
        c = cyl('BarrelCut', r - 2 * tr - 0.008, w * 0.9, (0, 0, 0), None, rot=(0, math.radians(90), 0), verts=96); c.hide_render = True; c.display_type = 'WIRE'
        c.parent = spin
        md = o.modifiers.new('hollow', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c
    rr = r - 2 * tr
    for k in range(5):
        a = 2 * math.pi * k / 5
        s_ = box('Spoke', (0.02, 0.045, rr - 0.04), (0, 0, 0), M['rim'], bevel=0.006)
        s_.parent = spin; s_.location = (side * w * 0.33, (rr / 2 + 0.02) * math.cos(a), (rr / 2 + 0.02) * math.sin(a)); s_.rotation_euler = (a - math.radians(90), 0, 0)
    hc = cyl('HubCap', 0.05, 0.03, (side * w * 0.35, 0, 0), M['rim'], rot=(0, math.radians(90), 0), verts=32); hc.parent = spin
    dm = dm or disc_mat()[0]
    rt = rotor(M, dm, r=rr * 0.85); rt.parent = spin; rt.location = (-side * 0.0, 0, 0)
    rt.scale = (side, 1, 1)
    cr, pads = caliper(M, side, r=rr * 0.85, ang=cal_ang)
    cr.parent = rig
    bp = cyl('Backplate', rr * 0.8, 0.004, (-side * 0.06, 0, 0), M['dark'], rot=(0, math.radians(90), 0), verts=64); bp.parent = rig
    return rig, spin

def roll(spin, pts_y, r=0.33):
    """Key the wheel spin from a list of (t, distance travelled)."""
    key(spin, 'rotation_euler', [(t, Vector((-y / r, 0, 0))) for t, y in pts_y], interp='LINEAR')

TAIL = {}
def car(M, color=(0.03, 0.045, 0.07), dm=None, name='Car', lights=True):
    """Simple hatchback; origin on the ground at the body centre, nose +Y. Returns (rig, body, wheels{fl,fr,rl,rr})."""
    rig = bpy.data.objects.new(name, None); link(rig)
    body = bpy.data.objects.new('Body', None); link(body); body.parent = rig
    pm, _ = mat_simple('CarPaint', color, 0.25, 0.55, coat=1.0)
    lo = box('Lower', (1.8, 4.3, 0.62), (0, 0, 0.64), pm, bevel=0.12, segs=5)
    for y in (-1.33, 1.38):
        c = cyl('ArchCut', 0.385, 2.4, (0, y, 0.33), None, rot=(0, math.radians(90), 0), verts=64); c.hide_render = True; c.display_type = 'WIRE'
        md = lo.modifiers.new('arch', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c; c.parent = body
    cab = box('Cabin', (1.62, 2.4, 0.56), (0, -0.25, 1.2), M['cabglass'], bevel=0.16, segs=5)
    tp_ = cab.modifiers.new('taper', 'SIMPLE_DEFORM'); tp_.deform_method = 'TAPER'; tp_.factor = -0.55; tp_.deform_axis = 'Z'
    cab.modifiers.move(len(cab.modifiers) - 1, 0)
    roof = box('Roof', (1.22, 1.55, 0.06), (0, -0.28, 1.47), pm, bevel=0.03)
    for o in (lo, cab, roof): o.parent = body
    for sx in (-1, 1):
        box('Mirror', (0.18, 0.08, 0.1), (sx * 0.95, 0.75, 1.05), pm, bevel=0.03).parent = body
    if lights:
        hm, _ = mat_emit('Head', (1, 0.95, 0.85), 6); tm, tp = mat_emit('Tail', (1, 0.03, 0.02), 1.5)
        for sx in (-1, 1):
            box('HeadL', (0.4, 0.05, 0.1), (sx * 0.6, 2.14, 0.8), hm).parent = body
            box('TailL', (0.38, 0.05, 0.1), (sx * 0.62, -2.14, 0.86), tm).parent = body
        TAIL[body.name] = tp.inputs['Strength']
    W = {}
    for k, (x, y) in dict(fl=(-0.8, 1.38), fr=(0.8, 1.38), rl=(-0.8, -1.33), rr=(0.8, -1.33)).items():
        rg, sp = wheel(M, (x, y, 0.33), side=(1 if x > 0 else -1), dm=dm, name='W' + k)
        rg.parent = rig; W[k] = (rg, sp)
    return rig, body, W

def garage(M, lamp=900):
    plane('Floor', 30, 30, (0, 0, 0), M['floor'])
    box('BackWall', (14, 0.25, 4), (0, 4.0, 2), M['brick']); box('SideWall', (0.25, 14, 4), (-4.5, 0, 2), M['brick'])
    lm = mat_emit('Tube', (1, 0.97, 0.92), 18)[0]
    for x in (-1.2, 1.2):
        box('Fixture', (0.12, 1.4, 0.05), (x, 0.5, 3.2), lm); light('AREA', (x, 0.5, 3.15), lamp, (1, 0.96, 0.9), 1.4)
    bench = box('Bench', (2.2, 0.7, 0.9), (2.2, 3.4, 0.45), mat_simple('BenchPaint', (0.06, 0.07, 0.08), 0.45, 0.5)[0], bevel=0.01)
    box('BenchTop', (2.24, 0.74, 0.04), (2.2, 3.4, 0.92), mat_textured('BenchWood', ['rough_wood', 'plywood'], 0.8, (0.35, 0.25, 0.16))[0])
    box('Toolboard', (2.0, 0.04, 1.0), (2.2, 3.85, 1.6), mat_simple('Pegboard', (0.08, 0.08, 0.085), 0.7)[0])
    world_hdri('studio_small_09', 0.25, 0, 'studio')

def studio(M, key_e=420):
    global _hide
    world_hdri('studio_small_09', 0.3, 0, 'studio')
    plane('Floor', 30, 30, (0, 0, 0), M['studio'])
    for (loc, rot) in (((-3.0, 0, 3), (0, math.radians(90), 0)), ((0, 3.0, 3), (math.radians(90), 0, 0)), ((3.0, 0, 3), (0, math.radians(90), 0))):
        w_ = plane('Backdrop', 12, 12, loc, M['studio']); w_.rotation_euler = rot
    k = light('AREA', (-1.6, -2.2, 1.9), key_e, (1, 0.96, 0.9), 2.0); aim(k, (0, 0, 0.2))
    rl = light('AREA', (1.8, 1.8, 1.6), key_e * 0.6, (0.85, 0.9, 1.0), 1.6); aim(rl, (0, 0, 0.2))
    for l in (k, rl):
        try: l.visible_camera = False
        except Exception: pass

def smoke(loc, t0, t1, n=10, seed=1, rise=0.6, size=0.12, col=(0.75, 0.75, 0.75), dens=1.2):
    random.seed(seed)
    m = bpy.data.materials.new('Smoke'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*col, 1); v.inputs['Density'].default_value = dens; nt.links.new(v.outputs['Volume'], o.inputs['Volume'])
    for i in range(n):
        tb = t0 + (t1 - t0) * i / n
        s = sphere('Puff', size, loc, m, sub=2)
        p0 = Vector(loc) + Vector((random.uniform(-0.03, 0.03), random.uniform(-0.05, 0.05), 0))
        p1 = p0 + Vector((random.uniform(-0.15, 0.15), random.uniform(-0.3, 0.1), rise))
        key(s, 'location', [(tb, p0), (tb + 1.2, p1)], interp='LINEAR')
        key(s, 'scale', [(0, Vector((0, 0, 0))), (tb - 0.01, Vector((0, 0, 0))), (tb, Vector((0.4, 0.4, 0.4))), (tb + 1.2, Vector((1.8, 1.8, 1.8))), (tb + 1.25, Vector((0, 0, 0)))])

def brake_y(t, y0, v0, tb, dec):
    """Distance along Y: constant v0 until tb, then constant deceleration dec until stop."""
    if t <= tb: return y0 + v0 * t
    ts = v0 / dec; dt = min(t - tb, ts)
    return y0 + v0 * tb + v0 * dt - 0.5 * dec * dt * dt


# ================================================================ engine kit
# One cylinder unit in its own rig: crank axis along X at the rig origin, cylinder up +Z, cut-away open towards -Y.
# Units are 0.095 wide in X so four of them make an inline-4.
ER, ECR, ERL = 0.043, 0.043, 0.145          # bore radius, crank throw, rod length
DECK, CTOP = 0.232, 0.25                    # block deck, combustion chamber roof (local z)
TAU = 2 * math.pi

def emats(M):
    M['alu'] = mat_simple('CastAlu', (0.5, 0.51, 0.52), 0.5, 1.0)[0]
    M['cut'] = mat_simple('CutFace', (0.72, 0.73, 0.74), 0.3, 1.0)[0]
    M['pistonm'] = mat_simple('PistonAlu', (0.78, 0.78, 0.77), 0.22, 1.0)[0]
    M['ring'] = mat_simple('Ring', (0.08, 0.08, 0.085), 0.3, 1.0)[0]
    M['forged'] = mat_simple('Forged', (0.42, 0.43, 0.45), 0.32, 1.0)[0]
    M['bore'] = mat_simple('Bore', (0.45, 0.46, 0.47), 0.32, 1.0)[0]
    M['ceramic'] = mat_simple('Ceramic', (0.92, 0.91, 0.88), 0.25, sss=0.1)[0]
    M['pan'] = mat_simple('PanBlack', (0.025, 0.025, 0.028), 0.4, 0.5, coat=0.4)[0]
    M['enginepaint'] = mat_simple('EnginePaint', (0.05, 0.06, 0.08), 0.35, 0.4, coat=0.6)[0]
    return M

def vol_mat(name, col, dens, ecol=(1, 0.45, 0.08), estr=0.0, aniso=0.0, wisp=0.0, nscale=55):
    """Volume material. Returns (mat, node) where node.inputs['Density'] / ['Emission Strength'] can be keyed.
    wisp>0: density and emission are modulated by 3D noise so the gas looks like swirling haze, not a solid block."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*col, 1); v.inputs['Density'].default_value = dens
    v.inputs['Emission Color'].default_value = (*ecol, 1); v.inputs['Emission Strength'].default_value = estr
    v.inputs['Anisotropy'].default_value = aniso
    out = v
    if wisp > 0:
        # a proxy node holds the keyable values; the real volume gets them times noise
        prox = nt.nodes.new('ShaderNodeVolumePrincipled'); prox.inputs['Density'].default_value = dens
        prox.inputs['Emission Strength'].default_value = estr
        tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = nscale; n.inputs['Detail'].default_value = 5
        try: n.inputs['W'].default_value = 0.0
        except Exception: pass
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.38; mr.inputs['From Max'].default_value = 0.62
        mr.inputs['To Min'].default_value = 1.0 - wisp; mr.inputs['To Max'].default_value = 1.0 + wisp
        nt.links.new(n.outputs['Fac'], mr.inputs['Value'])
        for nm in ('Density', 'Emission Strength'):
            vn = nt.nodes.new('ShaderNodeValue'); vn.label = nm
            mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.use_clamp = False
            nt.links.new(vn.outputs[0], mu.inputs[0]); nt.links.new(mr.outputs['Result'], mu.inputs[1])
            mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; mx.inputs[1].default_value = 0.0
            nt.links.new(mu.outputs[0], mx.inputs[0]); nt.links.new(mx.outputs[0], v.inputs[nm])
            vn.outputs[0].default_value = prox.inputs[nm].default_value
            prox[nm] = vn.name
        class P:  # tiny adapter: .inputs['Density'] -> the Value node output socket
            pass
        P.inputs = {nm: nt.nodes[prox[nm]].outputs[0] for nm in ('Density', 'Emission Strength')}
        nt.nodes.remove(prox)
        out = P
    nt.links.new(v.outputs['Volume'], o.inputs['Volume'])
    return m, out

def bool_cut(o, cutter, op='DIFFERENCE'):
    md = o.modifiers.new('b', 'BOOLEAN'); md.operation = op; md.object = cutter
    try: md.solver = 'EXACT'
    except Exception: pass
    return md

def hidden(o): o.hide_render = True; o.display_type = 'WIRE'; return o

def engine_unit(M, rig_parent, x=0.0, pin_off=0.0, cyc=0.0, cut=True, crank=True, head=True, name='U', fire_e=1.0):
    """Returns dict of animated parts. pin_off: crank pin angle offset; cyc: 4-stroke cycle offset (0 or 2pi)."""
    U = dict(pin_off=pin_off, cyc=cyc, x=x, fire_e=fire_e)
    g = bpy.data.objects.new(name, None); link(g); g.parent = rig_parent; g.location = (x, 0, 0); U['g'] = g
    def add(o): o.parent = g; return o
    W = 0.0475
    cutter = None
    if cut:
        cutter = add(hidden(box('Cut', (0.2, 0.2, 0.8), (0, -0.1, 0.1))))
    blk = add(box('Block', (2 * W, 0.13, DECK - 0.06), (0, 0, (DECK + 0.06) / 2), M['alu']))
    bore = add(hidden(cyl('BoreCut', ER + 0.0008, 0.3, (0, 0, DECK), verts=96)))
    bool_cut(blk, bore)
    if cutter: bool_cut(blk, cutter)
    if cut:   # shiny bore wall (back half only)
        bw = add(cyl('BoreWall', ER + 0.0009, DECK - 0.07, (0, 0, (DECK + 0.07) / 2), M['bore'], verts=96)); bool_cut(bw, cutter)
        ins = add(hidden(cyl('BoreIn', ER + 0.0006, 0.4, (0, 0, DECK), verts=96))); bool_cut(bw, ins)
    # crankcase back wall + oil pan
    add(box('CaseBack', (2 * W, 0.04, 0.15), (0, 0.05, -0.015), M['alu']))
    if not cut: add(box('CaseFront', (2 * W, 0.04, 0.15), (0, -0.05, -0.015), M['alu']))
    add(box('Pan', (2 * W, 0.14, 0.055), (0, 0, -0.115), M['pan'], bevel=0.004))
    if head:
        hd = add(box('Head', (2 * W, 0.13, 0.07), (0, 0, DECK + 0.035), M['alu']))
        ch = add(hidden(cyl('ChamberCut', ER, CTOP - DECK + 0.002, (0, 0, (DECK + CTOP) / 2 - 0.001), verts=96))); bool_cut(hd, ch)
        if cutter: bool_cut(hd, cutter)
        cv = add(box('Cover', (2 * W - 0.004, 0.11, 0.035), (0, 0.0, DECK + 0.07 + 0.0175), M['enginepaint'], bevel=0.006))
        if cutter: bool_cut(cv, cutter)
        # spark plug
        add(cyl('PlugThread', 0.006, 0.04, (0, 0, CTOP + 0.018), M['steel'], verts=24))
        add(cyl('PlugHex', 0.009, 0.014, (0, 0, DECK + 0.075), M['steel'], verts=6))
        add(cyl('PlugCeramic', 0.0058, 0.05, (0, 0, DECK + 0.105), M['ceramic'], verts=32))
        add(cyl('PlugCap', 0.0035, 0.012, (0, 0, DECK + 0.135), M['steel'], verts=16))
        add(box('Electrode', (0.002, 0.004, 0.004), (0.0015, 0, CTOP - 0.001), M['steel']))
        sm, sp = mat_emit('Spark', (0.6, 0.75, 1.0), 0.0)
        U['spark'] = sp.inputs['Strength']; add(sphere('SparkGlow', 0.0035, (0, 0, CTOP - 0.0025), sm, sub=2))
        # valves (intake -X, exhaust +X)
        U['valves'] = []
        for vx in (-0.02, 0.02):
            vg = bpy.data.objects.new('Valve', None); link(vg); vg.parent = g; vg.location = (vx, 0, 0)
            cyl('VHead', 0.0135, 0.0025, (0, 0, CTOP - 0.0018), M['forged'], verts=48).parent = vg
            cyl('VStem', 0.0028, 0.085, (0, 0, CTOP + 0.042), M['forged'], verts=16).parent = vg
            cyl('VCap', 0.008, 0.003, (0, 0, DECK + 0.07 + 0.012), M['steel'], verts=24).parent = vg
            U['valves'].append(vg)
    # piston
    pg = bpy.data.objects.new('PistonG', None); link(pg); pg.parent = g; U['piston'] = pg
    cyl('Piston', ER - 0.0009, 0.065, (0, 0, 0.0075), M['pistonm'], verts=96).parent = pg
    for k, dz in enumerate((0.032, 0.0255, 0.019)):
        cyl('Ring', ER - 0.0004, 0.0022, (0, 0, dz), M['ring'], verts=96).parent = pg
    # connecting rod (origin at the piston pin, hangs down -Z)
    rg = bpy.data.objects.new('RodG', None); link(rg); rg.parent = g; U['rod'] = rg
    box('Rod', (0.012, 0.016, ERL - 0.02), (0, 0, -ERL / 2), M['forged'], bevel=0.003).parent = rg
    cyl('SmallEnd', 0.011, 0.014, (0, 0, 0), M['forged'], rot=(0, math.radians(90), 0), verts=32).parent = rg
    cyl('BigEnd', 0.022, 0.018, (0, 0, -ERL), M['forged'], rot=(0, math.radians(90), 0), verts=48).parent = rg
    box('Cap', (0.018, 0.05, 0.012), (0, 0, -ERL - 0.018), M['forged'], bevel=0.003).parent = rg
    # crankshaft piece
    if crank:
        cg = bpy.data.objects.new('CrankG', None); link(cg); cg.parent = g; U['crank'] = cg
        cyl('Journal', 0.02, 2 * W, (0, 0, 0), M['steel'], rot=(0, math.radians(90), 0), verts=48).parent = cg
        cyl('Pin', 0.019, 0.022, (0, 0, ECR), M['steel'], rot=(0, math.radians(90), 0), verts=48).parent = cg
        for sx in (-1, 1):
            w_ = box('Web', (0.01, 0.05, 0.075), (sx * 0.016, 0, ECR / 2 - 0.006), M['forged'], bevel=0.004); w_.parent = cg
            cw = cyl('Counter', 0.055, 0.01, (sx * 0.016, 0, 0), M['forged'], rot=(0, math.radians(90), 0), verts=48); cw.parent = cg
            ccut = hidden(box('CwCut', (0.03, 0.2, 0.2), (sx * 0.016, 0, 0.1))); ccut.parent = cg; bool_cut(cw, ccut)
    # gases inside the cylinder (resized per frame to sit between crown and chamber roof)
    fm, fv = vol_mat('Fire', (0.2, 0.1, 0.05), 0.4, (1.0, 0.33, 0.04), 0.0, wisp=1.0, nscale=80)
    chm, chv = vol_mat('Charge', (0.55, 0.75, 1.0), 0.0, (0.35, 0.6, 1.0), 0.0, wisp=1.0, nscale=70)
    exm, exv = vol_mat('Exhaust', (0.62, 0.6, 0.57), 0.0, wisp=1.0, nscale=70)
    U['gas'] = []
    for k, (nm, mt) in enumerate((('FireV', fm), ('ChargeV', chm), ('ExhV', exm))):
        o = cyl(nm, ER - 0.0012 - 0.0009 * k, 1.0, (0, 0, 0), mt, verts=48); o.parent = g; U['gas'].append(o)
    U['fire'] = fv.inputs['Emission Strength']; U['charge'] = chv; U['exh'] = exv.inputs['Density']
    U['flash'] = light('POINT', (x, -0.03, DECK + 0.002), 0.0, (1, 0.4, 0.1), 0.02); U['flash'].parent = rig_parent
    U['flash'].location = (x, -0.035, DECK - 0.005)
    return U

def stroke_state(phi):
    """phi = cycle angle (0 = TDC start of intake, 2pi = firing TDC). Returns dict of visual levels 0..1."""
    p = phi % (2 * TAU)
    s = dict(iv=0.0, ev=0.0, fire=0.0, charge=0.0, exh=0.0, spark=0.0)
    if p < math.pi: s['iv'] = math.sin(p); s['charge'] = p / math.pi
    elif p < TAU: s['charge'] = 1.0
    if TAU - 0.12 < p < TAU + 0.06: s['spark'] = 1.0
    if p >= TAU:
        q = p - TAU
        s['fire'] = math.exp(-q * 2.2) if q < 2.6 else 0.0
        s['exh'] = min(1.0, q / 0.8) if p < TAU + math.pi else 1.0 - (p - TAU - math.pi) / math.pi
    if p >= TAU + math.pi: s['ev'] = math.sin(p - TAU - math.pi)
    if p < 0.25 * math.pi: s['exh'] = max(s['exh'], 0.0)
    return s

def run_engine(units, theta, d, step=1, fire_l=1.0, gas=True, shake=None):
    """theta(t) -> crank angle (rad). Keys every frame (linear)."""
    n = round(d * FPS)
    for U in units:
        for f in range(0, n + 1, step):
            t = f / FPS; th = theta(t) + U['pin_off']; phi = theta(t) + U['pin_off'] + U['cyc']
            zp = ECR * math.cos(th) + math.sqrt(ERL ** 2 - (ECR * math.sin(th)) ** 2)
            fr = F(t)
            U['piston'].location = (0, 0, zp); U['piston'].keyframe_insert('location', frame=fr)
            U['rod'].location = (0, 0, zp); U['rod'].rotation_euler = (math.asin(-ECR * math.sin(th) / ERL), 0, 0)
            U['rod'].keyframe_insert('location', frame=fr); U['rod'].keyframe_insert('rotation_euler', frame=fr)
            if 'crank' in U: U['crank'].rotation_euler = (th, 0, 0); U['crank'].keyframe_insert('rotation_euler', frame=fr)
            s = stroke_state(phi)
            if 'valves' in U:
                for vg, k in zip(U['valves'], ('iv', 'ev')):
                    vg.location = (vg.location[0], 0, -0.008 * s[k]); vg.keyframe_insert('location', frame=fr)
                U['spark'].default_value = 400.0 * s['spark']; U['spark'].keyframe_insert('default_value', frame=fr)
            crown = zp + 0.04
            for o in U['gas']:
                o.location = (0, 0, (crown + CTOP) / 2); o.scale = (1, 1, max(0.002, CTOP - crown))
                o.keyframe_insert('location', frame=fr); o.keyframe_insert('scale', frame=fr)
            fe = s['fire'] * U['fire_e'] if gas else 0.0
            U['fire'].default_value = 70.0 * fe; U['fire'].keyframe_insert('default_value', frame=fr)
            U['flash'].data.energy = 5.0 * fire_l * fe; U['flash'].data.keyframe_insert('energy', frame=fr)
            cd = U['charge'].inputs['Density']; ce = U['charge'].inputs['Emission Strength']
            cd.default_value = (10.0 * s['charge']) if gas else 0.0; cd.keyframe_insert('default_value', frame=fr)
            ce.default_value = (2.5 * s['charge']) if gas else 0.0; ce.keyframe_insert('default_value', frame=fr)
            U['exh'].default_value = (16.0 * s['exh']) if gas else 0.0; U['exh'].keyframe_insert('default_value', frame=fr)
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            for fc in fcurves_of(o.animation_data.action):
                for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    for blk in list(bpy.data.lights) + list(bpy.data.materials):
        ad = blk.animation_data if hasattr(blk, 'animation_data') else None
        nt = getattr(blk, 'node_tree', None)
        for a_ in [ad, nt.animation_data if nt else None]:
            if a_ and a_.action:
                for fc in fcurves_of(a_.action):
                    for k in fc.keyframe_points: k.interpolation = 'LINEAR'

def single(M, loc=(0, 0, 0.145), rot_z=0.0, **kw):
    rig = bpy.data.objects.new('Engine', None); link(rig); rig.location = loc; rig.rotation_euler = (0, 0, rot_z)
    U = engine_unit(M, rig, **kw); return rig, U

def inline4(M, loc=(0, 0, 0.145), rot_z=0.0, cut=True):
    rig = bpy.data.objects.new('Engine4', None); link(rig); rig.location = loc; rig.rotation_euler = (0, 0, rot_z)
    spec = [(0.0, 0.0), (math.pi, 0.0), (math.pi, TAU), (0.0, TAU)]   # firing order 1-3-4-2
    us = [engine_unit(M, rig, x=(i - 1.5) * 0.095, pin_off=po, cyc=cy, cut=cut, name=f'U{i}') for i, (po, cy) in enumerate(spec)]
    return rig, us

def dark_studio(M, key_e=120, fill=0.12):
    world_hdri('studio_small_09', fill, 0, 'studio')
    plane('Floor', 30, 30, (0, 0, 0), M['studio'])
    w_ = plane('Backdrop', 12, 12, (0, 3.0, 3), M['studio']); w_.rotation_euler = (math.radians(90), 0, 0)
    k = light('AREA', (-1.2, -1.6, 1.4), key_e, (1, 0.96, 0.9), 1.2); aim(k, (0, 0, 0.25))
    rl = light('AREA', (1.3, 1.2, 1.2), key_e * 0.9, (0.75, 0.85, 1.0), 1.0); aim(rl, (0, 0, 0.25))
    for l in (k, rl):
        try: l.visible_camera = False; l.visible_glossy = True
        except Exception: pass

def lin(th0, w): return lambda t: th0 + w * t

# ================================================================ shots
def S00(a, b):  # hook: dark studio, cut-away cylinder; the mixture explodes again and again, the flash lights the metal
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 45, 0.06)
    rig, U = single(M, rot_z=math.radians(-12))
    w = 1.5 * TAU; run_engine([U], lin(TAU - w * 1.2, w), d, fire_l=1.6)
    camera([(0, (0.22, -0.8, 0.48), (0.0, 0.0, 0.3)), (d, (0.16, -0.66, 0.44), (0.0, 0.0, 0.31))], lens=50, fstop=4)

def flame_tongues(loc, d, n=7, seed=2, h=0.32, r=0.12):
    random.seed(seed)
    fm = bpy.data.materials.new('Flame'); fm.use_nodes = True; nt = fm.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Density'].default_value = 0.0; v.inputs['Color'].default_value = (0.05, 0.03, 0.02, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 8
    nz.inputs['Distortion'].default_value = 1.2
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    key_socket(nz.inputs['W'], [(0, 0.0), (d + 0.2, 3.0 * (d + 0.2))], 'LINEAR')
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
    mk = nt.nodes.new('ShaderNodeMapRange'); mk.inputs['From Min'].default_value = 1.0; mk.inputs['From Max'].default_value = 0.2
    nt.links.new(ln.outputs['Value'], mk.inputs['Value'])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    hz = nt.nodes.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = -1.0; hz.inputs['From Max'].default_value = 1.0
    hz.inputs['To Min'].default_value = 0.12; hz.inputs['To Max'].default_value = -0.12
    nt.links.new(sep.outputs['Z'], hz.inputs['Value'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(nz.outputs['Fac'], ad.inputs[0]); nt.links.new(hz.outputs['Result'], ad.inputs[1])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.42; cr.elements[0].color = (0, 0, 0, 1)
    e = cr.elements.new(0.5); e.color = (0.7, 0.07, 0.005, 1)
    e = cr.elements.new(0.6); e.color = (1.0, 0.3, 0.02, 1)
    cr.elements[-1].position = 0.78; cr.elements[-1].color = (1.0, 0.62, 0.18, 1)
    nt.links.new(ad.outputs[0], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], v.inputs['Emission Color'])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 200.0
    nt.links.new(mk.outputs['Result'], st.inputs[0]); nt.links.new(st.outputs[0], v.inputs['Emission Strength'])
    nt.links.new(v.outputs['Volume'], o_.inputs['Volume'])
    for i in range(n):
        x = loc[0] + random.uniform(-r, r) * 0.7; y = loc[1] + random.uniform(-r, r) * 0.7
        k = random.uniform(0.6, 1.0)
        s = sphere('Tongue', 1.0, (x, y, loc[2] + h * k * 0.32), fm, sub=3)
        tex = bpy.data.textures.new('flameN', 'CLOUDS'); tex.noise_scale = 0.5
        dm_ = s.modifiers.new('disp', 'DISPLACE'); dm_.texture = tex; dm_.strength = 0.2
        pts = []; t = 0.0
        while t <= d + 0.1:
            j = random.uniform(0.75, 1.15); pts.append((t, Vector((0.07 * k * j, 0.07 * k * j, h * k * 0.55 * random.uniform(0.85, 1.15))))); t += random.uniform(0.08, 0.16)
        key(s, 'scale', pts)
    fl = light('POINT', (loc[0], loc[1], loc[2] + 0.18), 90, (1, 0.5, 0.18), 0.08)
    pts = []; t = 0.0
    while t <= d + 0.1: pts.append((t, random.uniform(60, 110))); t += 0.09
    key_light(fl.data, 'energy', pts)
    return fl

def S01(a, b):  # garage: gasoline burning in an open steel tray on the floor; a mechanic watches, nothing moves
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); garage(M, 260)
    tray = cyl('Tray', 0.17, 0.035, (0.3, 1.0, 0.0175), M['steel'], verts=64)
    ins = hidden(cyl('TrayIn', 0.16, 0.04, (0.3, 1.0, 0.04), verts=64)); bool_cut(tray, ins)
    cyl('Fuel', 0.16, 0.004, (0.3, 1.0, 0.012), mat_simple('FuelFilm', (0.05, 0.04, 0.02), 0.05, coat=1.0)[0], verts=64)
    flame_tongues((0.3, 1.0, 0.02), d, n=6, h=0.4)
    arm = person('Mechanic', loc=(1.5, 2.65, 0), rot_z=math.radians(-37), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, d, {'neck01': (0, 0, 6)})
    camera([(0, (0.02, 0.18, 0.36), (0.36, 1.0, 0.36)), (d, (0.06, 0.28, 0.35), (0.36, 1.0, 0.36))], lens=30, fstop=2.8)

def S02(a, b):  # cut-away: the piston drops and sucks in a blue puff of fuel and air, then squeezes it up into the chamber
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 110, 0.12)
    rig, U = single(M, rot_z=math.radians(-10))
    th0 = 0.08 * math.pi; th1 = 1.92 * math.pi
    run_engine([U], lin(th0, (th1 - th0) / d), d)
    camera([(0, (0.14, -0.84, 0.4), (0.0, 0.0, 0.31)), (d, (0.12, -0.74, 0.4), (0.0, 0.0, 0.32))], lens=50, fstop=4.5)

def S03(a, b):  # close: the spark plug flashes, the mixture explodes and shoves the piston down
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 70, 0.08)
    rig, U = single(M, rot_z=math.radians(8))
    w = 0.42 * math.pi; th0 = TAU - w * 1.0
    run_engine([U], lin(th0, w), d, fire_l=1.4)
    camera([(0, (-0.1, -0.42, 0.42), (0.0, 0.0, 0.35)), (d, (-0.08, -0.4, 0.38), (0.0, 0.0, 0.3))], lens=50, fstop=3.5)

def S04(a, b):  # studio: a piston bobs straight up and down beside a car wheel that needs to turn
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); studio(M, 380)
    rig, U = single(M, loc=(-0.2, -0.3, 0.145), crank=False, rot_z=math.radians(-15))
    U['rod'].hide_render = True
    for o in U['rod'].children: o.hide_render = True
    run_engine([U], lin(0.5 * math.pi, 1.0 * TAU), d, gas=False)
    wr, sp = wheel(M, (0.3, 0.35, 0.33), side=-1, name='Wheel'); wr.rotation_euler = (0, 0, math.radians(62))
    key(sp, 'rotation_euler', [(0, Vector((0, 0, 0))), (d, Vector((-1.6 * d, 0, 0)))], interp='LINEAR')
    camera([(0, (-0.02, -1.5, 0.4), (0.0, 0.0, 0.32)), (d, (-0.04, -1.4, 0.4), (0.0, 0.0, 0.32))], lens=40, fstop=8)

def S05(a, b):  # cut-away, lower: the rod pushes the crank pin round and round, like legs on bike pedals
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 120, 0.12)
    rig, U = single(M, rot_z=math.radians(-28))
    run_engine([U], lin(0.0, 0.55 * TAU), d)
    camera([(0, (0.32, -0.6, 0.34), (0.0, 0.0, 0.25)), (d, (0.26, -0.55, 0.2), (0.0, 0.0, 0.18))], lens=45, fstop=4.5)

def S06(a, b):  # cut-away: after the bang the piston sits low and the cylinder is full of grey burnt gas
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 110, 0.12)
    rig, U = single(M, rot_z=math.radians(-6))
    th0 = TAU + 0.55 * math.pi; th1 = TAU + 0.98 * math.pi
    run_engine([U], lambda t: th0 + (th1 - th0) * (1 - (1 - min(1, t / d)) ** 2), d)
    camera([(0, (0.05, -0.55, 0.36), (0.0, 0.0, 0.31)), (d, (0.04, -0.5, 0.35), (0.0, 0.0, 0.31))], lens=50, fstop=4)

def S07(a, b):  # cut-away: one full cycle on the words: suck in, squeeze, bang, blow out
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 100, 0.1)
    rig, U = single(M, rot_z=math.radians(-14))
    w = 0.9 * TAU; t0 = 1.71
    run_engine([U], lambda t: w * (t - t0), d, fire_l=1.3)
    camera([(0, (0.14, -0.7, 0.4), (0.0, 0.0, 0.3)), (d, (0.1, -0.64, 0.38), (0.0, 0.0, 0.3))], lens=50, fstop=4.5)

def lobe_mesh(name, rb, rn, e, width, mat):
    import bmesh
    me = bpy.data.meshes.new(name); bm = bmesh.new(); vs = []
    for k in range(48):
        a_ = TAU * k / 48
        for (cx, r) in ((0.0, rb), (e, rn)):
            for xx in (-width / 2, width / 2):
                vs.append(bm.verts.new((xx, cx * 0 + r * math.cos(a_), -cx + r * math.sin(a_))))
    bmesh.ops.convex_hull(bm, input=vs); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    try: me.set_sharp_from_angle(angle=math.radians(40))
    except Exception: pass
    return o   # nose points -Z at rotation 0 (axis X)

def spring(name, loc, r, h, turns, wire, mat):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = wire; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); N = int(turns * 24); sp.points.add(N)
    for i in range(N + 1):
        a_ = TAU * turns * i / N; sp.points[i].co = (r * math.cos(a_), r * math.sin(a_), h * i / N - h / 2, 1)
    o = bpy.data.objects.new(name, cu); link(o); o.location = loc; cu.materials.append(mat); return o

def S08(a, b):  # macro: a spinning camshaft's egg-shaped lobes press two spring-loaded valves open in turn
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 130, 0.12)
    zc = 0.42; rb, rn, e = 0.016, 0.008, 0.016
    rig = bpy.data.objects.new('Cam', None); link(rig); rig.location = (0, 0, zc)
    cyl('CamShaft', 0.011, 0.24, (0, 0, 0), M['steel'], rot=(0, math.radians(90), 0), verts=48).parent = rig
    lobes = []
    for vx, off in ((-0.028, 0.0), (0.028, math.radians(-110))):
        lb = lobe_mesh('Lobe', rb, rn, e, 0.016, M['steel']); lb.parent = rig; lb.location = (vx, 0, 0); lb.rotation_euler = (off, 0, 0); lobes.append((vx, off))
    hd = box('HeadBlock', (0.16, 0.09, 0.2), (0, 0.0, 0.22), M['alu'])
    cutter = hidden(box('Cut', (0.3, 0.1, 0.5), (0, -0.05, 0.25))); bool_cut(hd, cutter)
    box('CamBearing', (0.012, 0.05, 0.05), (-0.075, 0.0, zc), M['alu'])
    box('CamBearing', (0.012, 0.05, 0.05), (0.075, 0.0, zc), M['alu'])
    vg = []
    for vx, off in lobes:
        g = bpy.data.objects.new('ValveG', None); link(g); g.location = (vx, 0, 0)
        top = zc - rb
        cyl('Bucket', 0.013, 0.012, (0, 0, top - 0.006), M['steel'], verts=48).parent = g
        cyl('Stem', 0.0032, 0.25, (0, 0, top - 0.13), M['forged'], verts=16).parent = g
        cyl('VHead', 0.016, 0.003, (0, 0, top - 0.255), M['forged'], verts=48).parent = g
        cyl('Retainer', 0.011, 0.003, (0, 0, top - 0.016), M['steel'], verts=32).parent = g
        spr = spring('Spring', (vx, 0, top - 0.06), 0.0105, 0.085, 6, 0.0017, M['steel'])
        vg.append((g, spr, off))
    w = 0.42 * TAU; n = round(d * FPS)
    for f in range(n + 1):
        t = f / FPS; th = w * t + math.radians(150); fr = F(t)
        rig.rotation_euler = (th, 0, 0); rig.keyframe_insert('rotation_euler', frame=fr)
        for g, spr, off in vg:
            al = th + off
            lift = max(rb, e * math.cos(al) + rn) - rb
            g.location = (g.location[0], 0, -lift); g.keyframe_insert('location', frame=fr)
            spr.scale = (1, 1, (0.085 - lift) / 0.085); spr.location = (g.location[0], 0, zc - rb - 0.016 - (0.085 - lift) / 2 - lift)
            spr.keyframe_insert('scale', frame=fr); spr.keyframe_insert('location', frame=fr)
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            for fc in fcurves_of(o.animation_data.action):
                for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    camera([(0, (0.2, -0.27, 0.45), (0.0, 0.0, 0.385)), (d, (0.17, -0.25, 0.445), (0.0, 0.0, 0.385))], lens=55, fstop=4)

def S09(a, b):  # garage bench: a closed one-cylinder engine runs and shakes on every power stroke; the mechanic watches
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); garage(M, 700)
    rig, U = single(M, loc=(1.45, 3.2, 0.94 + 0.145), rot_z=math.radians(-28))
    fw = cyl('Flywheel', 0.11, 0.025, (0.07, 0, 0), M['steel'], rot=(0, math.radians(90), 0), verts=64); fw.parent = U['g']
    w = 1.6 * TAU; th = lin(0.3, w)
    run_engine([U], th, d, fire_l=1.4)
    pts = []
    for f in range(0, round(d * FPS) + 1):
        t = f / FPS; s = stroke_state(th(t))
        j = s['fire'] if s['fire'] > 0.05 else 0.0
        pts.append((t, Vector((math.radians(1.8) * j * math.sin(t * 90), 0, math.radians(-28) + math.radians(1.2) * j * math.cos(t * 70)))))
        fw.rotation_euler = (th(t), 0, 0); fw.keyframe_insert('rotation_euler', frame=F(t))
    key(rig, 'rotation_euler', pts, interp='LINEAR')
    arm = person('Mechanic', loc=(3.55, 3.15, 0), rot_z=math.radians(-90), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, d, {'neck01': (0, 0, -8)})
    camera([(0, (0.55, 2.5, 1.35), (1.95, 3.2, 1.18)), (d, (0.62, 2.56, 1.33), (1.95, 3.2, 1.18))], lens=35, fstop=4)

def S10(a, b):  # cut-away inline-4: four pistons take turns, the flashes run along the engine 1-3-4-2
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); dark_studio(M, 120, 0.1)
    rig, us = inline4(M, rot_z=math.radians(-22))
    run_engine(us, lin(0.4, 0.7 * TAU), d, fire_l=1.0)
    camera([(0, (0.36, -0.95, 0.5), (0.0, 0.0, 0.25)), (d, (0.26, -0.88, 0.47), (0.0, 0.0, 0.25))], lens=45, fstop=5.6)

def S11(a, b):  # dusk highway: the car flies past low beside the camera, motion blur
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats())
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(200)); sun(1.6, 7, 200, color=(1, 0.75, 0.5))
    road(length=600, y0=-300)
    rig, body, W = car(M, (0.45, 0.04, 0.03))
    v = 24.0
    key(rig, 'location', [(0, Vector((1.85, -30, 0))), (d, Vector((1.85, -30 + v * d, 0)))], interp='LINEAR')
    for k, (rg, sp) in W.items(): roll(sp, [(0, 0), (d, v * d)])
    cam, tgt = camera([(0, (2.7, -1.3, 0.55), (0.9, 1.6, 0.5)), (d, (2.65, -1.0, 0.55), (0.9, 1.6, 0.5))], lens=28, fstop=4)
    cam.parent = rig; tgt.parent = rig
    trees(30, xr=(16, 60), yr=(-320, 300))

def S12(a, b):  # garage bench: a cut-away inline-4 running; the mechanic points at the flashing cylinders
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); garage(M, 520)
    rig, us = inline4(M, loc=(1.55, 3.2, 0.94 + 0.145), rot_z=math.radians(-25))
    run_engine(us, lin(0.2, 0.8 * TAU), d, fire_l=1.6)
    arm = person('Mechanic', loc=(3.55, 3.1, 0), rot_z=math.radians(-90), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.7, STANCES['relax']); pose(arm, 1.8, STANCES['point_r'])
    camera([(0, (0.6, 2.45, 1.38), (2.05, 3.2, 1.18)), (d, (0.7, 2.55, 1.35), (2.05, 3.2, 1.18))], lens=35, fstop=4)

def S13(a, b):  # garage: the car with its engine on a stand beside it; the mechanic points at it as we pull back
    sc = new_scene(a, b); d = dur(a, b); M = emats(mats()); garage(M, 900)
    rig, body, W = car(M, (0.45, 0.04, 0.03)); rig.location = (-0.4, 0.9, 0); rig.rotation_euler = (0, 0, math.radians(-25))
    stand = box('Stand', (0.5, 0.4, 0.6), (1.35, 1.25, 0.3), mat_simple('StandPaint', (0.5, 0.06, 0.04), 0.5, 0.3)[0], bevel=0.01)
    er, us = inline4(M, loc=(1.35, 1.2, 0.6 + 0.145), rot_z=math.radians(-20))
    run_engine(us, lin(0.0, 0.7 * TAU), d, fire_l=1.4)
    arm = person('Mechanic', loc=(2.05, 1.85, 0), rot_z=math.radians(-60), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.8, STANCES['relax']); pose(arm, 1.8, STANCES['point_r'])
    camera([(0, (0.9, -0.35, 1.1), (1.45, 1.4, 0.85)), (d, (0.75, -0.85, 1.2), (1.3, 1.4, 0.9))], lens=32, fstop=4.5)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13]

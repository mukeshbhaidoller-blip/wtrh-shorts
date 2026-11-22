# Shots for "If You Press a Pedal With Your Foot..." (how car brakes work). One function per line.
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
    bench = box('Bench', (2.2, 0.7, 0.9), (2.2, 3.4, 0.45), mat_simple('BenchPaint', (0.12, 0.2, 0.32), 0.5, 0.3)[0], bevel=0.01)
    box('Toolboard', (2.0, 0.04, 1.0), (2.2, 3.85, 1.6), mat_simple('Pegboard', (0.45, 0.35, 0.25), 0.8)[0])
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

# ================================================================ shots
def S00(a, b):  # dusk road, low beside the front wheel: the car brakes and stops, nose dipping
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(210)); sun(1.6, 7, 210, color=(1, 0.75, 0.5))
    road(length=300, y0=-150)
    rig, body, W = car(M, (0.03, 0.045, 0.07))
    v0, tb, dec = 9.0, 0.7, 7.5; y0 = -(v0 * tb + v0 * v0 / (2 * dec))
    N = 24; ts = [d * i / N for i in range(N + 1)]
    key(rig, 'location', [(t, Vector((1.85, brake_y(t, y0, v0, tb, dec), 0))) for t in ts], interp='LINEAR')
    for k, (rg, sp) in W.items(): roll(sp, [(t, brake_y(t, y0, v0, tb, dec) - y0) for t in ts])
    tst = tb + v0 / dec
    key(body, 'rotation_euler', [(0, Vector((0, 0, 0))), (tb, Vector((0, 0, 0))), (tb + 0.35, Vector((math.radians(-1.6), 0, 0))), (tst, Vector((math.radians(-1.4), 0, 0))), (tst + 0.25, Vector((math.radians(0.5), 0, 0))), (min(d, tst + 0.6), Vector((0, 0, 0)))])
    key_socket(TAIL[body.name], [(0, 1.5), (tb, 1.5), (tb + 0.05, 8.0)])
    camera([(0, (4.55, 0.55, 0.32), (2.75, 1.4, 0.36)), (d, (4.5, 0.65, 0.31), (2.75, 1.4, 0.36))], lens=32, fstop=2.8)

def S01(a, b):  # garage: a man stands beside a two-ton car
    sc = new_scene(a, b); d = dur(a, b); M = mats(); garage(M)
    rig, body, W = car(M, (0.03, 0.045, 0.07)); rig.location = (0.4, 0.8, 0); rig.rotation_euler = (0, 0, math.radians(-28))
    arm = person('Owner', loc=(-1.35, -1.25, 0), rot_z=math.radians(-35), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.8, STANCES['relax']); pose(arm, 1.8, {'neck01': (0, 0, -14)})
    camera([(0, (-0.75, -4.6, 1.35), (-0.45, 0.2, 0.85)), (d, (-0.65, -4.2, 1.32), (-0.45, 0.2, 0.85))], lens=26, fstop=5.6)

def S02(a, b):  # studio cut-away: the pedal pushes a piston into a glass master cylinder full of amber brake fluid
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio(M)
    t0, t1 = 0.6, 1.7; ang = 14
    pv = bpy.data.objects.new('PedalPivot', None); link(pv); pv.location = (0, -0.55, 0.62)
    arm_ = box('PedalArm', (0.03, 0.03, 0.5), (0, 0, -0.25), M['dark'], bevel=0.005); arm_.parent = pv
    pad = box('PedalPad', (0.11, 0.025, 0.07), (0, -0.015, -0.5), mat_simple('PadRubber', (0.03, 0.03, 0.03), 0.8)[0], bevel=0.008); pad.parent = pv
    key(pv, 'rotation_euler', [(0, Vector((0, 0, 0))), (t0, Vector((0, 0, 0))), (t1, Vector((math.radians(-ang), 0, 0)))])
    # glass master cylinder along +Y at z 0.42
    zc = 0.42; y0, y1 = -0.2, 0.32
    g = cyl('Bore', 0.042, y1 - y0, (0, (y0 + y1) / 2, zc), M['glass'], rot=(math.radians(90), 0, 0), verts=64)
    fl = cyl('Fluid', 0.038, y1 - y0 - 0.1, (0, (y0 + y1) / 2 + 0.05, zc), M['fluid'], rot=(math.radians(90), 0, 0), verts=48)
    pis = cyl('Piston', 0.037, 0.05, (0, y0 + 0.05, zc), M['steel'], rot=(math.radians(90), 0, 0), verts=48)
    rod = cyl('PushRod', 0.008, 0.32, (0, y0 - 0.12, zc), M['steel'], rot=(math.radians(90), 0, 0), verts=16)
    dy = 0.08
    key(pis, 'location', [(0, Vector((0, y0 + 0.05, zc))), (t0, Vector((0, y0 + 0.05, zc))), (t1, Vector((0, y0 + 0.05 + dy, zc)))])
    key(rod, 'location', [(0, Vector((0, y0 - 0.12, zc))), (t0, Vector((0, y0 - 0.12, zc))), (t1, Vector((0, y0 - 0.12 + dy, zc)))])
    key(fl, 'location', [(0, Vector((0, (y0 + y1) / 2 + 0.05, zc))), (t0, Vector((0, (y0 + y1) / 2 + 0.05, zc))), (t1, Vector((0, (y0 + y1) / 2 + 0.05 + dy / 2, zc)))])
    key(fl, 'scale', [(0, Vector((1, 1, 1))), (t0, Vector((1, 1, 1))), (t1, Vector((1, 1, (y1 - y0 - 0.1 - dy) / (y1 - y0 - 0.1))))])
    box('Reservoir', (0.09, 0.14, 0.08), (0, 0.06, zc + 0.08), M['glass'], bevel=0.01)
    box('ResFluid', (0.08, 0.13, 0.05), (0, 0.06, zc + 0.065), M['fluid'], bevel=0.008)
    box('Mount', (0.16, 0.03, 0.16), (0, y0 - 0.02, zc), M['dark'], bevel=0.01)
    tube('Line', [(0, y1, zc), (0, y1 + 0.12, zc), (0.0, y1 + 0.2, zc - 0.1), (0.0, y1 + 0.2, 0.02)], 0.006, M['steel'])
    pm, pe = mat_emit('Pulse', (1, 0.55, 0.12), 0.0)
    pulse = sphere('Pulse', 0.012, (0, y1 + 0.05, zc), pm, sub=2)
    key(pulse, 'location', [(t1 - 0.3, Vector((0, y1 + 0.01, zc))), (t1 + 0.4, Vector((0, y1 + 0.15, zc - 0.03))), (t1 + 1.0, Vector((0, y1 + 0.2, 0.05)))], interp='LINEAR')
    key_socket(pe.inputs['Strength'], [(0, 0.0), (t1 - 0.35, 0.0), (t1 - 0.25, 25.0), (t1 + 1.0, 25.0), (t1 + 1.1, 0.0)])
    camera([(0, (0.85, -0.55, 0.62), (0, 0.02, 0.36)), (d, (0.78, -0.45, 0.6), (0, 0.04, 0.36))], lens=35, fstop=4.5)

def S03(a, b):  # studio layout: brake lines from the master cylinder to four brake corners; glowing pulses race out
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio(M, 500)
    mc = (-0.35, 0.95, 0.12)
    cyl('Master', 0.05, 0.26, mc, M['steel'], rot=(math.radians(90), 0, 0), verts=32)
    box('Booster', (0.3, 0.12, 0.3), (mc[0], mc[1] - 0.2, 0.16), M['dark'], bevel=0.04)
    corners = dict(fl=(-0.78, 1.38), fr=(0.78, 1.38), rl=(-0.78, -1.33), rr=(0.78, -1.33))
    pm, pe = mat_emit('Pulse', (1, 0.55, 0.12), 30.0)
    tp0, tp1 = 0.5, 1.9
    for k, (x, y) in corners.items():
        sx = 1 if x > 0 else -1
        rg = bpy.data.objects.new('Corner', None); link(rg); rg.location = (x, y, 0.17)
        dm, es = disc_mat('Disc' + k)
        rt = rotor(M, dm); rt.parent = rg; rt.scale = (sx, 1, 1)
        cr, pads = caliper(M, sx); cr.parent = rg
        squeeze(pads, tp1 - 0.05, tp1 + 0.15)
        path = [(mc[0], mc[1] + 0.13, mc[2]), (mc[0] * 0.3 + x * 0.7, mc[1] + 0.13 if y > 0 else 0.0, 0.03), (x - sx * 0.15, y, 0.03), (x - sx * 0.06, y + 0.12, 0.2)]
        if y < 0: path = [(mc[0], mc[1] - 0.05, 0.03), (0.0 if x > 0 else mc[0], 0.0, 0.03), (x - sx * 0.15, y, 0.03), (x - sx * 0.06, y + 0.12, 0.2)]
        tube('Line', path, 0.005, M['steel'], verts=8)
        p = sphere('Pulse', 0.018, path[0], pm, sub=2)
        segs = len(path) - 1; pts = [(0, Vector(path[0])), (tp0, Vector(path[0]))]
        for i in range(1, len(path)): pts.append((tp0 + (tp1 - tp0) * i / segs, Vector(path[i])))
        pts.append((tp1 + 0.05, Vector(path[-1])))
        key(p, 'location', pts, interp='LINEAR')
        key(p, 'scale', [(0, Vector((1, 1, 1))), (tp1, Vector((1, 1, 1))), (tp1 + 0.1, Vector((0, 0, 0)))])
    camera([(0, (1.9, -3.3, 2.6), (0, 0.05, 0.1)), (d, (2.4, -2.9, 2.4), (0, 0.05, 0.1))], lens=28, fstop=8)

def S04(a, b):  # studio cut-away: the black vacuum booster, its diaphragm pushes the rod harder into the master cylinder
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio(M)
    zc = 0.4; t0, t1 = 0.5, 1.6
    shell, _ = mat_simple('BoosterShell', (0.02, 0.02, 0.022), 0.25, 0.8, coat=0.8)
    dr = cyl('Booster', 0.24, 0.2, (0, 0, zc), shell, rot=(math.radians(90), 0, 0), verts=96)
    cutr = box('Cutaway', (0.4, 0.4, 0.4), (0.2, -0.2, zc + 0.2), None); cutr.hide_render = True; cutr.display_type = 'WIRE'
    md = dr.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutr
    inner = cyl('Inner', 0.232, 0.19, (0, 0, zc), mat_simple('BoosterInside', (0.16, 0.16, 0.17), 0.6, 0.5)[0], rot=(math.radians(90), 0, 0), verts=96)
    md2 = inner.modifiers.new('cut', 'BOOLEAN'); md2.operation = 'DIFFERENCE'; md2.object = cutr
    # inner is a solid; hollow it so we see the diaphragm
    hol = cyl('Hollow', 0.226, 0.18, (0, 0, zc), None, rot=(math.radians(90), 0, 0), verts=96); hol.hide_render = True; hol.display_type = 'WIRE'
    md3 = inner.modifiers.new('hol', 'BOOLEAN'); md3.operation = 'DIFFERENCE'; md3.object = hol
    md4 = dr.modifiers.new('hol', 'BOOLEAN'); md4.operation = 'DIFFERENCE'; md4.object = hol
    dia = cyl('Diaphragm', 0.22, 0.012, (0, -0.04, zc), mat_simple('Diaphragm', (0.06, 0.06, 0.06), 0.7)[0], rot=(math.radians(90), 0, 0), verts=96)
    plate = cyl('DiaPlate', 0.12, 0.016, (0, -0.03, zc), M['steel'], rot=(math.radians(90), 0, 0), verts=64)
    rod = cyl('Rod', 0.012, 0.3, (0, 0.12, zc), M['steel'], rot=(math.radians(90), 0, 0), verts=16)
    mcyl = cyl('Master', 0.045, 0.24, (0, 0.33, zc), mat_simple('MCAlu', (0.6, 0.6, 0.62), 0.35, 1.0)[0], rot=(math.radians(90), 0, 0), verts=48)
    box('Reservoir', (0.08, 0.14, 0.07), (0, 0.33, zc + 0.08), mat_simple('ResPlastic', (0.85, 0.8, 0.6), 0.4, trans=0.3)[0], bevel=0.01)
    for o, y in ((dia, -0.04), (plate, -0.03), (rod, 0.12)):
        key(o, 'location', [(0, Vector((0, y, zc))), (t0, Vector((0, y, zc))), (t1, Vector((0, y + 0.06, zc)))])
    tube('VacHose', [(0, -0.02, zc + 0.24), (0, -0.02, zc + 0.36), (0.25, 0.1, zc + 0.55), (0.6, 0.3, zc + 0.6)], 0.018, mat_simple('Hose', (0.02, 0.02, 0.02), 0.6)[0], verts=16)
    camera([(0, (0.95, -0.9, 0.75), (0, 0.05, 0.4)), (d, (0.85, -0.8, 0.7), (0, 0.05, 0.4))], lens=35, fstop=4.5)

def S05(a, b):  # garage: wheel off, a mechanic points at the red caliper as the pads clamp the turning disc
    sc = new_scene(a, b); d = dur(a, b); M = mats(); garage(M, 700)
    rig, body, W = car(M, (0.03, 0.045, 0.07)); rig.location = (0, 1.0, 0.12)
    rg, sp = W['fr']
    for o in sp.children:
        if not o.name.startswith('Rotor'): o.hide_render = True
    spin_ = sp; key(spin_, 'rotation_euler', [(0, Vector((0, 0, 0))), (1.3, Vector((-1.2, 0, 0))), (1.6, Vector((-1.3, 0, 0))), (d, Vector((-1.3, 0, 0)))])
    pads = []
    for o in bpy.data.objects:
        if o.name.startswith('Pad') and o.parent and o.parent.parent == rg: pads.append((o, 1 if o.location.x > 0 else -1))
    squeeze(pads, 1.15, 1.35)
    # jack stand + the wheel leaning on the wall
    arm = person('Mechanic', loc=(1.05, 3.75, 0), rot_z=math.radians(-8), outfit='worker')
    PL = {'upperarm01.R': (0, 0, 55), 'upperarm01.L': (45, 0, -25), 'lowerarm01.L': (5, 0, 0), 'lowerarm01.R': (10, 0, 0)}
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.6, STANCES['relax']); pose(arm, 1.5, STANCES['point_r'])
    camera([(0, (1.95, 1.35, 0.72), (0.88, 2.8, 0.68)), (d, (1.85, 1.45, 0.7), (0.88, 2.8, 0.68))], lens=24, fstop=4)

def brake_macro(M, glow_pts, rev, pads_t=(0.15, 0.35), cam_path=None, lights=True):
    garage(M, 300)
    hub = bpy.data.objects.new('Hub', None); link(hub); hub.location = (0, 0, 0.5)
    dm, es = disc_mat('HotDisc')
    rt = rotor(M, dm); rt.parent = hub
    spin(rt, 0, rev[0], rev[1])
    cr, pads = caliper(M, 1); cr.parent = hub
    squeeze(pads, *pads_t)
    key_glow(es, glow_pts)
    box('Knuckle', (0.06, 0.12, 0.3), (-0.06, 0, -0.12), M['dark'], bevel=0.01).parent = hub
    box('DarkArch', (2.0, 0.05, 2.0), (0, 0.7, 0.6), mat_simple('ArchShadow', (0.01, 0.01, 0.012), 0.8)[0])
    return hub, rt, cr, es

def spin(o, t0, t1, rev, axis=0, start=0.0):
    for t, v in ((t0, start), (t1, start + rev * 2 * math.pi)):
        o.rotation_euler[axis] = v; o.keyframe_insert('rotation_euler', index=axis, frame=F(t))
    for fc in fcurves_of(o.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

def S06(a, b):  # macro: the pads clamp the spinning disc and it starts to heat up
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    hub, rt, cr, es = brake_macro(M, [(0, 0.0), (0.6, 0.0), (d, 0.5)], (d, -2.5), pads_t=(0.2, 0.4))
    camera([(0, (0.42, -0.36, 0.72), (0, 0.05, 0.6)), (d, (0.38, -0.32, 0.7), (0, 0.05, 0.6))], lens=40, fstop=2.8)

def S07(a, b):  # macro: the disc glows orange and smoke curls off the pads (brake fade)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    hub, rt, cr, es = brake_macro(M, [(0, 0.9), (d, 1.8)], (d, -1.6), pads_t=(0.0, 0.01))
    light('POINT', (0.12, -0.05, 0.62), 0, (1, 0.4, 0.1), 0.1).data.energy = 6
    smoke((0.0, 0.0, 0.66), 0.2, d - 0.4, n=12, seed=5, rise=0.5, size=0.05, dens=0.8)
    camera([(0, (0.5, -0.45, 0.62), (0, 0.04, 0.55)), (d, (0.45, -0.4, 0.62), (0, 0.04, 0.56))], lens=36, fstop=2.8)

def S08(a, b):  # workbench: a vented disc on its edge shows the air vanes between its two faces; mechanic behind
    sc = new_scene(a, b); d = dur(a, b); M = mats(); garage(M, 700)
    dm, es = disc_mat('BenchDisc')
    rt = rotor(M, dm, r=0.165); rt.location = (2.2, 3.25, 0.9 + 0.165); rt.rotation_euler = (0, 0, math.radians(160))
    qc = box('Quadrant', (0.03, 0.2, 0.2), (0, 0, 0), None); qc.hide_render = True; qc.display_type = 'WIRE'; qc.parent = rt; qc.location = (0.016, 0.1, 0.1)
    for o in rt.children:
        if o.name.startswith('Plate') and o.location.x > 0:
            md = o.modifiers.new('q', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = qc
    spin(rt, 0, d, 0.12)
    # faint air wisps drawn through the vanes
    wm = mat_emit('Air', (0.75, 0.85, 1.0), 0.0)
    random.seed(7)
    arm = person('Mechanic', loc=(2.5, 2.55, 0), rot_z=math.radians(-160), outfit='worker')
    pose(arm, 0.0, STANCES['relax'])
    camera([(0, (1.5, 2.4, 1.18), (2.2, 3.25, 1.05)), (d, (1.56, 2.46, 1.16), (2.2, 3.25, 1.05))], lens=75, fstop=3.5)

def S09(a, b):  # night race track: camera rides beside the front wheel, the disc glows red hot through the spokes
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('dikhololo_night', 0.5, 0, 'night')
    road(length=600, y0=-300, lanes=3, worn=0.0, shoulder=False, edge=True)
    for y in range(-280, 300, 22):
        light('POINT', (6.5, y, 8.0), 900, (1, 0.85, 0.65), 0.5)
    dm, es = disc_mat('RaceDisc', 3.0)
    rig, body, W = car(M, (0.85, 0.85, 0.82), dm=dm, lights=True)
    v = 14.0
    key(rig, 'location', [(0, Vector((1.0, -20, 0))), (d, Vector((1.0, -20 + v * d * 0.8, 0)))], interp='LINEAR')
    for k, (rg, sp) in W.items(): roll(sp, [(0, 0), (d, v * d * 0.8)])
    gl = light('POINT', (0, 0, 0), 25, (1, 0.35, 0.08), 0.12); gl.parent = W['fr'][0]; gl.location = (0.2, 0, 0)
    cam, tgt = camera([(0, (2.25, 1.05, 0.38), (0.8, 1.38, 0.34)), (d, (2.15, 1.1, 0.38), (0.8, 1.38, 0.34))], lens=30, fstop=2.8)
    cam.parent = rig; tgt.parent = rig

def S10(a, b):  # day road: the wheels lock and stop turning, the car slides, tire smoke and black skid marks behind
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, math.radians(40)); sun(2.2, 40, 130)
    road(length=400, y0=-200)
    rig, body, W = car(M, (0.03, 0.045, 0.07))
    v0, tl, dec = 12.0, 1.0, 6.0
    N = 24; ts = [d * i / N for i in range(N + 1)]
    yy = lambda t: brake_y(t, -14.0, v0, tl, dec)
    key(rig, 'location', [(t, Vector((1.85, yy(t), 0))) for t in ts], interp='LINEAR')
    key(rig, 'rotation_euler', [(0, Vector((0, 0, 0))), (tl, Vector((0, 0, 0))), (d, Vector((0, 0, math.radians(-5))))])
    for k, (rg, sp) in W.items(): roll(sp, [(0, 0), (tl, v0 * tl), (d, v0 * tl)])
    key(body, 'rotation_euler', [(0, Vector((0, 0, 0))), (tl, Vector((0, 0, 0))), (tl + 0.3, Vector((math.radians(-2.0), 0, 0)))])
    sk, _ = mat_simple('Skid', (0.01, 0.01, 0.01), 0.6)
    for x in (1.05, 2.65):
        y_l = yy(tl) + 1.38
        m = box('SkidMark', (0.2, 1.0, 0.002), (x, y_l, 0.002), sk)
        L = lambda t: max(0.01, yy(t) - yy(tl))
        key(m, 'scale', [(t, Vector((1, L(t), 1))) for t in ts if t >= tl] + [(0, Vector((1, 0.01, 1))), (tl, Vector((1, 0.01, 1)))])
        key(m, 'location', [(0, Vector((x, y_l, 0.002)))] + [(t, Vector((x, y_l + L(t) / 2, 0.002))) for t in ts if t > tl])
    for k in ('fr', 'rr'):
        e = bpy.data.objects.new('SmokeAnchor', None); link(e)
    smoke((2.75, yy(tl) + 1.1, 0.12), tl + 0.1, d - 0.2, n=14, seed=3, rise=0.5, size=0.18, col=(0.8, 0.8, 0.8), dens=0.5)
    cam, tgt = camera([(0, (2.45, -0.75, 0.45), (0.8, 1.2, 0.3)), (d, (2.4, -0.7, 0.45), (0.8, 1.2, 0.3))], lens=28, fstop=4)
    cam.parent = rig; tgt.parent = rig

def S11(a, b):  # day road: ABS pulses the pads on and off, the wheel keeps turning and the car steers around
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, math.radians(80)); sun(2.2, 40, 120)
    road(length=400, y0=-200)
    rig, body, W = car(M, (0.03, 0.045, 0.07))
    v0 = 10.0; dec = 1.4
    N = 30; ts = [d * i / N for i in range(N + 1)]
    yy = lambda t: v0 * t - 0.5 * dec * t * t
    key(rig, 'location', [(t, Vector((1.85 - 0.06 * max(0, t - 1.5) ** 2, -10 + yy(t), 0))) for t in ts], interp='LINEAR')
    key(rig, 'rotation_euler', [(0, Vector((0, 0, 0))), (1.5, Vector((0, 0, 0))), (d, Vector((0, 0, math.radians(6))))])
    pulses = []; t = 0.3
    while t < d - 0.2: pulses.append((t, t + 0.12)); t += 0.25
    for k, (rg, sp) in W.items():
        pts = [(0, 0.0)]; acc = 0.0
        for (ta, tb2) in pulses:
            pts.append((ta, yy(ta))); pts.append((tb2, yy(ta) + 0.02))
        roll(sp, sorted(pts))
        pads = [(o, 1 if o.location.x > 0 else -1) for o in bpy.data.objects if o.name.startswith('Pad') and o.parent and o.parent.parent == rg]
        squeeze(pads, 0, 0, pulses=pulses)
    for k in ('fl', 'fr'):
        rg = W[k][0]; key(rg, 'rotation_euler', [(0, Vector((0, 0, 0))), (1.3, Vector((0, 0, 0))), (2.2, Vector((0, 0, math.radians(14))))])
    cam, tgt = camera([(0, (2.35, 0.65, 0.42), (0.8, 1.38, 0.33)), (d, (2.3, 0.7, 0.42), (0.8, 1.38, 0.33))], lens=30, fstop=3.2)
    cam.parent = rig; tgt.parent = rig

def S12(a, b):  # dark studio: slow orbit around a glowing disc in its caliper, heat fading
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.08, 0, 'studio')
    plane('Floor', 20, 20, (0, 0, 0), M['studio'])
    hub = bpy.data.objects.new('Hub', None); link(hub); hub.location = (0, 0, 0.3)
    dm, es = disc_mat('GlowDisc', 2.2)
    rt = rotor(M, dm); rt.parent = hub; spin(rt, 0, d, -0.4)
    cr, pads = caliper(M, 1); cr.parent = hub
    key_glow(es, [(0, 2.2), (d, 1.0)])
    gl = light('POINT', (0.1, 0, 0.3), 30, (1, 0.35, 0.08), 0.1)
    k = light('AREA', (-0.8, -1.2, 1.0), 40, (0.8, 0.85, 1.0), 1.2); aim(k, (0, 0, 0.3))
    smoke((0.0, 0.0, 0.46), 0.0, d - 0.3, n=10, seed=8, rise=0.45, size=0.05, dens=0.6)
    camera([(0, (0.75, -0.5, 0.42), (0, 0, 0.3)), (d, (0.35, -0.82, 0.38), (0, 0, 0.3))], lens=38, fstop=2.8)

def S13(a, b):  # dusk mountain overlook: car parked by the guard rail, a man touches near the front wheel to feel the heat
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(150)); sun(1.8, 6, 150, color=(1, 0.72, 0.48))
    road(length=300, y0=-150, shoulder=False)
    plane('Valley', 400, 400, (0, 0, -60), M['grass'])
    gm = M['grass']
    for (x, y, s) in ((-90, 220, 70), (60, 300, 90), (160, 180, 60), (-200, 120, 80)):
        h = sphere('Hill', 1.0, (x, y, -60), gm, sub=5); h.scale = (s * 1.6, s, s * 0.9)
        tex = bpy.data.textures.new('hillN', 'CLOUDS'); tex.noise_scale = 0.6
        dm_ = h.modifiers.new('disp', 'DISPLACE'); dm_.texture = tex; dm_.strength = 0.08
    rail, _ = mat_simple('Rail', (0.6, 0.61, 0.62), 0.3, 1.0)
    box('Guardrail', (0.06, 300, 0.32), (4.25, 0, 0.6), rail)
    y = -150
    while y < 150:
        box('Post', (0.12, 0.12, 0.75), (4.3, y, 0.37), mat_simple('PostWood', (0.25, 0.18, 0.12), 0.8)[0]); y += 2.0
    plane('Shoulder', 1.2, 300, (4.3, 0, -0.01), M['asphalt'])
    dm, es = disc_mat('WarmDisc', 0.25)
    rig, body, W = car(M, (0.03, 0.045, 0.07), dm=dm); rig.location = (2.9, 0, 0)
    arm = person('Driver', loc=(1.6, 2.6, 0), rot_z=math.radians(35), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.2, STANCES['relax']); pose(arm, 2.4, STANCES['point_r'])
    camera([(0, (0.55, -0.55, 0.78), (2.15, 1.55, 0.6)), (d, (0.65, -0.4, 0.76), (2.15, 1.55, 0.6))], lens=26, fstop=4)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13]

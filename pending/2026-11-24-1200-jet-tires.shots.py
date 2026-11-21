# Shots for "These Tires Hit the Runway at 150 MPH" (airliner main-gear tires). One function per script line.
# Runway runs along +Y. Wheels roll along +Y with their axle along X. t = seconds from shot start.
from mathutils import Matrix
ASPH = ['asphalt_04', 'asphalt_02']
DUSK = 'qwantani_dusk_2_puresky'
V = 67.0          # ~150 mph in m/s
R = 0.56          # 737-size main tire radius (m)

def dur(a, b): return (b - a) / FPS

def flat(o):
    for pg in o.data.polygons: pg.use_smooth = False
    return o

def mat_rubber(name='Rubber', col=(0.022, 0.022, 0.024)):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = 0.72
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 140; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.6; rr.inputs['To Max'].default_value = 0.85
    nt.links.new(nz.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
    return m

def mats():
    return dict(rub=mat_rubber(), alu=mat_simple('Alu', (0.75, 0.76, 0.78), 0.28, 1.0)[0],
                chrome=mat_simple('Chrome', (0.9, 0.9, 0.92), 0.08, 1.0)[0], grey=mat_simple('GearGrey', (0.32, 0.33, 0.35), 0.45, 0.6)[0],
                dark=mat_simple('Dark', (0.03, 0.03, 0.035), 0.5, 0.3)[0])

def tire(M, loc=(0, 0, 0), r=R, w=0.38, worn=False, hub=True, name='Wheel', ribs=True):
    """Airliner tire + wheel, axle along X. Returns an empty at the axle centre (rotate its X to roll)."""
    rig = bpy.data.objects.new(name, None); link(rig); rig.location = loc
    rot = (0, math.radians(90), 0); parts = []
    core = cyl('Casing', r - 0.014, w, (0, 0, 0), M['rub'], rot=rot, verts=96, bevel=0.07); parts.append(core)
    if ribs:
        n = 4; gap = 0.016; rw = (w * 0.72 - gap * (n - 1)) / n
        for k in range(n):
            x = -w * 0.36 + rw / 2 + k * (rw + gap)
            parts.append(cyl('Rib', r - (0.0115 if worn else 0.0), rw, (x, 0, 0), M['rub'], rot=rot, verts=96, bevel=0.004))
    if hub:
        for s in (-1, 1):
            parts.append(cyl('Rim', r * 0.56, 0.02, (s * w * 0.47, 0, 0), M['alu'], rot=rot, verts=64, bevel=0.006))
            parts.append(cyl('HubCap', r * 0.2, 0.04, (s * w * 0.5, 0, 0), M['alu'], rot=rot, verts=48, bevel=0.01))
            for k in range(10):
                a = k * 2 * math.pi / 10
                parts.append(cyl('Bolt', 0.016, 0.03, (s * w * 0.49, math.cos(a) * r * 0.32, math.sin(a) * r * 0.32), M['grey'], rot=rot, verts=6))
    for o in parts: o.parent = rig
    return rig

def gear(M, loc=(0, 0, 0)):
    """Dual-wheel main gear: rig origin at the axle centre."""
    rig = bpy.data.objects.new('Gear', None); link(rig); rig.location = loc
    ws = [tire(M, (-0.36, 0, 0), name='WheelL'), tire(M, (0.36, 0, 0), name='WheelR')]
    parts = [cyl('Axle', 0.06, 1.0, (0, 0, 0), M['grey'], rot=(0, math.radians(90), 0), verts=32),
             cyl('Piston', 0.085, 1.2, (0, 0, 0.6), M['chrome'], verts=48),
             cyl('Cylinder', 0.13, 2.4, (0, 0, 2.3), M['grey'], verts=48, bevel=0.01),
             cyl('Brace', 0.05, 2.6, (0, -0.9, 2.3), M['grey'], rot=(math.radians(-38), 0, 0), verts=24)]
    for o in parts + ws: o.parent = rig
    return rig, ws

def airframe(M, gx, gy_fn=None):
    """Wing underside + engine nacelle above the gear (parented to the gear rig by the caller)."""
    paint, _ = mat_simple('Paint', (0.78, 0.79, 0.8), 0.35, 0.15, coat=0.4)
    wing = box('Wing', (14, 4.2, 0.35), (gx - 5.5, 0.2, 3.7), paint, bevel=0.05, rot=(0, math.radians(-4), 0))
    nac = cyl('Nacelle', 0.95, 3.6, (gx - 3.3, 1.2, 2.5), paint, rot=(math.radians(90), 0, 0), verts=64, bevel=0.1)
    inlet = cyl('Inlet', 0.8, 0.05, (gx - 3.3, 3.02, 2.5), M['dark'], rot=(math.radians(90), 0, 0), verts=64)
    return [wing, nac, inlet]

def runway(length=900, y0=-100, cx=-3.0):
    am, _ = mat_textured('Asphalt', ASPH, 0.5, (0.14, 0.14, 0.145), rough=(0.7, 0.95))
    plane('Runway', 45, length, (cx, y0 + length / 2, 0), am)
    wm, wp = mat_simple('Marking', (0.82, 0.82, 0.8), 0.55)
    y = y0
    while y < y0 + length:
        box('Center', (0.9, 36, 0.004), (cx, y + 18, 0.002), wm); y += 60
    for y in range(int(y0) + 40, int(y0) + 400, 150):
        for s in (-1, 1):
            for k in range(3):
                box('TDZ', (0.9, 22, 0.004), (cx + s * (6 + k * 1.5), y, 0.002), wm)
    rm, _ = mat_simple('RubberDeposit', (0.05, 0.05, 0.052), 0.7)
    for s in (-1, 1):
        for k in range(3):
            box('Deposit', (random.uniform(0.3, 0.8), random.uniform(120, 300), 0.002), (cx + s * random.uniform(2.5, 4.5), y0 + random.uniform(150, 300), 0.003), rm)
    gm, _ = mat_textured('Grass', ['aerial_grass_rock'], 0.05, (0.12, 0.15, 0.07), rough=(0.85, 1.0))
    for s in (-1, 1): plane('Infield', 200, length, (cx + s * (22.5 + 100), y0 + length / 2, -0.02), gm)
    em, _ = mat_emit('EdgeLight', (1, 0.85, 0.6), 30)
    for yy in range(int(y0), int(y0 + length), 60):
        for s in (-1, 1): sphere('Edge', 0.12, (cx + s * 23.5, yy, 0.25), em, sub=1)

def smoke_mat(strength=3.0):
    m = bpy.data.materials.new('Smoke'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (0.92, 0.91, 0.9, 1); v.inputs['Density'].default_value = strength
    try: v.inputs['Absorption Color'].default_value = (0.85, 0.85, 0.85, 1)
    except Exception: pass
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 4
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.7; mr.inputs['To Max'].default_value = strength
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], v.inputs['Density'])
    nt.links.new(v.outputs['Volume'], o.inputs['Volume'])
    return m, mr

def smoke(points, t0, t1, mat, seed=4, n=16, speed=V):
    """Puffs born at the contact patches between t0 and t1; carried along in the wheel's wake, trailing behind it."""
    random.seed(seed)
    for i in range(n):
        tb = t0 + (t1 - t0) * i / max(1, n - 1)
        px, py = random.choice(points)(tb)
        s = sphere('Puff', 0.25, (px, py, 0.1), mat, sub=2)
        life = 1.4
        key(s, 'scale', [(tb - 0.02, Vector((0.01, 0.01, 0.01))), (tb, Vector((0.8, 1.4, 0.6))), (tb + life, Vector((2.6, 6.0, 2.0)))])
        key(s, 'location', [(tb, Vector((px, py - 0.4, 0.15))), (tb + life, Vector((px + random.uniform(-0.6, 0.6), py + speed * life - random.uniform(4, 8), 0.8)))])

def landing(a, b, tc, cam, speed=V, smoke_on=True, ground_cam=False, skid=False):
    sc = new_scene(a, b); d = dur(a, b)
    world_hdri(DUSK, 0.7, 2.2, 'dusk'); sn = sun(3.6, 14, 230, (1, 0.74, 0.5), 1.5)
    random.seed(2); runway(1100, -150)
    M = mats()
    gx = 0.0
    rig, ws = gear(M, (gx, 0, R))
    for o in airframe(M, 0.0): o.parent = rig
    h0 = 1.1
    def gy(t): return speed * t
    pts = [(0, Vector((gx, gy(0), R + (h0 if tc > 0 else 0))))]
    if tc > 0: pts.append((tc, Vector((gx, gy(tc), R))))
    pts.append((d, Vector((gx, gy(d), R))))
    key(rig, 'location', pts, interp='LINEAR')
    for w in ws:
        key(w, 'rotation_euler', [(0, Vector((0, 0, 0))), (max(tc, 0) + 0.001, Vector((0, 0, 0))), (d, Vector((-speed * (d - max(tc, 0)) / R, 0, 0)))], interp='LINEAR')
    if smoke_on:
        m, mr = smoke_mat(30.0)
        key_socket(mr.inputs['To Max'], [(tc, 30.0), (tc + 0.8, 18.0), (tc + 2.5, 1.0)])
        smoke([lambda t: (gx - 0.36, gy(t)), lambda t: (gx + 0.36, gy(t))], tc, tc + 0.45, m, n=18, speed=speed)
    if skid:
        sm, _ = mat_simple('Skid', (0.02, 0.02, 0.02), 0.8)
        for x in (gx - 0.36, gx + 0.36):
            mk = box('SkidMark', (0.3, 1.0, 0.002), (0, 0, 0), sm); mk.data.transform(Matrix.Translation((0, 0.5, 0)))
            mk.location = (x, gy(tc), 0.004); L = speed * 0.25
            key(mk, 'scale', [(tc, Vector((1, 0.01, 1))), (tc + 0.25, Vector((1, L, 1)))], interp='LINEAR')
    path = [(t, (gx + c[0], gy(t) + c[1], c[2]), (gx + q[0], gy(t) + q[1], q[2])) for t in (0, d) for (c, q) in [cam(t)]]
    camera(path, lens=cam.lens if hasattr(cam, 'lens') else 30, fstop=4, interp='LINEAR')

def S00(a, b):  # wide tracking shot: gear drops onto the runway, puff of smoke (contact ~2.3 s)
    def cam(t): return ((2.9, -4.2 + 0.5 * t / 5.2, 0.55), (-0.2, 1.5, 1.2))
    landing(a, b, 2.3, cam)

def S01(a, b):  # low close-up at the contact patch: skid + smoke + skid mark
    def cam(t): return ((3.0, -0.3, 0.6), (0.36, -0.05, 0.45))
    cam.lens = 28
    landing(a, b, 0.35, cam, skid=True)

def text(body, loc, size, mat, rot=(math.radians(90), 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot); t = bpy.context.active_object
    t.data.body = body; t.data.size = size; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'; t.data.extrude = 0.004
    t.data.materials.append(mat); return t

def hangar(strength=0.35):
    world_hdri('studio_small_09', strength, 0, 'studio')
    fm, _ = mat_textured('HangarFloor', ['concrete_floor_02', 'concrete_floor_worn_001'], 0.6, (0.35, 0.35, 0.34), rough=(0.4, 0.8), wet=0.15)
    plane('Floor', 40, 40, (0, 0, 0), fm)
    light('AREA', (-2.0, -2.5, 3.5), 650, (1, 0.97, 0.92), 3.0, rot=(math.radians(38), 0, math.radians(-38)))
    light('AREA', (2.8, 1.5, 2.0), 220, (0.75, 0.85, 1.0), 2.0, rot=(math.radians(60), 0, math.radians(120)))

def S02(a, b):  # jet tire vs car tire, pressure labels
    sc = new_scene(a, b); hangar(); d = dur(a, b); M = mats()
    jt = tire(M, (-0.45, 0, R), name='Jet'); jt.rotation_euler = (0, 0, math.radians(-25))
    ct = tire(M, (0.55, -0.2, 0.33), r=0.33, w=0.21, name='Car'); ct.rotation_euler = (0, 0, math.radians(-25))
    em, _ = mat_emit('Label', (1, 1, 1), 6); gm, _ = mat_emit('LabelHot', (1, 0.55, 0.1), 8)
    t1 = text('200 PSI', (-0.45, -0.1, 1.45), 0.2, gm); t2 = text('~33 PSI', (0.55, -0.25, 0.92), 0.13, em)
    for t, k in ((t2, 0.8), (t1, 2.0)):
        key(t, 'scale', [(k, Vector((0.01, 0.01, 0.01))), (k + 0.3, Vector((1, 1, 1)))])
    camera([(0, (0.5, -3.2, 1.05), (0.0, 0, 0.75)), (d, (0.3, -2.7, 1.0), (0.0, 0, 0.75))], lens=32, fstop=5)

def brake_wheel(M, glow_pts, loc=(0, 0, R)):
    """Inboard view of a wheel: open rim with a stack of carbon brake discs that glows."""
    rig = bpy.data.objects.new('BrakeWheel', None); link(rig); rig.location = loc
    rot = (0, math.radians(90), 0)
    casing = cyl('Casing', R - 0.01, 0.38, (0, 0, 0), M['rub'], rot=rot, verts=96, bevel=0.07)
    hole = cyl('Hole', R * 0.57, 0.6, (0, 0, 0), None, rot=rot, verts=64); hole.hide_render = True; hole.display_type = 'WIRE'
    bo = casing.modifiers.new('h', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = hole
    rim = cyl('Rim', R * 0.57, 0.36, (0, 0, 0), M['alu'], rot=rot, verts=64)
    rh = cyl('RimHole', R * 0.52, 0.5, (0, 0, 0), None, rot=rot, verts=64); rh.hide_render = True; rh.display_type = 'WIRE'
    b2 = rim.modifiers.new('h', 'BOOLEAN'); b2.operation = 'DIFFERENCE'; b2.object = rh
    cm, cp = mat_simple('Carbon', (0.06, 0.055, 0.05), 0.6, emit=(1, 0.35, 0.05), estr=0.0)
    key_socket(inp(cp, 'Emission Strength'), glow_pts)
    discs = []
    for k in range(7):
        discs.append(cyl('Disc', R * 0.5, 0.03, (-0.15 + k * 0.045, 0, 0), cm, rot=rot, verts=64, bevel=0.003))
    axle = cyl('Axle', 0.07, 0.8, (-0.3, 0, 0), M['grey'], rot=rot, verts=32)
    for o in [casing, hole, rim, rh, axle] + discs: o.parent = rig
    return rig, cp

def S03(a, b):  # night: brakes glow orange-hot inside the wheel
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('dikhololo_night', 0.25, 0, 'night')
    random.seed(2); runway(300, -150)
    rig, cp = brake_wheel(M, [(0, 0.3), (d * 0.8, 5.0)])
    pl = light('POINT', (-0.1, 0, R), 0, (1, 0.4, 0.08), 0.3); key_light(pl.data, 'energy', [(0, 3), (d * 0.8, 70)])
    light('SPOT', (-3, -4, 4), 900, (0.85, 0.9, 1.0), 0.3, spot=30);
    camera([(0, (-1.3, -1.5, 0.95), (0.0, 0, R)), (d, (-1.1, -1.3, 0.85), (0.0, 0, R))], lens=40, fstop=4.0)

def S04(a, b):  # cutaway: oxygen (red) leaves, dry nitrogen (blue) fills the tire
    sc = new_scene(a, b); hangar(0.3); d = dur(a, b); M = mats()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.42, minor_radius=0.17, major_segments=96, minor_segments=32, location=(0, 0, 0.75), rotation=(math.radians(90), 0, 0))
    tor = bpy.context.active_object; bpy.ops.object.shade_smooth()
    sol = tor.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.025
    cutb = box('Cut', (2, 1, 2), (0, -0.5, 0.75), None); cutb.hide_render = True; cutb.display_type = 'WIRE'
    bo = tor.modifiers.new('half', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cutb
    tor.data.materials.append(M['rub'])
    cyl('Rim', 0.27, 0.04, (0, 0.12, 0.75), M['alu'], rot=(math.radians(90), 0, 0), verts=64, bevel=0.005)
    nm, _ = mat_simple('N2', (0.04, 0.16, 0.9), 0.3, emit=(0.05, 0.2, 1.0), estr=0.5)
    om, _ = mat_simple('O2', (0.9, 0.06, 0.03), 0.3, emit=(1, 0.1, 0.05), estr=0.5)
    random.seed(31)
    def mol(mat, p, rot):
        s1 = sphere('A', 0.022, (0, 0, 0), mat, sub=2); s2 = sphere('B', 0.022, (0.034, 0, 0), mat, sub=2)
        e = bpy.data.objects.new('Mol', None); link(e); s1.parent = e; s2.parent = e; e.location = p; e.rotation_euler = rot
        return e
    def in_tube():
        ang = random.uniform(-math.pi, math.pi); rr = 0.42 + random.uniform(-0.11, 0.11)
        return Vector((math.cos(ang) * rr, random.uniform(-0.12, 0.02), 0.75 + math.sin(ang) * rr))
    for i in range(70):
        is_o = i % 4 == 0
        p = in_tube(); e = mol(om if is_o else nm, p, (random.random() * 3, random.random() * 3, random.random() * 3))
        p2 = p + Vector((random.uniform(-0.03, 0.03), 0, random.uniform(-0.03, 0.03)))
        if is_o:
            t0 = random.uniform(1.6, 4.0)
            key(e, 'scale', [(t0, Vector((1, 1, 1))), (t0 + 0.4, Vector((0.01, 0.01, 0.01)))])
            key(e, 'location', [(0, p), (t0 + 0.4, p + Vector((0, -0.25, 0.05)))])
        else:
            key(e, 'location', [(0, p), (d, p2)])
    for i in range(18):   # extra nitrogen arrives
        p = in_tube(); e = mol(nm, p, (random.random() * 3, random.random() * 3, random.random() * 3)); t0 = random.uniform(1.0, 3.0)
        key(e, 'scale', [(t0, Vector((0.01, 0.01, 0.01))), (t0 + 0.3, Vector((1, 1, 1)))])
    camera([(0, (0.35, -1.75, 1.0), (0, 0, 0.75)), (d, (0.15, -1.45, 0.9), (0, 0, 0.75))], lens=40, fstop=6)

def hub_face(M, melt_t=None, d=3.0, jets=False):
    """Close-up of the wheel face with three brass fuse plugs; one melts (and vents gas)."""
    rot = (0, math.radians(90), 0)
    casing = cyl('Casing', R - 0.01, 0.38, (0, 0, R), M['rub'], rot=rot, verts=96, bevel=0.07)
    for k in range(4):
        cyl('Rib', R, 0.06, (-0.12 + k * 0.08, 0, R), M['rub'], rot=rot, verts=96, bevel=0.004)
    rim = cyl('Rim', R * 0.58, 0.04, (0.2, 0, R), M['alu'], rot=rot, verts=96, bevel=0.01)
    cyl('HubCap', R * 0.2, 0.08, (0.22, 0, R), M['alu'], rot=rot, verts=64, bevel=0.015)
    brass, _ = mat_simple('Brass', (0.85, 0.62, 0.25), 0.3, 1.0)
    core_m, cp = mat_simple('PlugCore', (0.7, 0.68, 0.6), 0.4, 0.6, emit=(1, 0.35, 0.05), estr=0.0)
    cores = []
    for k in range(3):
        a = math.radians(40 + k * 120); y = math.cos(a) * R * 0.4; z = R + math.sin(a) * R * 0.4
        cyl('PlugHex', 0.028, 0.02, (0.225, y, z), brass, rot=rot, verts=6, bevel=0.002)
        c = cyl('PlugCore', 0.013, 0.024, (0.228, y, z), core_m, rot=rot, verts=24); cores.append((c, y, z))
    if melt_t is not None:
        key_socket(inp(cp, 'Emission Strength'), [(0, 0.0), (melt_t - 0.3, 6.0)])
        c, y, z = cores[0]
        key(c, 'scale', [(melt_t, Vector((1, 1, 1))), (melt_t + 0.5, Vector((0.05, 0.05, 1)))])
        hm, _ = mat_simple('Hole', (0.005, 0.005, 0.005), 0.9)
        h = cyl('Hole', 0.012, 0.024, (0.227, y, z), hm, rot=rot, verts=24)
        key(h, 'scale', [(melt_t, Vector((0.05, 0.05, 1))), (melt_t + 0.5, Vector((1, 1, 1)))])
        if jets:
            gm, _ = mat_simple('Gas', (0.9, 0.92, 0.95), 0.5, trans=0.0)
            vm, vr = smoke_mat(40.0)
            random.seed(5)
            for i in range(26):
                tb = melt_t + 0.3 + i * (d - melt_t - 0.3) / 26
                s = sphere('Jet', 0.03, (0.25, y, z), vm, sub=2)
                key(s, 'location', [(tb, Vector((0.25, y, z))), (tb + 0.6, Vector((0.9 + random.uniform(0, 0.3), y + random.uniform(-0.2, 0.2), z + random.uniform(-0.1, 0.25))))], interp='LINEAR')
                key(s, 'scale', [(tb - 0.01, Vector((0.01, 0.01, 0.01))), (tb, Vector((1, 1, 1))), (tb + 0.6, Vector((5, 5, 5)))])
    return cores

def S05(a, b):  # fuse plugs in the wheel: one heats up and its core melts away
    sc = new_scene(a, b); hangar(0.2); d = dur(a, b); M = mats()
    light('POINT', (-0.1, 0, R), 120, (1, 0.4, 0.08), 0.3)
    hub_face(M, melt_t=d * 0.6, d=d)
    y = math.cos(math.radians(40)) * R * 0.4; z = R + math.sin(math.radians(40)) * R * 0.4
    camera([(0, (0.95, -0.35, z + 0.15), (0.22, y * 0.5, z)), (d, (0.75, -0.2, z + 0.1), (0.22, y * 0.7, z))], lens=50, fstop=3.2)

def S06(a, b):  # gas jets out of the melted plug, the tire settles flat instead of bursting
    sc = new_scene(a, b); hangar(0.3); d = dur(a, b); M = mats()
    root = bpy.data.objects.new('Root', None); link(root)
    before = set(bpy.data.objects)
    hub_face(M, melt_t=0.01, d=d, jets=True)
    for o in bpy.data.objects:
        if o not in before and o.parent is None and not o.name.startswith('Jet'): o.parent = root
    key(root, 'scale', [(0.3, Vector((1, 1, 1))), (d * 0.9, Vector((1, 1.04, 0.86)))])
    camera([(0, (1.9, -1.6, 0.9), (0.1, 0, 0.5)), (d, (1.6, -1.3, 0.8), (0.1, 0, 0.48))], lens=35, fstop=5)

def S07(a, b):  # bald, worn-out tread on a stand in the hangar
    sc = new_scene(a, b); hangar(); d = dur(a, b); M = mats()
    w = tire(M, (0, 0, R + 0.02), worn=True, name='Worn')
    key(w, 'rotation_euler', [(0, Vector((0, 0, math.radians(-20)))), (d, Vector((-0.6, 0, math.radians(-20))))])
    camera([(0, (0.25, -1.0, 1.55), (0, 0, R + 0.45)), (d, (0.15, -0.8, 1.45), (0, 0, R + 0.45))], lens=35, fstop=3.5)

def S08(a, b):  # fresh tread blocks wrap around the same casing
    sc = new_scene(a, b); hangar(); d = dur(a, b); M = mats()
    w = tire(M, (0, 0, R + 0.02), worn=True, ribs=True, name='Casing')
    w.rotation_euler = (0, 0, math.radians(-20))
    newm = mat_rubber('NewTread', (0.012, 0.012, 0.013))
    n = 60; rw = 0.055
    for k in range(4):
        x = -0.38 * 0.36 + rw / 2 + k * (rw + 0.016)
        for i in range(n):
            ang = 2 * math.pi * i / n
            blk = box('Block', (rw, 2 * math.pi * R / n * 0.92, 0.012), (0, 0, 0), newm, bevel=0.002)
            blk.parent = w; blk.location = (x, math.sin(ang) * (R + 0.004), math.cos(ang) * (R + 0.004)); blk.rotation_euler = (-ang, 0, 0)
            t0 = 0.2 + (d - 0.9) * i / n
            key(blk, 'scale', [(t0, Vector((0.01, 0.01, 0.01))), (t0 + 0.15, Vector((1, 1, 1)))])
    camera([(0, (0.3, -1.1, 1.6), (0, 0, R + 0.4)), (d, (0.2, -0.9, 1.5), (0, 0, R + 0.4))], lens=35, fstop=4)

def S09(a, b):  # dusk rollout: gear rolls past, lights glowing
    def cam(t): return ((-2.6, 4.5 - 0.8 * t, 0.6), (0.0, 0.0, 1.3))
    cam.lens = 30
    landing(a, b, 0.0, cam, speed=32.0, smoke_on=False)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09]

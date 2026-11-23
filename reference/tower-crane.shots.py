# Shots for "This Crane Lifts Itself Into the Sky" (how a tower crane works, problem -> fix chain).
# Z up, metres. The crane mast stands at the origin, the working jib points along local +X of the slewing unit.
# Person faces -Y at rot_z=0 (rot_z = theta faces (sin theta, -cos theta)). t = seconds from the shot start.
import bmesh
from mathutils import Matrix, Euler

def dur(a, b): return (b - a) / FPS

MW = 2.0          # mast width (lattice square)
SEC = 6.0         # one mast section (about 20 ft)
PADT = 0.25       # pad top above the ground
NSEC = 7
H = PADT + NSEC * SEC   # mast top (slewing unit sits here)
JL = 44.0         # working jib length
CJ = 15.0         # counter-jib length
JZ = 1.6          # jib bottom above the slewing ring (slew-local)

# ---------------------------------------------------------------- materials
def paint_mat(name, col, rough=0.45, grime=0.3, metal=0.3):
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 1.2; n.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * (1 - grime) for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    return m

def facade_mat(name, night=False, base=(0.55, 0.55, 0.56), lit=0.18, seed=0.0):
    """Office facade: wall bands + window grid (brick texture on (x+y, z)); at night some windows glow."""
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs['Vector'])
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(sp.outputs['X'], ad.inputs[0]); nt.links.new(sp.outputs['Y'], ad.inputs[1])
    cb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(ad.outputs['Value'], cb.inputs['X']); nt.links.new(sp.outputs['Z'], cb.inputs['Y'])
    cb.inputs['Z'].default_value = seed
    def brick():
        b = nt.nodes.new('ShaderNodeTexBrick'); b.offset = 0.0; b.squash = 1.0
        b.inputs['Scale'].default_value = 1.0; b.inputs['Mortar Size'].default_value = 0.5
        b.inputs['Brick Width'].default_value = 3.0; b.inputs['Row Height'].default_value = 3.8
        b.inputs['Mortar Smooth'].default_value = 0.05
        nt.links.new(cb.outputs['Vector'], b.inputs['Vector']); return b
    b = brick()
    b.inputs['Color1'].default_value = (0.03, 0.045, 0.06, 1); b.inputs['Color2'].default_value = (0.06, 0.08, 0.1, 1)
    b.inputs['Mortar'].default_value = (*base, 1)
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sn.inputs['Vector'])
    roof = nt.nodes.new('ShaderNodeMath'); roof.operation = 'GREATER_THAN'; roof.inputs[1].default_value = 0.5
    nt.links.new(sn.outputs['Z'], roof.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(roof.outputs['Value'], mx.inputs['Factor'])
    nt.links.new(b.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = (base[0] * 0.7, base[1] * 0.7, base[2] * 0.7, 1)
    nt.links.new(mx.outputs[2], p.inputs['Base Color'])
    mxf = nt.nodes.new('ShaderNodeMath'); mxf.operation = 'MAXIMUM'
    nt.links.new(b.outputs['Fac'], mxf.inputs[0]); nt.links.new(roof.outputs['Value'], mxf.inputs[1])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.06; rr.inputs['To Max'].default_value = 0.8
    nt.links.new(mxf.outputs['Value'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
    if night:
        b2 = brick(); b2.inputs['Color1'].default_value = (1, 1, 1, 1); b2.inputs['Color2'].default_value = (0, 0, 0, 1)
        b2.inputs['Mortar'].default_value = (0, 0, 0, 1); b2.inputs['Bias'].default_value = 0.0
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 1.0 - lit
        bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(b2.outputs['Color'], bw.inputs['Color']); nt.links.new(bw.outputs['Val'], gt.inputs[0])
        mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 2.0
        nr = nt.nodes.new('ShaderNodeMath'); nr.operation = 'SUBTRACT'; nr.inputs[0].default_value = 1.0
        nt.links.new(mxf.outputs['Value'], nr.inputs[1])
        mw = nt.nodes.new('ShaderNodeMath'); mw.operation = 'MULTIPLY'
        nt.links.new(gt.outputs['Value'], mw.inputs[0]); nt.links.new(nr.outputs['Value'], mw.inputs[1])
        nt.links.new(mw.outputs['Value'], mu.inputs[0])
        inp(p, 'Emission Color', 'Emission').default_value = (1.0, 0.78, 0.5, 1)
        nt.links.new(mu.outputs['Value'], inp(p, 'Emission Strength'))
    return m

def mats(night=False):
    M = {}
    M['yellow'] = paint_mat('CraneYellow', (0.86, 0.58, 0.03), 0.42, 0.22, 0.15)
    M['white'] = paint_mat('CabWhite', (0.8, 0.8, 0.78), 0.4, 0.15, 0.0)
    M['red'] = paint_mat('HookRed', (0.62, 0.05, 0.03), 0.4, 0.2, 0.0)
    M['conc'] = mat_textured('Concrete', ['concrete_floor_02'], 0.22, (0.55, 0.54, 0.52), tint=(1.0, 0.98, 0.95))[0]
    M['block'] = mat_textured('Block', ['concrete_floor_02'], 0.5, (0.6, 0.6, 0.58), tint=(1.25, 1.25, 1.25))[0]
    M['ground'] = mat_textured('Ground', ['dry_ground_rocks'], 0.2, (0.35, 0.3, 0.24), tint=(0.62, 0.58, 0.54))[0]
    M['asphalt'] = mat_textured('CityGround', ['asphalt_02'], 0.12, (0.12, 0.12, 0.12), tint=(0.75, 0.75, 0.75))[0]
    M['gravel'] = mat_textured('Gravel', ['gravel_floor_02'], 0.5, (0.4, 0.4, 0.38), tint=(0.55, 0.53, 0.5))[0]
    M['steel'] = mat_simple('Steel', (0.42, 0.42, 0.43), 0.32, 1.0)[0]
    M['dark'] = mat_simple('DarkSteel', (0.05, 0.05, 0.055), 0.5, 0.6)[0]
    M['chrome'] = mat_simple('Chrome', (0.85, 0.85, 0.87), 0.08, 1.0)[0]
    M['rust'] = mat_textured('Rust', ['rusty_metal_02'], 2.0, (0.25, 0.13, 0.07), tint=(0.7, 0.55, 0.45))[0]
    M['plate'] = mat_textured('Plate', ['metal_plate'], 1.0, (0.3, 0.3, 0.3), tint=(0.6, 0.6, 0.6))[0]
    M['beam'] = mat_textured('BeamSteel', ['rusty_metal_02'], 1.0, (0.2, 0.12, 0.08), tint=(0.5, 0.36, 0.3))[0]
    M['win'] = mat_simple('CabGlass', (0.02, 0.03, 0.04), 0.05, 0.8)[0]
    M['rope'] = mat_simple('Rope', (0.15, 0.15, 0.16), 0.35, 1.0)[0]
    M['facade'] = facade_mat('Facade', night, (0.6, 0.6, 0.6), seed=0.3)
    M['facade2'] = facade_mat('Facade2', night, (0.42, 0.4, 0.38), seed=1.7)
    M['facade3'] = facade_mat('Facade3', night, (0.7, 0.68, 0.64), seed=3.1)
    M['redlamp'] = mat_emit('RedLamp', (1, 0.05, 0.02), 30)[0]
    return M

# ---------------------------------------------------------------- lattice geometry
def strut(bm, p, q, r):
    p = Vector(p); q = Vector(q); d = q - p; L = d.length
    if L < 1e-6: return
    rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((p + q) / 2) @ rot @ Matrix.Diagonal((r, r, L, 1)))

def cube(bm, size, loc):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(loc) @ Matrix.Diagonal((*size, 1)))

def bm_obj(name, bm, mat, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); link(e); e.location = loc
    if parent: e.parent = parent
    return e

def mast_bm(bm, z0, n, w=MW, r=0.14, bay=2.0):
    h = w / 2; C = [(-h, -h), (h, -h), (h, h), (-h, h)]
    for x, y in C: strut(bm, (x, y, z0), (x, y, z0 + n * SEC), r)
    nb = int(round(n * SEC / bay))
    for k in range(nb + 1):
        z = z0 + k * bay
        for i in range(4):
            (x0, y0), (x1, y1) = C[i], C[(i + 1) % 4]
            strut(bm, (x0, y0, z), (x1, y1, z), r * 0.6)
            if k < nb:
                if k % 2 == 0: strut(bm, (x0, y0, z), (x1, y1, z + bay), r * 0.55)
                else: strut(bm, (x1, y1, z), (x0, y0, z + bay), r * 0.55)

def mast_obj(M, z0, n, name='Mast', parent=None):
    bm = bmesh.new(); mast_bm(bm, z0, n)
    return bm_obj(name, bm, M['yellow'], parent)

def jib_bm(bm, x0, x1, z0, wb=1.5, ht=1.7, r=0.11, bay=2.0):
    n = int((x1 - x0) / bay)
    for s in (-1, 1): strut(bm, (x0, s * wb / 2, z0), (x1, s * wb / 2, z0), r)
    strut(bm, (x0, 0, z0 + ht), (x1 - 1.0, 0, z0 + ht), r)
    strut(bm, (x1 - 1.0, 0, z0 + ht), (x1, 0, z0), r * 0.7)
    for k in range(n + 1):
        x = x0 + k * bay
        if x > x1 - 1.0: break
        strut(bm, (x, -wb / 2, z0), (x, wb / 2, z0), r * 0.55)
        for s in (-1, 1): strut(bm, (x, s * wb / 2, z0), (x, 0, z0 + ht), r * 0.5)
        if k < n:
            xb = x + bay
            for s in (-1, 1): strut(bm, (x, s * wb / 2, z0), (xb, 0, z0 + ht), r * 0.45)

def crane(M, slew_deg=0.0, trolley=18.0, drop=10.0, load='beam', blocks=True, nsec=NSEC, cab=True, lights=False, base_pad=True):
    """Returns dict(root, slew, trolley, hook, rope, top). root sits at the ground under the mast."""
    top = PADT + nsec * SEC
    root = empty('CraneRoot')
    mast_obj(M, PADT, nsec, parent=root)
    if base_pad:
        pad = box('Pad', (9, 9, 1.6), (0, 0, PADT - 0.8), M['conc'], bevel=0.02, segs=1); pad.parent = root
    slew = empty('Slew', (0, 0, top), root); slew.rotation_euler = (0, 0, math.radians(slew_deg))
    # slewing unit + turntable
    bm = bmesh.new()
    cube(bm, (2.6, 2.6, 0.5), (0, 0, 0.25)); cube(bm, (2.2, 2.2, 1.1), (0, 0, 1.05))
    bm_obj('SlewUnit', bm, M['yellow'], slew)
    ring = cyl('Ring', 1.25, 0.25, (0, 0, 0.55), M['dark'], verts=48); ring.parent = slew
    # working jib + counter-jib
    bm = bmesh.new(); jib_bm(bm, 1.1, JL, JZ); bm_obj('Jib', bm, M['yellow'], slew)
    bm = bmesh.new()
    for s in (-1, 1): strut(bm, (-1.1, s * 1.0, JZ + 0.2), (-CJ, s * 1.0, JZ + 0.2), 0.3)
    for k in range(int(CJ / 1.5)): strut(bm, (-1.2 - k * 1.5, -1.0, JZ + 0.2), (-1.2 - k * 1.5, 1.0, JZ + 0.2), 0.14)
    for s in (-1, 1): strut(bm, (-1.1, s * 1.35, JZ + 1.2), (-CJ + 5, s * 1.35, JZ + 1.2), 0.04)   # hand rails
    bm_obj('CounterJib', bm, M['yellow'], slew)
    gr = plane('Grating', CJ - 1.2, 2.0, (-(CJ + 1.2) / 2, 0, JZ + 0.36), M['plate']); gr.parent = slew
    # winch drum box on the counter-jib
    wn = box('Winch', (1.6, 1.4, 1.0), (-6.5, 0, JZ + 0.86), M['white'], bevel=0.04, segs=2); wn.parent = slew
    B = []
    if blocks:
        for i in range(4):
            b = box('CW', (0.85, 2.5, 2.8), (-CJ + 0.55 + i * 0.9, 0, JZ + 0.2 - 0.6), M['block'], bevel=0.03, segs=1); b.parent = slew; B.append(b)
    # tower head (apex) + pendant ties
    bm = bmesh.new(); ap = (0, 0, JZ + 8.5)
    for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)): strut(bm, (x, y, JZ - 0.2), ap, 0.16)
    for k in (2.5, 5.0):
        f = k / 8.7; hw = 1 - f
        for (x0, y0), (x1, y1) in (((-hw, -hw), (hw, -hw)), ((hw, -hw), (hw, hw)), ((hw, hw), (-hw, hw)), ((-hw, hw), (-hw, -hw))):
            strut(bm, (x0, y0, JZ + k), (x1, y1, JZ + k), 0.08)
    bm_obj('Apex', bm, M['yellow'], slew)
    bm = bmesh.new()
    strut(bm, ap, (JL * 0.5, 0, JZ + 1.7), 0.06); strut(bm, ap, (JL * 0.82, 0, JZ + 1.7), 0.05)
    for s in (-1, 1): strut(bm, ap, (-CJ + 1.0, s * 1.0, JZ + 0.4), 0.06)
    bm_obj('Pendants', bm, M['dark'], slew)
    if cab:
        c = box('Cab', (2.0, 1.9, 2.2), (2.0, -2.05, 0.35 + 1.1), M['white'], bevel=0.08, segs=2); c.parent = slew
        w = box('CabWin', (0.08, 1.7, 1.4), (3.0, -2.05, 1.7), M['win'], bevel=0.02, segs=1); w.parent = slew
        w2 = box('CabWin2', (1.7, 0.06, 1.2), (2.0, -3.0, 1.7), M['win'], bevel=0.02, segs=1); w2.parent = slew
    if lights:
        for p in ((0, 0, JZ + 8.7), (JL, 0, JZ + 0.2), (-CJ, 0, JZ + 1.5)):
            s = sphere('Lamp', 0.22, p, M['redlamp'], sub=2); s.parent = slew
    # trolley + hoist ropes + hook block + load
    tr = empty('Trolley', (trolley, 0, JZ - 0.1), slew)
    tb = box('TrolleyBody', (1.8, 1.9, 0.55), (0, 0, -0.2), M['yellow'], bevel=0.03, segs=1); tb.parent = tr
    rope = bm_rope(M, tr)
    rope.scale = (1, 1, drop)
    hook = empty('Hook', (0, 0, -drop), tr)
    hb = box('HookBlock', (0.9, 0.5, 1.1), (0, 0, -0.45), M['red'], bevel=0.06, segs=2); hb.parent = hook
    hk = cyl('HookStem', 0.08, 0.5, (0, 0, -1.2), M['dark'], verts=16); hk.parent = hook
    if load == 'beam':
        L = empty('Load', (0, 0, -3.6), hook)
        bm = bmesh.new()
        for s in (-1, 1):
            strut(bm, (0, 0, -1.3), (s * 2.8, 0, -3.3), 0.035)   # slings
        cube(bm, (8.5, 0.32, 0.04), (0, 0, -3.32)); cube(bm, (8.5, 0.32, 0.04), (0, 0, -3.88)); cube(bm, (8.5, 0.03, 0.56), (0, 0, -3.6))
        bo = bm_obj('Beam', bm, M['beam'], hook)
    elif load == 'bucket':
        b = cyl('Bucket', 0.9, 1.6, (0, 0, -2.6), M['dark'], verts=32); b.parent = hook
        bm = bmesh.new()
        for s in (-1, 1): strut(bm, (0, 0, -1.3), (s * 0.85, 0, -1.8), 0.03)
        bm_obj('Bail', bm, M['dark'], hook)
    elif load == 'section':
        bm = bmesh.new(); mast_bm(bm, -1.6 - SEC, 1)
        for s in (-1, 1):
            for q in (-1, 1): strut(bm, (0, 0, -1.3), (s * MW / 2, q * MW / 2, -1.6), 0.03)
        bm_obj('NewSection', bm, M['yellow'], hook)
    return dict(root=root, slew=slew, trolley=tr, hook=hook, rope=rope, top=top, blocks=B)

def bm_rope(M, parent):
    bm = bmesh.new()
    for y in (-0.22, 0.22): strut(bm, (0, y, -0.4), (0, y, -1.0), 0.03)
    o = bm_obj('Rope', bm, M['rope'], parent)
    # mesh spans z -0.4..-1.0; rebuild so it spans 0..-1 exactly
    for v in o.data.vertices: v.co.z = 0.0 if v.co.z > -0.7 else -1.0
    return o

def set_drop(C, pts):
    key(C['rope'], 'scale', [(t, Vector((1, 1, d))) for t, d in pts])
    key(C['hook'], 'location', [(t, Vector((0, 0, -d))) for t, d in pts])

# ---------------------------------------------------------------- site + city
def ground(M, size=1400):
    plane('Ground', size, size, (0, 0, 0), M['asphalt'])

def site(M, gravel=True):
    plane('SiteDirt', 110, 110, (0, 0, 0.01), M['ground'])
    if gravel: plane('SiteGravel', 14, 14, (0, 0, 0.02), M['gravel'])

def city(M, seed=5, rmin=70, rmax=420, n=120, hmax=130, avoid=None, cam=None):
    random.seed(seed); out = []
    fac = [M['facade'], M['facade2'], M['facade3']]
    for i in range(n):
        a = random.uniform(0, 2 * math.pi); r = random.uniform(rmin, rmax)
        x, y = r * math.cos(a), r * math.sin(a)
        if avoid and avoid(x, y): continue
        if cam and math.hypot(x - cam[0], y - cam[1]) < 45: continue
        w = random.uniform(18, 40); d = random.uniform(18, 40); h = random.uniform(15, hmax) * (0.5 + 0.5 * random.random())
        o = box('Bldg', (w, d, h), (x, y, h / 2), random.choice(fac)); o.rotation_euler = (0, 0, random.uniform(-0.15, 0.15))
        out.append(o)
    return out

def frame_building(M, x0, y0, nf, w=20.0, d=16.0, fh=3.6, name='Frame'):
    """Concrete frame under construction: one object per floor (columns + slab on top), origin at the floor base."""
    F = []
    for k in range(nf):
        bm = bmesh.new()
        cube(bm, (w, d, 0.3), (0, 0, fh - 0.15))
        for i in range(5):
            for j in range(4):
                cx = -w / 2 + 0.5 + i * (w - 1) / 4; cy = -d / 2 + 0.5 + j * (d - 1) / 3
                cube(bm, (0.55, 0.55, fh - 0.3), (cx, cy, (fh - 0.3) / 2))
        o = bm_obj(f'{name}{k}', bm, M['conc']); o.location = (x0, y0, k * fh); F.append(o)
    return F

def day(rot=30, sun_e=2.2, elev=38, azim=150, col=(1, 0.96, 0.9), s=0.8):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', s, math.radians(rot)); sun(sun_e, elev, azim, color=col)

def worker(name, loc, rot_deg, outfit='worker'):
    return person(name, loc=loc, rot_z=math.radians(rot_deg), outfit=outfit, stance='relax')

def look_up(arm, t=0.0):
    pose(arm, t, {'neck01': (-22, 0, 0)})

def tilt(C, pts):
    """Tip the whole crane about its +X foot edge: rotation about Y (positive = toward +X)."""
    piv = empty('Pivot', (4.5, 0, 0)); C['root'].parent = piv; C['root'].location = (-4.5, 0, 0)
    key(piv, 'rotation_euler', [(t, Vector((0, math.radians(a), 0))) for t, a in pts])
    return piv

# ---------------------------------------------------------------- shots
def S00(a, b):  # no counterweight: a steel beam hangs far out on the jib and the whole crane slowly starts to tip; worker looks up
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(200, 2.4, 40, 210)
    ground(M); site(M); city(M, seed=3, rmin=110)
    C = crane(M, slew_deg=55, trolley=32, drop=16, load='beam', blocks=False)
    tilt(C, [(0, 0.0), (d * 0.3, 1.0), (d, 9.0)])
    arm = worker('Worker', (3.5, -38.0, 0), 175)
    look_up(arm, 0.0); pose(arm, d * 0.6, {'neck01': (-26, 0, 0), 'spine02': (-6, 0, 0)})
    camera([(0, (6.0, -47.0, 1.6), (8.0, 0.0, 24.0)), (d, (5.6, -48.0, 1.5), (8.5, 0.0, 23.5))], lens=20)

def S01(a, b):  # high on the counter-jib: concrete counterweight blocks are lowered onto it one by one; a worker points
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(200, 2.4, 40, 210)
    ground(M); city(M, seed=3, rmin=80)
    C = crane(M, slew_deg=0, trolley=12, drop=8, load='none', blocks=True)
    for i, blk in enumerate(C['blocks']):
        p0 = blk.location.copy(); tl = (0.9, 1.5, 1.5, 1.5)[i]
        if i < 2:
            key(blk, 'location', [(0, p0 + Vector((0, 0, 6))), (tl - 0.55, p0 + Vector((0, 0, 1.2))), (tl, p0)])
    arm = worker('Worker', (-8.6, 0.5, H + JZ + 0.36), -100)
    pose(arm, 0.3, STANCES['relax']); pose(arm, 1.2, STANCES['point_r'])
    camera([(0, (-4.5, -9.5, H + 4.6), (-12.5, 0, H + 1.2)), (d, (-5.2, -9.0, H + 4.4), (-12.5, 0, H + 1.2))], lens=26, fstop=8)

def S02(a, b):  # at the foot of the mast looking straight up the skinny lattice tower; worker beside it for scale
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(120, 2.4, 45, 160)
    ground(M); site(M); city(M, seed=3, rmin=110)
    C = crane(M, slew_deg=60, trolley=20, drop=10, load='bucket')
    arm = worker('Worker', (2.6, -2.2, PADT), 150)
    look_up(arm, 0.0)
    camera([(0, (5.2, -5.4, 1.2), (0.0, 0.0, 30.0)), (d, (5.0, -5.2, 1.0), (0.0, 0.0, 34.0))], lens=16)

def S03(a, b):  # close at the mast foot: anchor bolts and nuts tighten into the huge concrete pad; worker crouches with a wrench
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(120, 2.4, 35, 160)
    ground(M); site(M)
    C = crane(M, slew_deg=60, trolley=20, drop=10, load='bucket', nsec=2, cab=False)
    # fish-plate base: steel plates under each leg + 4 bolts + nuts per leg
    h = MW / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            box('BasePlate', (0.7, 0.7, 0.06), (sx * h, sy * h, PADT + 0.03), M['dark'], bevel=0.01, segs=1)
            for dx in (-0.22, 0.22):
                for dy in (-0.22, 0.22):
                    bx, by = sx * h + dx, sy * h + dy
                    cyl('Bolt', 0.03, 0.22, (bx, by, PADT + 0.13), M['steel'], verts=12)
                    nut = cyl('Nut', 0.055, 0.06, (bx, by, PADT + 0.24), M['steel'], verts=6)
                    if sx == 1 and sy == -1:
                        key(nut, 'location', [(0, Vector((bx, by, PADT + 0.24))), (0.4, Vector((bx, by, PADT + 0.24))), (1.2, Vector((bx, by, PADT + 0.095)))])
                        key(nut, 'rotation_euler', [(0, Vector((0, 0, 0))), (0.4, Vector((0, 0, 0))), (1.2, Vector((0, 0, 9.0)))])
                    else:
                        nut.location.z = PADT + 0.095
    arm = worker('Worker', (2.3, -1.9, PADT), 60)
    pose(arm, 0.0, STANCES['work_low'])
    wr = box('Wrench', (0.05, 0.4, 0.03), (0, 0, 0), M['steel']); hold(arm, wr, 'wrist.R', (0, 0.12, 0), (0, 0, 0))
    camera([(0, (2.4, -3.4, 0.9), (1.0, -1.0, 0.25)), (d, (5.5, -9.5, 3.6), (0.6, -0.6, 0.6))], lens=26, fstop=4.0)

def S04(a, b):  # under the jib: the trolley rolls a heavy concrete bucket far out and the jib starts to dip
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(210, 2.4, 42, 230)
    ground(M); city(M, seed=3, rmin=80)
    C = crane(M, slew_deg=0, trolley=10, drop=12, load='bucket')
    key(C['trolley'], 'location', [(0, Vector((10, 0, JZ - 0.1))), (0.35, Vector((10, 0, JZ - 0.1))), (d, Vector((40, 0, JZ - 0.1)))])
    tilt(C, [(0, 0.0), (d * 0.55, 0.0), (d, 2.2)])
    camera([(0, (-2.0, -9.0, H - 7.0), (16.0, 0, H)), (d, (-1.5, -9.5, H - 7.3), (24.0, 0, H - 1.0))], lens=22)

def S05(a, b):  # inside the cab: the load gauge climbs from green into red, a red warning lamp flashes, the jib out the window
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(210, 2.4, 42, 230)
    ground(M); city(M, seed=3, rmin=80)
    C = crane(M, slew_deg=0, trolley=34, drop=14, load='bucket', cab=False)
    s = C['slew']
    # cab shell around the camera (open front window), console with a gauge display
    shell = []
    for sz, lc in (((2.6, 0.08, 2.4), (2.0, -1.0, 1.5)), ((2.6, 0.08, 2.4), (2.0, -3.1, 1.5)), ((2.6, 2.2, 0.08), (2.0, -2.05, 2.7)),
                   ((2.6, 2.2, 0.08), (2.0, -2.05, 0.3)), ((0.08, 2.2, 2.4), (0.7, -2.05, 1.5))):
        o = box('CabWall', sz, lc, M['white']); o.parent = s; shell.append(o)
    for y in (-1.05, -3.05):
        f = box('Pillar', (0.1, 0.1, 2.4), (3.3, y, 1.5), M['dark']); f.parent = s
    sill = box('Sill', (0.1, 2.2, 0.5), (3.3, -2.05, 0.55), M['dark']); sill.parent = s
    con = box('Console', (0.55, 1.2, 0.18), (2.9, -2.05, 0.95), M['dark'], bevel=0.02, segs=1); con.parent = s; con.rotation_euler = (0, math.radians(-25), 0)
    scr = box('Screen', (0.04, 0.62, 0.42), (2.95, -2.05, 1.28), mat_simple('ScreenBack', (0.01, 0.01, 0.012), 0.3)[0]); scr.parent = s
    scr.rotation_euler = (0, math.radians(-18), 0)
    bars = []
    for i in range(10):
        col = (0.1, 1.0, 0.2) if i < 6 else ((1.0, 0.7, 0.05) if i < 8 else (1.0, 0.08, 0.03))
        bm_ = mat_emit(f'Bar{i}', col, 0.0); br = box(f'Bar{i}', (0.012, 0.045, 0.24), (-0.03, -0.25 + i * 0.055, -0.02), bm_[0])
        br.parent = scr; bars.append((br, bm_[1], i))
    for br, em, i in bars:
        ton = 0.3 + i * 0.17
        key_socket(em.inputs['Strength'], [(0, 0.0), (max(0.0, ton - 0.05), 0.0), (ton, 6.0)], 'CONSTANT')
    lamp = sphere('Warn', 0.06, (2.7, -1.3, 1.9), None, sub=2); lamp.parent = s
    lm, le = mat_emit('WarnLamp', (1, 0.05, 0.02), 0.0); lamp.data.materials.append(lm)
    pts = [(0, 0.0), (1.85, 0.0)]; t = 1.9
    while t < d:
        pts += [(t, 40.0), (t + 0.18, 0.0)]; t += 0.36
    key_socket(le.inputs['Strength'], pts, 'CONSTANT')
    rl = light('POINT', (2.7, -1.35, 1.85), 0.0, (1, 0.1, 0.05), 0.05); rl.parent = s
    key_light(rl.data, 'energy', [(p[0], p[1] * 0.6) for p in pts])
    for fc in fcurves_of(rl.data.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    fill = light('AREA', (1.4, -2.05, 2.4), 25.0, (1, 0.97, 0.92), 1.2); fill.parent = s; fill.rotation_euler = (0, 0, 0)
    camera([(0, (1.25, -2.0, H + 1.75), (3.0, -2.05, H + 1.25)), (d, (1.2, -2.0, H + 1.8), (3.0, -2.08, H + 1.25))], lens=22, fstop=2.8)

def S06(a, b):  # time-lapse: the concrete frame building rises floor by floor beside the crane until it is taller than it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(160, 2.4, 30, 200)
    ground(M); site(M); city(M, seed=9, rmin=130)
    C = crane(M, slew_deg=150, trolley=22, drop=8, load='bucket')
    nf = 15
    Fl = frame_building(M, -2.0, 13.5, nf)
    for k, f in enumerate(Fl):
        tk = 0.2 + k * (d - 0.6) / nf
        key(f, 'scale', [(0, Vector((1, 1, 0.0001))), (tk, Vector((1, 1, 0.0001))), (tk + 0.12, Vector((1, 1, 1)))], interp='LINEAR')
    arm = worker('Worker', (9.0, -24.0, 0), 160)
    look_up(arm)
    camera([(0, (22.0, -62.0, 2.0), (-1.0, 6.0, 27.0)), (d, (21.0, -60.0, 2.0), (-1.0, 6.0, 30.0))], lens=24)

def climb_frame(M, z0, parent=None):
    """Climbing frame (sleeve) around the top mast section: 4 outer columns, platform, two hydraulic cylinders."""
    bm = bmesh.new(); w = MW / 2 + 0.45
    C4 = [(-w, -w), (w, -w), (w, w), (-w, w)]
    for x, y in C4: strut(bm, (x, y, z0), (x, y, z0 + SEC + 1.5), 0.2)
    for z in (z0, z0 + 2.5, z0 + 5.0, z0 + SEC + 1.5):
        for i in range(4):
            (x0_, y0_), (x1_, y1_) = C4[i], C4[(i + 1) % 4]; strut(bm, (x0_, y0_, z), (x1_, y1_, z), 0.14)
    o = bm_obj('ClimbFrame', bm, M['white'], parent)
    pl = box('Platform', (5.6, 5.6, 0.08), (0, 0, z0 + 0.04), M['plate']); pl.parent = parent
    return o

def rams(M, zf, ext0, ext1=None, d=1.0, parent_yoke=None):
    """Two hydraulic rams on the climbing frame; rod length ext0 -> ext1 (from the barrel top at zf+1.8)."""
    for s in (-1, 1):
        cyl('RamBarrel', 0.16, 2.8, (s * 1.65, -1.65, zf + 0.4), M['dark'], verts=24)
        rod = cyl('RamRod', 0.09, 1.0, (s * 1.65, -1.65, zf + 1.8), M['chrome'], verts=24)
        rod.data.transform(Matrix.Translation((0, 0, 0.5))); rod.location.z = zf + 1.8
        if ext1 is None: rod.scale = (1, 1, ext0)
        else: key(rod, 'scale', [(0, Vector((1, 1, ext0))), (0.6, Vector((1, 1, ext0))), (d, Vector((1, 1, ext1)))], interp='LINEAR')
        y = box('Yoke', (0.5, 0.5, 0.3), (s * 1.65, -1.65, zf + 1.8 + ext0 + 0.15), M['white'])
        if parent_yoke: y.parent = parent_yoke

def S07(a, b):  # high on the climbing frame: hydraulic rams push the whole top of the crane up one section; worker watches
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(220, 2.4, 38, 240)
    ground(M); city(M, seed=9, rmin=110, n=90)
    zf = PADT + (NSEC - 1) * SEC   # the climbing frame sits around the top section
    C = crane(M, slew_deg=-60, trolley=14, drop=6, load='none', nsec=NSEC - 1)
    up = empty('UpRig', (0, 0, 0))
    bm = bmesh.new(); mast_bm(bm, zf, 1); bm_obj('TopSec', bm, M['yellow'], up)
    C['slew'].parent = up; C['slew'].location = (0, 0, zf + SEC)
    climb_frame(M, zf - 1.0)
    rams(M, zf, 0.7, 0.7 + SEC, d, parent_yoke=up)
    key(up, 'location', [(0, Vector((0, 0, 0))), (0.6, Vector((0, 0, 0))), (d, Vector((0, 0, SEC)))], interp='LINEAR')
    arm = worker('Worker', (1.3, -2.55, zf - 0.92), 30)
    look_up(arm, 0.0)
    camera([(0, (6.5, -10.0, zf + 1.0), (0.0, 0.0, zf + 3.6)), (d, (6.6, -10.6, zf + 2.0), (0.0, 0.0, zf + 6.0))], lens=24, fstop=3.5)

def S08(a, b):  # same height: a new yellow mast section rolls into the gap under the raised top and seats with a slam
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(220, 2.4, 38, 240)
    ground(M); city(M, seed=9, rmin=110, n=90)
    zf = PADT + (NSEC - 1) * SEC
    C = crane(M, slew_deg=-60, trolley=10, drop=5, load='none', nsec=NSEC - 1)
    C['slew'].location = (0, 0, zf + 2 * SEC)
    bm = bmesh.new(); mast_bm(bm, zf + SEC, 1); bm_obj('TopSec', bm, M['yellow'])
    climb_frame(M, zf - 1.0)
    rams(M, zf, 0.7 + SEC)
    ns = empty('NewSec', (0, -7.0, zf + 0.12))
    bm = bmesh.new(); mast_bm(bm, 0, 1); bm_obj('NewSection', bm, M['yellow'], ns)
    rail = box('MonoRail', (0.25, 9.0, 0.35), (0, -6.0, zf + SEC + 0.2), M['dark'])
    key(ns, 'location', [(0, Vector((0, -7.0, zf + 0.12))), (1.55, Vector((0, 0, zf + 0.12))), (1.8, Vector((0, 0, zf)))])
    arm = worker('Worker', (2.4, -2.55, zf - 0.92), -20)
    pose(arm, 0.2, STANCES['relax']); pose(arm, 0.9, STANCES['point_r'])
    camera([(0, (9.5, -9.0, zf + 2.0), (0.0, -2.0, zf + 3.6)), (d, (9.0, -8.6, zf + 2.2), (0.0, -1.5, zf + 3.6))], lens=24, fstop=3.5)

def S09(a, b):  # night: the parked crane, red lamps glowing, slowly swings round with the wind over the lit city
    sc = new_scene(a, b); d = dur(a, b); M = mats(night=True)
    world_hdri('dikhololo_night', 0.5, math.radians(40), 'night')
    moon = sun(0.08, 30, 60, color=(0.6, 0.7, 1.0))
    ground(M); city(M, seed=9, rmin=60, n=140, cam=(-30, -46))
    C = crane(M, slew_deg=-20, trolley=6, drop=4, load='none', lights=True)
    key(C['slew'], 'rotation_euler', [(0, Vector((0, 0, math.radians(-20)))), (d, Vector((0, 0, math.radians(28))))])
    fl = light('SPOT', (0, -12, 2), 2500, (1, 0.85, 0.6), 0.4, spot=40); aim(fl, (0, 0, 30))
    camera([(0, (-30.0, -46.0, 2.0), (6.0, 0.0, 33.0)), (d, (-31.0, -47.0, 2.0), (6.0, 0.0, 34.0))], lens=22)

def S10(a, b):  # golden dusk: the balanced crane lifts a beam smoothly; worker in the foreground watches it rise
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(190)); sun(1.2, 6, 190, color=(1, 0.66, 0.42))
    ground(M); site(M); city(M, seed=5, rmin=90)
    C = crane(M, slew_deg=-40, trolley=24, drop=24, load='beam')
    set_drop(C, [(0, 30.0), (d, 22.0)])
    key(C['slew'], 'rotation_euler', [(0, Vector((0, 0, math.radians(-40)))), (d, Vector((0, 0, math.radians(-30))))])
    arm = worker('Worker', (-7.0, -13.0, 0), 215)
    look_up(arm)
    camera([(0, (-10.0, -22.0, 1.4), (6.0, 4.0, 22.0)), (d, (-11.0, -21.0, 1.4), (6.0, 4.0, 23.0))], lens=20)

def S11(a, b):  # morning: a man in casual clothes walks on the sidewalk, the crane over the street now points a new way
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(70, 2.6, 20, 95, col=(1, 0.9, 0.78))
    ground(M)
    plane('Sidewalk', 5, 400, (12, 0, 0.12), M['conc'])
    city(M, seed=12, rmin=80, n=120, avoid=lambda x, y: abs(x - 12) < 45)
    for i, y in enumerate((-40, -8, 26, 70, 110)):
        h = (32, 55, 24, 70, 48)[i]
        box('StreetBldg', (18, 30, h), (-6, y, h / 2), M['facade' if i % 2 else 'facade3'])
    C = crane(M, slew_deg=-15, trolley=20, drop=6, load='none')
    C['root'].location = (34, 58, 0)
    Fl = frame_building(M, 34.0, 72.0, 10)
    arm = worker('Walker', (12.0, 7.0, 0.12), 0, outfit='casual')
    if arm:
        key(arm, 'location', [(0, Vector((12.0, 7.0, 0.12))), (d, Vector((12.0, 2.2, 0.12)))], interp='LINEAR')
    walk(arm, 0.0, d)
    camera([(0, (9.0, -12.0, 1.5), (22.0, 45.0, 28.0)), (d, (8.9, -11.0, 1.5), (22.0, 45.0, 29.0))], lens=20)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11]

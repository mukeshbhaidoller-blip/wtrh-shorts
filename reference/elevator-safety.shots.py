# Shots for "If You Hang a Box From a Rope..." (how elevators stay safe). One function per script line.
# Z up. Modern shaft: car centred at x=0,y=0 between two T-rails at x=+-0.95; counterweight at x=+1.6 on its own rails.
# Person faces -Y at rot_z=0 (towards the usual camera side). t = seconds from the shot start.
from mathutils import Matrix
CONC = ['concrete_floor_worn_001', 'concrete_floor_02']

def dur(a, b): return (b - a) / FPS

def mats():
    M = {}
    M['conc'] = mat_textured('Concrete', CONC, 0.45, (0.5, 0.5, 0.48), rough=(0.75, 0.95), tint=(0.85, 0.85, 0.83))[0]
    M['floor'] = mat_textured('Floor', ['concrete_floor_02'], 0.5, (0.45, 0.45, 0.44), rough=(0.4, 0.8))[0]
    M['rail'] = mat_simple('RailSteel', (0.42, 0.43, 0.45), 0.3, 1.0)[0]
    M['stain'] = mat_simple('Stainless', (0.78, 0.78, 0.8), 0.2, 1.0)[0]
    M['paint'] = mat_simple('FramePaint', (0.09, 0.1, 0.11), 0.45, 0.3)[0]
    M['cw'] = mat_simple('CWPaint', (0.2, 0.22, 0.25), 0.55, 0.2)[0]
    M['yellow'] = mat_simple('SafetyYellow', (0.85, 0.6, 0.04), 0.4)[0]
    M['rope'] = rope_mat()
    M['hemp'] = mat_simple('Hemp', (0.5, 0.4, 0.26), 0.95)[0]
    M['wood'] = mat_textured('Wood', ['plywood'], 0.7, (0.45, 0.32, 0.2), rough=(0.6, 0.85), tint=(0.62, 0.48, 0.34))[0]
    M['brick'] = mat_textured('Brick', ['red_brick_03'], 0.4, (0.45, 0.2, 0.14), rough=(0.8, 0.95))[0]
    M['iron'] = mat_simple('Iron', (0.06, 0.06, 0.065), 0.5, 0.8)[0]
    M['machine'] = mat_simple('MachineGreen', (0.08, 0.17, 0.14), 0.4, 0.3, coat=0.3)[0]
    M['lamp'] = mat_emit('Lamp', (1, 0.93, 0.8), 25)[0]
    M['panel'] = mat_simple('CabPanel', (0.3, 0.31, 0.32), 0.45, 0.6)[0]
    return M

def rope_mat():
    m, nt, p = nodes_mat('SteelRope')
    p.inputs['Base Color'].default_value = (0.32, 0.32, 0.33, 1); p.inputs['Metallic'].default_value = 1.0; p.inputs['Roughness'].default_value = 0.38
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'; wv.inputs['Scale'].default_value = 140
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def mark_cam(sc, t, cam):
    m = sc.timeline_markers.new('c%d' % len(sc.timeline_markers), frame=F(t)); m.camera = cam

# ---------------------------------------------------------------- modern shaft kit
def rail(M, x, y, z0, z1, toward='x', sign=1):
    """T guide rail running z0..z1. The blade points towards the car: along -sign*X (toward='x') or -sign*Y."""
    L = z1 - z0; zc = (z0 + z1) / 2; out = []
    if toward == 'x':
        out.append(box('RailBlade', (0.09, 0.016, L), (x + sign * 0.045, y, zc), M['rail']))
        out.append(box('RailFlange', (0.012, 0.13, L), (x + sign * 0.096, y, zc), M['rail']))
        z = z0 + 1.0
        while z < z1:
            out.append(box('Bracket', (0.3, 0.16, 0.08), (x + sign * 0.25, y, z), M['paint'])); z += 3.0
    else:
        out.append(box('RailBlade', (0.016, 0.09, L), (x, y + sign * 0.045, zc), M['rail']))
        out.append(box('RailFlange', (0.13, 0.012, L), (x, y + sign * 0.096, zc), M['rail']))
    return out

def shaft(M, z0=-2.0, z1=40.0, front=False, side_r=True, lamps=True):
    """Concrete hoistway: x -1.3..2.0, back wall at y=+1.0. Car rails at x=+-0.95, counterweight rails at x=1.6, y=+-0.43."""
    H = z1 - z0; zc = (z0 + z1) / 2
    box('BackWall', (3.6, 0.3, H), (0.35, 1.15, zc), M['conc'])
    box('WallL', (0.3, 2.6, H), (-1.45, 0.0, zc), M['conc'])
    if side_r: box('WallR', (0.3, 2.6, H), (2.15, 0.0, zc), M['conc'])
    if front:
        box('FrontWall', (3.6, 0.3, H), (0.35, -1.15, zc), M['conc'])
    box('Pit', (3.6, 2.6, 0.3), (0.35, 0, z0 - 0.15), M['conc'])
    for s in (-1, 1): rail(M, s * 0.93, 0, z0, z1, 'x', s)
    for s in (-1, 1): rail(M, 1.6, s * 0.4, z0, z1, 'y', s)
    if lamps:
        z = z0 + 2.0
        while z < z1:
            box('ShaftLamp', (0.05, 0.12, 0.3), (-1.28, 0.75, z), M['lamp'])
            l = light('POINT', (-1.15, 0.75, z), 45, (1, 0.9, 0.75), 0.15)
            z += 4.0

def car(M, zb, ropes=True, name='Car', rope_len=50.0, n_ropes=6):
    """Elevator car with sling frame; origin at the platform bottom. Returns (rig, dict of parts)."""
    rig = bpy.data.objects.new(name, None); link(rig); rig.location = (0, 0, zb); parts = {}
    P = []
    P.append(box('Platform', (1.7, 1.5, 0.16), (0, 0, 0.08), M['paint'], bevel=0.01))
    P.append(box('Cab', (1.58, 1.38, 2.3), (0, 0, 1.31), M['panel'], bevel=0.015))
    for s in (-1, 1):
        P.append(box('Stile', (0.1, 0.2, 3.0), (s * 0.84, 0, 1.45), M['paint']))
        P.append(box('ShoeTop', (0.12, 0.16, 0.12), (s * 0.85, 0, 2.95), M['paint']))
        for sy in (-1, 1):
            P.append(box('SafetyBlock', (0.2, 0.09, 0.24), (s * 0.95, sy * 0.075, -0.08), M['yellow'], bevel=0.01))
    P.append(box('Crosshead', (1.8, 0.24, 0.22), (0, 0, 2.96), M['paint'], bevel=0.01))
    P.append(box('Plank', (1.8, 0.24, 0.18), (0, 0, -0.08), M['paint'], bevel=0.01))
    P.append(box('ToeGuard', (1.58, 0.02, 0.9), (0, -0.76, -0.45), M['paint']))
    P.append(box('HitchPlate', (0.36, 0.14, 0.03), (0, 0, 3.09), M['paint']))
    rl = []
    if ropes:
        for k in range(n_ropes):
            x = -0.1 + k * 0.2 / max(1, n_ropes - 1)
            spr = cyl('HitchSpring', 0.014, 0.16, (x, 0, 3.19), M['yellow'], verts=16); P.append(spr)
            r = cyl('Rope', 0.0065, rope_len, (x, 0, 3.27 + rope_len / 2), M['rope'], verts=12); P.append(r); rl.append(r)
    for o in P: o.parent = rig
    parts['ropes'] = rl
    return rig, parts

def counterweight(M, zb, rope_len=50.0, plates=36, name='CW'):
    rig = bpy.data.objects.new(name, None); link(rig); rig.location = (1.6, 0, zb); P = []
    for s in (-1, 1):
        P.append(box('CWUpright', (0.16, 0.06, 2.6), (0, s * 0.32, 1.3), M['paint']))
    P.append(box('CWTop', (0.28, 0.76, 0.16), (0, 0, 2.58), M['paint'], bevel=0.01))
    P.append(box('CWBot', (0.28, 0.76, 0.16), (0, 0, 0.08), M['paint'], bevel=0.01))
    pl = []
    proto = box('Plate', (0.24, 0.56, 0.05), (0, 0, 0), M['cw'], bevel=0.006)
    for i in range(plates):
        o = proto if i == 0 else dup(proto, (0, 0, 0))
        o.location = (0, 0, 0.19 + i * 0.062); P.append(o); pl.append(o)
    for k in range(6):
        y = -0.1 + k * 0.04
        P.append(cyl('CWRope', 0.0065, rope_len, (0, y, 2.66 + rope_len / 2), M['rope'], verts=12))
    for o in P: o.parent = rig
    return rig, pl

def shaft_world():
    world_hdri('studio_small_09', 0.06, 0, 'studio')

# ---------------------------------------------------------------- 1854 kit
def warehouse(M, lamp_x=-2.5):
    box('BrickBack', (14, 0.4, 7), (0, 3.2, 3.5), M['brick'])
    box('BrickSide', (0.4, 10, 7), (-4.5, 0, 3.5), M['brick'])
    plane('Planks', 14, 12, (0, 0, 0), M['wood'])
    box('Beam', (9, 0.3, 0.35), (0, 0, 4.2), M['wood'], bevel=0.01)
    for x in (-3.5, 3.5): box('Post', (0.3, 0.3, 4.2), (x, 0, 2.1), M['wood'], bevel=0.01)
    # tall window on the side wall (warm daylight) + soft fill
    box('Window', (0.05, 1.6, 2.6), (-4.28, -0.5, 2.6), mat_emit('WinGlow', (1, 0.92, 0.78), 6)[0])
    light('AREA', (-3.9, -0.5, 2.6), 1400, (1, 0.9, 0.75), 2.2, rot=(0, math.radians(-90), 0))
    light('AREA', (2.5, -4.0, 3.5), 260, (0.8, 0.85, 1.0), 3.0, rot=(math.radians(50), 0, math.radians(30)))
    world_hdri('studio_small_09', 0.12, 0, 'studio')

def crate(M, loc, s=(1.1, 1.0, 0.75), name='Crate'):
    rig = bpy.data.objects.new(name, None); link(rig); rig.location = loc
    w, d, h = s; P = []
    P.append(box('CrateFloor', (w, d, 0.05), (0, 0, 0.025), M['wood'], bevel=0.005))
    for sx in (-1, 1):
        P.append(box('CrateSide', (0.04, d, h), (sx * (w / 2 - 0.02), 0, h / 2), M['wood'], bevel=0.004))
    for sy in (-1, 1):
        P.append(box('CrateEnd', (w, 0.04, h), (0, sy * (d / 2 - 0.02), h / 2), M['wood'], bevel=0.004))
    for sx in (-1, 1):   # sling irons up to the rope ring
        for sy in (-1, 1):
            r = cyl('Sling', 0.008, 1.0, (0, 0, 0), M['iron'], verts=8)
            a = Vector((sx * w / 2 * 0.9, sy * d / 2 * 0.9, h)); bpt = Vector((0, 0, h + 0.7))
            r.location = (a + bpt) / 2; r.scale = (1, 1, (bpt - a).length)
            r.rotation_euler = (bpt - a).to_track_quat('Z', 'Y').to_euler(); P.append(r)
    P.append(sphere('Ring', 0.04, (0, 0, h + 0.7), M['iron'], sub=2))
    for o in P: o.parent = rig
    return rig

def otis_tower(M, deck_z=4.0, H=8.5):
    """Open timber hoist tower with ratchet bars on the inner faces of both posts; platform rig at deck_z."""
    out = {}
    for s in (-1, 1):
        box('TowerPost', (0.22, 0.22, H), (s * 1.12, 0, H / 2), M['wood'], bevel=0.01)
        bar = box('RatchetBar', (0.04, 0.12, H - 0.4), (s * 0.99, 0, H / 2), M['iron'])
        # teeth: a strip of small wedges every 6 cm
        proto = box('Tooth', (0.04, 0.1, 0.05), (0, 0, 0), M['iron'])
        z = 0.4
        while z < H - 0.4:
            t = dup(proto, (s * 0.955, 0, z), rot=(0, s * math.radians(-30), 0)); z += 0.08
        proto.location = (0, -99, 0)
    box('TowerTop', (2.6, 0.3, 0.3), (0, 0, H), M['wood'], bevel=0.01)
    cyl('Pulley', 0.22, 0.1, (0, 0, H - 0.25), M['iron'], rot=(math.radians(90), 0, 0), verts=48)
    rig = bpy.data.objects.new('Platform', None); link(rig); rig.location = (0, 0, deck_z); P = []
    P.append(box('Deck', (1.9, 1.5, 0.08), (0, 0, 0), M['wood'], bevel=0.005))
    for s in (-1, 1):
        P.append(box('Upright', (0.08, 0.1, 1.6), (s * 0.9, 0, 0.8), M['wood']))
    P.append(box('TopBar', (1.9, 0.12, 0.1), (0, 0, 1.62), M['wood']))
    # wagon spring: stacked steel leaves hinged at the centre; rope tension bows them down, slack lets them flatten out
    ss = mat_simple('SpringSteel', (0.16, 0.16, 0.17), 0.35, 1.0)[0]
    P.append(box('RopeClamp', (0.14, 0.12, 0.1), (0, 0, 1.97), M['iron'], bevel=0.01))
    leaves = []
    for s in (-1, 1):
        pv = bpy.data.objects.new('Leaf', None); link(pv); pv.location = (0, 0, 1.95); P.append(pv)
        for k, L in enumerate((0.9, 0.72, 0.54)):
            lf = box('Leaf', (L, 0.08, 0.018), (0, 0, 0), ss, bevel=0.004); lf.parent = pv; lf.location = (s * L / 2, 0, -0.02 * k)
        pw = box('Pawl', (0.12, 0.09, 0.06), (0, 0, 0), M['iron'], bevel=0.005); pw.parent = pv; pw.location = (s * 0.9, 0, -0.01)
        pv.rotation_euler = (0, s * math.radians(35), 0); leaves.append((pv, s))
    for o in P: o.parent = rig
    out.update(rig=rig, leaves=leaves)
    return out

def hall(M):
    """Exhibition hall feel: brick back wall, tall iron columns, bright high windows."""
    box('HallBack', (30, 0.5, 16), (0, 8, 8), M['brick'])
    plane('HallFloor', 40, 40, (0, 0, 0), M['wood'])
    wm = mat_emit('HighWin', (0.9, 0.93, 1.0), 4)[0]
    for x in (-9, -4.5, 0, 4.5, 9):
        box('HighWindow', (3.2, 0.05, 4), (x, 7.74, 11), wm)
    col, _ = mat_simple('ColumnPaint', (0.75, 0.74, 0.7), 0.5, 0.2)
    for x in (-6, 6):
        for y in (-2, 5):
            cyl('Column', 0.22, 16, (x, y, 8), col, verts=32)
    light('AREA', (0, 2, 14), 9000, (1, 0.97, 0.92), 12, rot=(0, 0, 0))
    light('AREA', (-4, -8, 5), 1800, (1, 0.93, 0.85), 5, rot=(math.radians(70), 0, math.radians(-30)))
    world_hdri('studio_small_09', 0.15, 0, 'studio')

# ---------------------------------------------------------------- machine room kit
def machine_room(M):
    plane('MRFloor', 10, 10, (0, 0, 0), M['floor'])
    wall, _ = mat_simple('MRWall', (0.55, 0.56, 0.55), 0.85)
    box('MRBack', (10, 0.2, 4), (0, 2.5, 2), wall); box('MRSide', (0.2, 10, 4), (-3, 0, 2), wall)
    box('Fixture', (1.2, 0.15, 0.05), (0, 0, 3.2), M['lamp'])
    light('AREA', (0, 0, 3.15), 700, (1, 0.96, 0.9), 1.4)
    light('AREA', (-2.0, -2.5, 2.4), 300, (0.85, 0.9, 1.0), 2.0, rot=(math.radians(60), 0, math.radians(-40)))
    world_hdri('studio_small_09', 0.12, 0, 'studio')

def traction_machine(M, loc=(0, 0, 0)):
    """Bedplate, green motor, brake drum and grooved drive sheave (axle along X). Returns sheave rig (rotate X)."""
    x, y, z = loc; rot = (0, math.radians(90), 0)
    box('Bedplate', (2.0, 0.9, 0.25), (x, y, z + 0.125), M['paint'], bevel=0.01)
    cyl('Motor', 0.36, 0.9, (x - 0.55, y, z + 0.72), M['machine'], rot=rot, bevel=0.03)
    cyl('MotorCap', 0.3, 0.06, (x - 1.02, y, z + 0.72), M['machine'], rot=rot, bevel=0.01)
    box('MotorFoot', (0.8, 0.6, 0.2), (x - 0.55, y, z + 0.35), M['machine'])
    cyl('BrakeDrum', 0.28, 0.2, (x - 0.02, y, z + 0.72), M['rail'], rot=rot)
    for s in (-1, 1): box('BrakeArm', (0.08, 0.06, 0.6), (x - 0.02, y + s * 0.3, z + 0.65), M['yellow'])
    box('Bearing', (0.25, 0.4, 0.45), (x + 0.75, y, z + 0.45), M['machine'])
    rig = bpy.data.objects.new('Sheave', None); link(rig); rig.location = (x + 0.35, y, z + 0.72)
    P = [cyl('SheaveCore', 0.33, 0.36, (0, 0, 0), M['rail'], rot=rot, verts=96)]
    for k in range(7): P.append(cyl('Flange', 0.35, 0.014, (-0.165 + k * 0.055, 0, 0), M['rail'], rot=rot, verts=96))
    for k in range(6): P.append(box('Spoke', (0.37, 0.05, 0.62), (0, 0, 0), M['paint']))
    for k, o in enumerate(P[-6:]): o.rotation_euler = (k * math.pi / 6, 0, 0)
    for o in P: o.parent = rig
    for k in range(6):   # ropes leave the sheave at front and back, straight down through the floor
        xx = x + 0.35 - 0.1375 + k * 0.055
        for yy in (-0.335, 0.335):
            cyl('Rope', 0.0065, 3.0, (xx, y + yy, z + 0.72 - 1.5), M['rope'], verts=12)
    box('FloorSlot', (0.5, 0.9, 0.01), (x + 0.35, y, 0.003), mat_simple('Hole', (0.01, 0.01, 0.01), 0.9)[0])
    return rig

def governor(M, loc=(0, 0, 0)):
    """Overspeed governor: stand, small sheave (axle along X), two flyweights on pivots. Returns (sheave rig, [weight pivots])."""
    x, y, z = loc; rot = (0, math.radians(90), 0)
    box('GovBase', (0.5, 0.5, 0.08), (x, y, z + 0.04), M['paint'])
    for s in (-1, 1): box('GovStand', (0.05, 0.12, 0.6), (x + s * 0.16, y, z + 0.38), M['yellow'])
    rig = bpy.data.objects.new('GovSheave', None); link(rig); rig.location = (x, y, z + 0.62)
    P = [cyl('GovWheel', 0.2, 0.08, (0, 0, 0), M['rail'], rot=rot, verts=72)]
    for k in (-1, 1): P.append(cyl('GovFlange', 0.215, 0.012, (k * 0.03, 0, 0), M['rail'], rot=rot, verts=72))
    P.append(cyl('GovHub', 0.05, 0.12, (0, 0, 0), M['paint'], rot=rot, verts=32))
    piv = []
    for s in (-1, 1):
        pv = bpy.data.objects.new('Pivot', None); link(pv); pv.parent = rig; pv.location = (-0.07, s * 0.04, 0); P.append(pv)
        arm_ = box('FlyArm', (0.02, 0.02, 0.12), (0, 0, s * 0.06), M['rail']); arm_.parent = pv
        wgt = box('Flyweight', (0.05, 0.07, 0.07), (0, 0, s * 0.13), mat_simple('FlyRed', (0.5, 0.05, 0.03), 0.4, 0.2)[0], bevel=0.01); wgt.parent = pv
        piv.append(pv)
    P.append(cyl('GovAxle', 0.02, 0.4, (0, 0, 0), M['rail'], rot=rot, verts=16))
    for o in P:
        if o.parent is None: o.parent = rig
    for yy in (-0.2, 0.2):
        cyl('GovRope', 0.005, 2.0, (x, y + yy, z + 0.62 - 1.0), M['rope'], verts=10)
    return rig, piv

def spin(o, t0, t1, rev, axis=0, start=0.0):
    pts = [(t0, start), (t1, start + rev * 2 * math.pi)]
    for t, v in pts:
        o.rotation_euler[axis] = v; o.keyframe_insert('rotation_euler', index=axis, frame=F(t))
    for fc in fcurves_of(o.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'

# ================================================================ shots
def S00(a, b):  # 1850s warehouse: a crate hangs from a hemp rope, a worker beside it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); warehouse(M)
    c = crate(M, (-0.35, 0.2, 1.55))
    cyl('HempRope', 0.018, 1.0, (-0.35, 0.2, 3.5), M['hemp'], verts=16)
    cyl('Block', 0.12, 0.12, (-0.35, 0.2, 4.0), M['iron'], rot=(math.radians(90), 0, 0))
    key(c, 'rotation_euler', [(0, Vector((0, 0, math.radians(-8)))), (d, Vector((0, 0, math.radians(-2))))])
    arm = person('Worker', loc=(1.05, -0.15, 0), rot_z=math.radians(-70), outfit='worker', stance='relax')
    pose(arm, 0.6, STANCES['relax']); pose(arm, 1.8, STANCES['point_r'])
    pose(arm, 1.8, {'neck01': (0, 0, 12)})
    camera([(0, (0.7, -5.4, 1.55), (0.15, 0.2, 1.65)), (d, (0.55, -4.6, 1.5), (0.15, 0.2, 1.65))], lens=32, fstop=4.0)

def S01(a, b):  # the rope snaps, the crate drops to the floor
    sc = new_scene(a, b); d = dur(a, b); M = mats(); warehouse(M)
    tb = 1.0; z0 = 1.55; tf = tb + math.sqrt(2 * z0 / 9.81)
    c = crate(M, (-0.35, 0.2, z0))
    top = cyl('RopeTop', 0.018, 0.5, (-0.35, 0.2, 3.75), M['hemp'], verts=16)
    low = cyl('RopeLow', 0.018, 0.5, (0, 0, 0), M['hemp'], verts=16); low.parent = c; low.location = (0, 0, 1.7)
    cyl('Block', 0.12, 0.12, (-0.35, 0.2, 4.0), M['iron'], rot=(math.radians(90), 0, 0))
    pts = [(0, Vector((-0.35, 0.2, z0))), (tb, Vector((-0.35, 0.2, z0)))]
    k = 6
    for i in range(1, k + 1):
        tt = tb + (tf - tb) * i / k; pts.append((tt, Vector((-0.35, 0.2, z0 - 0.5 * 9.81 * (tt - tb) ** 2))))
    pts.append((tf + 0.06, Vector((-0.35, 0.2, 0.02)))); pts.append((d, Vector((-0.35, 0.2, 0.0))))
    key(c, 'location', pts, interp='LINEAR')
    key(c, 'rotation_euler', [(0, Vector((0, 0, math.radians(-4)))), (tb, Vector((0, 0, math.radians(-4)))), (tf, Vector((math.radians(3), math.radians(-6), math.radians(-1)))), (tf + 0.15, Vector((0, math.radians(-2), 0)))])
    key(top, 'location', [(tb, Vector((-0.35, 0.2, 3.75))), (tb + 0.3, Vector((-0.32, 0.2, 3.8)))])
    # dust puff at impact
    dm = bpy.data.materials.new('Dust'); dm.use_nodes = True; nt = dm.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value = 0.0
    v.inputs['Color'].default_value = (0.75, 0.68, 0.58, 1); nt.links.new(v.outputs['Volume'], o.inputs['Volume'])
    key_socket(v.inputs['Density'], [(tf - 0.01, 0.0), (tf + 0.05, 2.5), (d, 0.15)])
    dust = sphere('Dust', 1.0, (-0.35, 0.2, 0.1), dm, sub=3)
    key(dust, 'scale', [(tf, Vector((0.6, 0.6, 0.15))), (d, Vector((1.6, 1.4, 0.5)))])
    camera([(0, (0.9, -3.6, 1.2), (-0.35, 0.2, 1.7)), (d, (0.85, -3.4, 1.0), (-0.35, 0.2, 1.1))], lens=30, fstop=4.0)

def S02(a, b):  # 1854: Otis stands on his raised platform in a big hall
    sc = new_scene(a, b); d = dur(a, b); M = mats(); hall(M)
    T = otis_tower(M, deck_z=4.0)
    rope = cyl('HoistRope', 0.02, 8.5 - 0.25 - 5.8, (0, 0, 5.8 + (8.5 - 0.25 - 5.8) / 2), M['hemp'], verts=16)
    for i, (x, y) in enumerate(((-0.6, 0.35), (0.55, 0.4))):
        c = box('Barrel', (0.38, 0.38, 0.5), (x, y, 4.04 + 0.25), M['wood'], bevel=0.06, segs=4)
    arm = person('Otis', loc=(0.05, -0.15, 4.04), rot_z=0, outfit='casual', stance='relax', age=0.6)
    pose(arm, 2.8, STANCES['relax']); pose(arm, 4.2, STANCES['wave_r'])
    camera([(0, (0.6, -9.5, 1.6), (0, 0, 4.6)), (d, (0.4, -8.2, 1.7), (0, 0, 4.7))], lens=35, fstop=5.6)

def S03(a, b):  # rope cut: the spring snaps out into the ratchet teeth, the platform drops a few cm and stops
    sc = new_scene(a, b); d = dur(a, b); M = mats(); hall(M)
    T = otis_tower(M, deck_z=4.0); rig = T['rig']; tc = 0.35; tcatch = tc + 0.12
    rope = cyl('HoistRope', 0.02, 2.5, (0, 0, 5.85 + 1.25), M['hemp'], verts=16)
    key(rope, 'location', [(tc, Vector((0, 0, 7.1))), (tc + 0.5, Vector((0.05, 0.02, 7.4)))])
    key(rope, 'scale', [(tc, Vector((1, 1, 1))), (tc + 0.5, Vector((1, 1, 0.6)))])
    for pv, sg in T['leaves']:
        key(pv, 'rotation_euler', [(tc, Vector((0, sg * math.radians(35), 0))), (tc + 0.1, Vector((0, sg * math.radians(4), 0)))], interp='LINEAR')
    key(rig, 'location', [(tc, Vector((0, 0, 4.0))), (tcatch, Vector((0, 0, 3.93))), (tcatch + 0.08, Vector((0, 0, 3.945))), (d, Vector((0, 0, 3.945)))], interp='LINEAR')
    arm = person('Otis', loc=(0.05, -0.15, 0.04), rot_z=0, outfit='casual', stance='relax', age=0.6)
    if arm: arm.parent = rig; arm.location = (0.05, -0.15, 0.04)
    pose(arm, 0.0, STANCES['wave_r']); pose(arm, 1.6, STANCES['wave_r']); pose(arm, 2.8, STANCES['relax'])
    # camera on a little shake at the catch
    cam, tgt = camera([(0, (1.9, -3.4, 5.3), (0.45, 0, 5.25)), (d, (1.8, -3.1, 5.3), (0.45, 0, 5.2))], lens=30, fstop=4.0)
    key(cam, 'rotation_euler', [(0, Vector((0, 0, 0))), (tcatch, Vector((0, 0, 0))), (tcatch + 0.05, Vector((0.01, 0, 0.006))), (tcatch + 0.25, Vector((0, 0, 0)))])

def key_socket_mod(mod, attr, pts):
    for t, v in pts:
        setattr(mod, attr, v); mod.id_data.keyframe_insert('modifiers["%s"].%s' % (mod.name, attr), frame=F(t))

def S04(a, b):  # modern hoistway from the pit, looking up at the car rising to a tall building's top
    sc = new_scene(a, b); d = dur(a, b); M = mats(); shaft_world()
    shaft(M, -2.0, 60.0, front=True)
    rig, _ = car(M, 4.0)
    key(rig, 'location', [(0, Vector((0, 0, 3.2))), (d, Vector((0, 0, 6.2)))], interp='LINEAR')
    cw, _ = counterweight(M, 30.0)
    box('Skylight', (1.2, 1.2, 0.05), (0.3, 0, 59.9), mat_emit('Top', (1, 0.97, 0.9), 15)[0])
    light('SPOT', (0.0, -0.6, -1.6), 1500, (1, 0.95, 0.85), 0.3, rot=(math.pi, 0, 0), spot=70)
    camera([(0, (-0.55, -0.55, -1.5), (0.0, 0.1, 8.0)), (d, (-0.5, -0.5, -1.4), (0.1, 0.1, 9.0))], lens=18, fstop=None)

def S05(a, b):  # side cut-away: car goes up while the counterweight comes down past it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); shaft_world()
    shaft(M, -2.0, 30.0)
    rig, _ = car(M, 0)
    key(rig, 'location', [(0, Vector((0, 0, 2.2))), (d, Vector((0, 0, 5.6)))], interp='LINEAR')
    cw, _ = counterweight(M, 0)
    key(cw, 'location', [(0, Vector((1.6, 0, 6.8))), (d, Vector((1.6, 0, 3.4)))], interp='LINEAR')
    light('AREA', (-1.0, -2.5, 9.5), 500, (1, 0.96, 0.9), 2.5, rot=(math.radians(35), 0, math.radians(-20)))
    camera([(0, (0.5, -5.6, 5.0), (0.45, 0, 5.2)), (d, (0.5, -5.2, 5.0), (0.45, 0, 5.2))], lens=24, fstop=None)

def S06(a, b):  # close-up: steel plates drop into the counterweight frame one after another
    sc = new_scene(a, b); d = dur(a, b); M = mats(); shaft_world()
    shaft(M, -2.0, 10.0, lamps=False)
    cw, pl = counterweight(M, 0.5, plates=30)
    n = len(pl)
    for i, o in enumerate(pl):
        z = o.location.z; t0 = 0.15 + (d - 0.9) * i / n
        if i < 8: continue   # first plates already in
        key(o, 'location', [(0, Vector((0, 0, z + 3.0))), (t0, Vector((0, 0, z + 3.0))), (t0 + 0.28, Vector((0, 0, z)))], interp='LINEAR')
    light('AREA', (0.4, -1.8, 2.8), 260, (1, 0.95, 0.88), 1.6, rot=(math.radians(70), 0, math.radians(-30)))
    light('POINT', (2.0, -0.4, 1.0), 40, (0.7, 0.8, 1.0), 0.3)
    camera([(0, (0.55, -1.75, 1.55), (1.6, 0, 1.55)), (d, (0.65, -1.55, 1.75), (1.6, 0, 1.6))], lens=30, fstop=3.5)

def S07(a, b):  # machine room: the motor turns the drive sheave; a technician points at it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); machine_room(M)
    sh = traction_machine(M, (0, 0.4, 0))
    box('Controller', (1.0, 0.45, 2.0), (-1.6, 2.1, 1.0), mat_simple('Cabinet', (0.62, 0.63, 0.6), 0.5, 0.3)[0], bevel=0.01)
    for k in range(4): sphere('LED', 0.012, (-1.85 + k * 0.08, 1.87, 1.7), mat_emit('LED', (0.2, 1, 0.3) if k else (1, 0.3, 0.1), 12)[0], sub=1)
    box('Conduit', (0.06, 0.06, 2.0), (-1.0, 2.35, 2.9), M['rail'], rot=(0, math.radians(90), 0))
    spin(sh, 0, d, -0.6)
    arm = person('Tech', loc=(1.25, -0.35, 0), rot_z=math.radians(-100), outfit='worker', stance='relax')
    pose(arm, 0.3, STANCES['relax']); pose(arm, 1.2, STANCES['point_r'])
    camera([(0, (-0.5, -3.2, 1.25), (0.45, 0.4, 1.05)), (d, (-0.35, -2.9, 1.25), (0.45, 0.4, 1.05))], lens=30, fstop=4.0)

def S08(a, b):  # looking down the shaft: the car speeds away downward
    sc = new_scene(a, b); d = dur(a, b); M = mats(); shaft_world()
    shaft(M, -80.0, 8.0)
    rig, _ = car(M, 0, rope_len=20)
    lt = light('POINT', (0, 0, 0), 300, (1, 0.93, 0.8), 0.1); lt.parent = rig; lt.location = (0.4, -0.5, 3.6)
    lp = box('CarTopLamp', (0.12, 0.08, 0.06), (0, 0, 0), M['lamp']); lp.parent = rig; lp.location = (0.4, -0.55, 3.12)
    pts = []
    for i in range(9):
        tt = d * i / 8; pts.append((tt, Vector((0, 0, -0.5 - 2.0 * tt - 2.2 * tt * tt))))
    key(rig, 'location', pts, interp='LINEAR')
    camera([(0, (-0.35, -0.55, 6.5), (0.0, 0.05, -6.0)), (d, (-0.35, -0.55, 6.3), (0.0, 0.05, -8.0))], lens=20, fstop=None)

def S09(a, b):  # the governor spins on its stand; a technician watches it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); machine_room(M)
    traction_machine(M, (-1.2, 1.3, 0))
    g, piv = governor(M, (0.6, 0.2, 0))
    spin(g, 0, d, -2.5)
    arm = person('Tech', loc=(1.15, 1.9, 0), rot_z=math.radians(-20), outfit='worker', stance='relax')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.5, {'spine02': (12, 0, 0), 'neck01': (10, 0, 0)})
    camera([(0, (0.0, -1.35, 1.0), (0.65, 0.2, 0.75)), (d, (0.1, -1.15, 0.98), (0.65, 0.2, 0.75))], lens=36, fstop=2.8)

def S10(a, b):  # A: governor overspeeds, flyweights fly out. B: under the car the safety wedges clamp the rail, the car stops
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    tcut = 2.55; tclamp = 3.3; tstop = 4.1
    # --- part A: governor in the machine room (placed far away at x=+50)
    machine_room_at(M, 50)
    g, piv = governor(M, (50.6, 0.2, 0))
    spin(g, 0, tcut, -5.5)
    for s, pv in zip((-1, 1), piv):
        key(pv, 'rotation_euler', [(0, Vector((0, 0, 0))), (1.4, Vector((0, 0, 0))), (1.9, Vector((s * math.radians(55), 0, 0)))])
    camA, _ = camera([(0, (49.95, -0.45, 0.75), (50.6, 0.2, 0.62)), (tcut, (50.05, -0.4, 0.72), (50.6, 0.2, 0.62))], lens=40, fstop=3.2)
    # --- part B: safety gear at the left rail, camera rides with the car
    shaft_world(); shaft(M, -60.0, 20.0)
    rig, parts = car(M, 0, rope_len=30)
    v0 = 6.0
    def zc(t):
        if t <= tclamp: return 10.0 - v0 * (t - tcut)
        dt = min(t, tstop) - tclamp; T = tstop - tclamp
        return 10.0 - v0 * (tclamp - tcut) - v0 * dt + 0.5 * (v0 / T) * dt * dt
    pts = [(tcut + (d - tcut) * i / 20, Vector((0, 0, zc(tcut + (d - tcut) * i / 20)))) for i in range(21)]
    key(rig, 'location', pts, interp='LINEAR')
    wm, wp = mat_simple('Wedge', (0.5, 0.5, 0.52), 0.3, 1.0)
    for sy in (-1, 1):
        w = box('Wedge', (0.07, 0.03, 0.14), (-0.965, sy * 0.05, -0.36), wm, bevel=0.004); w.parent = rig
        key(w, 'location', [(tclamp - 0.12, Vector((-0.965, sy * 0.05, -0.36))), (tclamp, Vector((-0.965, sy * 0.024, -0.27)))], interp='LINEAR')
    # sparks at the clamp
    sm, _ = mat_emit('Spark', (1, 0.55, 0.15), 40)
    random.seed(9)
    for i in range(40):
        tb = tclamp + random.uniform(0, tstop - tclamp)
        s = sphere('Spark', 0.006, (0, 0, 0), sm, sub=1); s.parent = rig
        p0 = Vector((-0.965, random.choice((-0.03, 0.03)), -0.34)); p1 = p0 + Vector((random.uniform(0.1, 0.5), random.uniform(-0.6, -0.1), random.uniform(0.1, 0.6)))
        key(s, 'scale', [(tb - 0.02, Vector((0, 0, 0))), (tb, Vector((1, 1, 1))), (tb + 0.3, Vector((0.2, 0.2, 0.2))), (tb + 0.32, Vector((0, 0, 0)))])
        key(s, 'location', [(tb, p0), (tb + 0.3, p1)], interp='LINEAR')
    lb = light('POINT', (0, 0, 0), 90, (1, 0.95, 0.88), 0.2); lb.parent = rig; lb.location = (-0.45, -0.5, -0.4)
    camB, tgtB = camera([(0, (-0.4, -0.66, -0.42), (-0.95, 0.0, -0.2)), (d, (-0.45, -0.62, -0.4), (-0.95, 0.0, -0.2))], lens=28, fstop=2.8)
    camB.parent = rig; tgtB.parent = rig
    mark_cam(sc, 0, camA); mark_cam(sc, tcut, camB); sc.camera = camA

def machine_room_at(M, x0):
    plane('MRFloor', 6, 6, (x0, 0, 0), M['floor'])
    wall, _ = mat_simple('MRWall', (0.55, 0.56, 0.55), 0.85)
    box('MRBack', (6, 0.2, 4), (x0, 2.0, 2), wall)
    light('AREA', (x0, -0.5, 3.0), 500, (1, 0.96, 0.9), 1.4)
    light('AREA', (x0 - 1.5, -2.0, 1.8), 200, (0.85, 0.9, 1.0), 1.5, rot=(math.radians(60), 0, math.radians(-40)))

def S11(a, b):  # on top of the car: six steel ropes run up into the dark
    sc = new_scene(a, b); d = dur(a, b); M = mats(); shaft_world()
    shaft(M, -2.0, 60.0, front=True)
    rig, parts = car(M, 0)
    key(rig, 'location', [(0, Vector((0, 0, 8.0))), (d, Vector((0, 0, 9.0)))], interp='LINEAR')
    lt = light('SPOT', (0.5, -0.6, 3.4), 400, (1, 0.95, 0.88), 0.1, spot=60); lt.parent = rig; lt.location = (0.5, -0.55, 3.3); lt.rotation_euler = (math.radians(160), 0, 0)
    cam, tgt = camera([(0, (0.45, -0.55, 3.35), (0.0, 0.0, 3.6)), (d, (0.4, -0.5, 3.3), (0.0, 0.05, 8.0))], lens=24, fstop=2.8, focus=0.7)
    cam.parent = rig; tgt.parent = rig

def S12(a, b):  # the whole car between its two rails; light runs along the rails
    sc = new_scene(a, b); d = dur(a, b); M = mats(); shaft_world()
    shaft(M, -2.0, 30.0, side_r=False, lamps=False)
    rig, _ = car(M, 3.0)
    cw, _ = counterweight(M, 9.0)
    light('AREA', (-1.0, -2.5, 10.0), 500, (1, 0.96, 0.9), 2.5, rot=(math.radians(35), 0, math.radians(-20)))
    for s in (-1, 1):
        l = light('SPOT', (s * 1.15, -0.5, 0.5), 0, (0.85, 0.92, 1.0), 0.05, spot=12, blend=0.6)
        aim(l, (s * 0.95, 0, 12)); key_light(l.data, 'energy', [(0, 0), (2.0, 0), (2.6, 2500)])
    camera([(0, (2.6, -6.2, 3.2), (0.0, 0, 4.7)), (d, (1.0, -6.6, 3.6), (0.0, 0, 4.7))], lens=28, fstop=None)

def S13(a, b):  # modern lobby: a man waits, the stainless doors slide open
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.15, 0, 'studio')
    fl, fp = mat_textured('Marble', ['concrete_floor_02'], 0.35, (0.7, 0.7, 0.68), rough=(0.15, 0.4), tint=(1.1, 1.08, 1.04), wet=0.6)
    plane('LobbyFloor', 12, 12, (0, -3, 0), fl)
    wall, _ = mat_simple('LobbyWall', (0.62, 0.58, 0.52), 0.6)
    box('WallL', (2.2, 0.2, 3.2), (-1.65, 0.1, 1.6), wall); box('WallR', (2.2, 0.2, 3.2), (1.65, 0.1, 1.6), wall)
    box('Lintel', (1.1, 0.2, 0.9), (0, 0.1, 2.75), wall)
    box('FrameL', (0.06, 0.24, 2.3), (-0.58, 0.1, 1.15), M['stain']); box('FrameR', (0.06, 0.24, 2.3), (0.58, 0.1, 1.15), M['stain'])
    box('FrameT', (1.22, 0.24, 0.06), (0, 0.1, 2.33), M['stain'])
    box('Ceiling', (12, 12, 0.1), (0, -3, 3.25), wall)
    for x in (-2.0, 0.0, 2.0):
        box('Downlight', (0.2, 0.2, 0.02), (x, -1.6, 3.19), M['lamp']); light('SPOT', (x, -1.6, 3.15), 260, (1, 0.9, 0.78), 0.1, spot=70)
    btn_m, btn_p = mat_simple('Button', (0.9, 0.9, 0.9), 0.3, emit=(1, 0.75, 0.35), estr=0.0)
    box('Panel', (0.1, 0.02, 0.25), (0.82, -0.005, 1.15), M['stain']); sphere('Btn', 0.018, (0.82, -0.02, 1.15), btn_m, sub=2)
    key_socket(inp(btn_p, 'Emission Strength'), [(0, 4.0), (1.7, 4.0), (1.8, 0.0)])
    to = 1.8
    for s in (-1, 1):
        dr = box('Door', (0.55, 0.04, 2.27), (s * 0.275, 0.12, 1.135), M['stain'], bevel=0.004)
        key(dr, 'location', [(to, Vector((s * 0.275, 0.12, 1.135))), (to + 1.2, Vector((s * 0.82, 0.12, 1.135)))])
    # car interior behind the doors
    box('CarBack', (1.6, 0.05, 2.4), (0, 1.55, 1.2), M['stain']); box('CarL', (0.05, 1.4, 2.4), (-0.8, 0.85, 1.2), M['stain']); box('CarR', (0.05, 1.4, 2.4), (0.8, 0.85, 1.2), M['stain'])
    box('CarFloor', (1.6, 1.4, 0.02), (0, 0.85, 0.01), mat_simple('CarFloor', (0.12, 0.11, 0.1), 0.4)[0])
    box('CarCeil', (1.6, 1.4, 0.05), (0, 0.85, 2.42), mat_emit('CarCeil', (1, 0.97, 0.92), 6)[0])
    light('AREA', (0, 0.85, 2.35), 220, (1, 0.97, 0.92), 1.0)
    arm = person('Rider', loc=(-0.45, -1.35, 0), rot_z=math.radians(160), outfit='casual', extra=(), stance='relax')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.6, {'neck01': (0, 0, -6)})
    camera([(0, (-1.6, -4.6, 1.6), (0, 0, 1.3)), (d, (-1.25, -3.7, 1.55), (0, 0.2, 1.25))], lens=32, fstop=3.5)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13]

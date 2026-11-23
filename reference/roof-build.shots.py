# Shots for "Why Your Roof Isn't Just Flat Boards" (how a house roof is built). One function per line.
# Z up, metres. House walls x in [-3, 3], y in [-2.5, 2.5], wall top z = H. Ridge runs along X; side s=-1 is the
# front slope (faces -Y), s=+1 the back slope. Person faces -Y at rot_z=0. t = seconds from the shot start.
import bmesh

def dur(a, b): return (b - a) / FPS

H = 2.5; W = 6.0; D = 5.0; OV = 0.4; XL = 3.3
PITCH = math.radians(30); TN = math.tan(PITCH); CS = math.cos(PITCH); SN = math.sin(PITCH)
SL = (D / 2 + OV) / CS            # rafter length along the slope (3.35 m)
DECK = 0.018; UL = 0.002; SH0 = DECK + UL
XS = [-2.7 + 0.6 * i for i in range(10)]   # trusses 24 in (0.6 m) apart
EXPO = 0.143; ROWL = 0.305; TB = 0.012; TAB = 0.333

def rv(s): return Vector((0, -s * CS, SN)), Vector((0, s * SN, CS))   # up-slope dir, outward normal
def RP(s, u, x, off):
    """point on roof side s: u m up the slope from the rafter tail, x along the ridge, off m above the rafter tops"""
    d, n = rv(s)
    e = Vector((x, s * (D / 2 + OV), H + 0.1 - OV * TN))
    return e + d * u + n * (0.07 + off)
ZR = H + 0.1 + (D / 2) * TN      # rafter centre line at the ridge

def upd(): bpy.context.view_layer.update()
def empty(name, loc):
    e = bpy.data.objects.new(name, None); link(e); e.location = loc; upd(); return e
def adopt(o, p):
    upd(); o.parent = p; o.matrix_parent_inverse = p.matrix_world.inverted(); return o
def hide(o, t0=None, t1=None):
    """visible only between t0 and t1 (shot time)"""
    pts = [(0, True)] if t0 is not None and t0 > 0 else [(0, False)]
    if t0 is not None and t0 > 0: pts.append((t0, False))
    if t1 is not None: pts.append((t1, True))
    for t, v in pts:
        o.hide_render = v; o.keyframe_insert('hide_render', frame=F(t))
        o.hide_viewport = v; o.keyframe_insert('hide_viewport', frame=F(t))
    ad = o.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

def mesh_obj(name, verts, faces, mats, mi=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o)
    for m in mats: o.data.materials.append(m)
    if mi:
        for f, k in zip(o.data.polygons, mi): f.material_index = k
    return o

def slabs_obj(name, slabs, mats, idx=None):
    """slabs: [(b0, b1, b2, b3, t0, t1, t2, t3)] bottom + top quads (same winding)"""
    V, Fc, MI = [], [], []
    for k, sl in enumerate(slabs):
        o = len(V); V += [tuple(p) for p in sl]
        fs = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        for f in fs: Fc.append(tuple(o + i for i in f)); MI.append(idx[k] if idx else 0)
    return mesh_obj(name, V, Fc, mats, MI)

def roof_prism(name, s, prof, xa, xb, mat):
    """extrude a (u, off) outline of roof side s from x=xa to x=xb"""
    n = len(prof); V = [tuple(RP(s, u, xa, f)) for u, f in prof] + [tuple(RP(s, u, xb, f)) for u, f in prof]
    Fc = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_obj(name, V, Fc, [mat])

def rod(name, p0, p1, r, mat, verts=12):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    o = cyl(name, r, d.length, (p0 + p1) / 2, mat, verts=verts)
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); return o

def arrow(name, p, dirv, length, mat, r=0.035):
    p = Vector(p); dv = Vector(dirv).normalized(); tip = p + dv * length
    a = rod(name, p, tip - dv * 0.14, r, mat)
    bpy.ops.mesh.primitive_cone_add(radius1=r * 2.6, radius2=0, depth=0.16, location=tip - dv * 0.08, vertices=16)
    c = bpy.context.active_object; c.data.materials.append(mat); c.rotation_euler = dv.to_track_quat('Z', 'Y').to_euler()
    return [a, c]

def rain(cam_p, tgt, d, dists=(2.5, 5.5, 9.5), strength=0.6, spread=0.0):
    cp = Vector(cam_p); v = Vector(tgt) - cp; v.z = 0; v.normalize()
    yaw = math.atan2(-v.x, v.y); out = []
    for k, dd in enumerate(dists):
        c = cp + v * dd
        r = plane('Rain', 14, 9, (c.x, c.y, cp.z + 1.0), mat_rain('Rain%d' % k, strength * (1.0 - 0.18 * k), 34 + 6 * k, d))
        r.rotation_euler = (math.radians(90), math.radians(10), yaw); out.append(r)
    return out

def drops(M, pts, d, seed=1, r=0.012, cyc=0.75, fall=2.5, t0=0.0, xyz=None):
    """water drops falling `fall` m from each start point, repeating every cyc s (staggered)"""
    random.seed(seed); out = []
    for (x, y, z) in pts:
        t = t0 + random.uniform(0, cyc)
        while t < d:
            o = sphere('Drop', r, (x, y, z), M['water'], sub=2); o.scale = (0.7, 0.7, 2.2)
            tf = math.sqrt(2 * fall / 9.8)
            key(o, 'location', [(t, Vector((x, y, z))), (t + tf, Vector((x, y, z - fall)))], interp='LINEAR')
            hide(o, t, t + tf); out.append(o); t += cyc * random.uniform(0.8, 1.25)
    return out

# ---------------------------------------------------------------- materials
def siding_mat(col=(0.70, 0.74, 0.74)):
    m, nt, p = nodes_mat('Siding')
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 2 * math.pi / (10 * 0.15)
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * 0.72 for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    ramp.color_ramp.elements[1].position = 0.25
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.55
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.01
    nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def underlay_mat():
    m, nt, p = nodes_mat('Underlayment')
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 2 * math.pi / (10 * 0.5)
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.07, 0.075, 0.085, 1); ramp.color_ramp.elements[1].color = (0.16, 0.17, 0.19, 1)
    ramp.color_ramp.elements[0].position = 0.93; ramp.color_ramp.elements[1].position = 0.95
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.82
    return m

def mats():
    M = {}
    M['dirt'] = mat_textured('Dirt', ['brown_mud_02'], 0.5, (0.25, 0.18, 0.12), rough=(0.7, 0.95), tint=(0.85, 0.75, 0.62))[0]
    M['gravel'] = mat_textured('Gravel', ['gravel_floor_02'], 0.7, (0.4, 0.38, 0.35), rough=(0.7, 0.95))[0]
    M['conc'] = mat_textured('Slab', ['concrete_floor_worn_001'], 0.9, (0.55, 0.55, 0.53), rough=(0.7, 0.95))[0]
    M['wetconc'] = mat_textured('WetSlab', ['concrete_floor_worn_001'], 0.9, (0.4, 0.4, 0.39), rough=(0.2, 0.4), tint=(0.62, 0.62, 0.6), wet=0.9)[0]
    M['lumber'] = mat_textured('Lumber', ['rough_wood', 'plywood'], 0.9, (0.7, 0.55, 0.38), rough=(0.6, 0.85), tint=(1.05, 0.9, 0.7))[0]
    M['wetlumber'] = mat_textured('WetLumber', ['rough_wood', 'plywood'], 0.9, (0.5, 0.38, 0.26), rough=(0.2, 0.4), tint=(0.62, 0.5, 0.38), wet=0.8)[0]
    M['ply'] = mat_textured('Plywood', ['plywood'], 1.2, (0.72, 0.56, 0.38), rough=(0.6, 0.85), tint=(1.0, 0.9, 0.75))[0]
    M['wetply'] = mat_textured('WetPly', ['plywood'], 1.2, (0.45, 0.33, 0.22), rough=(0.15, 0.35), tint=(0.5, 0.38, 0.27), wet=0.9)[0]
    M['rot'] = mat_textured('Rot', ['brown_mud_02'], 3.0, (0.1, 0.08, 0.05), rough=(0.7, 0.9), tint=(0.35, 0.3, 0.22))[0]
    M['mold'] = mat_simple('Mold', (0.03, 0.045, 0.03), 0.95)[0]
    M['felt'] = underlay_mat()
    M['shing'] = [mat_textured('Shingle%d' % k, ['asphalt_04'], 1.6, (0.16, 0.16, 0.17), rough=(0.75, 0.95), tint=tn)[0]
                  for k, tn in enumerate(((0.42, 0.4, 0.4), (0.36, 0.35, 0.36), (0.48, 0.45, 0.43)))]
    M['siding'] = siding_mat()
    M['trim'] = mat_simple('Trim', (0.88, 0.88, 0.86), 0.45)[0]
    M['door'] = mat_simple('DoorPaint', (0.1, 0.16, 0.24), 0.4, coat=0.1)[0]
    M['glass'] = mat_simple('WinGlass', (0.02, 0.025, 0.03), 0.04, coat=1.0)[0]
    M['lit'] = mat_simple('LitGlass', (0.05, 0.04, 0.03), 0.1, emit=(1, 0.7, 0.38), estr=2.6)[0]
    M['hole'] = mat_simple('Opening', (0.015, 0.013, 0.012), 0.9)[0]
    M['snow'] = mat_textured('Snow', ['snow_02'], 0.6, (0.9, 0.92, 0.95), rough=(0.4, 0.8))[0]
    M['ice'] = mat_simple('Ice', (0.82, 0.9, 1.0), 0.08, trans=0.75, ior=1.31)[0]
    M['puddle'] = mat_simple('Puddle', (0.05, 0.055, 0.06), 0.03, coat=1.0)[0]
    M['water'] = mat_simple('Water', (0.6, 0.7, 0.78), 0.02, trans=0.95, ior=1.33)[0]
    M['pool'] = mat_simple('Pool', (0.18, 0.4, 0.62), 0.05, coat=1.0, emit=(0.15, 0.45, 0.9), estr=1.6)[0]
    M['steel'] = mat_simple('Galv', (0.62, 0.63, 0.64), 0.32, 1.0)[0]
    M['dark'] = mat_simple('Dark', (0.012, 0.012, 0.012), 0.9)[0]
    M['vent'] = mat_simple('VentSlot', (0.02, 0.02, 0.022), 0.7, 0.3)[0]
    M['insul'] = mat_textured('Insulation', ['snow_02'], 0.5, (0.9, 0.75, 0.45), rough=(0.9, 1.0), tint=(1.0, 0.78, 0.45))[0]
    M['grass'] = mat_textured('Lawn', ['sparse_grass'], 0.4, (0.15, 0.25, 0.08), rough=(0.85, 1.0), bump=0.8)[0]
    M['studio'] = mat_simple('StudioFloor', (0.045, 0.045, 0.05), 0.55)[0]
    M['red'] = mat_emit('Push', (1.0, 0.12, 0.05), 6.0)[0]
    M['glow'] = mat_emit('Tri', (1.0, 0.78, 0.2), 9.0)[0]
    M['air'] = mat_emit('Air', (0.45, 0.8, 1.0), 14.0)[0]
    M['warm'] = mat_emit('Warm', (1.0, 0.55, 0.25), 2.5)[0]
    return M

# ---------------------------------------------------------------- set pieces
def day(rot=30, e=2.2, elev=38, azim=150):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, math.radians(rot)); return sun(e, elev, azim)
def overcast(e=0.7):
    world_hdri('kloofendal_overcast_puresky', 0.55, 0, 'overcast'); return sun(e, 40, 160, color=(0.85, 0.9, 1.0))
def winter_dusk():
    world_hdri('snowy_field', 0.32, math.radians(40), 'overcast'); return sun(0.5, 10, 200, color=(0.75, 0.82, 1.0))

def studio_lights(key_e=500, rim_e=300):
    k = light('AREA', (-2.2, -3.0, 2.6), key_e, (1, 0.96, 0.9), 2.5); aim(k, (0, 0, 0))
    r = light('AREA', (2.6, 2.0, 2.2), rim_e, (0.85, 0.9, 1.0), 2.0); aim(r, (0, 0, 0))

def site(M, snow=False, lawn=False):
    g = plane('Ground', 140, 140, (0, 0, -0.02), M['snow'] if snow else (M['grass'] if lawn else M['dirt']))
    if not snow and not lawn:
        plane('Lawn', 160, 160, (0, 0, -0.06), M['grass'])
        box('Gravel', (W + 2.2, D + 2.2, 0.04), (0, 0, -0.01), M['gravel'])
    box('Slab', (W + 0.2, D + 0.2, 0.3), (0, 0, -0.15 + (0.01 if lawn or snow else 0.0)), M['conc'])
    return g

def lumber_pile(M, loc, n=7, rot=0.2):
    rig = empty('Pile', loc); rig.rotation_euler = (0, 0, rot)
    for i in range(n):
        o = box('Board', (3.6, 0.14, 0.045), (0, (i % 4) * 0.15 - 0.22, 0.12 + (i // 4) * 0.046), M['lumber'])
        o.parent = rig
    for x in (-1.3, 0, 1.3): box('Sticker', (0.08, 0.7, 0.09), (x, 0, 0.045), M['lumber']).parent = rig
    return rig

def frame_walls(M, sheath=None):
    """sheathed wall boxes with dark rough openings. Returns {'f': front pivot, 'b': back pivot, 'all': [...]}"""
    m = sheath or M['ply']; P = {}; allo = []
    for s, k in ((-1, 'f'), (1, 'b')):
        pv = empty('WallPivot', (0, s * D / 2, 0)); P[k] = pv
        w = box('Wall', (W, 0.15, H), (0, s * (D / 2 - 0.075), H / 2), m); adopt(w, pv); allo.append(w)
        tp = box('TopPlate', (W, 0.15, 0.04), (0, s * (D / 2 - 0.075), H - 0.02), M['lumber']); adopt(tp, pv)
        for x in (-1.6, 1.6):
            o = box('Opening', (1.0, 0.16, 1.2), (x, s * (D / 2 - 0.075), 1.45), M['hole']); adopt(o, pv)
        if s < 0:
            o = box('DoorOpening', (0.95, 0.16, 2.1), (0, -(D / 2 - 0.075), 1.05), M['hole']); adopt(o, pv)
    for sx in (-1, 1):
        allo.append(box('EndWall', (0.15, D - 0.3, H), (sx * (W / 2 - 0.075), 0, H / 2), m))
        box('TopPlate', (0.15, D - 0.3, 0.04), (sx * (W / 2 - 0.075), 0, H - 0.02), M['lumber'])
        box('Opening', (0.16, 1.0, 1.2), (sx * (W / 2 - 0.075), 0, 1.45), M['hole'])
    P['all'] = allo
    return P

def finished_walls(M, lit=False):
    gm = M['lit'] if lit else M['glass']
    box('Walls', (W, D, H), (0, 0, H / 2), M['siding'])
    for sx in (-1, 1):
        for sy in (-1, 1): box('Corner', (0.12, 0.12, H), (sx * W / 2, sy * D / 2, H / 2), M['trim'])
    def window(x, y, z, face='y'):
        if face == 'y':
            box('WinTrim', (1.16, 0.06, 1.36), (x, y, z), M['trim']); box('Win', (1.0, 0.08, 1.2), (x, y, z), gm)
            box('Mullion', (0.04, 0.1, 1.2), (x, y, z), M['trim']); box('Sill', (1.3, 0.12, 0.05), (x, y - math.copysign(0.03, y), z - 0.7), M['trim'])
        else:
            box('WinTrim', (0.06, 1.16, 1.36), (x, y, z), M['trim']); box('Win', (0.08, 1.0, 1.2), (x, y, z), gm)
    for x in (-1.6, 1.6): window(x, -D / 2, 1.45); window(x, D / 2, 1.45)
    window(-W / 2, 0, 1.45, 'x'); window(W / 2, 0, 1.45, 'x')
    box('DoorTrim', (1.12, 0.06, 2.2), (0, -D / 2, 1.08), M['trim']); box('Door', (0.95, 0.08, 2.08), (0, -D / 2, 1.04), M['door'])
    sphere('Knob', 0.03, (0.36, -D / 2 - 0.05, 1.0), M['steel'], sub=2)
    box('Step', (1.6, 0.6, 0.18), (0, -D / 2 - 0.3, 0.09), M['conc'])

def gable(M, sx, mat=None):
    """gable-end triangle above the wall at x = sx * (W/2 - 0.075)"""
    top = ZR - 0.07 / CS - 0.02
    pts = [(-D / 2, H), (D / 2, H), (0, top)]
    x0 = sx * (W / 2 - 0.075); V = [(x0 - 0.075, y, z) for y, z in pts] + [(x0 + 0.075, y, z) for y, z in pts]
    return mesh_obj('Gable', V, [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], [mat or M['siding']])

def rafter(M, x, s, mat=None):
    yc = s * (D / 2 + OV) / 2; zc = H + 0.1 + (D / 2 - abs(yc)) * TN
    return box('Rafter', (0.045, SL, 0.14), (x, yc, zc), mat or M['lumber'], rot=(-s * PITCH, 0, 0))

def truss(M, x, chord=True, webs=True, plates=True):
    out = [rafter(M, x, -1), rafter(M, x, 1)]
    if chord:
        out.append(box('Chord', (0.045, D, 0.14), (x, 0, H + 0.07), M['lumber']))
        if webs:
            for s in (-1, 1):
                p0 = Vector((x, s * 0.85, H + 0.13)); p1 = Vector((x, s * 1.75, H + 0.1 + (D / 2 - 1.75) * TN - 0.06))
                w = box('Web', (0.04, (p1 - p0).length, 0.09), (p0 + p1) / 2, M['lumber'])
                w.rotation_euler = (math.atan2(p1.z - p0.z, p1.y - p0.y), 0, 0); out.append(w)
                p2 = Vector((x, 0, ZR - 0.1)); p3 = Vector((x, s * 0.85, H + 0.13))
                w = box('Web', (0.04, (p3 - p2).length, 0.09), (p2 + p3) / 2, M['lumber'])
                w.rotation_euler = (math.atan2(p3.z - p2.z, p3.y - p2.y), 0, 0); out.append(w)
        if plates:
            for sx in (-1, 1):
                for (y, z) in ((-D / 2 + 0.2, H + 0.12), (D / 2 - 0.2, H + 0.12), (0, ZR - 0.12), (-0.85, H + 0.08), (0.85, H + 0.08)):
                    out.append(box('Plate', (0.004, 0.22, 0.14), (x + sx * 0.0245, y, z), M['steel']))
    return out

def trusses(M, chord=True, xs=XS):
    out = []
    for x in xs: out += truss(M, x, chord)
    return out

def deck(M, sides=(-1, 1), stop=0.0, mat=None):
    """4x8 sheets (1.22 x 2.44 m), staggered rows. Returns per side lists of sheets (bottom row first)."""
    out = {}
    for s in sides:
        L = []; rows = [(0.0, 1.22), (1.22, 2.44), (2.44, SL - stop)]
        for r, (u0, u1) in enumerate(rows):
            cuts = [-XL, -0.86, 1.58, XL] if r % 2 == 0 else [-XL, -2.08, 0.36, 2.8, XL]
            for xa, xb in zip(cuts[:-1], cuts[1:]):
                c = RP(s, (u0 + u1) / 2, (xa + xb) / 2, DECK / 2)
                L.append(box('Sheet', (xb - xa - 0.004, u1 - u0 - 0.004, DECK), c, mat or M['ply'], rot=(-s * PITCH, 0, 0)))
        out[s] = L
    return out

def underlay(M, sides=(-1, 1), u1=None):
    out = []
    for s in sides:
        u1_ = SL if u1 is None else u1
        out.append(box('Felt', (2 * XL, u1_, UL), RP(s, u1_ / 2, 0, DECK + UL / 2), M['felt'], rot=(-s * PITCH, 0, 0)))
    return out

def shingle_row(M, s, k, xa=-XL - 0.02, xb=XL + 0.02, seed=0):
    random.seed(seed * 100 + k * 7 + (s + 1)); u0 = -0.02 + k * EXPO; u1 = u0 + ROWL
    sl, idx = [], []; x = xa - (k % 2) * TAB / 2
    while x < xb:
        x0, x1 = max(xa, x), min(xb, x + TAB - 0.006)
        if x1 - x0 > 0.01:
            b = [RP(s, u0, x0, SH0 + TB * 0.5), RP(s, u0, x1, SH0 + TB * 0.5), RP(s, u1, x1, SH0), RP(s, u1, x0, SH0)]
            t = [RP(s, u0, x0, SH0 + TB * 1.5), RP(s, u0, x1, SH0 + TB * 1.5), RP(s, u1, x1, SH0 + TB * 0.5), RP(s, u1, x0, SH0 + TB * 0.5)]
            sl.append(b + t); idx.append(random.randrange(3))
        x += TAB
    return slabs_obj('Row', sl, M['shing'], idx)

NROWS = int((SL - ROWL + 0.02) / EXPO) + 1
def shingles(M, sides=(-1, 1), rows=None, cap=True):
    out = {}
    for s in sides:
        out[s] = [shingle_row(M, s, k) for k in range(rows if rows is not None else NROWS)]
    if cap:
        for s in (-1, 1):
            roof_prism('Cap', s, [(SL - 0.18, SH0 + TB), (SL + 0.02, SH0 + TB), (SL + 0.02, SH0 + TB + 0.03), (SL - 0.18, SH0 + TB + 0.012)], -XL, XL, M['shing'][1])
    return out

def eaves(M, vents=False):
    for s in (-1, 1):
        zt = RP(s, 0, 0, DECK).z
        box('Fascia', (2 * XL, 0.025, 0.2), (0, s * (D / 2 + OV + 0.035), zt - 0.1), M['trim'])
        box('Soffit', (2 * XL, OV + 0.03, 0.015), (0, s * (D / 2 + (OV + 0.03) / 2), H - 0.22), M['trim'])
        if vents:
            box('SoffitVent', (2 * XL - 0.3, 0.09, 0.017), (0, s * (D / 2 + 0.22), H - 0.22), M['vent'])
    for sx in (-1, 1):   # rake boards along the gable edges
        for s in (-1, 1):
            p0 = RP(s, 0, sx * (XL + 0.012), DECK - 0.1); p1 = RP(s, SL, sx * (XL + 0.012), DECK - 0.1)
            r = box('Rake', (0.025, SL, 0.2), (p0 + p1) / 2, M['trim'], rot=(-s * PITCH, 0, 0))

def snow_cover(M, sides=(-1, 1), u0=-0.03, u1=None, th=0.13, off=SH0 + TB * 1.2):
    out = []
    for s in sides:
        u1_ = (SL - 0.12) if u1 is None else u1
        out.append(roof_prism('RoofSnow', s, [(u0, off), (u1_, off), (u1_, off + th * 0.8), (u0 + 0.05, off + th), (u0, off + th * 0.6)], -XL - 0.02, XL + 0.02, M['snow']))
    return out

def finished_roof(M, vents=False, ridge_gap=False):
    trusses(M); deck(M, stop=0.04 if ridge_gap else 0.0); underlay(M); shingles(M); eaves(M, vents)

def person_at(name, loc, face_to, outfit='worker', stance='relax'):
    v = Vector(face_to) - Vector(loc); th = math.atan2(v.x, -v.y)
    return person(name, loc=loc, rot_z=th, outfit=outfit, stance=stance)

# ================================================================ shots
def S00(a, b):  # hook: flat boards laid across the walls in the rain; water ponds on top and pours over the edges
    sc = new_scene(a, b); d = dur(a, b); M = mats(); overcast(0.6)
    site(M); P = frame_walls(M); lumber_pile(M, (-5.2, -1.2, 0), rot=0.5)
    x = -3.1
    while x < 3.15:
        box('Plank', (0.19, D + 0.3, 0.025), (x, 0, H + 0.0125), M['wetlumber']); x += 0.21
    random.seed(5)
    for i in range(7):
        px, py = random.uniform(-2.2, 2.2), random.uniform(-1.6, 1.6); r = random.uniform(0.5, 1.1)
        o = sphere('Puddle', 1.0, (px, py, H + 0.026), M['puddle'], sub=4)
        key(o, 'scale', [(0, Vector((r * 0.55, r * 0.45, 0.004))), (d, Vector((r * 1.1, r * 0.9, 0.006)))])
    pts = [(random.uniform(-2.9, 2.9), -D / 2 - 0.16, H) for i in range(14)] + [(-W / 2 - 0.16, random.uniform(-2.3, 2.3), H) for i in range(8)]
    drops(M, pts, d, seed=3, r=0.014, cyc=0.45, fall=H)
    arm = person_at('Owner', (-3.1, -4.1, 0), (0, 0, 0), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.0, STANCES['relax']); pose(arm, 3.2, {'neck01': (-8, 0, 0)})
    cp = (-6.4, -8.0, 4.3); tg = (0.2, 0.3, 2.0)
    camera([(0, cp, tg), (d, (-6.0, -7.4, 4.2), (0.2, 0.3, 2.0))], lens=24, fstop=9)
    rain(cp, tg, d)

def S01(a, b):  # gable view: the board halves swing up into a slope, the puddles drain and the water runs off the edges
    sc = new_scene(a, b); d = dur(a, b); M = mats(); overcast(0.6)
    site(M); frame_walls(M); lumber_pile(M, (-5.2, -3.0, 0), rot=0.2)
    L = D / 2 / CS; t0, t1 = 0.35, 1.5
    for s in (-1, 1):
        pv = empty('Hinge', (0, s * D / 2, H + 0.0125 + (0.026 if s > 0 else 0)))
        x = -3.1
        while x < 3.15:
            o = box('Plank', (0.19, L + 0.15, 0.025), (x, s * (D / 2 - (L - 0.15) / 2), pv.location.z), M['wetlumber']); adopt(o, pv); x += 0.21
        random.seed(8 + s)
        for i in range(3):
            o = sphere('Puddle', 1.0, (random.uniform(-2, 2), s * random.uniform(0.6, 1.8), pv.location.z + 0.014), M['puddle'], sub=4)
            o.scale = (0.7, 0.55, 0.005); adopt(o, pv)
            key(o, 'scale', [(0, Vector((0.7, 0.55, 0.005))), (t0, Vector((0.7, 0.55, 0.005))), (t1 - 0.3, Vector((0.05, 0.05, 0.002)))])
        key(pv, 'rotation_euler', [(0, Vector((0, 0, 0))), (t0, Vector((0, 0, 0))), (t1, Vector((-s * PITCH, 0, 0)))])
        random.seed(20 + s)
        pts = [(random.uniform(-2.9, 2.9), s * (D / 2 + 0.16), H - 0.06) for i in range(16)]
        drops(M, pts, d, seed=4 + s, r=0.014, cyc=0.3, fall=H - 0.06, t0=t1 - 0.1)
    cp = (10.5, -1.4, 2.7); tg = (0, 0, 2.6)
    camera([(0, cp, tg), (d, (10.0, -1.2, 2.7), tg)], lens=26, fstop=11)
    rain(cp, tg, d)

def S02(a, b):  # rafters alone: their weight shoves the wall tops outward, the walls lean, the ridge sags; worker points
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(rot=60, e=2.0, elev=30, azim=120)
    site(M); P = frame_walls(M); lumber_pile(M, (-5.2, -3.0, 0), rot=0.2)
    t0, t1 = 0.5, 2.8; lean = math.radians(4.0); dl = 0.1
    for s, k in ((-1, 'f'), (1, 'b')):
        key(P[k], 'rotation_euler', [(0, Vector((0, 0, 0))), (t0, Vector((0, 0, 0))), (t1, Vector((-s * lean, 0, 0)))])
        rp = empty('RidgePivot', (0, 0, ZR))
        for x in XS: adopt(rafter(M, x, s), rp)
        key(rp, 'rotation_euler', [(0, Vector((0, 0, 0))), (t0, Vector((0, 0, 0))), (t1, Vector((s * dl, 0, 0)))])
        key(rp, 'location', [(0, Vector((0, 0, ZR))), (t0, Vector((0, 0, ZR))), (t1, Vector((0, 0, ZR - 0.27)))])
        for o in arrow('Push', (3.25, s * (D / 2 - 0.25), H - 0.1), (0, s, 0), 0.75, M['red']):
            key(o, 'scale', [(0, Vector((0.001, 0.001, 0.001))), (t0 + 0.2, Vector((0.001, 0.001, 0.001))), (t0 + 0.6, Vector((1, 1, 1)))])
    arm = person_at('Worker', (4.8, -3.9, 0), (3.0, -2.5, 2.0))
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.0, STANCES['relax']); pose(arm, 1.8, STANCES['point_r'])
    camera([(0, (9.0, -5.5, 2.9), (0, -0.3, 2.7)), (d, (8.5, -5.2, 2.9), (0, -0.3, 2.7))], lens=24, fstop=11)

def S03(a, b):  # a bottom board drops in and ties the rafter feet together; the walls stand straight; the triangle glows
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(rot=60, e=2.0, elev=30, azim=120)
    site(M); P = frame_walls(M); lumber_pile(M, (-5.2, -3.0, 0), rot=0.2)
    lean = math.radians(4.0); dl = 0.1; tc0, tc1 = 0.75, 1.3; tw = 2.1
    for s, k in ((-1, 'f'), (1, 'b')):
        key(P[k], 'rotation_euler', [(0, Vector((-s * lean, 0, 0))), (tc1, Vector((-s * lean, 0, 0))), (tw, Vector((0, 0, 0)))])
        rp = empty('RidgePivot', (0, 0, ZR))
        for x in XS: adopt(rafter(M, x, s), rp)
        key(rp, 'rotation_euler', [(0, Vector((s * dl, 0, 0))), (tc1, Vector((s * dl, 0, 0))), (tw, Vector((0, 0, 0)))])
        key(rp, 'location', [(0, Vector((0, 0, ZR - 0.27))), (tc1, Vector((0, 0, ZR - 0.27))), (tw, Vector((0, 0, ZR)))])
    for i, x in enumerate(XS):
        c = box('Chord', (0.045, D + 0.3, 0.14), (x, 0, H + 0.07), M['lumber'])
        td = tc0 - 0.05 * (9 - i)
        key(c, 'location', [(0, Vector((x, 0, H + 1.6))), (max(0.01, td - 0.35), Vector((x, 0, H + 1.6))), (td + 0.3, Vector((x, 0, H + 0.07)))], interp='LINEAR')
    xg = XS[-1] + 0.06; tg0 = 2.5
    for p0, p1 in (((xg, -D / 2 - 0.05, H + 0.07), (xg, D / 2 + 0.05, H + 0.07)), ((xg, -D / 2 - 0.05, H + 0.07), (xg, 0, ZR + 0.07)), ((xg, D / 2 + 0.05, H + 0.07), (xg, 0, ZR + 0.07))):
        r = rod('Glow', p0, p1, 0.022, M['glow'])
        key(r, 'scale', [(0, Vector((0.001, 0.001, 1))), (tg0, Vector((0.001, 0.001, 1))), (tg0 + 0.5, Vector((1, 1, 1)))])
    camera([(0, (9.6, -1.6, 2.9), (0, -0.1, 2.9)), (d, (8.6, -1.4, 2.9), (0, -0.1, 2.9))], lens=26, fstop=11)

def S04(a, b):  # inside, looking up between the trusses: rain pours through the gaps onto a worker
    sc = new_scene(a, b); d = dur(a, b); M = mats(); overcast(0.9)
    site(M); frame_walls(M); trusses(M)
    plane('WetFloor', W - 0.3, D - 0.3, (0, 0, 0.002), M['wetconc'])
    random.seed(9)
    pts = [(random.uniform(-2.6, 2.6), random.uniform(-2.0, 2.2), H + 1.2) for i in range(60)]
    drops(M, pts, d, seed=10, r=0.009, cyc=0.6, fall=H + 1.2)
    arm = person_at('Worker', (-0.4, 0.9, 0), (1.4, -1.9, 1.5))
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.6, {'neck01': (-14, 0, 0), 'upperarm01.R': (60, 0, 30), 'lowerarm01.R': (40, 0, 0)})
    cp = (1.4, -1.9, 1.15); tg = (-0.6, 0.9, 2.9)
    camera([(0, cp, tg), (d, (1.3, -1.75, 1.1), (-0.6, 0.9, 3.0))], lens=20, fstop=8)
    for k, dd in enumerate((2.0, 3.6)):
        c = Vector(cp) + (Vector(tg) - Vector(cp)).normalized() * dd
        r = plane('Rain', 7, 7, c, mat_rain('RainIn%d' % k, 0.5, 34, d)); r.rotation_euler = (math.radians(90), 0, math.atan2(2.0, 2.8))

def S05(a, b):  # plywood sheets slam down onto the trusses one after another; a worker points up at them
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(rot=20, e=2.3, elev=35, azim=140)
    site(M); frame_walls(M); trusses(M); lumber_pile(M, (-5.2, -2.6, 0), rot=0.4)
    sh = deck(M)
    order = sh[-1]; nd = 0
    for i, o in enumerate(order):
        if i < 3: continue
        ti = 0.15 + nd * 0.33; nd += 1; _, n = rv(-1); p = o.location.copy()
        key(o, 'location', [(0, p + n * 1.2), (ti, p + n * 1.2), (ti + 0.22, p)], interp='LINEAR'); hide(o, ti - 0.05)
    for o in sh[1]: pass
    arm = person_at('Worker', (-2.4, -4.0, 0), (-0.5, -1.0, 3.2))
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.5, STANCES['point_r'])
    camera([(0, (-6.6, -8.6, 3.3), (0.2, -0.6, 2.9)), (d, (-6.2, -8.2, 3.3), (0.2, -0.6, 2.9))], lens=24, fstop=11)

def S06(a, b):  # macro: water beads on bare plywood, soaks in, the wood darkens and mold spots spread
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.35, 0, 'studio'); studio_lights(420, 260)
    plane('Floor', 20, 20, (0, 0, -0.01), M['studio'])
    box('Board', (0.9, 0.6, 0.018), (0, 0, 0.009), M['ply'])
    random.seed(13)
    for i in range(9):
        cx, cy = random.uniform(-0.12, 0.14), random.uniform(-0.09, 0.11); r0 = random.uniform(0.05, 0.11)
        w = sphere('WetPatch', 1.0, (cx, cy, 0.0184 + i * 0.00003), M['wetply'], sub=4); w.rotation_euler = (0, 0, random.uniform(0, 3))
        key(w, 'scale', [(0, Vector((r0 * 0.35, r0 * 0.25, 0.0006))), (d, Vector((r0, r0 * 0.7, 0.0008)))])
    rt = sphere('RotPatch', 1.0, (0.05, 0.03, 0.0188), M['rot'], sub=4)
    key(rt, 'scale', [(0, Vector((0.001, 0.001, 0.0005))), (d * 0.35, Vector((0.001, 0.001, 0.0005))), (d, Vector((0.12, 0.09, 0.0006)))])
    random.seed(12)
    for i in range(16):
        x, y = random.uniform(-0.18, 0.2), random.uniform(-0.14, 0.15)
        o = sphere('Bead', random.uniform(0.006, 0.014), (x, y, 0.018), M['water'], sub=3)
        tb = random.uniform(0.1, d); s0 = Vector((1, 1, 0.55))
        key(o, 'scale', [(0, s0), (tb, s0), (min(d, tb + 0.5), Vector((1.3, 1.3, 0.05)))])
    for i in range(20):
        x, y = random.uniform(-0.08, 0.16), random.uniform(-0.06, 0.12); r = random.uniform(0.004, 0.012)
        o = sphere('Mold', r, (x, y, 0.019), M['mold'], sub=2); tb = random.uniform(d * 0.3, d * 0.9)
        key(o, 'scale', [(0, Vector((0.01, 0.01, 0.01))), (tb, Vector((0.01, 0.01, 0.01))), (min(d, tb + 0.4), Vector((1, 1, 0.12)))])
    camera([(0, (0.18, -0.55, 0.3), (0.03, 0.0, 0.01)), (d, (0.14, -0.48, 0.26), (0.03, 0.0, 0.01))], lens=50, fstop=3.2)

def S07(a, b):  # a roll of grey waterproof underlayment unrolls across the plywood deck
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(rot=20, e=2.3, elev=35, azim=140)
    site(M); frame_walls(M); trusses(M); deck(M)
    box('Felt1', (2 * XL, 0.95, UL), RP(-1, 0.475, 0, DECK + UL / 2), M['felt'], rot=(PITCH, 0, 0))
    x0 = -XL; xe = lambda t: x0 + 0.25 + 4.4 * t / d
    st = box('Felt2', (1, 0.95, UL), RP(-1, 1.3, x0, DECK + UL * 1.5), M['felt'], rot=(PITCH, 0, 0))
    pts_l, pts_s, pts_r = [], [], []
    for k in range(7):
        t = d * k / 6; xx = xe(t)
        pts_l.append((t, RP(-1, 1.3, (x0 + xx) / 2, DECK + UL * 1.5))); pts_s.append((t, Vector((xx - x0, 1, 1))))
        pts_r.append((t, RP(-1, 1.3, xx, DECK + 0.075)))
    key(st, 'location', pts_l, interp='LINEAR'); key(st, 'scale', pts_s, interp='LINEAR')
    roll = cyl('Roll', 0.075, 0.95, pts_r[0][1], M['felt'], rot=(-math.radians(60), 0, 0), verts=32)
    key(roll, 'location', pts_r, interp='LINEAR')
    core = cyl('Core', 0.03, 0.97, pts_r[0][1], M['dark'], rot=(-math.radians(60), 0, 0), verts=16); adopt(core, roll)
    cam_p = RP(-1, -0.6, -2.9, 1.0); tgt = RP(-1, 1.1, -0.4, 0.0)
    camera([(0, cam_p, tgt), (d, cam_p + Vector((0.5, 0, 0)), tgt + Vector((0.7, 0, 0)))], lens=24, fstop=6)

def S08(a, b):  # shingle rows land one above the other from the eave up, each overlapping the one below
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(rot=20, e=2.4, elev=32, azim=135)
    site(M); frame_walls(M); trusses(M); deck(M); underlay(M); eaves(M)
    rows = shingles(M, sides=(-1,), cap=False)[-1]
    _, n = rv(-1)
    for k, o in enumerate(rows):
        tk = 0.05 + k * (d - 0.5) / len(rows)
        if tk < 0.1: continue
        key(o, 'location', [(0, n * 0.35), (tk, n * 0.35), (tk + 0.16, Vector((0, 0, 0)))], interp='LINEAR'); hide(o, tk - 0.02)
    cam_p = RP(-1, -1.3, 1.6, 0.75); tgt = RP(-1, 1.4, -0.2, 0.0)
    camera([(0, cam_p, tgt), (d, cam_p + Vector((0, 0, 0.12)), tgt + Vector((0, 0, 0.15)))], lens=26, fstop=7)

def S09(a, b):  # close-up on the newest shingle strip: four galvanized nails punch in, one after another
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(rot=20, e=2.4, elev=32, azim=135)
    site(M); frame_walls(M); trusses(M); deck(M, sides=(-1,)); underlay(M, sides=(-1,)); eaves(M)
    k = 8; shingles(M, sides=(-1,), rows=k + 1, cap=False)
    u = -0.02 + k * EXPO + 0.165; s = -1; _, n = rv(s)
    xa = -1.0
    for i, (xx, tn) in enumerate(zip((xa + 0.03, xa + 0.333, xa + 0.667, xa + 0.97), (0.6, 0.9, 1.2, 1.5))):
        p = RP(s, u, xx, SH0 + TB * 0.95)
        rig = empty('Nail', p + n * 0.25); rig.scale = (2.0, 2.0, 2.0); rig.rotation_euler = (-s * PITCH, 0, 0)
        cyl('Head', 0.0055, 0.0015, (0, 0, 0.0008), M['steel'], verts=24).parent = rig
        cyl('Shank', 0.0016, 0.032, (0, 0, -0.016), M['steel'], verts=12).parent = rig
        key(rig, 'location', [(0, p + n * 0.25), (tn - 0.12, p + n * 0.25), (tn, p)], interp='LINEAR'); hide(rig, tn - 0.14)
        for c in rig.children: hide(c, tn - 0.14)
    cam_p = RP(s, u - 0.17, xa + 0.05, 0.17); tgt = RP(s, u, xa + 0.5, SH0)
    camera([(0, cam_p, tgt), (d, cam_p + Vector((0.03, 0, 0)), tgt)], lens=32, fstop=4.5)

def S10(a, b):  # winter dusk: warm windows, the snow high on the roof thins and melts, water runs down to the cold edge
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('snowy_field', 0.45, math.radians(40), 'overcast'); sun(1.3, 14, 160, color=(0.8, 0.86, 1.0))
    site(M, snow=True); finished_walls(M, lit=True); gable(M, -1); gable(M, 1); finished_roof(M)
    for s in (-1, 1):
        snow_cover(M, (s,), u0=-0.03, u1=0.7)
        up = snow_cover(M, (s,), u0=0.7, u1=SL - 0.12)[0]; _, n = rv(s)
        key(up, 'location', [(0, Vector((0, 0, 0))), (d, -n * 0.085)])
    random.seed(30)
    for i in range(14):
        x = random.uniform(-2.9, 2.9); tb = random.uniform(0, d - 0.6)
        o = sphere('Melt', 0.012, RP(-1, 1.6, x, SH0 + 0.07), M['water'], sub=2)
        key(o, 'location', [(tb, RP(-1, 1.6, x, SH0 + 0.07)), (tb + 0.6, RP(-1, 0.7, x, SH0 + 0.07))], interp='LINEAR'); hide(o, tb, tb + 0.6)
    for i in range(18):
        x = random.uniform(-3.1, 3.1); L = random.uniform(0.08, 0.3); z = RP(-1, 0, 0, DECK).z - 0.2
        bpy.ops.mesh.primitive_cone_add(radius1=0.018, radius2=0, depth=L, location=(x, -(D / 2 + OV + 0.05), z - L / 2), rotation=(math.pi, 0, 0), vertices=10)
        c = bpy.context.active_object; c.data.materials.append(M['ice'])
    light('POINT', (0, 0, 1.6), 120, (1, 0.7, 0.4), 1.0)
    arm = person_at('Owner', (-2.6, -5.6, 0), (0, 0, 2.5), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.4, {'neck01': (-8, 0, 0)})
    camera([(0, (-4.8, -10.2, 1.7), (0.2, 0, 2.9)), (d, (-4.4, -9.5, 1.75), (0.2, 0, 2.95))], lens=26, fstop=9)

def S11(a, b):  # cut-away at the eave: an ice dam on the cold edge, melt water pools behind it and creeps up under the shingles
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter_dusk()
    world_hdri('snowy_field', 0.5, math.radians(40), 'overcast'); sun(0.8, 18, 210, color=(0.8, 0.86, 1.0))
    site(M, snow=True); finished_walls(M, lit=True); finished_roof(M)
    s = -1; _, n = rv(s)
    snow_cover(M, (s,), u0=0.75, u1=SL - 0.12, th=0.09)
    roof_prism('IceDam', s, [(-0.04, SH0 + TB), (0.5, SH0 + TB), (0.42, SH0 + TB + 0.07), (0.2, SH0 + TB + 0.15), (0.02, SH0 + TB + 0.13), (-0.06, SH0 + TB + 0.04)], -XL - 0.02, XL + 0.02, M['ice'])
    pool = roof_prism('Pool', s, [(0.42, SH0 + TB), (0.85, SH0 + TB), (0.42, SH0 + TB + 0.065)], -XL - 0.01, XL + 0.01, M['pool'])
    t0 = 0.6; t1 = d - 0.4
    wl = box('UnderWater', (2 * XL + 0.02, 1, 0.01), RP(s, 0.8, 0, SH0 - 0.001), M['pool'], rot=(-s * PITCH, 0, 0))
    key(wl, 'scale', [(0, Vector((1, 0.05, 1))), (t0, Vector((1, 0.05, 1))), (t1, Vector((1, 0.75, 1)))])
    key(wl, 'location', [(0, RP(s, 0.45 + 0.025, 0, SH0 - 0.001)), (t0, RP(s, 0.45 + 0.025, 0, SH0 - 0.001)), (t1, RP(s, 0.45 + 0.375, 0, SH0 - 0.001))])
    pts = [(XL - 0.25 - i * 0.18, -D / 2 + 0.25, H + 0.05) for i in range(4)]
    drops(M, pts, d, seed=40, r=0.01, cyc=0.7, fall=0.9, t0=t1 - 0.6)
    for i in range(10):
        x = XL - 0.05 - i * 0.12; L = 0.12 + 0.12 * ((i * 37) % 5) / 4; z = RP(s, 0, 0, DECK).z - 0.2
        bpy.ops.mesh.primitive_cone_add(radius1=0.02, radius2=0, depth=L, location=(x, -(D / 2 + OV + 0.05), z - L / 2), rotation=(math.pi, 0, 0), vertices=10)
        bpy.context.active_object.data.materials.append(M['ice'])
    light('AREA', (2.2, -1.5, H + 0.4), 60, (1, 0.55, 0.3), 1.5)
    cam_p = (XL + 1.7, -2.95, 2.85); tgt = (XL, -2.5, 2.6)
    camera([(0, cam_p, tgt), (d, (XL + 1.5, -2.9, 2.82), tgt)], lens=32, fstop=6)

def S12(a, b):  # attic cut-away (gable removed): cold air streams in at the soffit vents, under the deck and out the ridge
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter_dusk()
    world_hdri('snowy_field', 0.55, math.radians(40), 'overcast'); sun(1.0, 16, 120, color=(0.85, 0.9, 1.0))
    site(M, snow=True); finished_walls(M, lit=True); gable(M, -1); finished_roof(M, vents=True, ridge_gap=True)
    snow_cover(M, (-1, 1), u0=-0.03, u1=SL - 0.15, th=0.11)
    light('AREA', (0.5, 0, ZR - 0.5), 40, (0.7, 0.85, 1.0), 2.0)
    box('Insulation', (W - 0.3, D - 1.0, 0.25), (0, 0, H + 0.125), M['insul'])
    random.seed(50)
    for s in (-1, 1):
        for i in range(80):
            x = random.uniform(0.6, 3.2); tb = random.uniform(-1.5, d)
            p = [Vector((x, s * (D / 2 + 0.24), H - 0.55)), Vector((x, s * (D / 2 + 0.22), H - 0.2)), RP(s, 0.6, x, -0.06),
                 RP(s, SL * 0.55, x, -0.08), RP(s, SL - 0.15, x, -0.08), Vector((x, s * 0.02, ZR + 0.1)), Vector((x, s * 0.25, ZR + 0.55))]
            seg = [(p[j + 1] - p[j]).length for j in range(len(p) - 1)]; tot = sum(seg); T = 2.4
            pts = []; acc = 0.0
            for j, q in enumerate(p):
                pts.append((tb + T * acc / tot, q))
                if j < len(seg): acc += seg[j]
            o = sphere('Air', 0.06, p[0], M['air'], sub=2)
            key(o, 'location', pts, interp='LINEAR'); hide(o, max(0.0, tb) if tb > 0 else None, tb + T)
    arm = person_at('Worker', (4.6, -2.0, 0), (3.0, -2.75, 2.2))
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.8, STANCES['relax']); pose(arm, 1.6, STANCES['point_r'])
    camera([(0, (8.6, -1.6, 3.5), (0, -0.3, 2.9)), (d, (7.9, -1.4, 3.5), (0, -0.3, 2.95))], lens=24, fstop=11)

def S13(a, b):  # the finished house at dusk, warm windows; the owner walks up the path
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(200)); sun(1.4, 6, 200, color=(1, 0.72, 0.45))
    site(M, lawn=True); finished_walls(M, lit=True); gable(M, -1); gable(M, 1); finished_roof(M, vents=True)
    box('Path', (1.1, 6.0, 0.04), (0, -D / 2 - 3.6, 0.0), M['conc'])
    arm = person_at('Owner', (-0.15, -8.2, 0.02), (0, 0, 0), outfit='casual')
    if arm:
        key(arm, 'location', [(0, Vector((-0.15, -8.2, 0.02))), (d, Vector((-0.15, -5.6, 0.02)))], interp='LINEAR')
        walk(arm, 0.0, d)
    camera([(0, (-2.3, -12.4, 1.7), (0.1, 0, 2.3)), (d, (-1.9, -11.2, 1.75), (0.1, 0, 2.4))], lens=26, fstop=9)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13]

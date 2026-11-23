# Shots for "Why Train Tracks Sit on a Pile of Rocks" (how a railroad track is built, problem -> fix chain).
# Z up, metres. The track runs along +Y, centred on x = 0. Ground (subgrade dirt) is z = 0.
# Person faces -Y at rot_z=0 (rot_z = theta faces (sin theta, -cos theta)). t = seconds from the shot start.
import bmesh
from mathutils import Matrix, Euler

def dur(a, b): return (b - a) / FPS

G = 1.435                 # standard gauge (4 ft 8 1/2 in) between the inner faces of the rail heads
RX = G / 2 + 0.037        # rail centre line x
RH = 0.186                # rail height (136 lb rail ~ 7 5/16 in)
TW, TH_, TL = 0.23, 0.18, 2.59   # tie width (9 in), height (7 in), length (8.5 ft)
SP = 0.495                # tie spacing (19.5 in)
PL = 0.02                 # tie plate thickness
TB = 0.20                 # tie bottom when the track sits in ballast
BT = TB + 0.15            # ballast top (a little under the tie top)

PROF = [(-0.076, 0), (0.076, 0), (0.076, 0.012), (0.03, 0.026), (0.009, 0.04), (0.009, 0.145), (0.037, 0.152),
        (0.037, RH), (-0.037, RH), (-0.037, 0.152), (-0.009, 0.145), (-0.009, 0.04), (-0.03, 0.026), (-0.076, 0.012)]

# ---------------------------------------------------------------- materials
def rail_mat():
    m, p = mat_textured('RailRust', ['rusty_metal_02'], 2.5, (0.25, 0.13, 0.07), rough=(0.6, 0.9), tint=(0.62, 0.48, 0.4))
    nt = m.node_tree; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    p2 = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p2.inputs['Base Color'].default_value = (0.62, 0.61, 0.6, 1); p2.inputs['Metallic'].default_value = 1.0
    p2.inputs['Roughness'].default_value = 0.24
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = RH - 0.012; mr.inputs['From Max'].default_value = RH - 0.006
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mr.outputs['Result'], mix.inputs['Fac']); nt.links.new(p.outputs['BSDF'], mix.inputs[1]); nt.links.new(p2.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m

def stone_mat():
    m, nt, p = nodes_mat('Stone')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 9.0; n.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); e0, e1 = ramp.color_ramp.elements
    e0.color = (0.1, 0.097, 0.093, 1); e1.color = (0.32, 0.31, 0.295, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.82
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 140; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.003
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

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

def water_mat(name='Water', col=(0.05, 0.09, 0.1), rough=0.04):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 6
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def mats(wet=False):
    M = {}
    M['rail'] = rail_mat()
    M['tie'] = mat_textured('Tie', ['rough_wood'], 1.4, (0.18, 0.12, 0.08), rough=(0.7, 0.95), tint=(0.42, 0.32, 0.25), wet=0.5 if wet else None)[0]
    M['dirt'] = mat_textured('Dirt', ['dry_ground_rocks'], 0.45, (0.3, 0.22, 0.15), tint=(0.95, 0.85, 0.75))[0]
    M['mud'] = mat_textured('Mud', ['brown_mud_02'], 0.5, (0.2, 0.13, 0.08), tint=(0.62, 0.5, 0.38), wet=0.3)[0]
    M['grass'] = mat_textured('Grass', ['sparse_grass'], 0.25, (0.2, 0.3, 0.1), rough=(0.85, 1.0), bump=0.8, tint=(0.62, 0.72, 0.42))[0]
    M['gravel'] = mat_textured('Gravel', ['gravel_floor_02'], 0.9, (0.4, 0.4, 0.38), tint=(0.3, 0.295, 0.285))[0]
    M['stone'] = stone_mat()
    M['plate'] = mat_textured('Plate', ['rusty_metal_02'], 4.0, (0.2, 0.1, 0.06), tint=(0.45, 0.33, 0.28))[0]
    M['steel'] = mat_simple('Steel', (0.3, 0.3, 0.31), 0.35, 1.0)[0]
    M['dark'] = mat_simple('DarkSteel', (0.05, 0.05, 0.055), 0.5, 0.6)[0]
    M['car'] = paint_mat('CarBody', (0.22, 0.07, 0.04), 0.55, 0.45, 0.2)
    M['yellow'] = paint_mat('Yellow', (0.85, 0.55, 0.03), 0.4, 0.15, 0.0)
    M['chrome'] = mat_simple('Chrome', (0.8, 0.8, 0.82), 0.12, 1.0)[0]
    M['water'] = water_mat()
    M['studio'] = mat_simple('StudioFloor', (0.04, 0.04, 0.045), 0.55)[0]
    return M

# ---------------------------------------------------------------- geometry
def prism_y(name, pts, y0, y1, mat):
    """Extrude a 2D (x, z) outline along +Y from y0 to y1."""
    n = len(pts); verts = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n; faces.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o)
    if mat: o.data.materials.append(mat)
    return o

def rail(M, x, y0, y1, z0, seg=None, kink=None, name='Rail'):
    """A rail along +Y with its foot at z0. kink(y) -> dx adds a shape key 'kink'."""
    seg = seg or max(1, int((y1 - y0) / 4))
    n = len(PROF); verts = []; faces = []
    for s in range(seg + 1):
        y = y0 + (y1 - y0) * s / seg
        verts += [(x + px, y, pz) for px, pz in PROF]
    for s in range(seg):
        a = s * n; b = (s + 1) * n
        for i in range(n):
            j = (i + 1) % n; faces.append((a + i, a + j, b + j, b + i))
    faces.append(tuple(range(n - 1, -1, -1))); faces.append(tuple(range(seg * n, seg * n + n)))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); o.data.materials.append(M['rail']); o.location = (0, 0, z0)
    if kink:
        o.shape_key_add(name='Basis'); k = o.shape_key_add(name='kink')
        for i, v in enumerate(k.data):
            v.co.x += kink(v.co.y)
    return o

def rails(M, y0, y1, z0, seg=None, kink=None, spread=0.0):
    return [rail(M, s * (RX + spread), y0, y1, z0, seg, kink, 'RailL' if s < 0 else 'RailR') for s in (-1, 1)]

def ties(M, y0, y1, z0, seed=2, jitter=0.012):
    random.seed(seed)
    proto = box('Tie', (TL, TW, TH_), (0, -999, 0), M['tie'], bevel=0.008, segs=2)
    out = []; y = y0
    while y <= y1:
        o = dup(proto, (random.uniform(-jitter, jitter) * 2, y + random.uniform(-jitter, jitter), z0 + TH_ / 2),
                rot=(0, 0, random.uniform(-0.012, 0.012)))
        out.append(o); y += SP
    return out

def plates(M, tlist, spikes=True):
    """Tie plates under both rails on every tie, with 4 cut spikes each."""
    pp = box('TiePlate', (0.19, 0.36, PL), (0, -999, 0), M['plate'], bevel=0.003, segs=1)
    sp = box('Spike', (0.016, 0.016, 0.12), (0, -999, 0), M['plate'])
    sh = box('SpikeHead', (0.03, 0.05, 0.014), (0, -999, 0), M['plate'], bevel=0.003, segs=1)
    out = []
    for t in tlist:
        zt = t.location.z + TH_ / 2
        for s in (-1, 1):
            x = t.location.x + s * RX
            out.append(dup(pp, (x, t.location.y, zt + PL / 2)))
            if spikes:
                for dx, dy in ((-0.087, -0.06), (0.087, 0.06), (-0.087, 0.07), (0.087, -0.07)):
                    out.append(dup(sh, (x + dx, t.location.y + dy, zt + PL + 0.035)))
    return out

def ballast(M, y0, y1, prof_top=BT):
    pts = [(-2.75, 0.0), (2.75, 0.0), (1.95, prof_top), (-1.95, prof_top)]
    return prism_y('Ballast', pts, y0, y1, M['gravel'])

def zprof(x, top=BT):
    ax = abs(x)
    if ax <= 1.95: return top
    if ax <= 2.75: return top * (2.75 - ax) / 0.8
    return None

def stone_patch(M, y0, y1, n, top=BT, xr=2.8, seed=1, skip_ties=True, name='Stones', rmin=0.018, rmax=0.036):
    random.seed(seed); bm = bmesh.new()
    for i in range(n):
        x = random.uniform(-xr, xr); y = random.uniform(y0, y1); z = zprof(x, top)
        if z is None: continue
        if skip_ties and abs(x) < TL / 2 + 0.02:
            ph = (y % SP) / SP
            if ph < (TW / 2 + 0.01) / SP or ph > 1 - (TW / 2 + 0.01) / SP: continue
        r = random.uniform(rmin, rmax)
        mtx = Matrix.Translation((x, y, z - r * random.uniform(0.0, 0.7))) @ Euler((random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3))).to_matrix().to_4x4() \
            @ Matrix.Diagonal((random.uniform(0.75, 1.3), random.uniform(0.75, 1.3), random.uniform(0.55, 0.95), 1))
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=mtx)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); o.data.materials.append(M['stone'])
    return o

def ground(M, mat='dirt', size=600, z=0.0, grass=True, gx=4.5):
    g = plane('Ground', size, size, (0, size / 2 - 60, z), M[mat])
    if grass:
        for s in (-1, 1):
            plane('GrassL', size / 2, size, (s * (gx + size / 4), size / 2 - 60, z + 0.01), M['grass'])
    return g

def wheelset(M, y, zr, name='Wheels'):
    """Two 36-in wheels on an axle; returns the rotating empty (rotation x = roll angle)."""
    e = bpy.data.objects.new(name, None); link(e); e.location = (0, y, zr + 0.457)
    P = []
    for s in (-1, 1):
        w = cyl('Wheel', 0.457, 0.135, (0, 0, 0), M['steel'], rot=(0, math.radians(90), 0), verts=48)
        w.parent = e; w.location = (s * (G / 2 + 0.075), 0, 0)
        f = cyl('Flange', 0.485, 0.028, (0, 0, 0), M['dark'], rot=(0, math.radians(90), 0), verts=48)
        f.parent = e; f.location = (s * (G / 2 + 0.012), 0, 0)
        hb = cyl('Hub', 0.16, 0.16, (0, 0, 0), M['dark'], rot=(0, math.radians(90), 0), verts=24)
        hb.parent = e; hb.location = (s * (G / 2 + 0.17), 0, 0)
    ax = cyl('Axle', 0.085, G + 0.45, (0, 0, 0), M['dark'], rot=(0, math.radians(90), 0), verts=24); ax.parent = e; ax.location = (0, 0, 0)
    return e

def railcar(M, zr, loco=False, length=16.0):
    """A freight car (or a locomotive) on two trucks. Returns (root empty, wheel empties). Root origin = car centre at rail top."""
    root = bpy.data.objects.new('Car', None); link(root)
    W = []
    for ty in (-length / 2 + 2.4, length / 2 - 2.4):
        for dy in (-0.9, 0.9):
            w = wheelset(M, ty + dy, 0.0); w.parent = root; W.append(w)
        for s in (-1, 1):
            sf = box('SideFrame', (0.16, 2.7, 0.32), (s * 1.02, ty, 0.5), M['dark'], bevel=0.03, segs=2); sf.parent = root
            sp = box('Springs', (0.2, 0.5, 0.3), (s * 1.02, ty, 0.72), M['dark']); sp.parent = root
        bo = box('Bolster', (2.3, 0.4, 0.25), (0, ty, 0.78), M['dark']); bo.parent = root
    fr = box('Frame', (2.9, length, 0.3), (0, 0, 1.05), M['dark']); fr.parent = root
    if loco:
        bd = box('Hood', (2.6, length - 5.5, 2.7), (0, 1.6, 2.55), M['car'], bevel=0.06, segs=2); bd.parent = root
        cab = box('Cab', (3.0, 3.6, 3.2), (0, -length / 2 + 2.4, 2.8), M['car'], bevel=0.08, segs=2); cab.parent = root
        nose = box('Nose', (2.8, 1.3, 1.5), (0, -length / 2 + 0.2, 1.95), M['car'], bevel=0.08, segs=2); nose.parent = root
        gm = mat_simple('CabGlass', (0.02, 0.025, 0.03), 0.05, coat=1.0)[0]
        for s in (-1, 1):
            wi = box('Win', (1.1, 0.04, 0.8), (s * 0.65, -length / 2 + 0.58, 3.55), gm); wi.parent = root
        hm, he = mat_emit('Headlight', (1, 0.93, 0.8), 60)
        for x, z in ((-0.25, 4.25), (0.25, 4.25), (-1.05, 1.0), (1.05, 1.0)):
            h = cyl('HeadL', 0.11, 0.05, (x, -length / 2 - 0.49, z), hm, rot=(math.radians(90), 0, 0), verts=20); h.parent = root
            s_ = light('SPOT', (x, -length / 2 - 0.6, z), 1800, (1, 0.93, 0.82), 0.08, spot=40, blend=0.5)
            s_.rotation_euler = (math.radians(84), 0, math.radians(180)); s_.parent = root
            try: s_.visible_glossy = False
            except Exception: pass
    else:
        bd = box('Hopper', (3.1, length - 0.8, 2.9), (0, 0, 2.65), M['car'], bevel=0.04, segs=2); bd.parent = root
        for k in range(8):
            rb = box('Rib', (3.16, 0.1, 2.8), (0, -length / 2 + 1.2 + k * (length - 2.4) / 7, 2.65), M['car']); rb.parent = root
    root.location = (0, 0, zr)
    return root, W

def roll(root, W, pts):
    """pts: [(t, y)] linear car motion; wheels spin to match."""
    key(root, 'location', [(t, Vector((0, y, root.location.z))) for t, y in pts], interp='LINEAR')
    for w in W:
        key(w, 'rotation_euler', [(t, Vector((-(y - pts[0][1]) / 0.457, 0, 0))) for t, y in pts], interp='LINEAR')

def rel(o, pts, interp='BEZIER'):
    b = o.location.copy(); key(o, 'location', [(t, b + Vector(v)) for t, v in pts], interp=interp)

def worker(name, loc, rot_deg, M, stance='relax'):
    arm = person(name, loc=loc, rot_z=math.radians(rot_deg), outfit='worker', stance=stance)
    hardhat(arm, M); return arm

def hardhat(arm, M):
    return   # hard hat left out: its bone offset is not verified on the PC yet (it floated above the head)
    if arm is None: return
    hm = mat_simple('HatOrange', (0.9, 0.38, 0.04), 0.35)[0]
    # bone parenting puts the child at the bone TAIL (top of the skull); bone Y = up, so the dome is flattened on Y
    h = sphere('HardHat', 0.125, (0, 0, 0), hm, sub=3); h.scale = (1.0, 0.68, 1.12)
    brim = cyl('Brim', 0.16, 0.012, (0, 0, 0), hm, rot=(math.radians(90), 0, 0), verts=32); brim.parent = h; brim.location = (0, -0.045 / 0.68, 0)
    hold(arm, h, 'head', (0, -0.035, 0.005), (0, 0, 0))

def day(rot=30, sun_e=2.2, elev=38, azim=150, col=(1, 0.96, 0.9)):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, math.radians(rot)); sun(sun_e, elev, azim, color=col)

def studio_lights(key_e=500, rim_e=300, s=1.0):
    k = light('AREA', (-2.2 * s, -3.0 * s, 2.6 * s), key_e, (1, 0.96, 0.9), 2.5 * s); aim(k, (0, 0, 0))
    r = light('AREA', (2.6 * s, 2.0 * s, 2.2 * s), rim_e, (0.85, 0.9, 1.0), 2.0 * s); aim(r, (0, 0, 0))
    f = light('AREA', (1.5 * s, -3.5 * s, 0.2 * s), key_e * 0.25, (1, 1, 1), 2.0 * s); aim(f, (0, 0, -0.3))

def full_track(M, y0=-8, y1=120, stones=(-3, 9, 22000), plates_on=True, seg=None, kink=None, tie_dx=None):
    ground(M, 'dirt', grass=True, gx=3.2)
    ballast(M, y0, y1)
    if stones: stone_patch(M, stones[0], stones[1], stones[2])
    T = ties(M, y0, y1, TB)
    if tie_dx: tie_dx(T)
    P = plates(M, T) if plates_on else []
    R = rails(M, y0, y1, TB + TH_ + (PL if plates_on else 0), seg, kink)
    return T, P, R

# ---------------------------------------------------------------- shots
def S00(a, b):  # low by the dirt: bare rails lie on the ground, a loaded freight car rolls in and the rails sink
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 30, 120)
    ground(M, 'dirt', grass=True, gx=4.0)
    R = rails(M, -6, 140, 0.0)
    for r in R: rel(r, [(0, (0, 0, 0)), (d * 0.3, (0, 0, -0.01)), (d, (0, 0, -0.13))])
    car, W = railcar(M, RH)
    roll(car, W, [(0, 30.0), (d, 11.0)])
    key(car, 'location', [(0, Vector((0, 30.0, RH))), (d * 0.3, Vector((0, 24.3, RH - 0.01))), (d, Vector((0, 11.0, RH - 0.13)))], interp='LINEAR')
    arm = worker('Worker', (3.6, 9.0, 0), -55, M)
    camera([(0, (2.4, 1.2, 0.42), (0.3, 16, 0.9)), (d, (2.3, 2.2, 0.38), (0.3, 16, 0.9))], lens=26, fstop=4.0)

def S01(a, b):  # wooden ties drop in under the rails one by one; a worker points at them
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(60, 2.3, 34, 130)
    ground(M, 'dirt', grass=True, gx=4.0)
    T = ties(M, -2, 30, 0.0)
    for i, t in enumerate(T):
        z = t.location.z; t0 = 0.15 + min(i, 40) * 0.045
        key(t, 'location', [(0, Vector((t.location.x, t.location.y, z + 1.2))), (t0, Vector((t.location.x, t.location.y, z + 1.2))),
                            (t0 + 0.28, Vector((t.location.x, t.location.y, z)))])
    R = rails(M, -2, 31, TH_)
    for r in R: rel(r, [(0, (0, 0, 0.9)), (1.2, (0, 0, 0.9)), (1.7, (0, 0, 0))])
    arm = worker('Worker', (-1.95, 3.6, 0), 55, M)
    pose(arm, 0.6, STANCES['relax']); pose(arm, 1.4, STANCES['point_r'])
    camera([(0, (1.9, -1.8, 1.55), (-0.2, 7, 0.1)), (d, (1.7, -1.2, 1.45), (-0.2, 7.5, 0.1))], lens=26)

def S02(a, b):  # overcast rain: the dirt is mud with puddles and the ties sink and tilt into it
    sc = new_scene(a, b); d = dur(a, b); M = mats(wet=True)
    world_hdri('kloofendal_overcast_puresky', 0.55, math.radians(20)); sun(0.5, 40, 140, color=(0.85, 0.9, 1.0))
    ground(M, 'mud', grass=True, gx=4.0)
    for i, (x, y, r) in enumerate(((0.3, 3.0, 0.9), (-0.9, 6.5, 1.1), (0.8, 10, 1.3), (-0.4, 14, 1.0), (1.6, 1.0, 0.6))):
        pd = cyl('Puddle', r, 0.006, (x, y, 0.004), M['water'], verts=40); pd.scale = (1.0, 1.6, 1.0)
    T = ties(M, -2, 30, 0.0)
    random.seed(7)
    for t in T:
        z = t.location.z; dz = random.uniform(0.07, 0.12); rx = random.uniform(-0.05, 0.05)
        key(t, 'location', [(0, Vector((t.location.x, t.location.y, z))), (d, Vector((t.location.x, t.location.y, z - dz)))])
        key(t, 'rotation_euler', [(0, Vector((0, 0, t.rotation_euler.z))), (d, Vector((rx, random.uniform(-0.03, 0.03), t.rotation_euler.z)))])
    R = rails(M, -2, 31, TH_)
    for r in R: rel(r, [(0, (0, 0, 0)), (d, (0, 0, -0.09))])
    rm = mat_rain('Rain', 0.5, 34, d)
    for k, y in enumerate((1.0, 3.5, 7.0)):
        rp = plane('RainP', 8, 6, (0, y, 2.5), rm); rp.rotation_euler = (math.radians(90), 0, 0)
    arm = worker('Worker', (2.1, 6.0, 0), -115, M)
    pose(arm, 0.0, {'spine02': (14, 0, 0), 'neck01': (12, 0, 0)})
    camera([(0, (-1.4, -1.0, 1.25), (0.4, 6.5, 0.0)), (d, (-1.3, -0.5, 1.2), (0.4, 7.0, 0.0))], lens=28)

def S03(a, b):  # crushed rock pours in and rises up around the ties, lifting the track; a worker points at it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(80, 2.3, 34, 140)
    ground(M, 'dirt', grass=True, gx=3.2)
    bl = ballast(M, -6, 60); st = stone_patch(M, -2, 9, 20000)
    for o in (bl, st): key(o, 'location', [(0, Vector((0, 0, -0.42))), (0.4, Vector((0, 0, -0.42))), (3.2, Vector((0, 0, 0)))])
    T = ties(M, -6, 60, TB); R = rails(M, -6, 60, TB + TH_)
    for o in T + R:
        p0 = o.location.copy()
        key(o, 'location', [(0, p0 - Vector((0, 0, TB))), (1.0, p0 - Vector((0, 0, TB))), (3.4, p0)])
    arm = worker('Worker', (-2.6, 6.0, 0), 75, M)
    pose(arm, 0.8, STANCES['relax']); pose(arm, 1.8, STANCES['point_r'])
    camera([(0, (2.5, 0.6, 0.85), (-0.2, 6.5, 0.15)), (d, (2.3, 1.2, 0.8), (-0.2, 7.0, 0.15))], lens=24, fstop=5.6)

def S04(a, b):  # studio cut-away: a block of ballast under one tie; water poured on top drains straight down through the stones
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.3, 0, 'studio'); studio_lights(420, 320, 1.4)
    plane('Floor', 30, 30, (0, 0, -0.33), M['studio'])
    random.seed(4); bm = bmesh.new()
    for i in range(2600):
        r = random.uniform(0.022, 0.04)
        x = random.uniform(-0.62, 0.62); y = random.uniform(-0.22, 0.22); z = random.uniform(-0.3, 0.05)
        mtx = Matrix.Translation((x, y, z)) @ Euler((random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3))).to_matrix().to_4x4() \
            @ Matrix.Diagonal((random.uniform(0.75, 1.3), random.uniform(0.75, 1.3), random.uniform(0.6, 1.0), 1))
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=mtx)
    me = bpy.data.meshes.new('Block'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('Block', me); link(o); o.data.materials.append(M['stone'])
    t = box('Tie', (1.4, TW, TH_), (0, 0, 0.05 + TH_ / 2 - 0.02), M['tie'], bevel=0.008, segs=2)
    wm = mat_simple('WaterBlue', (0.25, 0.55, 0.8), 0.06, trans=0.85, ior=1.33)[0]
    w = box('WaterBody', (1.22, 0.42, 0.34), (0, 0, -0.12), wm)
    w.data.transform(Matrix.Translation((0, 0, 0.17)))  # origin at the bottom
    w.location = (0, 0, -0.31)
    key(w, 'scale', [(0, Vector((1, 1, 1.0))), (0.4, Vector((1, 1, 1.0))), (d - 0.4, Vector((1, 1, 0.03)))])
    drip = box('Drain', (1.6, 0.6, 0.004), (0, 0, -0.327), mat_glass('Puddle', (0.6, 0.75, 0.85), 0.05)[0])
    key(drip, 'scale', [(0, Vector((0.3, 0.3, 1))), (d, Vector((1.4, 1.6, 1)))])
    camera([(0, (0.55, -1.9, 0.62), (0.0, 0, 0.12)), (d, (0.35, -1.75, 0.56), (0.0, 0, 0.12))], lens=32, fstop=5.6)

def S05(a, b):  # from above the track: with every passing train the two rails slowly creep apart on the bare ties
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(100, 2.3, 40, 160)
    T, P, R = full_track(M, -6, 60, plates_on=False)
    for s, r in zip((-1, 1), R): rel(r, [(0, (0, 0, 0)), (0.6, (0, 0, 0)), (d - 0.3, (s * 0.07, 0, 0))])
    arm = worker('Worker', (-2.5, 4.6, 0), 95, M)
    pose(arm, 0.4, STANCES['relax']); pose(arm, 1.4, STANCES['point_r'])
    camera([(0, (0.25, -0.6, 2.0), (0, 3.6, 0.4)), (d, (0.2, -0.3, 1.9), (0, 3.9, 0.4))], lens=28)

def S06(a, b):  # close on a tie plate: two spikes are driven down; the camera rises to show both rails at gauge
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(120, 2.4, 42, 170)
    T, P, R = full_track(M, -6, 60)
    t1 = min(T, key=lambda t: abs(t.location.y - 1.0))
    heads = [o for o in P if o.name.startswith('SpikeHead') and abs(o.location.y - t1.location.y) < 0.1 and o.location.x > 0]
    for k, h in enumerate(heads[:2]):
        p0 = h.location.copy(); tt = (0.62, 1.42)[k]
        key(h, 'location', [(0, p0 + Vector((0, 0, 0.08))), (tt - 0.05, p0 + Vector((0, 0, 0.08))), (tt, p0)], interp='LINEAR')
    arm = worker('Worker', (2.6, 3.2, 0), -125, M, stance='relax')
    pose(arm, 0.0, STANCES['work_low'])
    camera([(0, (1.05, 0.15, 0.72), (RX, t1.location.y, 0.42)), (1.8, (1.0, 0.0, 0.8), (RX, t1.location.y + 0.1, 0.42)),
            (d, (0.35, -1.6, 1.55), (0, 2.6, 0.4))], lens=34, fstop=3.2)

def S07(a, b):  # hot summer sun: the welded track suddenly bends sideways into a sun kink; a worker looks at it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 1.0, math.radians(140)); sun(3.4, 58, 160, color=(1, 0.9, 0.76))
    YC = 15.0
    def kink(y): return 0.42 * (math.exp(-((y - YC) / 3.2) ** 2) - 0.55 * math.exp(-((y - YC - 6) / 3.2) ** 2) - 0.55 * math.exp(-((y - YC + 6) / 3.2) ** 2))
    ground(M, 'dirt', grass=True, gx=3.2); ballast(M, -6, 90); stone_patch(M, -3, 9, 22000)
    T = ties(M, -6, 90, TB); P = plates(M, T)
    R = rails(M, -6, 90, TB + TH_ + PL, seg=480, kink=kink)
    for r in R:
        kb = r.data.shape_keys.key_blocks['kink']
        for t, v in ((0, 0.0), (1.4, 0.0), (2.6, 0.85), (d, 1.0)):
            kb.value = v; kb.keyframe_insert('value', frame=F(t))
    for o in T + P:
        y = o.location.y; dx = kink(y)
        if abs(dx) > 0.003:
            p0 = o.location.copy()
            key(o, 'location', [(0, p0), (1.4, p0), (2.6, p0 + Vector((dx * 0.85, 0, 0))), (d, p0 + Vector((dx, 0, 0)))])
    arm = worker('Worker', (2.5, 8.5, 0), -154, M)
    camera([(0, (-1.0, -2.0, 1.25), (0.1, 16, 0.35)), (d, (-0.9, -1.4, 1.2), (0.1, 16, 0.35))], lens=34)

def S08(a, b):  # close at an old bolted rail joint with a small gap: the freight car's wheels clack over it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(150, 2.3, 30, 200)
    ground(M, 'dirt', grass=True, gx=3.2); ballast(M, -10, 80); stone_patch(M, -4, 8, 22000)
    T = ties(M, -10, 80, TB); P = plates(M, T)
    z0 = TB + TH_ + PL; JY = 3.0
    for s in (-1, 1):
        rail(M, s * RX, -10, JY - 0.006, z0); rail(M, s * RX, JY + 0.006, 80, z0)
        for side in (-1, 1):
            jb = box('JointBar', (0.022, 0.62, 0.085), (s * RX + side * 0.024, JY, z0 + 0.095), M['plate'], bevel=0.004, segs=1)
            for k in (-0.23, -0.08, 0.08, 0.23):
                cyl('Bolt', 0.014, 0.1, (s * RX + side * 0.04, JY + k, z0 + 0.095), M['plate'], rot=(0, math.radians(90), 0), verts=6)
    car, W = railcar(M, z0 + RH)
    # first wheelset of the near truck reaches the joint at 2.6 s, the second at 2.9 s (6 m/s)
    lead0 = car.location.y  # 0
    front = min(w.location.y for w in W)
    v = 1.8 / 0.3; y_at = lambda t: (JY - front) + v * (2.6 - t)
    roll(car, W, [(0, y_at(0)), (d, y_at(d))])
    camera([(0, (1.75, -0.6, 0.72), (RX, JY, 0.62)), (d, (1.75, -0.4, 0.72), (RX, JY, 0.62))], lens=40, fstop=3.5)

def S09(a, b):  # low by a new thermite weld glowing orange in one long ribbon of rail that runs to the horizon
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(200, 2.2, 26, 220, (1, 0.93, 0.84))
    T, P, R = full_track(M, -6, 420)
    z0 = TB + TH_ + PL; WY = 2.6
    em, ee = mat_emit('WeldGlow', (1, 0.42, 0.08), 22)
    wd = box('Weld', (0.17, 0.09, RH + 0.03), (RX, WY, z0 + RH / 2), em, bevel=0.01, segs=2)
    key_socket(ee.inputs['Strength'], [(0, 26), (d, 7)])
    pl = light('POINT', (RX, WY - 0.15, z0 + 0.25), 60, (1, 0.45, 0.12), 0.08)
    key_light(pl.data, 'energy', [(0, 70), (d, 18)])
    arm = worker('Welder', (2.2, 4.0, 0), -125, M)
    camera([(0, (1.35, 0.3, 0.78), (RX - 0.1, 7.0, 0.5)), (d, (1.3, 0.9, 0.74), (RX - 0.1, 7.6, 0.5))], lens=24, fstop=4.0)

def S10(a, b):  # a yellow hydraulic rail puller clamps the rail and stretches it to close the gap; a worker points at it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(230, 2.5, 44, 230, (1, 0.92, 0.8))
    ground(M, 'dirt', grass=True, gx=3.2); ballast(M, -6, 80); stone_patch(M, -3, 9, 22000)
    T = ties(M, -6, 80, TB); P = plates(M, T)
    z0 = TB + TH_ + PL; GY = 3.0
    rail(M, -RX, -6, 80, z0)
    rail(M, RX, -6, GY - 0.02, z0)
    rb = rail(M, RX, GY + 0.02, 80, z0)
    rel(rb, [(0, (0, 0.03, 0)), (0.6, (0, 0.03, 0)), (d - 0.6, (0, -0.017, 0))])
    U = []
    for cy in (GY - 0.75, GY + 0.75):
        c = box('Clamp', (0.42, 0.32, 0.36), (RX, cy, z0 + 0.2), M['yellow'], bevel=0.02, segs=2); U.append(c)
    for s in (-1, 1):
        cyl('RamBody', 0.06, 0.9, (RX + s * 0.27, GY - 0.25, z0 + 0.26), M['yellow'], rot=(math.radians(90), 0, 0), verts=24)
        cyl('RamRod', 0.035, 0.7, (RX + s * 0.27, GY + 0.45, z0 + 0.26), M['chrome'], rot=(math.radians(90), 0, 0), verts=20)
    key(U[1], 'location', [(0, U[1].location + Vector((0, 0.03, 0))), (0.6, U[1].location + Vector((0, 0.03, 0))), (d - 0.6, U[1].location - Vector((0, 0.017, 0)))])
    arm = worker('Worker', (2.1, 4.6, 0), -140, M)
    pose(arm, 0.3, STANCES['relax']); pose(arm, 1.3, STANCES['point_r'])
    camera([(0, (1.85, 0.5, 1.05), (RX, GY + 0.3, 0.45)), (d, (1.7, 0.8, 1.0), (RX, GY + 0.3, 0.45))], lens=30, fstop=4.0)

def S11(a, b):  # dusk: the finished track; a locomotive comes on with its headlights blazing, a worker stands beside it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(190)); sun(1.0, 4, 190, color=(1, 0.66, 0.42))
    T, P, R = full_track(M, -8, 420, stones=(-3, 8, 20000))
    z0 = TB + TH_ + PL + RH
    lo, W = railcar(M, z0, loco=True, length=20.0)
    roll(lo, W, [(0, 85.0), (d, 42.0)])
    arm = worker('Worker', (3.3, 7.5, 0), 175, M)
    camera([(0, (-2.4, -1.5, 0.75), (0.3, 40, 2.2)), (d, (-2.3, -0.9, 0.72), (0.3, 40, 2.2))], lens=30)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11]

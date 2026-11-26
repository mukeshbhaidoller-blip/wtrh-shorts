# Shots for "That Tiny Hole in Your Plane Window Is On Purpose" (cabin pressure, 3-pane acrylic window, breather hole).
# Z up, metres. Cabin axis along Y (nose +Y), floor z=0. Person faces -Y at rot_z=0. t = seconds from the shot start.
from mathutils import Matrix, Euler

def dur(a, b): return (b - a) / FPS

ZF = 3.2          # fuselage axis height
RF = 1.9          # fuselage radius
WR = 1.7          # wing root |x|
WS = 15.3         # wing half-span beyond the root
WZ = 2.0          # wing root height
WLE = 3.0         # root leading edge y
WSW = 7.0         # sweep: tip LE is this much further back
RC, TC = 6.0, 1.6 # root / tip chord
WDZ = 1.6         # dihedral rise at the tip
NIGHT = 'dikhololo_night'

def _yt(c, t): return 5 * t * (0.2969 * math.sqrt(max(c, 0)) - 0.126 * c - 0.3516 * c ** 2 + 0.2843 * c ** 3 - 0.1036 * c ** 4)

def _yc(c, m=0.022, p=0.4): return m / p ** 2 * (2 * p * c - c * c) if c < p else m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * c - c * c)

def wing_up(s, c, side=-1):
    """World point on the upper surface at span fraction s (0 root..1 tip) and chord fraction c (0 LE..1 TE)."""
    ch = RC + (TC - RC) * s; th = 0.13 - 0.03 * s
    x = side * (WR + WS * s); y = WLE - WSW * s - c * ch
    z = WZ + WDZ * s + ch * (_yc(c) + _yt(c, th))
    return Vector((x, y, z))

def wing_mesh(name, mat, side=-1, root=(WR, WLE, WZ), span=WS, sweep=WSW, rc=RC, tc=TC, dz=WDZ, vertical=False, th0=0.13, th1=0.10, N=22, M=14):
    cs = [0.5 * (1 - math.cos(math.pi * i / (N - 1))) for i in range(N)]
    verts, faces = [], []
    ring = None
    for j in range(M):
        s = j / (M - 1); ch = rc + (tc - rc) * s; th = th0 + (th1 - th0) * s
        yle = root[1] - sweep * s
        pts = []
        for c in reversed(cs): pts.append((c, _yc(c) + _yt(c, th)))
        for c in cs[1:-1]: pts.append((c, _yc(c) - _yt(c, th)))
        base = len(verts)
        for c, h in pts:
            if vertical:   # fin: span goes up (+Z), thickness along X
                verts.append((h * ch * 0.8, yle - c * ch, root[2] + span * s))
            else:
                verts.append((side * (root[0] + span * s), yle - c * ch, root[2] + dz * s + h * ch))
        n = len(pts)
        if ring is not None:
            for k in range(n):
                a0, a1 = ring + k, ring + (k + 1) % n; b0, b1 = base + k, base + (k + 1) % n
                faces.append((a0, a1, b1, b0) if side < 0 or vertical else (a0, b0, b1, a1))
        else:
            faces.append(tuple(range(base, base + n)))
        ring = base
    faces.append(tuple(range(ring, ring + n)))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.validate()
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(me); _bm.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o)
    for pg in me.polygons: pg.use_smooth = True
    if mat: me.materials.append(mat)
    bpy.context.view_layer.objects.active = o
    return o

def paint_mat(name, col, rough=0.32, metal=0.1, coat=0.35):
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 5
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * 0.88 for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if coat: inp(p, 'Coat Weight', 'Clearcoat').default_value = coat
    return m

def mats():
    M = {}
    M['white'] = paint_mat('JetWhite', (0.86, 0.87, 0.88), 0.28, 0.05, 0.5)
    M['blue'] = paint_mat('JetBlue', (0.03, 0.09, 0.28), 0.3, 0.1, 0.5)
    M['grey'] = paint_mat('JetGrey', (0.55, 0.57, 0.6), 0.35, 0.3, 0.3)
    M['dark'] = mat_simple('Dark', (0.03, 0.03, 0.035), 0.45, 0.3)[0]
    M['glass'] = mat_simple('CockpitGlass', (0.01, 0.012, 0.015), 0.05, 0.6, coat=1.0)[0]
    M['chrome'] = mat_simple('Chrome', (0.85, 0.85, 0.87), 0.1, 1.0)[0]
    M['rubber'] = mat_simple('Tire', (0.025, 0.025, 0.027), 0.75)[0]
    M['alu'] = mat_simple('Alu', (0.72, 0.73, 0.75), 0.3, 1.0)[0]
    M['yellow'] = paint_mat('TruckYellow', (0.86, 0.6, 0.04), 0.4, 0.1, 0.2)
    M['steel'] = mat_simple('Steel', (0.4, 0.4, 0.42), 0.35, 1.0)[0]
    M['winlit'] = mat_emit('CabinLight', (1.0, 0.86, 0.62), 3.0)[0]
    M['red'] = mat_emit('NavRed', (1, 0.05, 0.03), 20)[0]
    M['grn'] = mat_emit('NavGreen', (0.1, 1, 0.2), 20)[0]
    return M

def jet(M, wing_m, lit=True, fuselage=True, beacon=True):
    """Generic twin-jet airliner (no brand). Returns its root empty (origin on the ground under the wing root)."""
    root = bpy.data.objects.new('Jet', None); link(root)
    objs = []
    if fuselage:
        f = cyl('Fuselage', RF, 30, (0, -1, ZF), M['white'], rot=(math.radians(90), 0, 0), verts=96)
        objs.append(f)
        nose = sphere('Nose', 1, (0, 14, ZF), M['white'], sub=5); nose.scale = (RF, 3.2, RF * 0.96); objs.append(nose)
        bpy.ops.mesh.primitive_cone_add(radius1=RF, radius2=0.35, depth=8, vertices=96, location=(0, -20, ZF + 0.9), rotation=(math.radians(-90 - 6.5), 0, 0))
        tail = bpy.context.active_object; tail.name = 'TailCone'; bpy.ops.object.shade_smooth(); tail.data.materials.append(M['white']); objs.append(tail)
        belly = cyl('Belly', RF * 1.003, 30, (0, -1, ZF), M['blue'], rot=(math.radians(90), 0, 0), verts=96)
        cut = box('BellyCut', (6, 40, 6), (0, -1, ZF + 3 - 0.9), None); cut.hide_render = True; cut.display_type = 'WIRE'
        bo = belly.modifiers.new('c', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cut; objs += [belly, cut]
        # cockpit windows
        for k, (xx, ang) in enumerate(((-0.5, 14), (0.5, -14), (-1.15, 42), (1.15, -42))):
            yy = 14 + 3.2 * math.sqrt(max(0.01, 1 - (xx / RF) ** 2 - (0.85 / (RF * 0.96)) ** 2)) - 0.03
            w = box('CockpitWin', (0.55, 0.07, 0.34), (xx, yy, ZF + 0.85), M['glass'], bevel=0.04, rot=(math.radians(-48), 0, math.radians(ang)))
            objs.append(w)
        # cabin windows
        wm = M['winlit'] if lit else M['dark']
        y = 11.0
        while y > -14.5:
            for s in (-1, 1):
                objs.append(box('Win', (0.06, 0.24, 0.34), (s * (RF * 0.985), y, ZF + 0.45), wm, bevel=0.05, rot=(0, math.radians(s * -14), 0)))
            y -= 0.54
        for s in (-1, 1):   # doors
            objs.append(box('Door', (0.02, 0.95, 1.9), (s * RF * 0.99, 12.0, ZF - 0.05), M['dark'], rot=(0, 0, 0)))
        # vertical fin + stabilisers
        objs.append(wing_mesh('Fin', M['white'], root=(0, -16.0, ZF + 1.4), span=6.6, sweep=5.0, rc=5.5, tc=2.0, vertical=True, th0=0.10, th1=0.09))
        for s in (-1, 1):
            objs.append(wing_mesh('Stab', M['grey'], side=s, root=(0.4, -16.8, ZF + 0.9), span=6.0, sweep=3.6, rc=3.6, tc=1.3, dz=0.5, th0=0.10, th1=0.09))
    # wings
    for s in (-1, 1):
        objs.append(wing_mesh('Wing', wing_m, side=s))
        tip = wing_up(1.0, 0.1, s); objs.append(sphere('NavLight', 0.09, (tip.x + s * 0.02, tip.y, tip.z - 0.05), M['red'] if s < 0 else M['grn'], sub=2))
        # engine
        ex = s * 5.6; ey = 2.6; ez = 1.15
        nac = cyl('Nacelle', 0.92, 3.6, (ex, ey, ez), M['white'], rot=(math.radians(90), 0, 0), verts=72, bevel=0.12)
        lip = cyl('Lip', 0.95, 0.25, (ex, ey + 1.8, ez), M['alu'], rot=(math.radians(90), 0, 0), verts=72, bevel=0.08)
        fan = cyl('Fan', 0.78, 0.1, (ex, ey + 1.6, ez), M['dark'], rot=(math.radians(90), 0, 0), verts=48)
        spin = sphere('Spinner', 0.22, (ex, ey + 1.7, ez), M['chrome'], sub=3)
        noz = cyl('Nozzle', 0.55, 1.2, (ex, ey - 2.3, ez), M['grey'], rot=(math.radians(90), 0, 0), verts=48)
        pyl = box('Pylon', (0.3, 3.2, 1.0), (ex, ey - 0.6, ez + 0.9), M['white'], bevel=0.08)
        objs += [nac, lip, fan, spin, noz, pyl]
        # main gear
        gx = s * 2.9
        objs.append(cyl('Strut', 0.12, 2.0, (gx, -0.6, 1.5), M['chrome'], verts=24))
        for dx in (-0.3, 0.3):
            objs.append(cyl('MainTire', 0.56, 0.36, (gx + dx, -0.6, 0.56), M['rubber'], rot=(0, math.radians(90), 0), verts=64, bevel=0.08))
            objs.append(cyl('Hub', 0.32, 0.38, (gx + dx, -0.6, 0.56), M['alu'], rot=(0, math.radians(90), 0), verts=48))
        objs.append(cyl('Axle', 0.08, 0.9, (gx, -0.6, 0.56), M['steel'], rot=(0, math.radians(90), 0), verts=16))
    # nose gear
    if fuselage:
        objs.append(cyl('NoseStrut', 0.08, 1.6, (0, 12.0, 0.95), M['chrome'], verts=24))
        for s in (-1, 1): objs.append(cyl('NoseTire', 0.36, 0.22, (s * 0.16, 12.0, 0.36), M['rubber'], rot=(0, math.radians(90), 0), verts=48, bevel=0.05))
        if beacon:
            bm, bp = mat_simple('Beacon', (0.5, 0.02, 0.01), 0.3, emit=(1, 0.04, 0.02), estr=0.0)
            objs.append(sphere('BeaconTop', 0.12, (0, 2.0, ZF + RF), bm, sub=2))
            objs.append(sphere('BeaconBot', 0.12, (0, 2.0, ZF - RF), bm, sub=2))
            pts = []
            for k in range(14): pts += [(k * 1.0, 0.0), (k * 1.0 + 0.08, 40.0), (k * 1.0 + 0.2, 0.0)]
            key_socket(inp(bp, 'Emission Strength'), pts, 'CONSTANT')
    for o in objs:
        if o.parent is None: o.parent = root
    return root

def flood(loc, target, energy=9000, col=(1.0, 0.88, 0.72), spot=55, pole=True):
    s = light('SPOT', loc, energy * 1.4, col, 0.4, spot=spot, blend=0.6); aim(s, target)
    try: s.visible_glossy = True
    except Exception: pass
    if pole:
        pm, _ = mat_simple('Pole', (0.25, 0.25, 0.27), 0.5, 0.6)
        cyl('Pole', 0.18, loc[2], (loc[0], loc[1], loc[2] / 2), pm, verts=16)
        lm, _ = mat_emit('Lamp', (1.0, 0.9, 0.75), 60)
        box('Lamp', (1.4, 0.5, 0.25), (loc[0], loc[1], loc[2] + 0.1), lm)
    return s

def far_lights(y=120, n=40, seed=9, x0=-200, x1=200, z=(2, 10)):
    """Distant terminal + apron lights (bokeh in the background)."""
    random.seed(seed)
    lm, _ = mat_emit('FarLamp', (1.0, 0.82, 0.55), 25)
    bm, _ = mat_emit('FarBlue', (0.3, 0.5, 1.0), 25)
    for i in range(n):
        sphere('FarLight', random.uniform(0.25, 0.5), (random.uniform(x0, x1), y + random.uniform(-8, 8), random.uniform(*z)), lm if random.random() > 0.15 else bm, sub=1)
    tm = mat_simple('Terminal', (0.05, 0.055, 0.06), 0.6)[0]
    box('Terminal', (220, 30, 14), (0, y + (25 if y > 0 else -25), 7), tm)
    wm, _ = mat_emit('TermWin', (1.0, 0.85, 0.6), 2.5)
    s_ = 1 if y > 0 else -1
    for k in range(2):
        for i in range(30):
            if random.random() < 0.55: box('TermWin', (random.uniform(2, 5), 0.2, 1.1), (-100 + i * 7 + random.uniform(-1, 1), y + s_ * 9.9, 3.5 + k * 4.0), wm)

# ================================================================ window + cabin kit
WW, WH, WRR = 0.265, 0.375, 0.105      # structural pane (outer / middle) size
HOLE_Z = -0.155                        # breather hole: bottom of the middle pane (local z)
HOLE_R = 0.0042
R_IN, R_OUT = 2.76, 2.96               # wide-body cabin lining inner radius / skin outer radius
AXZ = 1.05                             # cabin axis height above the floor
WZC = 1.10                             # window centre height
WIN_YS = [round(0.53 * k, 3) for k in range(-6, 7)]
ROWS = [-2.6, -1.8, 0.95, 1.75, 2.55]  # seat rows (gap around y=0 = roomy exit row)

def wmats():
    M = {}
    M['acryl'] = mat_glass('Acrylic', (0.95, 0.97, 1.0), 0.0)[0]
    M['scratch'] = mat_glass('ScratchPane', (0.96, 0.97, 0.98), 0.025)[0]
    M['lining'] = mat_simple('Lining', (0.80, 0.79, 0.76), 0.5)[0]
    M['sleeve'] = mat_simple('Sleeve', (0.86, 0.85, 0.82), 0.42)[0]
    M['insul'] = mat_simple('Insulation', (0.78, 0.62, 0.30), 0.95, sss=0.1)[0]
    M['skin'] = paint_mat('Skin', (0.88, 0.89, 0.90), 0.28, 0.05, 0.5)
    M['alu'] = mat_simple('Alu', (0.72, 0.73, 0.75), 0.28, 1.0)[0]
    M['alu_rough'] = mat_simple('AluRough', (0.62, 0.63, 0.65), 0.45, 1.0)[0]
    M['rubber'] = mat_simple('Seal', (0.02, 0.02, 0.022), 0.6)[0]
    M['fabric'] = mat_simple('Fabric', (0.045, 0.06, 0.12), 0.92, sss=0.02)[0]
    M['headrest'] = mat_simple('Headrest', (0.75, 0.75, 0.74), 0.9)[0]
    M['plastic'] = mat_simple('SeatPlastic', (0.32, 0.33, 0.35), 0.45)[0]
    M['carpet'] = mat_simple('Carpet', (0.05, 0.06, 0.09), 0.97)[0]
    M['bin'] = mat_simple('Bin', (0.86, 0.86, 0.84), 0.4, coat=0.2)[0]
    M['cove'] = mat_emit('Cove', (1.0, 0.92, 0.80), 6.0)[0]
    M['studio'] = mat_simple('StudioFloor', (0.045, 0.045, 0.05), 0.55)[0]
    M['dark'] = mat_simple('HoleRim', (0.08, 0.085, 0.09), 0.35)[0]
    return M

def mesh_obj(name, verts, faces, mat=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.validate()
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(me); _bm.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o)
    if mat: me.materials.append(mat)
    return o

def rr_pts(w, h, r, n=12):
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4); pts = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-(w / 2 - r), h / 2 - r, 90), (-(w / 2 - r), -(h / 2 - r), 180), (w / 2 - r, -(h / 2 - r), 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts

def rr_prism(name, w, h, r, depth, loc=(0, 0, 0), mat=None, n=12, bevel=0.0):
    """Rounded-rectangle slab in the XZ plane, thickness along local Y."""
    P = rr_pts(w, h, r, n); N = len(P)
    verts = [(u, -depth / 2, v) for u, v in P] + [(u, depth / 2, v) for u, v in P]
    faces = [tuple(range(N)), tuple(range(2 * N - 1, N - 1, -1))] + [(i, (i + 1) % N, N + (i + 1) % N, N + i) for i in range(N)]
    o = mesh_obj(name, verts, faces, mat); o.location = loc
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    return o

def rr_ring(name, w, h, r, wi, hi, ri, depth, loc=(0, 0, 0), mat=None, n=12):
    """Rounded-rectangle frame (outer w,h,r minus inner wi,hi,ri), thickness along local Y."""
    Po = rr_pts(w, h, r, n); Pi = rr_pts(wi, hi, ri, n); N = len(Po)
    verts = [(u, -depth / 2, v) for u, v in Po] + [(u, depth / 2, v) for u, v in Po] + \
            [(u, -depth / 2, v) for u, v in Pi] + [(u, depth / 2, v) for u, v in Pi]
    F = []
    for i in range(N):
        j = (i + 1) % N
        F.append((i, j, N + j, N + i))                    # outer wall
        F.append((2 * N + i, 3 * N + i, 3 * N + j, 2 * N + j))  # inner wall
        F.append((i, 2 * N + i, 2 * N + j, j))            # front face
        F.append((N + i, N + j, 3 * N + j, 3 * N + i))    # back face
    return mesh_obj(name, verts, F, mat) if not loc else _at(mesh_obj(name, verts, F, mat), loc)

def _at(o, loc): o.location = loc; return o

def rim(name, w, h, r, mat, bev=0.0018, n=14):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); P = rr_pts(w, h, r, n); sp.points.add(len(P) - 1)
    for i, (u, v) in enumerate(P): sp.points[i].co = (u, 0, v, 1)
    sp.use_cyclic_u = True; cu.bevel_depth = bev; cu.bevel_resolution = 3
    o = bpy.data.objects.new(name, cu); link(o); cu.materials.append(mat)
    return o

def glow_mat(name, col, strength=0.0):
    m, p = mat_simple(name, (0.04, 0.04, 0.045), 0.4, emit=col, estr=strength)
    return m, inp(p, 'Emission Strength')

def child(o, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    o.parent = parent; o.location = loc; o.rotation_euler = rot; return o

def boolean(o, cutter, op='DIFFERENCE'):
    b = o.modifiers.new('b', 'BOOLEAN'); b.operation = op
    if isinstance(cutter, bpy.types.Collection): b.operand_type = 'COLLECTION'; b.collection = cutter
    else: b.object = cutter
    return b

def cutter_obj(o, col=None):
    o.hide_render = True; o.display_type = 'WIRE'
    if col is not None:
        for c in list(o.users_collection): c.objects.unlink(o)
        col.objects.link(o)
    return o

def hole_cutter(parent, y_local):
    c = cyl('HoleCut', HOLE_R, 0.05, (0, 0, 0), None, rot=(math.radians(90), 0, 0), verts=32)
    child(c, parent, (0, 0, HOLE_Z), (math.radians(90), 0, 0)); return cutter_obj(c)

def hole_ring(parent, M, y_off=0.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=HOLE_R + 0.0006, minor_radius=0.0009, major_segments=40, minor_segments=10)
    t = bpy.context.active_object; t.name = 'HoleRing'; t.data.materials.append(M['dark'])
    return child(t, parent, (0, y_off, HOLE_Z), (math.radians(90), 0, 0))

def arrow(name, p0, p1, r, mat):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length; hl = min(L * 0.38, r * 6)
    root = bpy.data.objects.new(name, None); link(root); root.location = p0
    root.rotation_euler = d.normalized().to_track_quat('Z', 'Y').to_euler()
    sh = cyl(name + 'S', r, L - hl, (0, 0, 0), mat, verts=24); child(sh, root, (0, 0, (L - hl) / 2))
    bpy.ops.mesh.primitive_cone_add(radius1=r * 2.5, radius2=0, depth=hl, vertices=32)
    c = bpy.context.active_object; c.data.materials.append(mat); child(c, root, (0, 0, L - hl / 2))
    return root

def pop_in(o, t0, dt=0.25, s=1.0):
    key(o, 'scale', [(t0 - 0.01, Vector((0.001, 0.001, 0.001))), (t0 + dt, Vector((s * 1.08,) * 3)), (t0 + dt + 0.12, Vector((s,) * 3))])

def particles(n, path_fn, t0, t1, life, r, mat, seed=1):
    """path_fn(rnd) -> list of points; each particle travels the path once in `life` seconds."""
    random.seed(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=1); proto = bpy.context.active_object
    proto.data.materials.append(mat); proto.location = (0, 0, -500); proto.scale = (r, r, r)
    for i in range(n):
        tb = t0 + (t1 - t0 - life) * i / max(1, n - 1) + random.uniform(-0.05, 0.05)
        pts = [Vector(p) for p in path_fn(random)]
        o = dup(proto, pts[0]); k = r * random.uniform(0.7, 1.2)
        key(o, 'scale', [(tb - 0.02, Vector((1e-4,) * 3)), (tb + 0.08, Vector((k,) * 3)), (tb + life - 0.12, Vector((k,) * 3)), (tb + life, Vector((1e-4,) * 3))])
        m = len(pts) - 1
        key(o, 'location', [(tb + life * q / m, pts[q]) for q in range(m + 1)], interp='LINEAR')

def cloud_deck(z=-450, size=9000, move=0.0, d=1.0):
    m = bpy.data.materials.new('Clouds'); m.use_nodes = True; nt = m.node_tree
    p = nt.nodes['Principled BSDF']; tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.0035; nz.inputs['Detail'].default_value = 12; nz.inputs['Roughness'].default_value = 0.62
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); e0, e1 = ramp.color_ramp.elements
    e0.position = 0.40; e0.color = (0.2, 0.3, 0.46, 1); e1.position = 0.52; e1.color = (0.95, 0.96, 0.98, 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 1.0
    sp_ = inp(p, 'Specular IOR Level', 'Specular')
    if sp_: sp_.default_value = 0.0
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 40
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    o = plane('CloudDeck', size, size, (0, 0, z), m)
    if move: key(o, 'location', [(0, Vector((0, 0, z))), (d, Vector((0, -move * d, z)))], interp='LINEAR')
    return o

def studio(strength=0.55, rot=0.0, floor_z=-0.6):
    world_hdri('studio_small_09', strength, rot, 'studio')
    M = wmats(); plane('Floor', 40, 40, (0, 0, floor_z), M['studio'])
    return M

# ---------------------------------------------------------------- the exploded window (studio, panes in XZ, outside = +Y)
def stack(M, sep=((0, 0.0),), cut=False, skin=True, rims=('outer', 'middle', 'inner')):
    """Outer + middle (with breather hole) + inner scratch pane. sep 0 = assembled, 1 = exploded. Returns dict."""
    O = {}
    def ys(s): return (0.030 - 0.02 * s, -0.14 * s, -0.060 - 0.24 * s)
    cutbox = None
    if cut:
        cutbox = cutter_obj(box('SectionCut', (1.0, 1.0, 1.2), (0.5, 0, 0), None))
    outer = rr_prism('OuterPane', WW, WH, WRR, 0.012, (0, 0.03, 0), M['acryl'], n=16, bevel=0.0015)
    middle = rr_prism('MiddlePane', WW, WH, WRR, 0.006, (0, 0, 0), M['acryl'], n=16, bevel=0.001)
    inner = rr_prism('InnerPane', WW + 0.05, WH + 0.06, WRR + 0.03, 0.003, (0, -0.06, 0), M['scratch'], n=16)
    boolean(middle, hole_cutter(middle, 0)); hole_ring(middle, M)
    seal = rr_ring('Seal', WW + 0.008, WH + 0.008, WRR + 0.004, WW - 0.004, WH - 0.004, WRR - 0.002, 0.006, (0, 0.0, 0), M['rubber'], n=16)
    child(seal, outer, (0, 0.009, 0))
    if cut: seal.hide_render = True
    O.update(outer=outer, middle=middle, inner=inner, seal=seal)
    for nm, col in (('outer', (1.0, 0.42, 0.06)), ('middle', (0.15, 1.0, 0.35)), ('inner', (0.2, 0.75, 1.0))):
        gm, gs = glow_mat('Glow_' + nm, col, 0.0)
        O['glow_' + nm] = gs
        if nm not in rims: continue
        pane = O[nm]; w = WW + (0.05 if nm == 'inner' else 0); h = WH + (0.06 if nm == 'inner' else 0); rr = WRR + (0.03 if nm == 'inner' else 0)
        rm = rim('Rim_' + nm, w + 0.004, h + 0.004, rr + 0.002, gm, bev=0.0022); child(rm, pane)
    if skin:
        sk = box('SkinPanel', (0.9, 0.004, 1.05), (0, 0.045, 0), M['skin'])
        boolean(sk, cutter_obj(rr_prism('SkinCut', WW - 0.02, WH - 0.02, WRR - 0.01, 0.2, (0, 0.045, 0))))
        fr = rr_ring('Forging', WW + 0.09, WH + 0.09, WRR + 0.045, WW + 0.012, WH + 0.012, WRR + 0.006, 0.016, (0, 0.035, 0), M['alu'], n=16)
        O.update(skin=sk, forging=fr)
        for o in (sk, fr):
            if cut: boolean(o, cutbox)
    if cut:
        tm = mat_simple('AcrylSec', (0.80, 0.92, 1.0), 0.06, coat=0.5, trans=0.85, ior=1.49)[0]
        om, op = mat_simple('OuterGlow', (0.85, 0.92, 1.0), 0.06, coat=0.5, trans=0.85, ior=1.49, emit=(1.0, 0.42, 0.06), estr=0.0)
        O['glow_outer'] = inp(op, 'Emission Strength')
        for o in (outer, middle, inner):
            boolean(o, cutbox); o.data.materials.clear(); o.data.materials.append(om if o is outer else tm)
    ks = list(sep)
    for nm, idx in (('outer', 0), ('middle', 1), ('inner', 2)):
        key(O[nm], 'location', [(t, Vector((0, ys(s)[idx], 0))) for t, s in ks])
    return O

def crack(pane, t0, t1, mat, seed=3, start=(0.07, -0.12), n=9, w=0.0011, angs=(2.2, 1.3, 2.9)):
    """White crack lines spreading over a pane (local XZ, on its cabin-side face)."""
    random.seed(seed); segs = []
    def branch(p, ang, depth, tt):
        if depth <= 0: return
        L = random.uniform(0.025, 0.05); q = (p[0] + L * math.cos(ang), p[1] + L * math.sin(ang))
        segs.append((p, q, tt)); nt_ = tt + (t1 - t0) / n
        branch(q, ang + random.uniform(-0.6, 0.6), depth - 1, nt_)
        if random.random() < 0.45: branch(q, ang + random.choice((-1, 1)) * random.uniform(0.7, 1.2), depth - 2, nt_)
    for a0 in angs: branch(start, a0, 5, t0)
    for p, q, tt in segs:
        L = math.hypot(q[0] - p[0], q[1] - p[1]); ang = math.atan2(q[1] - p[1], q[0] - p[0])
        b = box('Crack', (L, 0.0006, w), (0, 0, 0), mat)
        child(b, pane, ((p[0] + q[0]) / 2, -0.0065, (p[1] + q[1]) / 2), (0, -ang, 0))
        key(b, 'scale', [(tt - 0.01, Vector((0.001, 1, 1))), (tt + 0.15, Vector((1, 1, 1)))])

# ---------------------------------------------------------------- the cabin (wide-body, 3-3-3)
def tube(name, r0, r1, y0, y1, mat, seg=160):
    verts = []
    for y in (y0, y1):
        for r in (r0, r1):
            for k in range(seg):
                a = 2 * math.pi * k / seg; verts.append((r * math.cos(a), y, r * math.sin(a)))
    def V(yi, ri, k): return yi * 2 * seg + ri * seg + (k % seg)
    F = []
    for k in range(seg):
        F.append((V(0, 0, k), V(0, 0, k + 1), V(1, 0, k + 1), V(1, 0, k)))   # inner
        F.append((V(0, 1, k), V(1, 1, k), V(1, 1, k + 1), V(0, 1, k + 1)))   # outer
        F.append((V(0, 0, k), V(0, 1, k), V(0, 1, k + 1), V(0, 0, k + 1)))   # end y0
        F.append((V(1, 0, k), V(1, 0, k + 1), V(1, 1, k + 1), V(1, 1, k)))   # end y1
    o = mesh_obj(name, verts, F, mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

def wall_x(r, side=-1): return side * math.sqrt(r * r - (WZC - AXZ) ** 2)

def seat(M, x, y):
    box('Cushion', (0.44, 0.47, 0.12), (x, y, 0.43), M['fabric'], bevel=0.035)
    box('Back', (0.44, 0.09, 0.74), (x, y - 0.27, 0.84), M['fabric'], bevel=0.035, rot=(math.radians(10), 0, 0))
    box('Headrest', (0.40, 0.095, 0.2), (x, y - 0.335, 1.08), M['headrest'], bevel=0.03, rot=(math.radians(10), 0, 0))
    box('Shell', (0.45, 0.04, 0.6), (x, y - 0.33, 0.75), M['plastic'], bevel=0.015, rot=(math.radians(10), 0, 0))
    for dx in (-0.235, 0.235):
        box('Arm', (0.05, 0.42, 0.06), (x + dx, y - 0.04, 0.64), M['plastic'], bevel=0.015)
    for dy in (-0.15, 0.15):
        cyl('Leg', 0.022, 0.38, (x, y + dy, 0.19), M['alu'], verts=12)

SEAT_X = (-2.22, -1.75, -1.28, -0.47, 0.0, 0.47, 1.28, 1.75, 2.22)

def cabin(M, y0=-3.3, y1=3.3, sides=(-1, 1), shell_root=None, skip_left_seats_rows=(), wins=None, lights=True):
    """Returns the root empty of the shell and a dict side -> list of window group empties."""
    root = bpy.data.objects.new('Shell', None); link(root); root.location = (0, 0, AXZ)
    colL = bpy.data.collections.new('CutLining'); bpy.context.scene.collection.children.link(colL)
    colS = bpy.data.collections.new('CutSkin'); bpy.context.scene.collection.children.link(colS)
    lin = tube('Lining', R_IN, R_IN + 0.03, y0, y1, M['lining'])
    ins = tube('Insulation', R_IN + 0.03, R_OUT - 0.045, y0, y1, M['insul'], seg=120)
    skn = tube('Skin', R_OUT - 0.04, R_OUT, y0, y1, M['skin'])
    boolean(lin, colL); boolean(ins, colL); boolean(skn, colS)
    G = {}
    for s in sides:
        G[s] = []
        for y in (wins if wins is not None else WIN_YS):
            if not (y0 + 0.3 < y < y1 - 0.3): continue
            g = bpy.data.objects.new('Win', None); link(g)
            g.location = (wall_x(R_IN, s), y, WZC); g.rotation_euler = (0, 0, math.radians(90 if s < 0 else -90))
            cutter_obj(child(rr_prism('CutL', 0.31, 0.43, 0.13, 0.6), g, (0, 0.12, 0)), colL)
            cutter_obj(child(rr_prism('CutS', WW - 0.02, WH - 0.02, WRR - 0.01, 0.6), g, (0, 0.3, 0)), colS)
            child(rr_ring('Sleeve', 0.31, 0.43, 0.13, WW + 0.004, WH + 0.006, WRR + 0.002, 0.165), g, (0, 0.10, 0)).data.materials.append(M['sleeve'])
            inner = child(rr_prism('InnerPane', 0.33, 0.45, 0.14, 0.003), g, (0, -0.004, 0)); inner.data.materials.append(M['scratch'])
            mid = child(rr_prism('MiddlePane', WW, WH, WRR, 0.006, bevel=0.001), g, (0, 0.10, 0)); mid.data.materials.append(M['acryl'])
            boolean(mid, hole_cutter(mid, 0)); hole_ring(mid, M)
            out = child(rr_prism('OuterPane', WW, WH, WRR, 0.012, bevel=0.0015), g, (0, 0.13, 0)); out.data.materials.append(M['acryl'])
            child(rr_ring('Seal', WW + 0.008, WH + 0.008, WRR + 0.004, WW - 0.006, WH - 0.006, WRR - 0.003, 0.05), g, (0, 0.115, 0)).data.materials.append(M['rubber'])
            g['mid'] = mid.name; g['inner'] = inner.name; g['outer'] = out.name
            G[s].append(g)
    for o in (lin, ins, skn): o.parent = root; o.location = (0, 0, 0)
    for s in sides:
        for g in G[s]:
            mw = g.matrix_world.copy(); g.parent = root; g.matrix_parent_inverse = root.matrix_world.inverted()
    # floor, cargo deck
    box('Floor', (5.3, y1 - y0, 0.08), (0, (y0 + y1) / 2, -0.04), M['carpet'])
    box('Beam', (5.4, y1 - y0, 0.25), (0, (y0 + y1) / 2, -0.2), M['alu_rough'])
    box('CargoDeck', (3.8, y1 - y0, 0.05), (0, (y0 + y1) / 2, -1.25), M['alu_rough'])
    # bins + ceiling
    L = y1 - y0 - 0.02; yc = (y0 + y1) / 2
    for s in (-1, 1):
        box('SideBin', (0.78, L, 0.42), (s * 2.18, yc, 2.12), M['bin'], bevel=0.05, rot=(0, math.radians(s * 12), 0))
        box('BinLight', (0.04, L, 0.02), (s * 1.78, yc, 1.88), M['cove'])
    box('CenterBin', (1.7, L, 0.38), (0, yc, 2.35), M['bin'], bevel=0.05)
    box('Ceiling', (4.4, L, 0.04), (0, yc, 2.75), M['lining'])
    for s in (-1, 1): box('CeilCove', (0.05, L, 0.02), (s * 0.95, yc, 2.56), M['cove'])
    for r in ROWS:
        if not (y0 + 0.5 < r < y1 - 0.2): continue
        for x in SEAT_X:
            if r in skip_left_seats_rows and x < -1: continue
            seat(M, x, r)
    if lights:
        for y in (y0 + 1.2, yc, y1 - 1.2):
            light('AREA', (0, y, 2.6), 220, (1.0, 0.95, 0.88), 2.4, rot=(0, 0, 0))
    return root, G

def sky_out(strength=1.0, rot=0.0, sun_on=True, deck=True, d=1.0, move=0.0):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', strength, rot, 'day')
    if sun_on: sun(2.4, 32, 250, (1.0, 0.95, 0.88), 1.5)
    if deck: cloud_deck(move=move, d=d)

def win_target(g, local=(0, 0.10, HOLE_Z)):
    return g.matrix_world @ Vector(local)

def win_at(G, side, y):
    return min(G[side], key=lambda g: abs(g.matrix_world.translation.y - y))

def update(): bpy.context.view_layer.update()

# ================================================================ shots
def S00(a, b):  # hook: macro push-in on the tiny hole at the bottom of a cabin window, clouds outside
    sc = new_scene(a, b); d = dur(a, b); M = wmats()
    sky_out(1.0, 0.4, d=d, move=60)
    root, G = cabin(M, -2.0, 2.0, sides=(-1,), wins=[0.0, 0.53, -0.53, 1.06, -1.06], lights=True)
    update(); g = win_at(G, -1, 0.0); h = win_target(g)
    c0 = Vector((-2.33, -0.16, 1.16)); c1 = Vector((-2.55, -0.06, 1.0))
    camera([(0, c0, h + Vector((0, 0, 0.05))), (d, c1, h + Vector((0, 0, 0.01)))], lens=40, fstop=2.8)
    sc.camera.data.dof.focus_object = None; sc.camera.data.dof.focus_distance = (c0 - h).length
    dof = sc.camera.data.dof
    for tt, cc in ((0, c0), (d, c1)): dof.focus_distance = (cc - h).length; dof.keyframe_insert('focus_distance', frame=F(tt))

def S01(a, b):  # outside: the jet cruising high above the clouds
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 1.0, 0.9, 'day'); sun(2.6, 30, 120, (1.0, 0.96, 0.9), 1.0)
    cloud_deck(-900, 80000, move=230, d=d)
    j = jet(M, paint_mat('WingGrey', (0.62, 0.64, 0.67), 0.35, 0.3, 0.3), lit=False, beacon=False)
    for o in j.children:
        if o.name.startswith(('MainTire', 'Hub', 'Axle', 'Strut', 'NoseStrut', 'NoseTire')): o.hide_render = True
    key(j, 'location', [(0, Vector((0, 0, 0))), (d * 0.5, Vector((0, 0, 0.12))), (d, Vector((0, 0, 0.02)))])
    c0 = Vector((-19.0, 21.0, ZF + 2.4)); c1 = Vector((-18.0, 18.0, ZF + 2.0))
    camera([(0, c0, Vector((-2.0, 3.0, ZF - 1.2))), (d, c1, Vector((-2.0, 1.8, ZF - 1.3)))], lens=42, fstop=11)
    sc.camera.data.clip_end = 120000

def S02(a, b):  # cut-away: the cabin is pumped full of air like a balloon; a passenger stands in the aisle
    sc = new_scene(a, b); d = dur(a, b)
    M = studio(0.6, 1.2, floor_z=AXZ - R_OUT - 0.4)
    root, G = cabin(M, -2.6, 2.6, sides=(-1, 1), lights=True)
    key(root, 'scale', [(0, Vector((1, 1, 1))), (0.4, Vector((1, 1, 1))), (d, Vector((1.022, 1, 1.022)))])
    light('AREA', (3.5, 7.5, 6), 900, (1, 0.97, 0.92), 6, rot=(math.radians(-55), 0, math.radians(150)))
    light('AREA', (-5, 5, 3), 400, (0.85, 0.9, 1.0), 5, rot=(math.radians(-70), 0, math.radians(-120)))
    am, _ = mat_simple('Air', (0.5, 0.8, 1.0), 0.3, emit=(0.45, 0.8, 1.0), estr=6.0)
    def path(rnd):
        s = rnd.choice((-1, 1)); y = rnd.uniform(-2.2, 2.2)
        p0 = (s * rnd.uniform(0.9, 1.6), y, 2.25)
        p1 = (s * rnd.uniform(1.6, 2.6), y + rnd.uniform(-0.4, 0.4), rnd.uniform(0.3, 1.6))
        return [p0, ((p0[0] + p1[0]) / 2, y, (p0[2] + p1[2]) / 2 + 0.2), p1]
    particles(110, path, 0.0, d + 0.3, 1.3, 0.022, am, seed=4)
    arm = person('Passenger', loc=(0.85, 0.3, 0), rot_z=math.radians(180), outfit='casual')
    if arm:
        pose(arm, 0.0, STANCES['relax']); pose(arm, 0.9, {'neck01': (-16, 0, 0)}); pose(arm, d, {'neck01': (-20, 0, 6)})
    c0 = Vector((0.0, 10.6, 1.25)); c1 = Vector((0.0, 9.6, 1.15))
    camera([(0, c0, Vector((0, 0, 1.0))), (d, c1, Vector((0, 0, 1.0)))], lens=28, fstop=8)

def S03(a, b):  # inside: the air pushes out on every window (orange arrows press on the panes)
    sc = new_scene(a, b); d = dur(a, b); M = wmats()
    sky_out(1.0, 0.4, d=d, move=60)
    root, G = cabin(M, -3.0, 3.0, sides=(-1,), lights=True)
    update()
    pm, ps = mat_simple('PushArrow', (1.0, 0.35, 0.05), 0.4, emit=(1.0, 0.38, 0.06), estr=5.0)
    for k, g in enumerate(sorted(G[-1], key=lambda g: g.matrix_world.translation.y)):
        y = g.matrix_world.translation.y
        if y < -1.7: continue
        p1 = g.matrix_world @ Vector((0, -0.03, 0)); p0 = p1 + Vector((0.42, 0, 0))
        ar = arrow('Push', p0, p1, 0.014, pm); pop_in(ar, 0.4 + 0.18 * k)
        key(ar, 'location', [(0.4 + 0.18 * k + 0.35, p0), (d, p0 + Vector((-0.06, 0, 0)))])
    c0 = Vector((-1.15, -2.35, 1.42)); c1 = Vector((-1.3, -2.05, 1.38))
    camera([(0, c0, Vector((-2.7, 0.7, 1.08))), (d, c1, Vector((-2.7, 0.9, 1.08)))], lens=24, fstop=5)

def S04(a, b):  # studio: the window splits into three acrylic panes
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.6, 0.6)
    O = stack(M, sep=((0, 0.0), (1.4, 0.0), (3.3, 1.0), (d, 1.0)))
    light('AREA', (-0.8, -0.9, 0.9), 60, (1, 0.97, 0.92), 1.0, rot=(math.radians(-50), 0, math.radians(-35)))
    light('AREA', (0.9, 0.6, 0.5), 40, (0.8, 0.88, 1.0), 1.0, rot=(math.radians(-70), 0, math.radians(130)))
    c0 = Vector((-0.62, -0.95, 0.22)); c1 = Vector((-0.78, -0.82, 0.18))
    camera([(0, c0, Vector((0, -0.05, 0))), (d, c1, Vector((0, -0.13, 0)))], lens=45, fstop=5.6)

def S05(a, b):  # the thick outer pane holds back the pressure
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.6, 0.6)
    O = stack(M, sep=((0, 1.0),), rims=('outer',))
    key_socket(O['glow_outer'], [(0, 0.0), (0.35, 12.0), (d, 10.0)])
    pm, _ = mat_simple('PushArrow', (1.0, 0.35, 0.05), 0.4, emit=(1.0, 0.38, 0.06), estr=5.0)
    for k, (x, z) in enumerate(((0, 0), (-0.07, 0.1), (0.07, 0.1), (-0.07, -0.1), (0.07, -0.1))):
        ar = arrow('Push', (x, -0.09, z), (x, 0.019, z), 0.004, pm); pop_in(ar, 0.3 + 0.1 * k)
    light('AREA', (-0.8, -0.9, 0.9), 60, (1, 0.97, 0.92), 1.0, rot=(math.radians(-50), 0, math.radians(-35)))
    c0 = Vector((-0.55, -0.62, 0.16)); c1 = Vector((-0.5, -0.5, 0.12))
    camera([(0, c0, Vector((0, 0.0, 0))), (d, c1, Vector((0, 0.02, 0)))], lens=45, fstop=5.6)

def S06(a, b):  # the middle pane is a spare in case the outer one cracks
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.6, 0.6)
    O = stack(M, sep=((0, 1.0),), rims=('middle',))
    cm, _ = mat_simple('CrackWhite', (0.9, 0.92, 0.95), 0.6, emit=(0.8, 0.85, 0.9), estr=0.6)
    crack(O['outer'], 0.5, 1.6, cm)
    key_socket(O['glow_middle'], [(0, 0.0), (1.2, 0.0), (1.6, 12.0), (d, 10.0)])
    light('AREA', (-0.8, -0.9, 0.9), 60, (1, 0.97, 0.92), 1.0, rot=(math.radians(-50), 0, math.radians(-35)))
    c0 = Vector((-0.5, -0.75, 0.15)); c1 = Vector((-0.6, -0.85, 0.12))
    camera([(0, c0, Vector((0, 0.01, 0))), (1.4, c0, Vector((0, 0.0, 0))), (d, c1, Vector((0, -0.13, 0)))], lens=45, fstop=6)

def S07(a, b):  # cabin: a passenger in the roomy exit row reaches toward the thin inner pane
    sc = new_scene(a, b); d = dur(a, b); M = wmats()
    sky_out(1.0, 0.4, d=d, move=60)
    root, G = cabin(M, -3.0, 3.0, sides=(-1,), skip_left_seats_rows=(), lights=True)
    arm = person('Passenger', loc=(-2.12, 0.18, 0), rot_z=math.radians(-75), outfit='casual')
    if arm:
        pose(arm, 0.0, STANCES['relax']); pose(arm, 0.5, STANCES['relax'])
        pose(arm, 1.4, {'upperarm01.R': (40, 0, 30), 'lowerarm01.R': (25, 0, 0), 'neck01': (-6, 0, 0)})
    c0 = Vector((-0.45, -1.55, 1.5)); c1 = Vector((-0.62, -1.35, 1.45))
    camera([(0, c0, Vector((-2.45, 0.1, 1.15))), (d, c1, Vector((-2.5, 0.1, 1.12)))], lens=30, fstop=4)

def S08(a, b):  # section view: cabin air slips through the tiny hole in the middle pane
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.5, 0.6)
    O = stack(M, sep=((0, 0.0),), cut=True, rims=())
    am, _ = mat_simple('Air', (0.5, 0.8, 1.0), 0.3, emit=(0.45, 0.8, 1.0), estr=8.0)
    def path(rnd):
        x = rnd.uniform(-0.004, 0.002); zz = HOLE_Z + rnd.uniform(-0.002, 0.002)
        return [(x, -0.05, zz + rnd.uniform(-0.03, 0.03)), (x, -0.006, zz), (x, 0.006, zz),
                (x, 0.014, zz + rnd.uniform(0.0, 0.05)), (x, 0.016, zz + rnd.uniform(0.05, 0.16))]
    particles(70, path, 0.3, d + 0.2, 1.4, 0.0013, am, seed=7)
    light('AREA', (0.6, -0.5, 0.2), 30, (1, 0.97, 0.92), 0.8, rot=(math.radians(-80), 0, math.radians(50)))
    light('AREA', (0.5, 0.5, -0.1), 20, (0.8, 0.88, 1.0), 0.8, rot=(math.radians(-100), 0, math.radians(130)))
    c0 = Vector((0.24, -0.01, HOLE_Z + 0.035)); c1 = Vector((0.16, 0.0, HOLE_Z + 0.02))
    camera([(0, c0, Vector((0, 0.004, HOLE_Z + 0.02))), (d, c1, Vector((0, 0.006, HOLE_Z + 0.012)))], lens=50, fstop=8)

def S09(a, b):  # section: equal pressure on both sides of the middle pane, the load goes to the outer pane
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.5, 0.6)
    O = stack(M, sep=((0, 0.0),), cut=True, rims=())
    bm_, _ = mat_simple('EqArrow', (0.3, 0.7, 1.0), 0.4, emit=(0.3, 0.72, 1.0), estr=5.0)
    om, _ = mat_simple('LoadArrow', (1.0, 0.35, 0.05), 0.4, emit=(1.0, 0.38, 0.06), estr=6.0)
    for k, z in enumerate((0.09, -0.02)):
        a1 = arrow('Eq', (0.002, -0.032, z), (0.002, -0.0045, z), 0.0016, bm_); pop_in(a1, 0.3 + 0.15 * k)
        a2 = arrow('Eq', (0.002, 0.021, z + 0.035), (0.002, 0.0045, z + 0.035), 0.0016, bm_); pop_in(a2, 0.3 + 0.15 * k)
    for k, z in enumerate((0.13, 0.03, -0.07)):
        a3 = arrow('Load', (0.002, 0.005, z), (0.002, 0.0225, z), 0.0022, om); pop_in(a3, 1.8 + 0.15 * k)
    key_socket(O['glow_outer'], [(0, 0.0), (1.8, 0.0), (2.2, 10.0), (d, 9.0)])
    light('AREA', (0.6, -0.5, 0.2), 30, (1, 0.97, 0.92), 0.8, rot=(math.radians(-80), 0, math.radians(50)))
    c0 = Vector((0.62, -0.03, 0.02)); c1 = Vector((0.56, -0.01, 0.0))
    camera([(0, c0, Vector((0, 0.0, 0.0))), (d, c1, Vector((0, 0.01, 0.0)))], lens=50, fstop=8)

def fog_mat(level_pts):
    m = bpy.data.materials.new('Fog'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sp.inputs['Vector'])
    sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; nt.links.new(sp.outputs['Z'], sub.inputs[0])
    key_socket(sub.inputs[1], level_pts, 'BEZIER')
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 25; mul.use_clamp = True
    nt.links.new(sub.outputs['Value'], mul.inputs[0])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.7
    mr.inputs['To Min'].default_value = 0.55; mr.inputs['To Max'].default_value = 0.95
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    f = nt.nodes.new('ShaderNodeMath'); f.operation = 'MULTIPLY'; nt.links.new(mul.outputs['Value'], f.inputs[0]); nt.links.new(mr.outputs['Result'], f.inputs[1])
    ps = nt.nodes.new('ShaderNodeBsdfPrincipled'); ps.inputs['Base Color'].default_value = (0.92, 0.93, 0.95, 1); ps.inputs['Roughness'].default_value = 0.6
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(f.outputs['Value'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ps.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], o.inputs['Surface'])
    return m

def S10(a, b):  # cabin window: fog/frost between the panes clears from the bottom (the hole) up; the wing outside
    sc = new_scene(a, b); d = dur(a, b); M = wmats()
    sky_out(1.0, 0.4, d=d, move=60)
    root, G = cabin(M, -2.0, 2.0, sides=(-1,), wins=[0.0, 0.53, -0.53, 1.06], lights=True)
    update(); g = win_at(G, -1, 0.0)
    fm = fog_mat([(0, -0.3), (0.7, -0.3), (3.4, 0.3), (d, 0.3)])
    fogp = child(rr_prism('Fog', WW - 0.004, WH - 0.004, WRR - 0.002, 0.0008), g, (0, 0.096, 0)); fogp.data.materials.append(fm)
    fogp2 = child(rr_prism('Frost', WW - 0.004, WH - 0.004, WRR - 0.002, 0.0008), g, (0, 0.123, 0)); fogp2.data.materials.append(fog_mat([(0, -0.3), (0.9, -0.3), (3.6, 0.3), (d, 0.3)]))
    wm = paint_mat('WingGrey', (0.62, 0.64, 0.67), 0.35, 0.3, 0.3)
    wing = wing_mesh('Wing', wm, side=-1, root=(2.9, 1.5, -1.2), span=26, sweep=10, rc=8, tc=2.2, dz=2.2)
    wing.location = (-5.9, 0.0, 0.0)
    c0 = Vector((-2.30, -0.30, 1.22)); c1 = Vector((-2.44, -0.22, 1.16))
    t0 = win_target(g, (0, 0.10, 0.0))
    camera([(0, c0, t0), (d, c1, t0 + Vector((0, 0, -0.02)))], lens=34, fstop=3.5)
    sc.camera.data.dof.focus_object = None; sc.camera.data.dof.focus_distance = (c0 - t0).length

def S11(a, b):  # studio: square corner piles up stress and cracks; the round window spreads it. An engineer points.
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.55, 0.3, floor_z=0.0)
    back = box('Backdrop', (10, 0.1, 6), (0, 2.6, 3), M['studio'])
    Z = 1.45
    for s, sq in ((-1, True), (1, False)):
        cx = s * 0.62
        pnl = box('Panel', (0.86, 0.012, 1.05), (cx, 0, Z), M['skin'])
        boolean(pnl, cutter_obj(rr_prism('Cut', 0.30, 0.42, 0.006 if sq else 0.13, 0.2, (cx, 0, Z))))
        for dx in (-0.3, 0.3): cyl('Stand', 0.015, Z - 0.5, (cx + dx, 0.02, (Z - 0.5) / 2), M['alu'], verts=16)
        box('Foot', (0.75, 0.3, 0.03), (cx, 0.02, 0.015), M['alu_rough'])
        if sq:
            gm, gs = glow_mat('HotCorner', (1.0, 0.08, 0.02), 0.0)
            for ux in (-1, 1):
                for uz in (-1, 1):
                    sph = sphere('Hot', 0.05, (cx + ux * 0.15, -0.012, Z + uz * 0.21), gm, sub=3); sph.scale = (1, 0.2, 1)
            key_socket(gs, [(0, 0.0), (0.4, 14.0), (1.0, 7.0), (1.6, 16.0), (2.2, 8.0), (2.8, 16.0), (d, 10.0)])
            cm, _ = mat_simple('CrackDark', (0.01, 0.01, 0.012), 0.6)
            pv = bpy.data.objects.new('CrackRoot', None); link(pv); pv.location = (cx, -0.0075, Z); pv.rotation_euler = (0, 0, 0)
            crack(pv, 1.1, 2.6, cm, seed=5, start=(0.15, 0.21), n=8, w=0.004, angs=(0.75, 0.3, 1.25))
        else:
            gm, gs = glow_mat('EvenGlow', (1.0, 0.75, 0.15), 0.0)
            rm = rim('Even', 0.31, 0.43, 0.135, gm, bev=0.006); rm.location = (cx, -0.008, Z)
            key_socket(gs, [(0, 0.0), (1.6, 0.0), (2.2, 2.5), (d, 2.2)])
    arm = person('Engineer', loc=(-0.05, -0.45, 0), rot_z=math.radians(-35), outfit='casual')
    if arm:
        pose(arm, 0.0, STANCES['relax']); pose(arm, 0.6, STANCES['relax']); pose(arm, 1.5, STANCES['point_r'])
    light('AREA', (-2.0, -3.0, 3.2), 380, (1, 0.96, 0.9), 2.5, rot=(math.radians(55), 0, math.radians(-35)))
    light('AREA', (2.5, -1.5, 2.5), 200, (0.85, 0.9, 1.0), 2.0, rot=(math.radians(60), 0, math.radians(60)))
    c0 = Vector((-0.35, -3.45, 1.55)); c1 = Vector((0.25, -3.3, 1.5))
    camera([(0, c0, Vector((-0.3, 0, 1.3))), (d, c1, Vector((0.25, 0, 1.3)))], lens=32, fstop=8)

def S12(a, b):  # dusk at the gate: a mechanic walks along the lit cabin windows
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.7, 2.6, 'dusk'); sun(1.0, 4, 250, (1.0, 0.62, 0.38), 2.0)
    cm, _ = mat_textured('Apron', ['concrete_floor_02', 'asphalt_02'], 0.18, (0.4, 0.4, 0.4), rough=(0.35, 0.75), tint=(0.62, 0.62, 0.64))
    plane('Apron', 600, 600, (0, 0, 0), cm)
    j = jet(M, paint_mat('WingGrey', (0.62, 0.64, 0.67), 0.35, 0.3, 0.3), lit=True, beacon=True)
    far_lights(y=95, n=40)
    flood((-28, 22, 18), (-2, 4, 1), energy=6000)
    arm = person('Mechanic', loc=(-4.0, 2.0, 0), rot_z=math.radians(180), outfit='worker')
    if arm:
        key(arm, 'location', [(0, Vector((-4.0, 2.0, 0))), (d, Vector((-4.0, 2.0 + 0.7 * d, 0)))], interp='LINEAR')
        walk(arm, 0.0, d)
    c0 = Vector((-7.2, 12.5, 1.05)); c1 = Vector((-7.0, 11.8, 1.1))
    camera([(0, c0, Vector((-2.6, 2.5, 2.4))), (d, c1, Vector((-2.6, 3.2, 2.4)))], lens=35, fstop=5.6)

def S13(a, b):  # pull back from the window hole to a passenger looking out
    sc = new_scene(a, b); d = dur(a, b); M = wmats()
    sky_out(1.0, 0.4, d=d, move=60)
    root, G = cabin(M, -3.0, 3.0, sides=(-1,), skip_left_seats_rows=(0.95,), lights=True)
    update(); g = win_at(G, -1, 0.0); h = win_target(g)
    arm = person('Passenger', loc=(-2.08, 0.78, 0), rot_z=math.radians(-62), outfit='casual')
    if arm:
        pose(arm, 0.0, STANCES['relax']); pose(arm, d, {'neck01': (-8, 0, 0)})
    c0 = Vector((-2.48, -0.14, 1.02)); c1 = Vector((-0.75, -1.65, 1.45))
    camera([(0, c0, h), (1.0, c0 + (c1 - c0) * 0.3, h + Vector((0, 0.1, 0.1))), (d + 0.3, c1, Vector((-2.2, 0.75, 1.25)))], lens=32, fstop=4)

def _far(f):
    def g(a, b):
        f(a, b)
        c = bpy.context.scene.camera
        if c: c.data.clip_end = 120000
    return g

SHOTS = [_far(f) for f in (S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13)]

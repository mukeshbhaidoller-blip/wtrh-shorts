# Shots for "If You Connect Your Sink Straight to the Sewer..." (how a P-trap / drain vent works). One function per line.
# Z up, metres. Person faces -Y at rot_z=0 (facing vector = (sin rz, -cos rz)). Studio cut-aways: trap in the XZ plane at y=0,
# front half (y<0) cut away, camera looks +Y.
import bmesh

def dur(a, b): return (b - a) / FPS

# ---------------------------------------------------------------- materials
def mat_tile(name, c1, c2, mortar, bw, rh, rough=0.3, offset=0.5, bump=0.25, scale=1.0, coat=0.0, vertical=False, grain=0.0):
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    if vertical: mp.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); vec = mp.outputs['Vector']
    br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = offset
    br.inputs['Color1'].default_value = (*c1, 1); br.inputs['Color2'].default_value = (*c2, 1)
    br.inputs['Mortar'].default_value = (*mortar, 1); br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.004; br.inputs['Mortar Smooth'].default_value = 0.4
    br.inputs['Brick Width'].default_value = bw; br.inputs['Row Height'].default_value = rh
    nt.links.new(vec, br.inputs['Vector'])
    if grain:
        gn = nt.nodes.new('ShaderNodeTexNoise'); gn.inputs['Scale'].default_value = 260; gn.inputs['Detail'].default_value = 2
        nt.links.new(vec, gn.inputs['Vector'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = grain
        nt.links.new(br.outputs['Color'], mx.inputs[6]); nt.links.new(gn.outputs['Color'], mx.inputs[7])
        nt.links.new(mx.outputs[2], p.inputs['Base Color'])
    else:
        nt.links.new(br.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    if coat: inp(p, 'Coat Weight', 'Clearcoat').default_value = coat
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(br.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def mat_water(name='Water', col=(0.55, 0.78, 0.95), dirty=False):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = 0.03
    inp(p, 'Transmission Weight', 'Transmission').default_value = 0.92 if not dirty else 0.35
    p.inputs['IOR'].default_value = 1.33
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 90; n.inputs['Detail'].default_value = 3
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def gas_mat(name='Gas', dens=40.0, col=(0.66, 0.68, 0.28), emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*col, 1)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 2.2; n.inputs['Detail'].default_value = 5
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; nt.links.new(tc.outputs['Object'], ln.inputs[0])
    fo = nt.nodes.new('ShaderNodeMapRange'); fo.inputs['From Min'].default_value = 1.0; fo.inputs['From Max'].default_value = 0.0
    nt.links.new(ln.outputs['Value'], fo.inputs['Value'])
    sh = nt.nodes.new('ShaderNodeMapRange'); sh.inputs['From Min'].default_value = 0.3; sh.inputs['From Max'].default_value = 0.8
    nt.links.new(n.outputs['Fac'], sh.inputs['Value'])
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(fo.outputs['Result'], mu.inputs[0]); nt.links.new(sh.outputs['Result'], mu.inputs[1])
    mu2 = nt.nodes.new('ShaderNodeMath'); mu2.operation = 'MULTIPLY'; mu2.inputs[1].default_value = dens; nt.links.new(mu.outputs[0], mu2.inputs[0])
    nt.links.new(mu2.outputs[0], v.inputs['Density'])
    if emit:
        v.inputs['Emission Color'].default_value = (*col, 1)
        nt.links.new(mu.outputs[0], v.inputs['Emission Strength']) if False else None
        v.inputs['Emission Strength'].default_value = emit
    nt.links.new(v.outputs['Volume'], o.inputs['Volume'])
    return m

def mats():
    M = {}
    M['pvc'] = mat_simple('PVC', (0.86, 0.86, 0.84), 0.32, coat=0.15)[0]
    M['pvc_in'] = mat_simple('PVCin', (0.7, 0.7, 0.68), 0.5)[0]
    M['abs'] = mat_simple('ABS', (0.02, 0.02, 0.022), 0.45)[0]
    M['chrome'] = mat_simple('Chrome', (0.8, 0.8, 0.82), 0.08, 1.0)[0]
    M['steel'] = mat_simple('Stainless', (0.62, 0.63, 0.65), 0.28, 1.0)[0]
    M['dark'] = mat_simple('Dark', (0.012, 0.012, 0.013), 0.6)[0]
    M['water'] = mat_water()
    M['studio'] = mat_simple('Backdrop', (0.055, 0.058, 0.065), 0.55)[0]
    M['cab'] = mat_simple('CabinetNavy', (0.035, 0.06, 0.11), 0.42, coat=0.1)[0]
    M['cabin'] = mat_simple('CabinetInside', (0.72, 0.69, 0.62), 0.55)[0]
    M['counter'] = mat_textured('Quartz', [], 6.0, (0.88, 0.87, 0.84), rough=(0.12, 0.3), bump=0.05)[0]
    M['wall'] = mat_simple('WallPaint', (0.6, 0.58, 0.53), 0.85)[0]
    M['tile'] = mat_tile('Subway', (0.92, 0.92, 0.9), (0.86, 0.87, 0.86), (0.6, 0.6, 0.58), 0.15, 0.075, rough=0.12, coat=0.4, vertical=True)
    M['ftile'] = mat_tile('FloorTile', (0.42, 0.4, 0.37), (0.36, 0.35, 0.33), (0.25, 0.24, 0.22), 0.6, 0.3, rough=0.35, offset=0.5)
    M['shingle'] = mat_tile('Shingles', (0.075, 0.072, 0.07), (0.04, 0.04, 0.042), (0.012, 0.012, 0.012), 0.33, 0.3, rough=0.92, bump=0.9, grain=0.8)
    M['brick'] = mat_textured('Brick', ['red_brick_03', 'brick_wall_001'], 0.4, (0.45, 0.2, 0.14), rough=(0.8, 0.95))[0]
    M['deck'] = mat_simple('Deck', (0.03, 0.03, 0.03), 0.9)[0]
    M['trim'] = mat_simple('Trim', (0.9, 0.9, 0.88), 0.4)[0]
    M['grass'] = mat_textured('Grass', ['leafy_grass', 'aerial_grass_rock'], 0.3, (0.18, 0.26, 0.09), rough=(0.85, 1.0), bump=0.8)[0]
    M['slab'] = mat_textured('Slab', ['concrete_floor_02', 'concrete_floor_worn_001'], 0.6, (0.5, 0.5, 0.48), rough=(0.5, 0.85))[0]
    M['soil'] = mat_textured('Soil', ['brown_mud_02', 'forrest_ground_01'], 0.8, (0.25, 0.18, 0.12), rough=(0.8, 1.0))[0]
    M['block'] = mat_textured('Block', ['painted_brick'], 0.35, (0.7, 0.7, 0.68), rough=(0.8, 0.95), tint=(0.85, 0.85, 0.83))[0]
    M['sewer'] = mat_textured('SewerConcrete', ['concrete_pavement', 'concrete_floor_worn_001'], 0.5, (0.35, 0.34, 0.31), rough=(0.6, 0.95), tint=(0.55, 0.55, 0.5), wet=0.4)[0]
    M['cblock'] = mat_tile('ConcreteBlock', (0.52, 0.51, 0.48), (0.47, 0.46, 0.43), (0.36, 0.35, 0.33), 0.4, 0.2, rough=0.9, bump=0.5, vertical=True)
    M['murk'] = mat_water('Murk', (0.12, 0.1, 0.06), dirty=True)
    return M

# ---------------------------------------------------------------- geometry helpers
def tube_mesh(name, pts, r, mat, ring=40, cap=True):
    """Swept round tube along 3D points (parallel-transport frames), capped, smooth."""
    P = [Vector(p) for p in pts]; n = len(P)
    T = []
    for i in range(n):
        d = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]); T.append(d.normalized())
    up = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    N = (up - T[0] * up.dot(T[0])).normalized()
    bm = bmesh.new(); rings = []
    for i in range(n):
        if i > 0:
            N = (N - T[i] * N.dot(T[i])).normalized()
        B = T[i].cross(N)
        rv = []
        for k in range(ring):
            a = 2 * math.pi * k / ring
            rv.append(bm.verts.new(P[i] + r * (math.cos(a) * N + math.sin(a) * B)))
        rings.append(rv)
    for i in range(n - 1):
        for k in range(ring):
            k2 = (k + 1) % ring
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    if cap:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o)
    if mat: me.materials.append(mat)
    return o

def extend(pts, e):
    P = [Vector(p) for p in pts]
    a = P[0] + (P[0] - P[1]).normalized() * e; b = P[-1] + (P[-1] - P[-2]).normalized() * e
    return [tuple(a)] + [tuple(p) for p in P[1:-1]] + [tuple(b)]

def cutter(name, size, loc):
    c = box(name, size, loc); c.hide_render = True; c.display_type = 'WIRE'; return c

def boolean(o, c, op='DIFFERENCE'):
    md = o.modifiers.new('bool_' + c.name, 'BOOLEAN'); md.object = c; md.operation = op
    try: md.solver = 'EXACT'
    except Exception: pass
    return md

def arc(cx, cz, R, th0, th1, n):
    return [(cx + R * math.cos(th0 + (th1 - th0) * k / n), cz + R * math.sin(th0 + (th1 - th0) * k / n)) for k in range(n + 1)]

def trap_path(zt=0.30, R=0.045, rise=0.065, Re=0.03, L=0.36, n=18):
    """2D (x, z) centre line: tailpiece down x=0 from zt to 0, U bend (bottom at z=-R), up to the elbow, arm along +x at zA."""
    P = [(0, zt)] + arc(R, 0.0, R, math.pi, 2 * math.pi, n)
    zA = rise
    P += [(2 * R, zA - Re)] + arc(2 * R + Re, zA - Re, Re, math.pi, math.pi / 2, 10)[1:] + [(L, zA)]
    return P, zA

def trap(M, origin=(0, 0, 0), yaw=0.0, r=0.02, wall=0.003, zt=0.30, R=0.045, rise=0.065, L=0.36, cut=False, level=None,
         mat=None, water=True):
    """P-trap. Returns dict with levels: zw (full seal level), dip (lowest level that still seals), water obj, level cutter."""
    ox, oy, oz = origin; cy, sy = math.cos(yaw), math.sin(yaw)
    P2, zA = trap_path(zt, R, rise, max(0.03, r * 1.6), L)
    W = lambda x, z: (ox + x * cy, oy + x * sy, oz + z)
    P3 = [W(x, z) for x, z in P2]
    ri = r - wall
    pipe = tube_mesh('Trap', P3, r, mat or M['pvc'])
    res = dict(pipe=pipe, zA=oz + zA, zw=oz + zA - ri, dip=oz - R + ri, bottom=oz - R - ri, ri=ri, path=P3)
    if cut:
        inner = tube_mesh('TrapIn', extend(P3, 0.01), ri, None); inner.hide_render = True; inner.display_type = 'WIRE'
        boolean(pipe, inner)
        fc = cutter('CutFront', (6, 2, 6), (0, oy - 1.0, 1.0)); boolean(pipe, fc); res['front'] = fc
    if water:
        wp = extend(P3, -0.002)
        wtr = tube_mesh('TrapWater', wp, ri * 0.995, M['water'])
        lv = cutter('Level', (6, 6, 4), (0, 0, (res['zw'] - 0.0005 if level is None else level) + 2.0))
        boolean(wtr, lv)
        if cut: boolean(wtr, res['front'])
        res['water'] = wtr; res['lv'] = lv
    return res

def key_level(tr, pts):
    """pts [(t, z_level_world)]"""
    key(tr['lv'], 'location', [(t, Vector((0, 0, z + 2.0))) for t, z in pts])

def pipe_straight(name, p0, p1, r, mat, cut_front=None, hollow=0.0):
    o = tube_mesh(name, [p0, p1], r, mat)
    if hollow:
        i = tube_mesh(name + 'In', extend([p0, p1], 0.01), r - hollow, None); i.hide_render = True; i.display_type = 'WIRE'; boolean(o, i)
    if cut_front is not None: boolean(o, cut_front)
    return o

def stream(name, p0, p1, r, mat, n=80):
    p0 = Vector(p0); p1 = Vector(p1)
    o = tube_mesh(name, [p0 + (p1 - p0) * (k / n) for k in range(n + 1)], r, mat, ring=16)
    tx = bpy.data.textures.new(name + 'N', 'CLOUDS'); tx.noise_scale = 0.03
    tx.noise_scale = 0.02
    dm = o.modifiers.new('disp', 'DISPLACE'); dm.texture = tx; dm.strength = r * 1.1; dm.mid_level = 0.5
    sb = o.modifiers.new('sub', 'SUBSURF'); sb.levels = 1; sb.render_levels = 1
    return o

def puff(loc, size, mat, name='Gas'):
    o = sphere(name, 1.0, loc, mat, sub=3); o.scale = size if isinstance(size, tuple) else (size, size, size); return o

def drift(o, t0, t1, p0, p1, s0=None, s1=None):
    key(o, 'location', [(t0, Vector(p0)), (t1, Vector(p1))])
    if s0 is not None: key(o, 'scale', [(t0, Vector(s0)), (t1, Vector(s1))])

def studio(back_y=0.7, key_e=60, rim_e=35, tgt=(0.12, 0, 0.3), floor_z=0.0):
    world_hdri('studio_small_09', 0.25, 0, 'studio')
    M_ = mat_simple('Backdrop', (0.05, 0.053, 0.06), 0.55)[0]
    plane('Floor', 8, 8, (0, 2, floor_z), M_)
    box('Back', (8, 0.02, 6), (0, back_y + 0.4, 3), M_)
    k = light('AREA', (-0.9, -1.2, 1.2), key_e, (1, 0.96, 0.9), 1.2); aim(k, tgt)
    rl = light('AREA', (1.1, 0.5, 1.0), rim_e, (0.8, 0.88, 1.0), 0.8); aim(rl, tgt)
    f = light('AREA', (0.6, -1.4, 0.15), key_e * 0.3, (1, 1, 1), 1.0); aim(f, tgt)
    for l in (k, rl, f): l.visible_glossy = True

# ---------------------------------------------------------------- kitchen set
DRAIN = (0.0, 0.31, 0.70)

def kitchen(M, trap_kind='p', gas=False, doors=100, inner_light=6.0, doors_r=None):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.28, math.radians(80))
    plane('Floor', 8, 8, (0, 0, 0), M['ftile'])
    box('Wall', (6, 0.05, 3.0), (0, 0.65, 1.5), M['wall'])
    box('SideWall', (0.05, 4, 3.0), (-1.55, -1.3, 1.5), M['wall'])
    box('Splash', (3.0, 0.01, 0.55), (0, 0.62, 1.195), M['tile'])
    # sink cabinet carcass (open front)
    for x in (-0.45, 0.45): box('Side', (0.018, 0.6, 0.78), (x, 0.32, 0.49), M['cab'])
    box('Bottom', (0.9, 0.6, 0.018), (0, 0.32, 0.11), M['cabin'])
    box('BackPanel', (0.9, 0.01, 0.78), (0, 0.615, 0.49), M['cabin'])
    box('Toe', (0.9, 0.05, 0.1), (0, 0.06, 0.05), M['dark'])
    box('Rail', (0.9, 0.025, 0.09), (0, 0.025, 0.835), M['cab'], bevel=0.003)
    # neighbouring closed cabinets
    for sx in (-1, 1):
        cx = sx * 1.0
        box('Cab', (1.08, 0.58, 0.78), (cx, 0.33, 0.49), M['cab'])
        box('Toe', (1.08, 0.05, 0.1), (cx, 0.07, 0.05), M['dark'])
        for k in range(2):
            dx = cx + (k - 0.5) * 0.54
            box('Door', (0.52, 0.022, 0.74), (dx, 0.03, 0.49), M['cab'], bevel=0.006)
            box('Handle', (0.012, 0.03, 0.14), (dx + (0.2 if k == 0 else -0.2), 0.0, 0.62), M['steel'], bevel=0.004)
    # open doors on the sink cabinet
    for sx in (-1, 1):
        h = bpy.data.objects.new('Hinge', None); link(h); h.location = (sx * 0.45, 0.02, 0.48)
        d = box('SinkDoor', (0.44, 0.022, 0.72), (0, 0, 0), M['cab'], bevel=0.006); d.parent = h; d.location = (-sx * 0.22, -0.011, 0)
        hd = box('Handle', (0.012, 0.03, 0.14), (0, 0, 0), M['steel'], bevel=0.004); hd.parent = h; hd.location = (-sx * 0.40, -0.035, 0.12)
        h.rotation_euler = (0, 0, math.radians(sx * (doors if (sx < 0 or doors_r is None) else doors_r)))
    # counter with sink cut-out
    zc = 0.90
    box('CounterL', (1.18, 0.64, 0.04), (-0.91, 0.32, zc), M['counter'], bevel=0.004)
    box('CounterR', (1.18, 0.64, 0.04), (0.91, 0.32, zc), M['counter'], bevel=0.004)
    box('CounterF', (0.64, 0.12, 0.04), (0, 0.06, zc), M['counter'], bevel=0.003)
    box('CounterB', (0.64, 0.14, 0.04), (0, 0.57, zc), M['counter'], bevel=0.003)
    # stainless basin
    z0 = DRAIN[2]
    box('BasinBottom', (0.62, 0.38, 0.008), (0, 0.31, z0), M['steel'])
    for (sz, loc) in [((0.62, 0.008, 0.2), (0, 0.12, z0 + 0.1)), ((0.62, 0.008, 0.2), (0, 0.5, z0 + 0.1)),
                      ((0.008, 0.38, 0.2), (-0.31, 0.31, z0 + 0.1)), ((0.008, 0.38, 0.2), (0.31, 0.31, z0 + 0.1))]:
        box('BasinWall', sz, loc, M['steel'])
    cyl('Flange', 0.045, 0.006, (DRAIN[0], DRAIN[1], z0 + 0.005), M['steel'], verts=48)
    cyl('Hole', 0.034, 0.004, (DRAIN[0], DRAIN[1], z0 + 0.007), M['dark'], verts=48)
    # faucet
    cyl('FaucetBase', 0.028, 0.04, (0, 0.57, zc + 0.04), M['chrome'], verts=40)
    fp = [(0, 0.57, zc + 0.05), (0, 0.57, zc + 0.3)] + [(0, 0.57 - 0.09 + 0.09 * math.cos(a), zc + 0.3 + 0.09 * math.sin(a))
          for a in [math.radians(v) for v in range(0, 181, 15)]] + [(0, 0.39, zc + 0.24)]
    tube_mesh('Spout', fp, 0.014, M['chrome'], ring=24)
    # pipes under the sink
    tr = None
    if trap_kind == 'p':
        tr = trap(M, origin=(DRAIN[0], DRAIN[1], 0.40), yaw=math.radians(90), r=0.02, zt=z0 - 0.40, L=0.30, mat=M['pvc'], water=False)
        cyl('Nut', 0.026, 0.02, (DRAIN[0], DRAIN[1], 0.47), M['pvc'], verts=32)
        cyl('WallFlange', 0.04, 0.01, (0, 0.608, 0.465), M['chrome'], rot=(math.radians(90), 0, 0), verts=40)
    else:   # straight pipe right into the floor: no trap
        tube_mesh('Straight', [(DRAIN[0], DRAIN[1], z0), (DRAIN[0], DRAIN[1], 0.10)], 0.02, M['pvc'])
        cyl('FloorFlange', 0.04, 0.008, (DRAIN[0], DRAIN[1], 0.122), M['dark'], verts=40)
    tube_mesh('SupplyL', [(-0.12, 0.6, 0.36), (-0.12, 0.54, 0.36), (-0.06, 0.52, 0.66), (-0.04, 0.55, z0 - 0.01)], 0.005, M['chrome'], ring=12)
    tube_mesh('SupplyR', [(0.12, 0.6, 0.36), (0.12, 0.54, 0.36), (0.06, 0.52, 0.66), (0.04, 0.55, z0 - 0.01)], 0.005, M['chrome'], ring=12)
    for x in (-0.12, 0.12): cyl('Valve', 0.014, 0.05, (x, 0.585, 0.36), M['chrome'], rot=(math.radians(90), 0, 0), verts=24)
    # lights
    win = light('AREA', (-1.45, -0.2, 1.7), 80, (1, 0.97, 0.92), 1.4); aim(win, (0, 0.3, 0.8)); win.visible_glossy = False
    top = light('AREA', (0.3, -0.6, 2.6), 90, (1, 0.93, 0.84), 2.0); aim(top, (0, 0.3, 0.6)); top.visible_glossy = False
    il = light('POINT', (0.0, 0.12, 0.62), inner_light, (1, 0.95, 0.88), 0.15); il.visible_glossy = False
    return tr

def sink_gas(t0, d, rise=0.55, n=5, dens=140.0):
    g = gas_mat('SinkGas', dens, (0.6, 0.64, 0.3))
    for k in range(n):
        tt = t0 + k * 0.45
        s = 0.05 + 0.02 * k
        o = puff((DRAIN[0], DRAIN[1], DRAIN[2] + 0.02), 0.03, g)
        key(o, 'location', [(0, Vector((DRAIN[0], DRAIN[1], DRAIN[2] - 0.05))), (tt, Vector((DRAIN[0], DRAIN[1], DRAIN[2] + 0.02))),
                            (d + 0.5, Vector((DRAIN[0] + 0.04 * (k - 2), DRAIN[1] - 0.06, DRAIN[2] + rise * (d + 0.5 - tt) / max(d, 1))))])
        key(o, 'scale', [(0, Vector((0.01, 0.01, 0.01))), (tt, Vector((0.03, 0.03, 0.03))), (d + 0.5, Vector((s * 4.0, s * 4.0, s * 4.6)))])

# ---------------------------------------------------------------- studio cut-away trap
def studio_trap(M, level=None, gas='arm', basin=False, vent=False, origin=(0, 0, 0.32), gas_dens=320.0):
    tr = trap(M, origin=origin, r=0.02, zt=0.30, L=0.36 if not vent else 0.381, cut=True, level=level)
    ox, oy, oz = origin
    # cut slip nuts (rings) at the joints
    for (x, z) in [(0, 0.12), (0.12, tr['zA'] - oz)]:
        pass
    if basin:
        zb = oz + 0.30
        b = box('BasinBottom', (0.5, 0.36, 0.008), (0, 0.0, zb + 0.004), M['steel']); boolean(b, tr['front'])
        for sz, loc in [((0.008, 0.36, 0.16), (-0.25, 0, zb + 0.08)), ((0.008, 0.36, 0.16), (0.25, 0, zb + 0.08)), ((0.5, 0.008, 0.16), (0, 0.18, zb + 0.08))]:
            w = box('BasinWall', sz, loc, M['steel']); boolean(w, tr['front'])
        hole = cyl('Drain', 0.03, 0.03, (0, 0, zb), None, verts=40); hole.hide_render = True; hole.display_type = 'WIRE'; boolean(b, hole)
        tr['zb'] = zb
    if vent:
        xv = ox + 0.40
        tee_r = 0.024
        stk = pipe_straight('Stack', (xv, 0, oz - 0.5), (xv, 0, oz + 1.6), tee_r, M['pvc'], tr['front'], hollow=0.003)
        th = tube_mesh('TeeHole', [(xv - 0.05, 0, tr['zA']), (xv, 0, tr['zA'])], tr['ri'], None); th.hide_render = True; th.display_type = 'WIRE'; boolean(stk, th)
        tr['xv'] = xv
    if gas:
        g = gas_mat('TrapGas', gas_dens, (0.62, 0.66, 0.26))
        P = tr['path']; zA = tr['zA']
        xs = [0.2, 0.26, 0.32] if gas == 'arm' else []
        tr['gas'] = []
        for k, x in enumerate(xs):
            o = puff((ox + x, 0.0, zA), (0.035, 0.016, 0.017), g); tr['gas'].append(o)
        if vent and gas in ('arm', 'stack'):
            for k in range(4):
                o = puff((tr['xv'], 0.0, oz - 0.12 - 0.1 * k), (0.021, 0.02, 0.07), g); tr['gas'].append(o)
    return tr

def ruler(x, z0, z1, y=-0.035):
    yel = mat_simple('Tape', (0.85, 0.62, 0.04), 0.4)[0]; blk = mat_simple('Ink', (0.01, 0.01, 0.01), 0.5)[0]
    box('TapeBlade', (0.016, 0.002, z1 - z0 + 0.03), (x, y, (z0 + z1) / 2), yel)
    inch = 0.0254; k = 0; z = z0
    while z <= z1 + 1e-4:
        L = 0.011 if k % 2 == 0 else 0.006
        box('Tick', (L, 0.0006, 0.0009), (x - 0.008 + L / 2, y - 0.0012, z), blk)
        z += inch / 2; k += 1
    wht = mat_emit('Mark', (1, 1, 1), 4.0)[0]
    return wht

# ---------------------------------------------------------------- basement floor drain (section)
def basement(M, level=None, person_at=None):
    world_hdri('kloofendal_overcast_puresky', 0.15, 0, 'overcast')
    slab = box('Slab', (4, 3, 0.12), (0, 1.5, -0.06), M['slab'])
    hole = cyl('DrainHole', 0.06, 0.3, (0, 0, -0.06), None, verts=48); hole.hide_render = True; hole.display_type = 'WIRE'; boolean(slab, hole)
    box('Soil', (4, 3, 0.9), (0, 1.56, -0.57), M['soil'])
    box('BackWall', (4, 0.2, 2.6), (0, 2.6, 1.3), M['cblock'])
    # trap below the floor (cut in half), inlet straight up to the grate
    tr = trap(M, origin=(0, 0, -0.42), r=0.032, wall=0.004, zt=0.42, R=0.06, rise=0.085, L=1.6, cut=True, level=level, mat=M['pvc'])
    body = pipe_straight('DrainBody', (0, 0, -0.12), (0, 0, -0.004), 0.06, M['abs'], tr['front'], hollow=0.012)
    gm = mat_simple('Grate', (0.42, 0.42, 0.4), 0.35, 1.0)[0]
    gr = cyl('Grate', 0.07, 0.006, (0, 0, -0.001), gm, verts=64)
    for k in range(-3, 4):
        s = box('Slot', (0.008, 0.09 - abs(k) * 0.012, 0.02), (k * 0.016, 0, 0), None); s.hide_render = True; s.display_type = 'WIRE'; boolean(gr, s)
    boolean(gr, tr['front'])
    w = light('AREA', (-1.2, 2.3, 1.9), 60, (0.8, 0.88, 1.0), 1.0); aim(w, (0, 0.5, 0))
    b = light('POINT', (0.4, 1.0, 2.1), 40, (1, 0.85, 0.65), 0.1)
    f = light('AREA', (0.6, -1.6, 0.2), 25, (1, 0.97, 0.92), 1.5); aim(f, (0, 0, -0.3)); f.visible_glossy = False
    mat_emit('Window', (0.8, 0.88, 1.0), 6.0)
    win = plane('Window', 0.9, 0.4, (-1.2, 2.49, 1.95), mat_emit('WindowE', (0.85, 0.9, 1.0), 5.0)[0]); win.rotation_euler = (math.radians(90), 0, 0)
    return tr

def base_cam(d, near=False):
    if near:
        return camera([(0, (0.2, -0.82, 0.16), (0.08, 0.1, -0.26)), (d, (0.17, -0.76, 0.13), (0.08, 0.1, -0.27))], lens=30, fstop=6)
    return camera([(0, (0.32, -0.78, 0.14), (0.12, 0.1, -0.3)), (d, (0.26, -0.7, 0.1), (0.1, 0.1, -0.31))], lens=30, fstop=6)

# ================================================================ shots
def S00(a, b):  # kitchen, pipe goes straight to the floor (no trap); greenish sewer gas rises out of the sink, the owner leans away
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    kitchen(M, trap_kind='straight', doors=105)
    sink_gas(0.3, d, rise=0.6, n=6, dens=55.0)
    arm = person('Owner', loc=(-0.72, -0.28, 0), rot_z=math.radians(55), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.6, STANCES['relax'])
    pose(arm, 2.6, {'spine02': (-7, 0, 0), 'neck01': (-8, 0, 18)}); pose(arm, d, {'spine02': (-8, 0, 0), 'neck01': (-8, 0, 22)})
    camera([(0, (0.38, -2.2, 1.25), (-0.38, 0.1, 0.92)), (d, (0.3, -1.95, 1.2), (-0.36, 0.1, 0.9))], lens=24, fstop=4.0)

def S01(a, b):  # underground section: a concrete sewer main under the lawn, murky water, yellow-green gas inside; a house line drops in
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_overcast_puresky', 0.7, 0, 'overcast'); sun(1.6, 35, 160)
    zc = -1.6; ro, ri = 0.45, 0.38
    fc = cutter('CutFront', (12, 4, 12), (0, -2.0, 0))
    soil = box('Soil', (6, 3, 4.0), (0, 1.5, -2.0), M['soil'])
    trench = cyl('Trench', ro + 0.01, 7, (0, 0, zc), None, rot=(0, math.radians(90), 0), verts=96); trench.hide_render = True; trench.display_type = 'WIRE'
    boolean(soil, trench)
    lat_c = cyl('LatHole', 0.06, 1.6, (0.6, 0, -0.6), None, verts=32); lat_c.hide_render = True; lat_c.display_type = 'WIRE'; boolean(soil, lat_c)
    box('Turf', (6, 3, 0.06), (0, 1.5, 0.03), M['grass'])
    main = pipe_straight('SewerMain', (-3.2, 0, zc), (3.2, 0, zc), ro, M['sewer'], fc, hollow=ro - ri)
    lat = pipe_straight('HouseLine', (0.6, 0, 0.0), (0.6, 0, zc + ri - 0.02), 0.05, M['pvc'], fc, hollow=0.006)
    th = cyl('LatIn', 0.044, 0.3, (0.6, 0, zc + ri + 0.03), None, verts=32); th.hide_render = True; th.display_type = 'WIRE'; boolean(main, th)
    w = box('Sewage', (6.3, 0.22, 0.08), (0, 0.11, zc - ri + 0.04), M['murk'])
    g = gas_mat('SewerGas', 14.0, (0.62, 0.64, 0.26))
    for k in range(6):
        x = -1.4 + k * 0.55
        o = puff((x, 0.12, zc + 0.02 * k), (0.32, 0.2, 0.26), g)
        key(o, 'location', [(0, Vector((x, 0.12, zc))), (d, Vector((x + 0.35, 0.12, zc + 0.06)))])
    for k in range(3):
        o = puff((0.6, 0.0, zc + 0.5 + 0.3 * k), (0.035, 0.03, 0.12), g)
        key(o, 'location', [(0, Vector((0.6, 0.0, zc + 0.45 + 0.25 * k))), (d, Vector((0.6, 0.0, zc + 0.7 + 0.25 * k)))])
    f = light('AREA', (0.5, -2.5, -0.6), 260, (1, 0.97, 0.92), 2.0); aim(f, (0.3, 0, -1.4)); f.visible_glossy = False
    camera([(0, (0.55, -2.6, -0.95), (0.35, 0, -1.25)), (d, (0.4, -2.35, -1.0), (0.4, 0, -1.3))], lens=30, fstop=8)

def S02(a, b):  # plumber at the open sink cabinet, a white U-shaped trap under the drain
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    kitchen(M, trap_kind='p', doors=110, inner_light=10.0, doors_r=160)
    arm = person('Plumber', loc=(0.62, -0.42, 0), rot_z=math.radians(-139), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.7, STANCES['relax']); pose(arm, 1.8, STANCES['work_low']); pose(arm, d, STANCES['work_low'])
    camera([(0, (-0.55, -1.65, 1.05), (0.22, 0.05, 0.64)), (d, (-0.45, -1.45, 0.98), (0.2, 0.08, 0.6))], lens=24, fstop=4.0)

def S03(a, b):  # studio cut-away: water fills the U bend; sewer gas sits in the arm and stops at the water
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio()
    tr = studio_trap(M, level=None)
    key_level(tr, [(0, tr['bottom'] - 0.01), (1.2, tr['zw'] + 0.03), (1.9, tr['zw'] - 0.0005)])
    for k, o in enumerate(tr['gas']):
        p0 = Vector(o.location); key(o, 'location', [(0, p0 + Vector((0.06, 0, 0))), (2.2, p0), (d, p0 - Vector((0.012, 0, 0)))])
    camera([(0, (0.34, -0.72, 0.36), (0.13, 0, 0.30)), (d, (0.24, -0.66, 0.33), (0.13, 0, 0.30))], lens=40, fstop=4.0)

def S04(a, b):  # the seal: a tape measure next to the water plug, depth between the dip and the outlet
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio()
    tr = studio_trap(M)
    wht = ruler(-0.045, tr['dip'], tr['zw'] + 0.005)
    for z in (tr['zw'], tr['dip']):
        mk = box('MarkLine', (0.15, 0.0008, 0.0012), (0.035, -0.025, z), wht)
        key(mk, 'scale', [(0, Vector((0.01, 1, 1))), (0.8, Vector((0.01, 1, 1))), (1.6, Vector((1, 1, 1)))])
        mk.location.x = 0.035
    camera([(0, (0.0, -0.44, 0.33), (0.02, 0, 0.32)), (d, (0.03, -0.4, 0.32), (0.025, 0, 0.32))], lens=45, fstop=4.0)

def S05(a, b):  # full sink drains fast: water slug fills the whole trap, then siphons it right out
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio(tgt=(0.12, 0, 0.45))
    tr = studio_trap(M, basin=True, gas=False)
    zb = tr['zb']
    bw = box('BasinWater', (0.49, 0.35, 0.12), (0, 0.0, zb + 0.07), M['water']); boolean(bw, tr['front'])
    key(bw, 'scale', [(0, Vector((1, 1, 1))), (1.4, Vector((1, 1, 0.5))), (2.0, Vector((1, 1, 0.02)))])
    key(bw, 'location', [(0, Vector((0, 0, zb + 0.07))), (1.4, Vector((0, 0, zb + 0.04))), (2.0, Vector((0, 0, zb + 0.009)))])
    key_level(tr, [(0, tr['zw'] - 0.0005), (0.25, zb + 0.02), (1.9, zb + 0.02), (2.6, tr['zA'] + 0.03), (3.2, tr['dip'] - 0.012), (d, tr['dip'] - 0.014)])
    camera([(0, (0.2, -0.95, 0.5), (0.12, 0, 0.44)), (d, (0.16, -0.85, 0.42), (0.12, 0, 0.36))], lens=35, fstop=4.5)

def S06(a, b):  # the arm runs to a stack: a vent pipe goes up; small air motes come down the vent while the seal holds
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio(tgt=(0.3, 0, 0.6))
    tr = studio_trap(M, vent=True, gas='stack')
    xv = tr['xv']; zA = tr['zA']
    am = mat_emit('Air', (0.75, 0.88, 1.0), 3.0)[0]
    for k in range(12):
        o = sphere('Air', 0.0035, (xv, 0, 1.5), am, sub=1)
        t0 = -1.6 + k * 0.45
        pts = [(t0, Vector((xv + 0.006 * math.sin(k), -0.004, 1.4))), (t0 + 1.4, Vector((xv, -0.004, zA))), (t0 + 2.0, Vector((xv - 0.14, -0.004, zA + 0.004)))]
        key(o, 'location', [(max(0, t), p) for t, p in pts], interp='LINEAR')
    camera([(0, (0.4, -1.0, 1.2), (0.38, 0, 1.05)), (d, (0.2, -0.95, 0.5), (0.18, 0, 0.42))], lens=35, fstop=5.6)

def S07(a, b):  # outside: a house roof with a black vent pipe sticking out; a man on the lawn points up at it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.85, math.radians(30)); sun(2.2, 38, 150)
    plane('Lawn', 60, 60, (0, 0, 0), M['grass'])
    box('Walls', (8, 6, 2.8), (0, 4, 1.4), M['brick'])
    th = math.radians(30); run = 3.3; rise = run * math.tan(th); ze = 2.8 - 0.3 * math.tan(th)
    for s in (-1, 1):
        yc = 4 - s * (run / 2); zc = ze + rise / 2; Ls = run / math.cos(th) + 0.05
        box('Roof', (8.6, Ls, 0.08), (0, yc, zc), M['deck'] if s == 1 else M['shingle'], rot=(s * th, 0, 0))
        if s == 1:   # real overlapping shingle courses on the front slope
            rig = bpy.data.objects.new('Courses', None); link(rig); rig.location = (0, yc, zc); rig.rotation_euler = (th, 0, 0)
            nrow = int(Ls / 0.14)
            for k in range(nrow):
                rw = box('Course', (8.6, 0.2, 0.006), (0, 0, 0), M['shingle'])
                rw.parent = rig; rw.location = ((k * 0.117) % 0.33, -Ls / 2 + 0.1 + k * 0.14, 0.044 + 0.004); rw.rotation_euler = (math.radians(-1.6), 0, 0)
        box('Fascia', (8.6, 0.03, 0.2), (0, 4 - s * 3.3, ze - 0.05), M['trim'])
    for x in (-4.0, 4.0):   # gable ends
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in [(x, 1.0, 2.8), (x, 7.0, 2.8), (x, 4.0, 2.8 + 3.0 * math.tan(th))]]
        bm.faces.new(vs); me = bpy.data.meshes.new('Gable'); bm.to_mesh(me); bm.free(); me.materials.append(M['brick'])
        link(bpy.data.objects.new('Gable', me))
    for (x, f) in [(1.2, 0.6), (-1.6, 0.45)]:
        y = 0.7 + f * run; z = ze + f * rise
        cyl('Vent', 0.045, 0.55, (x, y, z + 0.2), M['abs'], verts=40)
        cyl('Boot', 0.11, 0.05, (x, y, z + 0.05), mat_simple('Boot', (0.15, 0.15, 0.16), 0.5, 0.6)[0], rot=(th, 0, 0), verts=40)
    for x in (-2.2, 2.2):
        box('Window', (1.1, 0.05, 1.2), (x, 0.98, 1.4), mat_simple('Glass', (0.02, 0.025, 0.03), 0.05, coat=1)[0])
        box('WinTrim', (1.25, 0.04, 1.35), (x, 1.0, 1.4), M['trim'])
    box('Door', (1.0, 0.05, 2.1), (0.2, 0.98, 1.05), mat_simple('FrontDoor', (0.25, 0.05, 0.04), 0.4)[0])
    camera([(0, (2.05, 0.35, 3.25), (1.2, 2.68, 3.95)), (d, (1.9, 0.6, 3.3), (1.2, 2.68, 3.97))], lens=38, fstop=2.8)

def S08(a, b):  # basement floor drain in section: the water in its trap slowly dries up
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    tr = basement(M)
    key_level(tr, [(0, tr['zw'] - 0.001), (0.6, tr['zw'] - 0.002), (d, tr['dip'] - 0.006)])
    base_cam(d)

def S09(a, b):  # the dry trap: sewer gas comes up through the grate; the owner in the basement steps back
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    tr = basement(M, level=None)
    key_level(tr, [(0, tr['dip'] - 0.008)])
    g = gas_mat('BaseGas', 160.0, (0.62, 0.65, 0.28))
    for k in range(5):
        o = puff((0, 0, -0.3), 0.03, g)
        t0 = k * 0.3
        key(o, 'location', [(0, Vector((0.6 - 0.05 * k, 0, tr['zA']))), (t0 + 0.4, Vector((0, 0, -0.2))), (t0 + 1.1, Vector((0, 0, 0.05))), (d + 0.6, Vector((0.05 * (k - 2), 0.1, 0.4 + 0.08 * k)))])
        key(o, 'scale', [(0, Vector((0.03, 0.02, 0.025))), (t0 + 1.1, Vector((0.05, 0.05, 0.05))), (d + 0.6, Vector((0.22, 0.22, 0.25)))])
    arm = person('Owner', loc=(0.85, 1.35, 0), rot_z=math.radians(-25), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.8, {'spine02': (-6, 0, 0), 'neck01': (-6, 0, 15)})
    camera([(0, (0.6, -1.55, 0.75), (0.35, 0.6, 0.3)), (d, (0.55, -1.4, 0.7), (0.35, 0.6, 0.3))], lens=26, fstop=5.6)

def S10(a, b):  # water is poured into the drain from above: the trap fills up again
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    tr = basement(M)
    wm = M['water']
    st = stream('Stream', (0.0, 0.03, 1.4), (0.0, 0.03, 0.0), 0.012, wm)
    st2 = stream('InnerStream', (0, 0.012, 0.0), (0, 0.012, -0.4), 0.01, wm)
    key_level(tr, [(0, tr['dip'] - 0.008), (0.8, tr['dip'] - 0.008), (2.4, tr['zw'] - 0.0008)])
    base_cam(d, near=True)

def S11(a, b):  # wide studio cut-away: basin above, a few inches of water in the bend, sewer gas held back below the stack
    sc = new_scene(a, b); d = dur(a, b); M = mats(); studio(tgt=(0.2, 0, 0.45))
    tr = studio_trap(M, basin=True, vent=True, gas='stack')
    camera([(0, (0.16, -0.55, 0.36), (0.12, 0, 0.31)), (d, (0.22, -1.25, 0.55), (0.22, 0, 0.42))], lens=35, fstop=5.0)

def S12(a, b):  # back in the kitchen: the owner points at the U-bend under the sink; the camera pushes in to it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    kitchen(M, trap_kind='p', doors=110, inner_light=10.0)
    arm = person('Owner', loc=(-0.62, -0.26, 0), rot_z=math.radians(60), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.5, STANCES['relax']); pose(arm, 1.4, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    camera([(0, (0.1, -2.3, 1.3), (-0.32, 0.1, 0.85)), (d, (0.08, -1.45, 0.85), (-0.15, 0.2, 0.55))], lens=24, fstop=4.0)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12]

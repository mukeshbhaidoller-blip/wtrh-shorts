# Shots for "If You Build a House Right on the Dirt..." (how house foundations / footings work). One function per line.
# Z up, metres. Person faces -Y at rot_z=0; his right hand is on the -X side then. t = seconds from the shot start.
import bmesh

def dur(a, b): return (b - a) / FPS

# ---------------------------------------------------------------- materials
def siding_mat(col=(0.74, 0.77, 0.75)):
    m, nt, p = nodes_mat('Siding')
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 2 * math.pi / (10 * 0.15)       # 15 cm lap exposure
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * 0.72 for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[1].position = 0.25
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.55
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.01
    nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def ice_mat():
    m, p = mat_simple('Ice', (0.86, 0.93, 1.0), 0.12, trans=0.55, ior=1.31)
    return m

def rebar_mat():
    m, nt, p = nodes_mat('Rebar')
    p.inputs['Metallic'].default_value = 0.5; p.inputs['Roughness'].default_value = 0.65
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 25; n.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.12, 0.06, 0.035, 1); ramp.color_ramp.elements[1].color = (0.36, 0.17, 0.08, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 2 * math.pi / (10 * 0.012)
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def mats():
    M = {}
    M['mud'] = mat_textured('Mud', ['brown_mud_02'], 0.35, (0.25, 0.18, 0.12), rough=(0.6, 0.9))[0]
    M['soil'] = mat_textured('Soil', ['brown_mud_02'], 0.7, (0.22, 0.16, 0.1), rough=(0.8, 1.0), tint=(0.62, 0.48, 0.36))[0]
    M['sub'] = mat_textured('Subsoil', ['brown_mud_02'], 0.45, (0.35, 0.27, 0.18), rough=(0.8, 1.0), tint=(1.05, 0.8, 0.56))[0]
    M['frozen'] = mat_textured('Frozen', ['brown_mud_02'], 0.7, (0.6, 0.62, 0.66), rough=(0.3, 0.55), tint=(1.35, 1.45, 1.65), wet=0.5)[0]
    M['conc'] = mat_textured('Concrete', ['concrete_floor_worn_001'], 0.6, (0.55, 0.55, 0.53), rough=(0.7, 0.95), tint=(1.0, 1.0, 1.0))[0]
    M['wetconc'] = mat_textured('WetConcrete', ['concrete_floor_02'], 0.6, (0.4, 0.4, 0.39), rough=(0.25, 0.45), tint=(0.6, 0.6, 0.58), wet=0.9)[0]
    M['wood'] = mat_textured('Lumber', ['plywood'], 0.8, (0.7, 0.55, 0.38), rough=(0.6, 0.85), tint=(1.0, 0.88, 0.72))[0]
    M['siding'] = siding_mat()
    M['trim'] = mat_simple('Trim', (0.88, 0.88, 0.86), 0.45)[0]
    M['door'] = mat_simple('DoorPaint', (0.08, 0.13, 0.2), 0.4, coat=0.1)[0]
    M['roof'] = mat_textured('Shingles', ['asphalt_04'], 0.9, (0.12, 0.12, 0.13), rough=(0.75, 0.95), tint=(0.5, 0.48, 0.48))[0]
    M['glass'] = mat_simple('WinGlass', (0.02, 0.025, 0.03), 0.04, coat=1.0)[0]
    M['snow'] = mat_textured('Snow', ['snow_02'], 0.5, (0.9, 0.92, 0.95), rough=(0.4, 0.8))[0]
    M['grass'] = mat_textured('Lawn', ['aerial_grass_rock'], 0.12, (0.15, 0.25, 0.08), rough=(0.85, 1.0), bump=0.8, tint=(0.55, 0.85, 0.45))[0]
    M['ice'] = ice_mat()
    M['rebar'] = rebar_mat()
    M['steel'] = mat_simple('Galv', (0.62, 0.63, 0.64), 0.32, 1.0)[0]
    M['dark'] = mat_simple('Crack', (0.008, 0.008, 0.008), 0.95)[0]
    M['studio'] = mat_simple('StudioFloor', (0.045, 0.045, 0.05), 0.55)[0]
    return M

# ---------------------------------------------------------------- geometry kit
def prism(name, pts, length, loc, mat):
    """Extrude a 2D (y, z) outline along X."""
    n = len(pts); verts = []
    for x in (-length / 2, length / 2):
        for (y, z) in pts: verts.append((x, y, z))
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n; faces.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); o.location = loc
    if mat: o.data.materials.append(mat)
    return o

def cut(target, size, loc, name='Cutter'):
    c = box(name, size, loc); c.hide_render = True; c.display_type = 'WIRE'
    md = target.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = c
    try: md.solver = 'EXACT'
    except Exception: pass
    return c

def ground(mat, size=60.0, depth=4.0, cuts=(), loc=(0, 0)):
    g = box('Ground', (size, size, depth), (loc[0], loc[1], -depth / 2), mat)
    for sz, c in cuts: cut(g, sz, c)
    return g

def house(M, w=6.0, d=5.0, h=2.7, lit=0.0, name='House'):
    """Wood-frame house, walls on z=0, front (door) faces -Y. Returns the rig empty (move/scale it)."""
    rig = bpy.data.objects.new(name, None); link(rig); P = []
    P.append(box('Walls', (w, d, h), (0, 0, h / 2), M['siding']))
    for sx in (-1, 1):
        for sy in (-1, 1): P.append(box('Corner', (0.12, 0.12, h), (sx * w / 2, sy * d / 2, h / 2), M['trim']))
    P.append(box('Fascia', (w + 0.04, d + 0.04, 0.16), (0, 0, h - 0.08), M['trim']))
    rh = d / 2 * math.tan(math.radians(30))
    P.append(prism('Gable', [(-d / 2, 0), (d / 2, 0), (0, rh)], w, (0, 0, h), M['siding']))
    ov = 0.45; L = (d / 2 + ov) / math.cos(math.radians(30))
    for sy in (-1, 1):
        r = box('Roof', (w + 0.6, L, 0.1), (0, sy * (d / 2 + ov) / 2, h + (rh - ov * math.tan(math.radians(30))) / 2 + 0.07), M['roof'])
        r.rotation_euler = (-sy * math.radians(30), 0, 0); P.append(r)
    P.append(box('Ridge', (w + 0.6, 0.2, 0.08), (0, 0, h + rh + 0.1), M['roof']))
    gm = M['glass']
    if lit:
        gm = mat_simple('LitGlass', (0.05, 0.04, 0.03), 0.1, emit=(1, 0.72, 0.4), estr=lit)[0]
    def window(x, y, z, face='y', ww=1.0, wh=1.2):
        if face == 'y':
            P.append(box('WinTrim', (ww + 0.16, 0.06, wh + 0.16), (x, y, z), M['trim']))
            P.append(box('Win', (ww, 0.08, wh), (x, y, z), gm))
            P.append(box('Mullion', (0.04, 0.1, wh), (x, y, z), M['trim']))
            P.append(box('Sill', (ww + 0.3, 0.12, 0.05), (x, y - 0.03, z - wh / 2 - 0.1), M['trim']))
        else:
            P.append(box('WinTrim', (0.06, ww + 0.16, wh + 0.16), (x, y, z), M['trim']))
            P.append(box('Win', (0.08, ww, wh), (x, y, z), gm))
    for x in (-1.9, 1.9): window(x, -d / 2, 1.55)
    for x in (-1.9, 1.9): window(x, d / 2, 1.55)
    window(-w / 2, 0, 1.55, 'x'); window(w / 2, 0, 1.55, 'x')
    P.append(box('DoorTrim', (1.12, 0.06, 2.2), (0, -d / 2, 1.08), M['trim']))
    P.append(box('Door', (0.95, 0.08, 2.08), (0, -d / 2, 1.04), M['door']))
    P.append(sphere('Knob', 0.03, (0.36, -d / 2 - 0.05, 1.0), M['steel'], sub=2))
    for o in P: o.parent = rig
    return rig

def foundation(M, w, d, top=0.3, bottom=-1.2, ft=0.3, fw=0.6, tw=0.2, mat=None):
    """Perimeter stem walls (outer faces on the house walls) on wide footings. Returns objects."""
    m = mat or M['conc']; P = []
    H = top - (bottom + ft); zc = bottom + ft + H / 2; fz = bottom + ft / 2
    for sy in (-1, 1):
        P.append(box('Stem', (w, tw, H), (0, sy * (d / 2 - tw / 2), zc), m))
        P.append(box('Footing', (w + fw - tw, fw, ft), (0, sy * (d / 2 - tw / 2), fz), m))
    for sx in (-1, 1):
        P.append(box('Stem', (tw, d - 2 * tw, H), (sx * (w / 2 - tw / 2), 0, zc), m))
        P.append(box('Footing', (fw, d - fw + tw, ft), (sx * (w / 2 - tw / 2), 0, fz), m))
    return P

def soil_block(M, size, front_y, top=0.0, topsoil=0.32, cx=0.0):
    """Soil with a cut face at y=front_y that runs back +Y. Topsoil over subsoil."""
    sx, sy, sz = size
    a = box('Topsoil', (sx, sy, topsoil), (cx, front_y + sy / 2, top - topsoil / 2), M['soil'])
    b = box('Subsoil', (sx, sy, sz - topsoil), (cx, front_y + sy / 2, top - topsoil - (sz - topsoil) / 2), M['sub'])
    return a, b

def frost_face(M, front_y, x0, x1, top, depth, seed=4, lenses=14, t_grow=None, skip=None):
    """Frozen layer on a soil cut face + ice lenses. t_grow=(t0, t1) animates it creeping down from the surface."""
    w = x1 - x0; xc = (x0 + x1) / 2
    fr = box('FrozenFace', (w, 0.01, depth), (xc, front_y - 0.004, top - depth / 2), M['frozen'])
    if t_grow:
        t0, t1 = t_grow
        key(fr, 'scale', [(0, Vector((1, 1, 0.001))), (t0, Vector((1, 1, 0.001))), (t1, Vector((1, 1, 1)))])
        key(fr, 'location', [(0, Vector((xc, front_y - 0.004, top))), (t0, Vector((xc, front_y - 0.004, top))), (t1, Vector((xc, front_y - 0.004, top - depth / 2)))])
    random.seed(seed); out = []
    for i in range(lenses):
        L = random.uniform(0.12, 0.5) * min(1.0, w / 2); th = random.uniform(0.008, 0.022)
        z = top - random.uniform(0.06, 0.92) * depth; x = random.uniform(x0 + L / 2, x1 - L / 2)
        if skip and x + L / 2 > skip[0] and x - L / 2 < skip[1]: continue
        o = box('IceLens', (L, 0.02, th), (x, front_y - 0.006, z), M['ice'], bevel=min(0.004, th / 3), segs=2)
        if t_grow:
            t0, t1 = t_grow; tz = t0 + (t1 - t0) * (top - z) / depth
            key(o, 'scale', [(0, Vector((0.001, 1, 0.001))), (tz, Vector((0.001, 1, 0.001))), (tz + 0.6, Vector((1, 1, 1)))])
        out.append(o)
    return fr, out

def studio_lights(key_e=500, rim_e=300):
    k = light('AREA', (-2.2, -3.0, 2.6), key_e, (1, 0.96, 0.9), 2.5); aim(k, (0, 0, 0))
    r = light('AREA', (2.6, 2.0, 2.2), rim_e, (0.85, 0.9, 1.0), 2.0); aim(r, (0, 0, 0))
    f = light('AREA', (1.5, -3.5, 0.2), key_e * 0.25, (1, 1, 1), 2.0); aim(f, (0, 0, -0.3))

def day(rot=30, sun_e=2.2, elev=38, azim=150):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, math.radians(rot)); sun(sun_e, elev, azim)

def winter(sun_e=1.6, elev=22, azim=145):
    world_hdri('snowy_field', 0.9, 0, 'overcast'); sun(sun_e, elev, azim, color=(1, 0.95, 0.9))

def piles(M, pts, mat):
    for (x, y, sx, sy, sz) in pts:
        o = sphere('Pile', 1.0, (x, y, 0), mat, sub=4); o.scale = (sx, sy, sz)
        tex = bpy.data.textures.new('pileN', 'CLOUDS'); tex.noise_scale = 0.35
        dm = o.modifiers.new('disp', 'DISPLACE'); dm.texture = tex; dm.strength = 0.12

def shovel(M, loc, tilt=18):
    rig = bpy.data.objects.new('Shovel', None); link(rig); rig.location = loc; rig.rotation_euler = (math.radians(tilt), 0, math.radians(20))
    h = cyl('Handle', 0.017, 1.2, (0, 0, 0.75), M['wood'], verts=16); h.parent = rig
    g = box('Grip', (0.14, 0.03, 0.03), (0, 0, 1.36), M['dark']); g.parent = rig
    bl = box('Blade', (0.24, 0.02, 0.3), (0, 0, 0.0), M['steel'], bevel=0.01); bl.parent = rig
    return rig

# ================================================================ shots
def S00(a, b):  # a house sitting right on bare mud slowly sinks, the owner watches
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(20)
    plane('Mud', 90, 90, (0, 0, 0), M['mud'])
    rig = house(M); rig.location = (0, 2.0, 0)
    key(rig, 'location', [(0, Vector((0, 2.0, 0.0))), (2.05, Vector((0, 2.0, -0.12))), (2.3, Vector((0, 2.0, -0.24))), (d, Vector((0, 2.0, -0.3)))])
    key(rig, 'rotation_euler', [(0, Vector((0, 0, 0))), (2.05, Vector((0, math.radians(0.6), 0))), (2.3, Vector((0, math.radians(1.6), 0))), (d, Vector((0, math.radians(1.9), 0)))])
    piles(M, [(-5.5, 5.0, 1.6, 1.0, 0.5), (6.0, 7.0, 2.0, 1.2, 0.6)], M['mud'])
    arm = person('Owner', loc=(-2.0, -2.4, 0), rot_z=math.radians(125), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.2, STANCES['relax']); pose(arm, 2.6, {'neck01': (6, 0, 8), 'spine02': (-4, 0, 0)})
    cam, _ = camera([(0, (-0.3, -9.6, 1.25), (0, 1.5, 1.45)), (d, (-0.25, -8.8, 1.2), (0, 1.5, 1.4))], lens=24, fstop=8)
    key(cam, 'rotation_euler', [(0, Vector((0, 0, 0))), (2.28, Vector((0, 0, 0))), (2.33, Vector((0.004, 0, 0.003))), (2.55, Vector((0, 0, 0)))])

def S01(a, b):  # studio cut-away: a small house sits on a block of soil and squeezes down into it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.35, 0, 'studio'); studio_lights()
    plane('Floor', 30, 30, (0, 0, -1.25), M['studio'])
    soil_block(M, (2.6, 1.6, 1.25), -0.8)
    rig = house(M); rig.scale = (0.3, 0.3, 0.3); rig.location = (0, 0, 0)
    key(rig, 'location', [(0, Vector((0, 0, 0))), (d, Vector((0, 0, -0.075)))])
    # soil crumbs pushed up around the walls
    random.seed(2)
    for i in range(26):
        sx = random.choice((-1, 1)); x = sx * random.uniform(0.92, 1.05); y = random.uniform(-0.75, 0.75)
        if random.random() < 0.5: x, y = random.uniform(-0.95, 0.95), random.choice((-1, 1)) * random.uniform(0.77, 0.86)
        c = sphere('Crumb', random.uniform(0.012, 0.03), (x, y, -0.01), M['soil'], sub=2)
        tb = random.uniform(0.3, d - 0.5)
        key(c, 'scale', [(0, Vector((0.01, 0.01, 0.01))), (tb, Vector((0.01, 0.01, 0.01))), (tb + 0.5, Vector((1, 1, 0.7)))])
    camera([(0, (1.0, -3.3, 0.55), (0, 0, -0.1)), (d, (0.75, -3.05, 0.45), (0, 0, -0.12))], lens=26, fstop=5.6)

def S02(a, b):  # building site: a trench in the mud, wet concrete pours in from a chute, a worker points at it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(70, elev=40, azim=120)
    ground(M['mud'], cuts=[((12, 0.7, 0.62), (0, 0, -0.29))])
    s0, s1 = 0.08, 1.0
    c = box('Pour', (12, 0.7, 0.3), (0, 0, -0.45), M['wetconc'])
    key(c, 'scale', [(0, Vector((1, 1, s0))), (d, Vector((1, 1, s1)))], interp='LINEAR')
    key(c, 'location', [(0, Vector((0, 0, -0.6 + 0.15 * s0))), (d, Vector((0, 0, -0.6 + 0.15 * s1)))], interp='LINEAR')
    # chute from a truck off-frame (up right), U-section
    ch = bpy.data.objects.new('Chute', None); link(ch)
    for o in (box('ChuteBase', (0.42, 3.0, 0.03), (0, 0, 0), M['steel']),
              box('ChuteSide', (0.03, 3.0, 0.16), (-0.21, 0, 0.08), M['steel']),
              box('ChuteSide', (0.03, 3.0, 0.16), (0.21, 0, 0.08), M['steel']),
              box('ChuteMix', (0.38, 3.0, 0.06), (0, 0, 0.04), M['wetconc'])):
        o.parent = ch
    ch.location = (0.4, 1.55, 0.85); ch.rotation_euler = (math.radians(24), 0, 0)
    st = cyl('Stream', 0.07, 0.72, (0.4, 0.12, -0.1), M['wetconc'], verts=24)
    piles(M, [(-2.2, 1.4, 1.3, 0.7, 0.45), (0.9, 1.6, 1.0, 0.6, 0.35), (-4.5, 1.5, 1.4, 0.8, 0.5)], M['mud'])
    shovel(M, (-2.0, 1.1, 0.25))
    arm = person('Worker', loc=(-0.95, -0.85, 0), rot_z=math.radians(100), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.9, STANCES['relax']); pose(arm, 1.9, STANCES['point_r'])
    camera([(0, (3.3, -0.8, 1.1), (-0.7, 0.05, -0.35)), (d, (3.0, -0.75, 1.0), (-0.7, 0.05, -0.4))], lens=24, fstop=5.6)

def snowshoe(M, loc, yaw=0.0):
    rig = bpy.data.objects.new('Snowshoe', None); link(rig)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.011, major_segments=64, minor_segments=10)
    fr = bpy.context.active_object; fr.scale = (0.37, 1, 1); fr.data.materials.append(M['steel']); fr.parent = rig
    deck = cyl('Deck', 0.295, 0.006, (0, 0, 0), mat_simple('Decking', (0.35, 0.05, 0.04), 0.6)[0], verts=48)
    deck.scale = (0.37, 1, 1); deck.parent = rig
    bnd = box('Binding', (0.13, 0.16, 0.05), (0, 0.04, 0.025), M['dark'], bevel=0.01); bnd.parent = rig
    rig.location = loc; rig.rotation_euler = (0, 0, yaw)
    return rig

def S03(a, b):  # snow: a hiker stands on snowshoes on top of the snow; beside them his boot prints sank deep
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter(1.8, 20, 150)
    holes = []
    for k in range(5):
        x = -0.75 + (0.13 if k % 2 else -0.13); y = -0.6 + k * 0.62
        holes.append(((0.15, 0.32, 0.7), (x, y, 0.0)))
    ground(M['snow'], cuts=holes)
    for (sz, (x, y, _)) in holes:   # dark packed bottom of each hole
        box('HoleBottom', (0.14, 0.3, 0.02), (x, y, -0.33), mat_simple('Packed', (0.55, 0.6, 0.7), 0.5)[0])
    for sx in (-1, 1):
        s = snowshoe(M, (0.35 + sx * 0.13, 0.25, 0.0))
        key(s, 'location', [(0, Vector((0.35 + sx * 0.13, 0.25, 0.012))), (d, Vector((0.35 + sx * 0.13, 0.25, -0.006)))])
    arm = person('Hiker', loc=(0.35, 0.3, 0.03), rot_z=math.radians(8), outfit='worker')
    pose(arm, 0.0, STANCES['relax'])
    camera([(0, (1.7, -3.3, 0.95), (-0.05, 0.4, 0.55)), (d, (1.55, -3.0, 0.9), (-0.05, 0.4, 0.55))], lens=30, fstop=4.5)

def S04(a, b):  # winter cut-away: frost creeps down into the soil and ice lenses grow in it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter(1.4, 18, 150)
    fy = -1.0
    soil_block(M, (14, 8, 2.2), fy)
    box('SnowCap', (14, 8, 0.09), (0, fy + 4, 0.045), M['snow'])
    plane('PitFloor', 14, 6, (0, fy - 3, -2.2), M['mud'])
    frost_face(M, fy, -1.2, 1.2, 0.0, 0.62, seed=5, lenses=18, t_grow=(0.2, d - 0.6))
    light('AREA', (-1.0, -3.0, 0.8), 160, (0.85, 0.9, 1.0), 2.0, rot=(math.radians(75), 0, math.radians(-15)))
    camera([(0, (0.35, -3.0, 0.05), (0, fy, -0.32)), (d, (0.25, -2.75, 0.0), (0, fy, -0.34))], lens=30, fstop=6)

def S05(a, b):  # frost heave: the shallow footing is lifted by ice below it, the foundation and siding crack, a worker points
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter(1.6, 20, 140)
    W, D = 6.0, 5.0; hy = 2.5   # house centre; front wall at y=0
    pit = [((2.4, 1.42, 1.5), (1.8, -0.89, -0.75))]
    g = ground(M['soil'], cuts=pit, loc=(0, 0))
    sn = box('SnowLayer', (60, 60, 0.06), (0, 0, 0.03), M['snow']); cut(sn, (2.4, 1.42, 0.4), (1.8, -0.89, 0.0))
    rig = bpy.data.objects.new('Heave', None); link(rig)
    h = house(M); h.parent = rig; h.location = (0, hy, 0.3)
    for o in foundation(M, W, D, top=0.3, bottom=-0.5): o.parent = rig; o.location.y += hy
    th0, th1 = 0.4, 2.0
    key(rig, 'location', [(0, Vector((0, 0, 0))), (th0, Vector((0, 0, 0))), (th1, Vector((0, 0, 0.055))), (d, Vector((0, 0, 0.07)))])
    key(rig, 'rotation_euler', [(0, Vector((0, 0, 0))), (th0, Vector((0, 0, 0))), (th1, Vector((0, math.radians(-0.7), 0))), (d, Vector((0, math.radians(-0.9), 0)))])
    frost_face(M, -0.18, 0.65, 2.95, 0.0, 0.95, seed=8, lenses=14)
    # cracks: on the stem wall above ground and up the siding from the window corner
    segs = [((1.55, -0.003, 0.24), 0.11, 25), ((1.6, -0.003, 0.14), 0.1, -30), ((1.57, -0.003, 0.05), 0.1, 20),
            ((1.18, -0.004, 0.75), 0.4, 35), ((1.05, -0.004, 1.05), 0.3, -15)]
    for (p, L, ang) in segs:
        c = box('Crack', (0.006, 0.004, L), (0, 0, 0), M['dark']); c.parent = rig
        c.location = (p[0], p[1], p[2] + (0.3 if p[2] > 0.5 else 0.0)); c.rotation_euler = (0, math.radians(ang), 0)
        key(c, 'scale', [(0, Vector((1, 1, 0.001))), (1.95, Vector((1, 1, 0.001))), (2.25, Vector((1, 1, 1)))])
    arm = person('Worker', loc=(0.75, -1.85, 0.06), rot_z=math.radians(70), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.1, STANCES['relax']); pose(arm, 2.9, STANCES['point_r'])
    light('AREA', (1.6, -3.0, 1.2), 300, (0.9, 0.93, 1.0), 2.5, rot=(math.radians(60), 0, 0))
    camera([(0, (1.3, -4.0, 1.3), (1.35, -0.2, -0.25)), (d, (1.35, -3.75, 1.25), (1.4, -0.2, -0.28))], lens=22, fstop=6)

def S06(a, b):  # deep cut-away: frozen top layer, the foundation wall runs down past it to a wide footing below
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter(1.4, 18, 150)
    fy = -1.0
    soil_block(M, (14, 8, 2.6), fy)
    box('SnowCap', (14, 8, 0.09), (0, fy + 4, 0.045), M['snow'])
    plane('PitFloor', 14, 6, (0, fy - 3, -2.6), M['mud'])
    frost_face(M, fy, -1.5, 1.5, 0.0, 1.0, seed=11, lenses=30, skip=(-0.12, 0.12))
    # inverted-T foundation section flush (+1 cm) with the cut face, wall running back into the soil
    box('StemSec', (0.2, 5.0, 1.85), (0, fy + 2.5 - 0.01, 0.3 - 1.85 / 2), M['conc'])
    box('FootSec', (0.6, 5.0, 0.3), (0, fy + 2.5 - 0.01, -1.55 - 0.15), M['conc'])
    box('Sill', (0.2, 5.0, 0.04), (0, fy + 2.5, 0.32), M['wood'])
    box('WallSec', (0.16, 5.0, 2.6), (0, fy + 2.5 + 0.02, 0.34 + 1.3), M['siding'])
    for k in range(2): cyl('RebarSec', 0.008, 5.0, (-0.15 + 0.3 * k, fy + 2.5, -1.62), M['rebar'], rot=(math.radians(90), 0, 0), verts=12)
    light('AREA', (-1.0, -3.0, 0.5), 220, (0.85, 0.9, 1.0), 2.5, rot=(math.radians(80), 0, math.radians(-15)))
    camera([(0, (0.55, -3.3, 0.75), (0, fy, 0.05)), (d, (0.5, -3.15, -0.55), (0, fy, -1.2))], lens=26, fstop=7)

def S07(a, b):  # northern Minnesota: a worker stands on the footing five feet down in a snowy excavation, a grade rod beside him
    sc = new_scene(a, b); d = dur(a, b); M = mats(); winter(1.7, 22, 135)
    Z = -1.524
    pit = ((5.0, 4.0, 3.0), (0, 1.5, Z - 1.5 + 3.0 / 2 * 0 + 0.0))
    g = ground(M['sub'], cuts=[((5.0, 4.0, 3.2), (0, 1.5, Z + 1.6))])
    sn = box('SnowLayer', (60, 60, 0.1), (0, 0, 0.05), M['snow']); cut(sn, (5.0, 4.0, 0.6), (0, 1.5, 0.0))
    plane('PitFloor', 5.0, 4.0, (0, 1.5, Z + 0.002), M['mud'])
    box('Footing', (5.0, 0.6, 0.3), (0, 3.2, Z + 0.15), M['conc'])
    for x in (-2.0, -1.2, -0.4, 0.4, 1.2, 2.0):
        cyl('Dowel', 0.008, 0.5, (x, 3.2, Z + 0.55), M['rebar'], verts=12)
    # grade rod with 1-foot bands
    for k in range(6):
        col = (0.75, 0.06, 0.04) if k % 2 == 0 else (0.9, 0.9, 0.88)
        box('RodBand', (0.06, 0.03, 0.3048), (-1.0, 0.9, Z + 0.1524 + k * 0.3048), mat_simple('Band%d' % (k % 2), col, 0.4)[0])
    arm = person('Worker', loc=(-0.15, 1.2, Z), rot_z=math.radians(-12), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.8, STANCES['relax']); pose(arm, 1.6, {'neck01': (-10, 0, 0)})
    camera([(0, (0.9, -1.75, 0.95), (-0.35, 1.5, -0.8)), (d, (0.8, -1.55, 0.85), (-0.35, 1.5, -0.8))], lens=24, fstop=6)

def S08(a, b):  # studio: a plain concrete beam on two supports is pressed in the middle; it cracks open at the bottom
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.3, 0, 'studio'); studio_lights(380, 260)
    plane('Floor', 20, 20, (0, 0, -0.35), M['studio'])
    for sx in (-1, 1):
        box('Support', (0.12, 0.3, 0.35), (sx * 0.72, 0, -0.175), M['steel'], bevel=0.005)
    piv = bpy.data.objects.new('Pivot', None); link(piv); piv.location = (0, 0, 0.15)
    halves = []
    for sx in (-1, 1):
        hp = bpy.data.objects.new('HalfPivot', None); link(hp); hp.parent = piv
        hb = box('BeamHalf', (0.8, 0.15, 0.15), (0, 0, 0), M['conc']); hb.parent = hp; hb.location = (sx * 0.4, 0, -0.075)
        halves.append((hp, sx))
    tc = 0.95
    def ang(t):
        if t < 0.25: return 0.0
        if t < tc: return 0.35 * (t - 0.25) / (tc - 0.25)
        return 2.4
    for hp, sx in halves:
        key(hp, 'rotation_euler', [(0, Vector((0, 0, 0))), (0.25, Vector((0, 0, 0))), (tc, Vector((0, -sx * math.radians(0.35), 0))), (tc + 0.08, Vector((0, -sx * math.radians(2.4), 0))), (d, Vector((0, -sx * math.radians(2.6), 0)))])
    drop = lambda t: 0.78 * math.sin(math.radians(ang(t)))
    key(piv, 'location', [(0, Vector((0, 0, 0.15))), (0.25, Vector((0, 0, 0.15))), (tc, Vector((0, 0, 0.15 - drop(tc - 0.01)))), (tc + 0.08, Vector((0, 0, 0.15 - drop(tc + 0.1)))), (d, Vector((0, 0, 0.15 - 0.78 * math.sin(math.radians(2.6)))))])
    ram = box('Ram', (0.1, 0.18, 0.8), (0, 0, 0.55), mat_simple('RamSteel', (0.18, 0.19, 0.2), 0.45, 0.8)[0], bevel=0.004)
    key(ram, 'location', [(0, Vector((0, 0, 0.72))), (0.25, Vector((0, 0, 0.55))), (tc, Vector((0, 0, 0.55 - drop(tc - 0.01)))), (tc + 0.08, Vector((0, 0, 0.55 - drop(tc + 0.1)))), (d, Vector((0, 0, 0.55 - 0.78 * math.sin(math.radians(2.6)))))])
    random.seed(4)
    for i in range(18):   # concrete grit falling out of the crack
        s = sphere('Grit', random.uniform(0.003, 0.007), (0, 0, 0), M['conc'], sub=1)
        p0 = Vector((random.uniform(-0.01, 0.01), random.uniform(-0.07, 0.07), -0.0)); tb = tc + random.uniform(0.0, 0.5)
        key(s, 'location', [(0, p0), (tb, p0), (tb + 0.4, p0 + Vector((random.uniform(-0.05, 0.05), random.uniform(-0.08, 0.02), -0.33)))], interp='LINEAR')
        key(s, 'scale', [(0, Vector((0, 0, 0))), (tb - 0.01, Vector((0, 0, 0))), (tb, Vector((1, 1, 1)))])
    camera([(0, (0.32, -1.45, 0.2), (0, 0, 0.04)), (d, (0.22, -1.3, 0.16), (0, 0, 0.02))], lens=32, fstop=3.2)

def S09(a, b):  # rebar on chairs in the footing trench, a worker bends over to tie it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(110, elev=36, azim=110)
    ground(M['mud'], cuts=[((14, 0.7, 0.62), (0, 0, -0.29))])
    plane('TrenchFloor', 14, 0.7, (0, 0, -0.598), M['soil'])
    for y in (-0.2, 0.0, 0.2):
        cyl('Bar', 0.008, 12, (0, y, -0.5), M['rebar'], rot=(0, math.radians(90), 0), verts=12)
    x = -6.0
    while x < 6.0:
        cyl('Cross', 0.006, 0.6, (x, 0, -0.485), M['rebar'], rot=(math.radians(90), 0, 0), verts=10)
        if int((x + 6) / 0.6) % 2 == 0:
            for y in (-0.2, 0.2): box('Chair', (0.04, 0.04, 0.09), (x, y, -0.555), M['conc'])
        x += 0.6
    piles(M, [(-1.5, 1.5, 1.4, 0.7, 0.4), (2.5, 1.7, 1.4, 0.8, 0.45)], M['mud'])
    arm = person('Worker', loc=(-0.35, 0.78, 0), rot_z=math.radians(-15), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.6, STANCES['work_low']); pose(arm, d, STANCES['work_low'])
    camera([(0, (1.25, -0.62, 0.55), (-0.3, 0.2, -0.42)), (d, (1.05, -0.58, 0.5), (-0.3, 0.2, -0.45))], lens=26, fstop=4)

def S10(a, b):  # storm: rain and a lightning flash, the wooden house is shoved sideways off its concrete base
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_overcast_puresky', 0.35, 0, 'overcast')
    sn = sun(0.6, 30, 160, color=(0.85, 0.9, 1.0))
    key_light(sn.data, 'energy', [(0, 0.6), (0.35, 0.6), (0.4, 9.0), (0.5, 0.8), (0.58, 6.0), (0.75, 0.6)])
    g = plane('Lawn', 90, 90, (0, 0, 0), mat_textured('WetLawn', ['sparse_grass'], 0.45, (0.12, 0.2, 0.07), rough=(0.5, 0.8))[0])
    for o in foundation(M, 6.0, 5.0, top=0.35, bottom=-1.2): o.location.y += 2.0
    rig = house(M); rig.location = (0, 2.0, 0.35)
    t0, t1 = 1.1, 2.1
    key(rig, 'location', [(0, Vector((0, 2.0, 0.35))), (t0, Vector((0, 2.0, 0.35))), (t1, Vector((0.75, 2.0, 0.35))), (t1 + 0.25, Vector((0.95, 2.0, 0.3))), (d, Vector((1.0, 2.0, 0.28)))])
    key(rig, 'rotation_euler', [(0, Vector((0, 0, 0))), (t0, Vector((0, 0, 0))), (t1, Vector((0, math.radians(1.0), math.radians(1.5)))), (t1 + 0.25, Vector((0, math.radians(2.6), math.radians(1.8))))])
    for k, (y, s) in enumerate(((-5.5, 0.7), (-2.5, 0.5), (1.0, 0.35))):
        r = plane('Rain', 14, 9, (0, y, 3.5), mat_rain('Rain%d' % k, s, 34 + 6 * k, d))
        r.rotation_euler = (math.radians(90), math.radians(12), 0)
    camera([(0, (-1.8, -10.5, 1.3), (0.4, 1.5, 1.6)), (d, (-1.6, -10.0, 1.3), (0.5, 1.5, 1.6))], lens=26, fstop=None)

def S11(a, b):  # close-up: J-bolts stick up from the foundation; a wooden sill plate drops over them, washers and nuts lock it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(40, elev=35, azim=130)
    ground(M['mud'])
    box('Stem', (8, 0.2, 1.5), (0, 0, 0.35 - 0.75), M['wetconc'])
    bolts = (-0.45, 0.75)
    for x in bolts:
        cyl('JBolt', 0.0065, 0.2, (x, 0, 0.35 + 0.1 - 0.02), M['steel'], verts=16)
    pl = box('SillPlate', (2.4, 0.14, 0.038), (0, 0, 0), M['wood'])
    for x in bolts:
        hc = cyl('Hole', 0.009, 0.2, (x, 0, 0), None, verts=16); hc.hide_render = True; hc.display_type = 'WIRE'; hc.parent = pl; hc.location = (x, 0, 0)
        md = pl.modifiers.new('hole', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = hc
    ts = 1.7
    key(pl, 'location', [(0, Vector((0, 0, 0.95))), (0.3, Vector((0, 0, 0.95))), (ts, Vector((0, 0, 0.35 + 0.019)))])
    for x in bolts:
        w = cyl('Washer', 0.026, 0.004, (x, 0, 0), M['steel'], verts=32)
        n = cyl('Nut', 0.013, 0.011, (x, 0, 0), M['steel'], verts=6)
        zt = 0.35 + 0.038 + 0.002
        key(w, 'location', [(0, Vector((x, 0, 0.75))), (ts + 0.2, Vector((x, 0, 0.75))), (ts + 0.8, Vector((x, 0, zt)))])
        key(n, 'location', [(0, Vector((x, 0, 0.8))), (ts + 0.4, Vector((x, 0, 0.8))), (ts + 1.0, Vector((x, 0, zt + 0.0075 + 0.01))), (d, Vector((x, 0, zt + 0.0075)))])
        key(n, 'rotation_euler', [(ts + 1.0, Vector((0, 0, 0))), (d, Vector((0, 0, math.radians(300))))], interp='LINEAR')
    camera([(0, (0.32, -0.62, 0.52), (-0.35, 0, 0.36)), (d, (0.22, -0.55, 0.47), (-0.42, 0, 0.36))], lens=40, fstop=2.8)

def S12(a, b):  # studio diorama orbit: house on its foundation, footings below the frozen layer of soil
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.35, 0, 'studio'); studio_lights()
    plane('Floor', 30, 30, (0, 0, -1.0), M['studio'])
    s = 0.3; fy = -0.745
    soil_block(M, (3.0, 2.0, 1.0), fy, topsoil=0.12)
    box('SnowCap', (3.0, 2.0, 0.025), (0, fy + 1.0, 0.0125), M['snow'])
    frost_face(M, fy, -1.5, 1.5, 0.0, 0.3, seed=3, lenses=20, skip=(-0.95, 0.95))
    rig = house(M); rig.scale = (s, s, s); rig.location = (0, 0, 0.1)
    for o in foundation(M, 6.0 * s, 5.0 * s, top=0.1, bottom=-0.55, ft=0.09, fw=0.18, tw=0.06): o.location.y += 0.0
    camera([(0, (-1.9, -3.6, 0.75), (0, 0, -0.1)), (d, (1.7, -3.7, 0.5), (0, 0, -0.12))], lens=26, fstop=6.5)

def S13(a, b):  # dusk: the finished house with warm windows; a cut-away in the lawn reveals the concrete foot under it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.7, math.radians(200)); sun(1.4, 6, 200, color=(1, 0.72, 0.45))
    hy = 3.0; Dd = 5.0; fy = hy - Dd / 2      # front wall y = 0.5
    g = ground(M['soil'], cuts=[((5.0, 2.0, 1.5), (0, fy - 0.16 - 1.0, -0.75)), ((5.0, 2.0, 0.95), (0, fy + 0.02 - 1.0, -0.475))])
    lawn = box('LawnTop', (60, 60, 0.05), (0, 0, -0.02), M['grass'])
    cut(lawn, (5.0, 2.0, 0.4), (0, fy + 0.02 - 1.0, 0.0))
    for o in foundation(M, 6.0, Dd, top=0.3, bottom=-1.2): o.location.y += hy
    rig = house(M, lit=3.5); rig.location = (0, hy, 0.3)
    l = light('POINT', (0, fy - 0.6, 2.4), 60, (1, 0.75, 0.45), 0.2)
    plane('PitFloor', 5.0, 2.0, (0, -0.66, -1.49), M['mud'])
    lc = light('AREA', (0.0, -1.3, -0.25), 260, (0.85, 0.9, 1.0), 1.5); aim(lc, (0.0, 0.4, -0.95))
    arm = person('Owner', loc=(-2.0, -2.6, 0), rot_z=math.radians(160), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.5, {'neck01': (-6, 0, 0)})
    camera([(0, (-1.9, -8.4, 2.0), (0.1, 0.3, -0.2)), (d, (-1.7, -7.6, 1.9), (0.1, 0.3, -0.25))], lens=24, fstop=8)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13]

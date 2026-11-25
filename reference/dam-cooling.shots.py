# Shots for "Why Hoover Dam Is Full of Pipes" (mass-concrete heat, cooling pipes, grouted columns). One function per line.
# Z up, metres. Person faces -Y at rot_z=0. t = seconds from the shot start.
import bmesh

def dur(a, b): return (b - a) / FPS

LIFT = 1.524   # 5 ft

# ---------------------------------------------------------------- materials
def lift_mat(name, tid, scale, tint, period=LIFT, line=0.6):
    """Concrete with a darker horizontal pour line every 5-ft lift (world Z)."""
    m, p = mat_textured(name, [tid], scale, (0.62, 0.61, 0.58), rough=(0.7, 0.95), tint=tint)
    nt = m.node_tree
    bc = p.inputs['Base Color']
    src = bc.links[0].from_socket if bc.links else None
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 2 * math.pi / (10 * period)
    try: wv.inputs['Distortion'].default_value = 0.6
    except Exception: pass
    nt.links.new(geo.outputs['Position'], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    e0, e1 = ramp.color_ramp.elements; e0.position = 0.0; e1.position = 0.035
    e0.color = (line, line, line, 1); e1.color = (1, 1, 1, 1)
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
    if src: nt.links.new(src, mix.inputs[6])
    else: mix.inputs[6].default_value = (0.6, 0.6, 0.58, 1)
    nt.links.new(ramp.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], bc)
    return m

def mats():
    M = {}
    M['conc'] = lift_mat('Concrete', 'concrete_floor_worn_001', 0.18, (1.45, 1.42, 1.34))
    M['conc_plain'] = mat_textured('ConcPlain', ['concrete_floor_worn_001'], 0.35, (0.6, 0.6, 0.58), tint=(1.4, 1.38, 1.3))[0]
    M['fresh'] = mat_textured('Fresh', ['concrete_floor_02'], 0.5, (0.45, 0.45, 0.44), rough=(0.3, 0.55), tint=(0.78, 0.78, 0.76), wet=0.35)[0]
    M['rock'] = mat_textured('Rock', ['rocky_terrain_02'], 0.18, (0.4, 0.3, 0.24), rough=(0.75, 1.0), bump=1.0, tint=(1.15, 0.82, 0.64))[0]
    M['floor'] = mat_textured('CanyonFloor', ['dry_ground_rocks'], 0.12, (0.4, 0.32, 0.25), rough=(0.8, 1.0), tint=(0.95, 0.82, 0.7))[0]
    M['wood'] = mat_textured('Forms', ['plywood'], 0.5, (0.7, 0.55, 0.38), rough=(0.6, 0.85), tint=(0.95, 0.85, 0.7))[0]
    M['rust'] = mat_textured('PipeSteel', ['rusty_metal_02'], 2.0, (0.25, 0.15, 0.1), rough=(0.5, 0.8), tint=(0.7, 0.62, 0.58))[0]
    M['steel'] = mat_simple('Steel', (0.5, 0.51, 0.52), 0.35, 1.0)[0]
    M['black'] = mat_simple('BlackPipe', (0.03, 0.03, 0.03), 0.4, 0.6)[0]
    M['dark'] = mat_simple('Crack', (0.006, 0.006, 0.006), 0.95)[0]
    M['frost'] = mat_simple('Frost', (0.9, 0.93, 0.97), 0.85, sss=0.2)[0]
    M['grout'] = mat_simple('Grout', (0.42, 0.42, 0.41), 0.35, coat=0.3)[0]
    M['hose'] = mat_simple('Hose', (0.02, 0.02, 0.02), 0.6)[0]
    M['water'] = mat_simple('Water', (0.02, 0.06, 0.07), 0.04, coat=1.0)[0]
    M['hdpe'] = mat_simple('HDPE', (0.05, 0.22, 0.55), 0.35)[0]
    M['rebar'] = mat_simple('Rebar', (0.2, 0.09, 0.05), 0.7, 0.4)[0]
    M['studio'] = mat_simple('StudioFloor', (0.045, 0.045, 0.05), 0.55)[0]
    M['ice'] = mat_simple('Ice', (0.85, 0.93, 1.0), 0.08, trans=0.7, ior=1.31)[0]
    M['rail'] = mat_simple('Rail', (0.3, 0.3, 0.28), 0.5, 0.8)[0]
    return M

def heat_face(name, w, h, loc, strength_pts, spread=1.55, rot=None, base=(0.32, 0.31, 0.29)):
    """A cut face (plane facing -Y) that glows red-orange from the centre outwards = hot concrete core."""
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (spread / w, spread / h, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
    nt.links.new(mp.outputs['Vector'], gr.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0, 0, 0, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (1.0, 0.45, 0.06, 1)
    e = cr.elements.new(0.3); e.color = (0.25, 0.008, 0.0, 1)
    e = cr.elements.new(0.65); e.color = (0.9, 0.12, 0.005, 1)
    nt.links.new(gr.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], inp(p, 'Emission Color', 'Emission'))
    # concrete look where it is cool
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 3.0; n.inputs['Detail'].default_value = 10
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    r2 = nt.nodes.new('ShaderNodeValToRGB')
    r2.color_ramp.elements[0].color = (*[c * 0.7 for c in base], 1); r2.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(n.outputs['Fac'], r2.inputs['Fac'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.clamp_factor = True
    fm = nt.nodes.new('ShaderNodeMath'); fm.operation = 'MULTIPLY'; fm.inputs[1].default_value = 2.2; fm.use_clamp = True
    nt.links.new(gr.outputs['Fac'], fm.inputs[0]); nt.links.new(fm.outputs['Value'], mx.inputs['Factor'])
    nt.links.new(r2.outputs['Color'], mx.inputs[6]); mx.inputs[7].default_value = (0.02, 0.015, 0.012, 1)
    nt.links.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    key_socket(inp(p, 'Emission Strength'), strength_pts)
    o = plane(name, w, h, loc, m)
    o.rotation_euler = rot or (math.radians(90), 0, 0)
    return o

# ---------------------------------------------------------------- geometry kit
def rock_wall(M, x, side, L=400, H=160, y0=0, seed=1, strength=7.0):
    """Displaced vertical rock face at x, facing the canyon centre (side=-1 left wall faces +X)."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=70, size=1)
    o = bpy.context.active_object; o.name = 'RockWall'
    o.scale = (H, L, 1); bpy.ops.object.transform_apply(scale=True)
    o.rotation_euler = (0, math.radians(-90 * side), 0)
    o.location = (x, y0, H / 2 - 3)
    tex = bpy.data.textures.new('rockN%d' % seed, 'CLOUDS'); tex.noise_scale = 9.0; tex.noise_depth = 4
    dm = o.modifiers.new('disp', 'DISPLACE'); dm.texture = tex; dm.strength = strength * 0.7; dm.mid_level = 0.5
    dm.texture_coords = 'GLOBAL'
    tex2 = bpy.data.textures.new('rockS%d' % seed, 'CLOUDS'); tex2.noise_scale = 2.0; tex2.noise_depth = 2
    dm2 = o.modifiers.new('disp2', 'DISPLACE'); dm2.texture = tex2; dm2.strength = 1.2; dm2.texture_coords = 'GLOBAL'
    o.data.materials.append(M['rock'])
    bpy.ops.object.shade_smooth()
    return o

def canyon(M, half=32, L=500, H=95, y0=60):
    rock_wall(M, -half - 3, -1, L, H, y0, 1)
    rock_wall(M, half + 3, 1, L, H, y0, 2)
    plane('Floor', 2 * half + 30, L, (0, y0, 0), M['floor'])

def arc_dam(M, R=80.0, half_ang=26, H=60.0, base_t=30.0, top_t=10.0, n=48, mat=None):
    """Curved concrete arch-gravity dam. Upstream (reservoir) side = +Y. Returns object."""
    cy = -R + 6.0   # centre of curvature downstream
    prof = [(R, 0.0), (R, H), (R - top_t, H), (R - top_t, H * 0.9), (R - base_t, 0.0)]
    verts = []; k = len(prof)
    for i in range(n + 1):
        a = math.radians(-half_ang + 2 * half_ang * i / n)
        for (r, z) in prof: verts.append((r * math.sin(a), cy + r * math.cos(a), z))
    faces = []
    for i in range(n):
        for j in range(k):
            jj = (j + 1) % k
            faces.append((i * k + j, i * k + jj, (i + 1) * k + jj, (i + 1) * k + j))
    faces.append(tuple(range(k))); faces.append(tuple(range(n * k + k - 1, n * k - 1, -1)))
    me = bpy.data.meshes.new('Dam'); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('Dam', me); link(o); o.data.materials.append(mat or M['conc'])
    return o

def column_grid(M, nx=8, ny=5, s=7.0, gap=0.06, y0=0.0, seed=3, hmin=4, hmax=12, forms=()):
    random.seed(seed); out = {}
    x0 = -(nx - 1) * (s + gap) / 2
    for i in range(nx):
        for j in range(ny):
            h = LIFT * random.randint(hmin, hmax)
            if j == 0: h = LIFT * random.randint(hmin, hmin + 3)
            x = x0 + i * (s + gap); y = y0 + j * (s + gap)
            out[(i, j)] = (box('Col', (s, s, h), (x, y, h / 2), M['conc'], bevel=0.03, segs=1), x, y, h)
    for (i, j) in forms:
        _, x, y, h = out[(i, j)]
        for sx, sy, w, dd in ((0, -1, s, 0.05), (0, 1, s, 0.05), (-1, 0, 0.05, s), (1, 0, 0.05, s)):
            box('Form', (w + 0.1, dd + 0.05, LIFT * 0.9), (x + sx * s / 2, y + sy * s / 2, h + LIFT * 0.45), M['wood'])
    return out

def bucket(M, loc, z_pts=None, cable_top=140):
    rig = bpy.data.objects.new('Bucket', None); link(rig); rig.location = loc
    b = cyl('BucketBody', 1.1, 2.2, (0, 0, 0), M['rust'], verts=40); b.parent = rig
    cone = cyl('BucketCone', 0.5, 0.6, (0, 0, -1.4), M['rust'], verts=24); cone.parent = rig
    bl = cyl('Bail', 0.05, 2.6, (0, 0, 1.7), M['steel'], rot=(0, math.radians(90), 0), verts=10); bl.parent = rig
    for sx in (-1, 1):
        a = cyl('BailArm', 0.05, 1.0, (sx * 1.2, 0, 1.3), M['steel'], verts=10); a.parent = rig
    c = cyl('Cable', 0.03, cable_top, (0, 0, 1.7 + cable_top / 2), M['steel'], verts=8); c.parent = rig
    if z_pts: key(rig, 'location', z_pts)
    return rig

def pipe_run(M, pts, r=0.0127, mat=None, t_grow=None):
    """Polyline pipe (thin, 1 inch) along (x, y, z) points via a curve with bevel."""
    cu = bpy.data.curves.new('Pipe', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for k, p in enumerate(pts): sp.points[k].co = (*p, 1)
    o = bpy.data.objects.new('Pipe', cu); link(o); o.data.materials.append(mat or M['black'])
    if t_grow:
        t0, t1 = t_grow
        cu.bevel_factor_end = 0.0; cu.keyframe_insert('bevel_factor_end', frame=F(t0))
        cu.bevel_factor_end = 1.0; cu.keyframe_insert('bevel_factor_end', frame=F(t1))
    return o

def serpentine(x0, x1, y0, dy, n, z, bend=0.35):
    pts = []
    for k in range(n):
        y = y0 + k * dy
        a, b = (x0, x1) if k % 2 == 0 else (x1, x0)
        pts.append((a, y, z)); pts.append((b, y, z))
    return pts

def day(rot=30, sun_e=2.2, elev=42, azim=150, hdri=0.8):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', hdri, math.radians(rot)); sun(sun_e, elev, azim)

def dusk(rot=0, sun_e=1.6, elev=8, azim=200):
    world_hdri('qwantani_dusk_2_puresky', 0.75, math.radians(rot)); sun(sun_e, elev, azim, color=(1, 0.72, 0.45))

def studio_lights(key_e=500, rim_e=300):
    k = light('AREA', (-2.2, -3.0, 2.6), key_e, (1, 0.96, 0.9), 2.5); aim(k, (0, 0, 0))
    r = light('AREA', (2.6, 2.0, 2.2), rim_e, (0.85, 0.9, 1.0), 2.0); aim(r, (0, 0, 0))
    f = light('AREA', (1.5, -3.5, 0.2), key_e * 0.25, (1, 1, 1), 2.0); aim(f, (0, 0, -0.3))

# ================================================================ shots
def S00(a, b):  # dusk canyon: one giant concrete monolith fills it; its face starts to glow hot; a worker looks up at it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); dusk(rot=math.radians(0))
    canyon(M, half=32)
    W, H, T = 70.0, 75.0, 40.0
    box('Monolith', (W, T, H), (0, T / 2, H / 2), M['conc_plain'])
    heat_face('HotCore', 62, 70, (0, -0.06, 36), [(0, 0.0), (0.6, 0.1), (d * 0.65, 1.8), (d, 2.2)], spread=1.7)
    arm = person('Worker', loc=(2.6, -27.0, 0), rot_z=math.radians(185), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.6, STANCES['relax']); pose(arm, 2.6, {'neck01': (-14, 0, 0), 'spine02': (-6, 0, 0)})
    camera([(0, (5.5, -34.0, 1.4), (0.5, 0, 16.0)), (d, (4.8, -32.0, 1.3), (0.5, 0, 24.0))], lens=18, fstop=11)

def S01(a, b):  # studio: a block of fresh concrete cut in half; its core heats up and glows; a thermometer probe sits in it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.35, 0, 'studio'); studio_lights(420, 280)
    plane('Floor', 30, 30, (0, 0, 0), M['studio'])
    box('Block', (1.2, 1.0, 1.0), (0, 0.5, 0.5), M['fresh'], bevel=0.01, segs=2)
    heat_face('CutFace', 1.2, 1.0, (0, -0.003, 0.5), [(0, 0.15), (d, 2.0)], spread=1.7, base=(0.4, 0.4, 0.39))
    pr = cyl('Probe', 0.012, 0.55, (0.32, 0.45, 1.15), M['steel'], verts=16)
    box('Meter', (0.16, 0.06, 0.24), (0.32, 0.45, 1.5), mat_simple('MeterBody', (0.85, 0.35, 0.05), 0.5)[0], bevel=0.01)
    box('MeterLCD', (0.11, 0.01, 0.06), (0.32, 0.418, 1.55), mat_emit('LCD', (0.6, 1.0, 0.75), 1.5)[0])
    camera([(0, (-1.2, -2.6, 1.1), (0, 0.2, 0.55)), (d, (-0.9, -2.35, 1.0), (0, 0.2, 0.55))], lens=40, fstop=4)

def S02(a, b):  # site: a big slab, hot core glowing in the cut face, the cold outside cracks; a worker points at the cracks
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(40, elev=35, azim=140)
    plane('Ground', 200, 200, (0, 0, 0), M['floor'])
    W, T, H = 9.0, 6.0, 4.5
    box('Slab', (W, T, H), (0, T / 2, H / 2), M['conc_plain'])
    heat_face('HotCore', W - 0.02, H - 0.02, (0, -0.01, H / 2), [(0, 1.9), (d, 1.7)], spread=1.6)
    segs = [((-2.6, H + 0.002, 4.0), 1.8, 20), ((-1.0, H + 0.002, 3.6), 1.4, -35), ((1.2, H + 0.002, 4.5), 2.2, 70),
            ((2.8, H + 0.002, 2.5), 1.6, 15)]
    for (p, L, ang) in segs:   # cracks across the top surface
        c = box('Crack', (0.03, L, 0.01), (p[0], p[2], H + 0.003), M['dark']); c.rotation_euler = (0, 0, math.radians(ang))
        key(c, 'scale', [(0, Vector((1, 0.001, 1))), (2.9, Vector((1, 0.001, 1))), (3.3, Vector((1, 1, 1)))])
    for (x, z, L, ang) in ((-3.9, 3.2, 1.3, 10), (3.85, 1.1, 1.2, -15), (-3.8, 1.5, 0.9, 25)):  # edge cracks on the face
        c = box('FaceCrack', (0.035, 0.03, L), (x, -0.03, z), M['dark']); c.rotation_euler = (0, math.radians(ang), 0)
        key(c, 'scale', [(0, Vector((1, 1, 0.001))), (2.9, Vector((1, 1, 0.001))), (3.3, Vector((1, 1, 1)))])
    arm = person('Worker', loc=(-4.6, -2.6, 0), rot_z=math.radians(-60), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.6, STANCES['relax']); pose(arm, 3.4, STANCES['point_r'])
    camera([(0, (-2.0, -13.5, 4.8), (-0.8, 1.5, 2.4)), (d, (-1.6, -12.6, 4.9), (-0.8, 1.5, 2.4))], lens=26, fstop=8)

def S03(a, b):  # Black Canyon: a grid of concrete columns at different heights, forms on top, a bucket of concrete comes down
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(60, elev=55, azim=20)
    canyon(M, half=32)
    cols = column_grid(M, nx=8, ny=6, s=7.0, y0=0.0, seed=5, hmin=5, hmax=13, forms=((3, 1), (4, 2), (2, 3), (5, 1)))
    _, bx, by, bh = cols[(4, 2)]
    bucket(M, (bx, by, bh + 9), [(0, Vector((bx, by, bh + 11))), (d, Vector((bx, by, bh + 5.5)))])
    _, wx, wy, wh = cols[(3, 0)]
    arm = person('Worker', loc=(wx + 1.0, wy - 1.5, wh), rot_z=math.radians(165), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.0, {'neck01': (-10, 0, 0)})
    camera([(0, (wx + 9.0, wy - 26.0, wh + 10.0), (bx - 2, by + 6, bh - 2)), (d, (wx + 8.0, wy - 24.0, wh + 10.5), (bx - 2, by + 6, bh - 1))],
           lens=22, fstop=11)

def S04(a, b):  # one column, cut open: the core is still glowing hot, a worker stands beside it for scale
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(80, elev=40, azim=120)
    plane('Ground', 200, 200, (0, 0, 0), M['floor'])
    S, H = 7.0, 9.0
    box('Column', (S, S, H), (0, S / 2, H / 2), M['conc'])
    heat_face('HotCore', S - 0.02, H - 0.02, (0, -0.01, H / 2), [(0, 1.7), (d, 1.9)], spread=1.6)
    for k in range(1, 6):   # lift lines on the cut face
        box('LiftLine', (S, 0.02, 0.03), (0, -0.02, k * LIFT), M['dark'])
    arm = person('Worker', loc=(-4.6, -0.9, 0), rot_z=math.radians(-50), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.2, {'neck01': (-8, 0, 6)})
    camera([(0, (-5.0, -14.0, 2.4), (-0.6, 2.0, 4.2)), (d, (-4.4, -13.2, 2.5), (-0.6, 2.0, 4.3))], lens=24, fstop=8)

def S05(a, b):  # top of a column: rows of 1-inch steel pipe laid in loops across fresh concrete; a worker lays one
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(20, elev=58, azim=25)
    canyon(M, half=32)
    box('ColTop', (7.0, 7.0, 6.0), (0, 0, 3.0), M['conc'])
    plane('FreshTop', 6.96, 6.96, (0, 0, 6.003), M['fresh'])
    for k, sx, sy, w, dd in ((0, 0, -1, 7.0, 0.05), (1, 0, 1, 7.0, 0.05), (2, -1, 0, 0.05, 7.0), (3, 1, 0, 0.05, 7.0)):
        box('Form', (w + 0.1, dd + 0.05, 0.6), (sx * 3.52, sy * 3.52, 6.3), M['wood'])
    for x in (-8.0, 8.0):
        box('NextCol', (7.0, 7.0, 9.0), (x, 0, 4.5), M['conc'])
    z = 6.0 + 0.012
    pts = serpentine(-3.2, 3.2, -3.0, 0.9, 7, z)
    pipe_run(M, pts, r=0.03, mat=M['black'], t_grow=(0.2, d - 0.8))
    pipe_run(M, [(3.2, -3.0, z), (3.6, -3.0, z), (3.6, -3.0, 6.6), (3.6, -4.5, 6.6)], r=0.03, mat=M['black'])
    arm = person('Worker', loc=(-1.0, -2.0, 6.0), rot_z=math.radians(20), outfit='worker')
    pose(arm, 0.0, STANCES['work_low']); pose(arm, d, {'spine02': (26, 0, 0)})
    camera([(0, (1.8, -5.6, 9.2), (-0.3, 0.6, 6.0)), (d, (1.4, -5.0, 8.9), (-0.3, 0.6, 6.0))], lens=24, fstop=6)

def S06(a, b):  # cut-away column: pipe ends in the face carry icy water, the hot core fades; a worker opens a frosted valve
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(100, elev=40, azim=135)
    plane('Ground', 200, 200, (0, 0, 0), M['floor'])
    S, H = 7.0, 7.6
    box('Column', (S, S, H), (0, S / 2, H / 2), M['conc'])
    heat_face('Core', S - 0.02, H - 0.02, (0, -0.01, H / 2), [(0, 1.9), (0.8, 1.8), (d, 0.08)], spread=1.6)
    cold = mat_emit('ColdWater', (0.35, 0.75, 1.0), 2.0)[0]
    for k in range(1, 5):
        for x in (-2.4, -0.8, 0.8, 2.4):
            cyl('PipeEnd', 0.09, 0.06, (x, -0.03, k * LIFT), M['black'], rot=(math.radians(90), 0, 0), verts=20)
            cyl('Water', 0.06, 0.062, (x, -0.035, k * LIFT), cold, rot=(math.radians(90), 0, 0), verts=16)
    # header pipe and valve outside the column, frosted (ice-cold water)
    cyl('Header', 0.09, 9.0, (0, -1.2, 0.5), M['frost'], rot=(0, math.radians(90), 0), verts=24)
    cyl('Riser', 0.07, 1.0, (-3.6, -1.2, 1.0), M['frost'], verts=20)
    vw = bpy.data.objects.new('ValveWheel', None); link(vw); vw.location = (-3.6, -1.2, 1.55)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.02, location=(0, 0, 0))
    tw = bpy.context.active_object; tw.data.materials.append(mat_simple('ValveRed', (0.55, 0.05, 0.03), 0.4)[0]); tw.parent = vw
    key(vw, 'rotation_euler', [(0, Vector((0, 0, 0))), (d, Vector((0, 0, math.radians(200))))])
    arm = person('Worker', loc=(-4.2, -1.75, 0), rot_z=math.radians(-60), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 0.8, {'upperarm01.R': (40, 0, 35), 'lowerarm01.R': (45, 0, 0), 'spine02': (10, 0, 0)})
    camera([(0, (-2.0, -11.5, 2.6), (-0.8, 1.0, 3.0)), (d, (-1.6, -10.8, 2.7), (-0.8, 1.0, 3.0))], lens=24, fstop=8)

def S07(a, b):  # two cooled columns pull apart a little: a thin dark gap opens between them
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(10, elev=55, azim=15, sun_e=3.0)
    canyon(M, half=32)
    S, H = 7.0, 9.0
    l = box('ColL', (S, S, H), (-S / 2 - 0.01, 0, H / 2), M['conc'])
    r = box('ColR', (S, S, H), (S / 2 + 0.01, 0, H / 2), M['conc'])
    key(l, 'location', [(0, Vector((-S / 2 - 0.01, 0, H / 2))), (1.2, Vector((-S / 2 - 0.01, 0, H / 2))), (d - 0.3, Vector((-S / 2 - 0.13, 0, H / 2)))])
    key(r, 'location', [(0, Vector((S / 2 + 0.01, 0, H / 2))), (1.2, Vector((S / 2 + 0.01, 0, H / 2))), (d - 0.3, Vector((S / 2 + 0.13, 0, H / 2)))])
    box('GapBack', (0.6, 0.05, H), (0, S / 2 - 0.3, H / 2), M['dark'])
    box('Below', (2 * S + 2, S + 2, 4.0), (0, 0, -2.0), M['conc'])
    camera([(0, (1.6, -8.5, 3.2), (0, -3.5, 4.2)), (d, (1.0, -7.2, 3.4), (0, -3.5, 4.4))], lens=28, fstop=5)

def S08(a, b):  # grout: grey grout fills the gap between the columns from the bottom up; a worker feeds the hose from the top
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(10, elev=55, azim=15, sun_e=3.0)
    canyon(M, half=32)
    S, H, g = 7.0, 9.0, 0.18
    box('ColL', (S, S, H), (-S / 2 - g / 2, S / 2, H / 2), M['conc'])
    box('ColR', (S, S, H), (S / 2 + g / 2, S / 2, H / 2), M['conc'])
    box('GapBack', (g, 0.05, H), (0, S - 0.1, H / 2), M['dark'])
    gr = box('Grout', (g - 0.01, S - 0.2, H), (0, S / 2, 0), M['grout'])
    z0, z1 = 0.05, 1.0
    key(gr, 'scale', [(0, Vector((1, 1, z0))), (0.4, Vector((1, 1, z0))), (d, Vector((1, 1, z1)))], interp='LINEAR')
    key(gr, 'location', [(0, Vector((0, S / 2 - 0.05, H * z0 / 2))), (0.4, Vector((0, S / 2 - 0.05, H * z0 / 2))), (d, Vector((0, S / 2 - 0.05, H * z1 / 2)))], interp='LINEAR')
    for k in range(1, 6):   # pipe ends in both faces get grouted too
        for x in (-5.2, -2.0, 2.0, 5.2):
            cyl('PipeEnd', 0.05, 0.06, (x, -0.03, k * LIFT), M['grout'], rot=(math.radians(90), 0, 0), verts=16)
    pipe_run(M, [(0.0, 1.5, H + 0.3), (0.0, 1.5, H - 0.2), (0.0, 1.5, 0.6)], r=0.04, mat=M['hose'])
    pipe_run(M, [(0.0, 1.5, H + 0.3), (0.3, 1.0, H + 0.9), (0.9, 0.6, H + 1.0)], r=0.04, mat=M['hose'])
    arm = person('Worker', loc=(1.4, 0.9, H), rot_z=math.radians(-125), outfit='worker')
    pose(arm, 0.0, STANCES['work_low'])
    camera([(0, (3.0, -12.0, 5.5), (0, 1.0, 5.0)), (d, (2.6, -11.0, 5.6), (0, 1.0, 5.2))], lens=26, fstop=8)

def S09(a, b):  # the finished curved dam holding back a lake; a visitor stands on the canyon floor and looks up at it
    sc = new_scene(a, b); d = dur(a, b); M = mats(); day(150, elev=42, azim=20)
    canyon(M, half=34)
    arc_dam(M, R=80, half_ang=26, H=62, base_t=34, top_t=11)
    plane('Lake', 80, 400, (0, 210, 56), M['water'])
    plane('River', 22, 300, (0, -150, 0.25), M['water'])
    cy = -80 + 6.0
    for k in range(-24, 25):   # parapet posts following the curved crest
        a = math.radians(26 * k / 25.0); r = 80 - 0.8
        o = box('Parapet', (1.2, 0.5, 1.1), (r * math.sin(a), cy + r * math.cos(a), 62.55), M['conc_plain']); o.rotation_euler = (0, 0, -a)
    box('Overlook', (8.0, 6.0, 12.0), (-6.0, -100.0, 6.0), M['conc_plain'], bevel=0.05, segs=1)
    for k in range(9):
        cyl('RailPost', 0.03, 1.05, (-9.6 + k * 0.9, -97.15, 12.52), M['rail'], verts=10)
    cyl('Rail', 0.035, 7.6, (-6.0, -97.15, 13.05), M['rail'], rot=(0, math.radians(90), 0), verts=12)
    cyl('Rail2', 0.02, 7.6, (-6.0, -97.15, 12.6), M['rail'], rot=(0, math.radians(90), 0), verts=10)
    arm = person('Visitor', loc=(-5.0, -97.7, 12.0), rot_z=math.radians(175), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.5, {'neck01': (-12, 0, 0)})
    camera([(0, (-9.0, -112.0, 14.0), (0, -6, 30)), (d, (-8.2, -108.0, 14.0), (0, -6, 31))], lens=26, fstop=11)

def S10(a, b):  # today: a big foundation pour; blue cooling pipes woven through the rebar, a tub of ice; a worker points
    sc = new_scene(a, b); d = dur(a, b); M = mats(); world_hdri('kloofendal_overcast_puresky', 1.0, 0); sun(1.2, 40, 150)
    plane('Ground', 200, 200, (0, 0, -0.01), M['floor'])
    W, Dp, H = 24.0, 18.0, 2.0
    box('PitFloor', (W, Dp, 0.1), (0, Dp / 2, 0.05), M['conc_plain'])
    for sx in (-1, 1): box('PitWall', (0.3, Dp, H), (sx * W / 2, Dp / 2, H / 2), M['wood'])
    box('PitBack', (W, 0.3, H), (0, Dp, H / 2), M['wood'])
    # rebar mat, two layers
    for z in (0.35, 1.55):
        for k in range(0, 48):
            cyl('RebarX', 0.016, W - 0.4, (0, 0.3 + k * 0.37, z), M['rebar'], rot=(0, math.radians(90), 0), verts=8)
        for k in range(0, 64):
            cyl('RebarY', 0.016, Dp - 0.4, (-W / 2 + 0.3 + k * 0.37, Dp / 2, z + 0.034), M['rebar'], rot=(math.radians(90), 0, 0), verts=8)
    for z in (0.75, 1.15):
        pipe_run(M, serpentine(-11.0, 11.0, 0.8, 1.5, 11, z), r=0.025, mat=M['hdpe'])
    # far half already poured
    pour = box('Pour', (W - 0.3, 7.0, H - 0.2), (0, Dp - 3.65, (H - 0.2) / 2), M['fresh'])
    # tub of ice next to the worker
    tub = box('Tub', (1.2, 0.8, 0.6), (3.2, -0.9, 0.3), mat_simple('TubBlue', (0.08, 0.2, 0.45), 0.4)[0], bevel=0.04)
    random.seed(4)
    for i in range(40):
        box('IceCube', (0.09, 0.09, 0.09), (3.2 + random.uniform(-0.5, 0.5), -0.9 + random.uniform(-0.3, 0.3), 0.62 + random.uniform(0, 0.08)),
            M['ice'], bevel=0.015, rot=(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)), segs=2)
    arm = person('Worker', loc=(1.6, -1.2, 0), rot_z=math.radians(160), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.4, STANCES['relax']); pose(arm, 2.4, STANCES['point_r'])
    camera([(0, (5.8, -4.2, 3.4), (-1.0, 5.0, 0.4)), (d, (5.2, -3.5, 3.5), (-1.0, 5.5, 0.4))], lens=24, fstop=8)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10]

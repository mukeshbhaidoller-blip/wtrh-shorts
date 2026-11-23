# Shots for "Ships Can't Sail Down Rapids... So We Built Water Elevators" (how the Soo Locks / navigation locks work).
# Z up, metres. The lock chamber runs along +Y (ships go downstream = +Y, from Lake Superior toward Lake Huron).
# Upper pool z = UP, lower pool z = LO. Person faces -Y at rot_z=0. t = seconds from the shot start.
import bmesh

def dur(a, b): return (b - a) / FPS

W = 33.5          # chamber inner width (Poe Lock: 110 ft)
LC = 260.0        # chamber length we model (Poe Lock: 1,200 ft; our freighter is 210 m)
TOP = 8.6         # wall coping height
FLOOR = -9.5      # chamber floor
UP = 6.4          # upper pool (21 ft above the lower pool)
LO = 0.0          # lower pool
TH = math.radians(20)   # miter angle of the gate leaves

# ---------------------------------------------------------------- materials
def water_mat(name='Water', col=(0.008, 0.026, 0.03), rough=0.035, wave=0.25, speed=(0, 1.2, 0), scale=0.35, d=6.0, foam=0.0, stretch=(1, 0.6, 1)):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    s = inp(p, 'Specular IOR Level', 'Specular')
    if s: s.default_value = 0.6
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale * stretch[0], scale * stretch[1], scale * stretch[2])
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    key_socket(mp.inputs['Location'], [(0, Vector((0, 0, 0))), (d, Vector((speed[0] * d * scale, speed[1] * d * scale, 0.4 * d * scale)))], 'LINEAR')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.noise_dimensions = '4D' if False else '3D'
    n.inputs['Scale'].default_value = 3.0; n.inputs['Detail'].default_value = 9; n.inputs['Roughness'].default_value = 0.62
    nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = wave; bp.inputs['Distance'].default_value = 0.15
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    if foam:
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        e0, e1 = ramp.color_ramp.elements; e0.position = 0.5 - foam * 0.25; e1.position = 0.62
        e0.color = (*col, 1); e1.color = (0.82, 0.86, 0.86, 1)
        nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
        rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough; rr.inputs['To Max'].default_value = 0.55
        nt.links.new(n.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
    return m

def stain_mat(name, tid, scale, col, tint, wet_z, dark=0.45):
    """Concrete that is darker/wetter below z=wet_z (old waterline)."""
    m, p = mat_textured(name, [tid], scale, col, rough=(0.7, 0.95), tint=tint)
    nt = m.node_tree
    bc = p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = wet_z - 0.25; mr.inputs['From Max'].default_value = wet_z + 0.25
    mr.inputs['To Min'].default_value = dark; mr.inputs['To Max'].default_value = 1.0
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    if bc is not None:
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        nt.links.new(bc, mul.inputs[6])
        cmb = nt.nodes.new('ShaderNodeCombineXYZ')
        for k in ('X', 'Y', 'Z'): nt.links.new(mr.outputs['Result'], cmb.inputs[k])
        nt.links.new(cmb.outputs['Vector'], mul.inputs[7]); nt.links.new(mul.outputs[2], p.inputs['Base Color'])
    return m

def paint_mat(name, col, rough=0.42, grime=0.35):
    """Smooth painted steel: colour/roughness vary with large soft noise, faint dents in the bump."""
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 0.35; n.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * (1 - grime) for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough - 0.12; rr.inputs['To Max'].default_value = rough + 0.15
    nt.links.new(n.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 1.6; nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.12
    nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def mats(wet_z=UP):
    M = {}
    M['wall'] = stain_mat('LockWall', 'concrete_floor_worn_001', 0.14, (0.55, 0.55, 0.52), (0.92, 0.91, 0.88), wet_z, 0.4)
    M['coping'] = mat_textured('Coping', ['concrete_floor_worn_001'], 0.3, (0.6, 0.6, 0.58), tint=(1.05, 1.05, 1.02))[0]
    M['grass'] = mat_textured('Grass', ['sparse_grass'], 0.15, (0.2, 0.3, 0.1), rough=(0.85, 1.0), bump=0.8, tint=(0.5, 0.78, 0.36))[0]
    M['rock'] = mat_textured('Rock', ['rocky_terrain_02'], 0.25, (0.35, 0.33, 0.3), tint=(0.85, 0.82, 0.78))[0]
    M['gate'] = paint_mat('GateSteel', (0.16, 0.17, 0.18), 0.5, 0.4)
    M['rust'] = paint_mat('GateWet', (0.09, 0.075, 0.06), 0.22, 0.5)
    M['hull'] = paint_mat('Hull', (0.36, 0.045, 0.03), 0.4, 0.3)
    M['black'] = mat_simple('HullBlack', (0.025, 0.025, 0.028), 0.45)[0]
    M['deck'] = mat_textured('Deck', ['concrete_floor_worn_001'], 0.3, (0.2, 0.22, 0.2), rough=(0.5, 0.8), tint=(0.3, 0.36, 0.32))[0]
    M['hatch'] = paint_mat('Hatch', (0.3, 0.05, 0.035), 0.5, 0.35)
    M['white'] = mat_simple('HouseWhite', (0.82, 0.83, 0.82), 0.4)[0]
    M['win'] = mat_simple('ShipGlass', (0.02, 0.025, 0.03), 0.05, coat=1.0)[0]
    M['yellow'] = mat_simple('SafetyYellow', (0.85, 0.6, 0.05), 0.45)[0]
    M['rail'] = mat_simple('RailPaint', (0.75, 0.75, 0.72), 0.4, 0.3)[0]
    M['bollard'] = mat_simple('Bollard', (0.04, 0.04, 0.045), 0.5, 0.5)[0]
    M['water'] = water_mat()
    M['studio'] = mat_simple('StudioFloor', (0.045, 0.045, 0.05), 0.55)[0]
    return M

# ---------------------------------------------------------------- geometry kit
def prism_z(name, pts, z0, z1, mat, loc=(0, 0, 0)):
    """Extrude a 2D (x, y) outline from z0 to z1."""
    n = len(pts); verts = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n; faces.append((i, j, n + j, n + i))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); link(o); o.location = loc
    if mat: o.data.materials.append(mat)
    return o

def rig(name, objs, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); link(e)
    for o in objs: o.parent = e
    e.location = loc; return e

def railing(M, x0, x1, y, z, h=1.05, step=1.8, axis='x'):
    P = []; L = abs(x1 - x0); c = (x0 + x1) / 2
    if axis == 'x':
        P.append(box('RailTop', (L, 0.06, 0.06), (c, y, z + h), M['rail']))
        P.append(box('RailMid', (L, 0.04, 0.04), (c, y, z + h * 0.5), M['rail']))
    else:
        P.append(box('RailTop', (0.06, L, 0.06), (y, c, z + h), M['rail']))
        P.append(box('RailMid', (0.04, L, 0.04), (y, c, z + h * 0.5), M['rail']))
    n = max(2, int(L / step) + 1)
    for i in range(n):
        v = min(x0, x1) + L * i / (n - 1)
        P.append(cyl('Post', 0.03, h, (v, y, z + h / 2) if axis == 'x' else (y, v, z + h / 2), M['rail'], verts=12))
    return P

def gate_leaf(M, side, yg, phi_closed, name='Leaf'):
    """One miter-gate leaf hinged at (side*W/2, yg). Returns the pivot empty; rotation_euler.z = angle (closed = phi_closed)."""
    Lf = (W / 2) / math.cos(TH) + 0.35
    H = TOP + 0.4 - FLOOR; zc = FLOOR + H / 2
    s = -side    # leaf extends toward the chamber centre
    P = [box(name, (Lf, 1.3, H), (s * Lf / 2, 0, zc), M['gate'])]
    # wet lower part on both faces
    for fy in (-0.66, 0.66):
        P.append(box('Wet', (Lf - 0.1, 0.02, UP - FLOOR - 0.3), (s * Lf / 2, fy, (FLOOR + UP) / 2 - 0.15), M['rust']))
    # horizontal girders + vertical stiffeners on the downstream face (local +y)
    for k in range(7):
        z = FLOOR + 1.2 + k * (H - 2.4) / 6
        P.append(box('Girder', (Lf - 0.6, 0.55, 0.32), (s * Lf / 2, 0.92, z), M['gate']))
    for k in range(6):
        P.append(box('Stiff', (0.22, 0.4, H - 1.2), (s * (0.8 + k * (Lf - 1.6) / 5), 0.85, zc), M['gate']))
    # walkway + railing on top
    P.append(box('Walk', (Lf, 1.7, 0.14), (s * Lf / 2, 0, TOP + 0.47), M['gate']))
    for fy in (-0.8, 0.8):
        P += railing(M, 0.2 * s, (Lf - 0.2) * s, fy, TOP + 0.54, step=2.2)
    piv = rig(name + 'Pivot', P, (side * W / 2, yg, 0))
    piv.rotation_euler = (0, 0, phi_closed)
    return piv

def gates(M, yg, open_f=0.0):
    """Pair of miter leaves at yg, V pointing upstream (-Y). open_f 0 = closed, 1 = open (parked along the walls)."""
    R = gate_leaf(M, 1, yg, TH, 'LeafR'); L = gate_leaf(M, -1, yg, -TH, 'LeafL')
    set_gates((R, L), open_f)
    return R, L

def gate_angles(f):
    return TH + (math.radians(-88) - TH) * f, -TH + (math.radians(88) + TH) * f

def set_gates(G, f):
    a, b = gate_angles(f); G[0].rotation_euler = (0, 0, a); G[1].rotation_euler = (0, 0, b)

def key_gates(G, pts):
    for t, f in pts:
        a, b = gate_angles(f)
        key(G[0], 'rotation_euler', [(t, (0, 0, a))]); key(G[1], 'rotation_euler', [(t, (0, 0, b))])

def lock(M, level=UP, lamps=False, up_open=0.0, lo_open=0.0, far=True):
    """The lock: walls, chamber water (returned so shots can animate z), both gate pairs, both pools, banks."""
    Y0, Y1 = -40, LC + 40
    for sx in (-1, 1):
        box('Wall', (10, Y1 - Y0, TOP - FLOOR + 3), (sx * (W / 2 + 5), (Y0 + Y1) / 2, (TOP + FLOOR - 3) / 2), M['wall'])
        box('Coping', (1.6, Y1 - Y0, 0.25), (sx * (W / 2 + 0.8), (Y0 + Y1) / 2, TOP + 0.12), M['coping'])
        box('Bank', (220, Y1 - Y0, 24), (sx * (W / 2 + 10 + 110), (Y0 + Y1) / 2, TOP - 12), M['grass'])
        box('Apron', (8.4, Y1 - Y0, 0.1), (sx * (W / 2 + 5.8), (Y0 + Y1) / 2, TOP + 0.05), M['coping'])
        for y in range(int(Y0) + 6, int(Y1), 18):
            cyl('Bollard', 0.32, 0.75, (sx * (W / 2 + 1.1), y, TOP + 0.6), M['bollard'], verts=24)
            cyl('BollardCap', 0.42, 0.12, (sx * (W / 2 + 1.1), y, TOP + 0.98), M['bollard'], verts=24)
        if lamps:
            for y in range(int(Y0) + 10, int(Y1), 30):
                cyl('Pole', 0.12, 9, (sx * (W / 2 + 7), y, TOP + 4.5), M['rail'], verts=16)
                b = box('LampHead', (1.2, 0.5, 0.25), (sx * (W / 2 + 6.4), y, TOP + 9.0), M['rail'])
                lm = mat_emit('LampGlow', (1, 0.78, 0.5), 25)[0]
                box('LampLens', (1.0, 0.4, 0.05), (sx * (W / 2 + 6.4), y, TOP + 8.86), lm)
                l = light('SPOT', (sx * (W / 2 + 6.4), y, TOP + 8.7), 2500, (1, 0.8, 0.55), 0.3, spot=95, blend=0.6)
                l.rotation_euler = (0, 0, 0)
    box('Floor', (W, Y1 - Y0, 1), (0, (Y0 + Y1) / 2, FLOOR - 0.5), M['wall'])
    wat = plane('Chamber', W, LC - 1.2, (0, LC / 2, level), M['water'])
    plane('UpperPool', 900, 700, (0, -350 - 1.0, UP), M['water'])
    plane('LowerPool', 900, 900, (0, LC + 450 + 1.0, LO), M['water'])
    if far:   # distant low shorelines so the horizon is not a pure water line
        for sy, yy, zz in ((-1, -600, UP), (1, LC + 820, LO)):
            box('FarShore', (1400, 60, 3), (0, yy, zz + 1.0), M['grass'])
    Gu = gates(M, 0.0, up_open); Gl = gates(M, LC, lo_open)
    return wat, Gu, Gl

def ship(M, L=210.0, B=31.4, draft=8.0, free=4.2, lit=0.0, name='Ship'):
    """Great Lakes freighter, origin at the waterline, bow toward +Y, stern house aft. Returns the rig."""
    P = []; hb = B / 2; yb = L / 2; ys = -L / 2
    out = [(-hb, ys), (hb, ys), (hb, yb - 22), (hb * 0.82, yb - 8), (hb * 0.45, yb - 2), (0, yb), (-hb * 0.45, yb - 2), (-hb * 0.82, yb - 8), (-hb, yb - 22)]
    P.append(prism_z('Hull', out, -draft, free - 1.6, M['hull']))
    P.append(prism_z('Sheer', out, free - 1.6, free, M['black']))
    inner = [(x * 0.985, y - (0.4 if y > 0 else -0.4)) for x, y in out]
    P.append(prism_z('Deck', inner, free - 0.4, free + 0.02, M['deck']))
    # hatch covers
    y = ys + 30
    while y < yb - 28:
        P.append(box('Hatch', (B - 7, 3.4, 0.7), (0, y, free + 0.35), M['hatch'], bevel=0.08)); y += 7.2
    # deck rails
    for sx in (-1, 1):
        P += railing(M, ys + 2, yb - 20, sx * (hb - 0.3), free, step=3.0, axis='y')
    # forecastle + bow mast
    fo = [(hb - 0.3, yb - 21), (hb * 0.8, yb - 8.5), (hb * 0.44, yb - 2.6), (0, yb - 0.6), (-hb * 0.44, yb - 2.6), (-hb * 0.8, yb - 8.5), (-hb + 0.3, yb - 21)]
    P.append(prism_z('Fo', fo, free, free + 2.4, M['hull']))
    P.append(prism_z('FoDeck', [(x * 0.96, y - 0.3) for x, y in fo], free + 2.4, free + 2.45, M['deck']))
    P.append(cyl('BowMast', 0.25, 9, (0, yb - 10, free + 6.9), M['white'], verts=16))
    # stern house (accommodation) with window rows and pilothouse
    hy = ys + 12
    gm = M['win'] if not lit else mat_simple('LitWin', (0.05, 0.04, 0.03), 0.1, emit=(1, 0.75, 0.45), estr=lit)[0]
    P.append(box('House', (B - 5, 18, 11), (0, hy, free + 5.5), M['white'], bevel=0.15))
    for k in range(3):
        z = free + 2.4 + k * 3.2
        P.append(box('WinRow', (B - 6.0, 0.12, 1.1), (0, hy + 9.03, z), gm))
        for sx in (-1, 1): P.append(box('WinSide', (0.12, 15, 1.1), (sx * (hb - 2.47), hy, z), gm))
    P.append(box('Pilot', (B - 2, 8, 3.4), (0, hy + 4, free + 12.7), M['white'], bevel=0.1))
    P.append(box('PilotWin', (B - 2.6, 0.12, 1.5), (0, hy + 8.03, free + 13.0), gm))
    for sx in (-1, 1): P.append(box('Wing', (0.1, 6.5, 1.5), (sx * (hb - 0.97), hy + 4, free + 13.0), gm))
    P.append(box('Stack', (4.5, 4.5, 6), (0, hy - 5, free + 14), M['black'], bevel=0.3))
    P.append(cyl('Mast', 0.2, 7, (0, hy + 1, free + 17.5), M['white'], verts=12))
    return rig(name, P)

def rapids(M, y0=0.0, length=36.0, width=180.0):
    """Rocky rapids: the river drops from UP to LO between y0 and y0+length, with white water and boulders; banks step down too."""
    plane('UpperRiver', width, 600, (0, y0 - 300, UP), water_mat('RiverUp', speed=(0, 1.0, 0)))
    s = (UP - LO) / length; ang = math.atan(s)
    f = water_mat('Rapids', col=(0.015, 0.04, 0.045), rough=0.08, wave=0.8, speed=(0, 5.0, 0), scale=0.45, foam=0.32, stretch=(1.0, 0.22, 1.0))
    o = plane('RapidsWater', width, length / math.cos(ang) + 2, (0, y0 + length / 2, (UP + LO) / 2 + 0.1), f, subdiv=70)
    o.rotation_euler = (-ang, 0, 0)
    tx = bpy.data.textures.new('Chop', 'CLOUDS'); tx.noise_scale = 1.4; tx.noise_depth = 2
    dm = o.modifiers.new('chop', 'DISPLACE'); dm.texture = tx; dm.strength = 1.3; dm.mid_level = 0.5
    o.modifiers.new('sm', 'SUBSURF').levels = 1
    plane('LowerRiver', width, 900, (0, y0 + length + 450, LO), water_mat('RiverLo', speed=(0, 1.6, 0), wave=0.35))
    rk = paint_mat('Boulder', (0.2, 0.19, 0.18), 0.75, 0.5)
    random.seed(5)
    for i in range(55):
        x = random.uniform(-width / 2 + 5, width / 2 - 5); yy = random.uniform(y0 + 1, y0 + length + 4)
        zz = UP - (min(max(yy - y0, 0), length)) * s
        r = random.uniform(0.7, 2.2)
        b = sphere('Boulder', r, (x, yy, zz - r * 0.15), rk, sub=3)
        b.scale = (random.uniform(0.9, 1.5), random.uniform(0.8, 1.3), random.uniform(0.5, 0.8))
    for sx in (-1, 1):
        xc = sx * (width / 2 + 150)
        box('BankUp', (300, 700, 14), (xc, y0 - 350, UP - 5.5), M['grass'])
        box('BankLo', (300, 900, 14), (xc, y0 + length + 450, LO - 5.5), M['grass'])
        sl = box('BankSlope', (300, length / math.cos(ang) + 1, 14), (xc, y0 + length / 2, (UP + LO) / 2 - 5.5), M['grass']); sl.rotation_euler = (-ang, 0, 0)

def day(rot=30, sun_e=2.2, elev=36, azim=150):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, math.radians(rot)); sun(sun_e, elev, azim)

def studio_lights(key_e=500, rim_e=300, s=1.0):
    k = light('AREA', (-2.2 * s, -3.0 * s, 2.6 * s), key_e, (1, 0.96, 0.9), 2.5 * s); aim(k, (0, 0, 0))
    r = light('AREA', (2.6 * s, 2.0 * s, 2.2 * s), rim_e, (0.85, 0.9, 1.0), 2.0 * s); aim(r, (0, 0, 0))
    f = light('AREA', (1.5 * s, -3.5 * s, 0.2 * s), key_e * 0.25, (1, 1, 1), 2.0 * s); aim(f, (0, 0, -0.3))

def hardhat(arm, M):
    """White hard hat on the head bone."""
    if arm is None: return
    hm = mat_simple('HatWhite', (0.86, 0.86, 0.84), 0.35)[0]
    h = sphere('HardHat', 0.135, (0, 0, 0), hm, sub=3); h.scale = (1.0, 1.12, 0.72)
    brim = cyl('Brim', 0.17, 0.012, (0, 0, 0), hm, verts=32); brim.parent = h; brim.location = (0, 0, -0.06)
    hold(arm, h, 'head', (0, 0.17, 0.02), (0, 0, 0))

# ---------------------------------------------------------------- shots
def S00(a, b):  # behind the captain at the bow rail: ahead, the river turns white and drops away
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(20, 2.2, 32, 330)
    rapids(M, 0.0)
    sh = ship(M); key(sh, 'location', [(0, Vector((0, -128, UP))), (d, Vector((0, -123, UP)))], interp='LINEAR')
    arm = person('Captain', loc=(0, 0, 0), rot_z=math.radians(180), outfit='casual')
    if arm:
        arm.parent = sh; arm.location = (0.6, 105 - 2.2, 4.2 + 2.4)
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.5, {'neck01': (6, 0, -4)})
    by = 105 - 128
    camera([(0, (1.6, by - 6.0, UP + 4.2 + 2.4 + 2.6), (0, by + 34, UP - 3.0)),
            (d, (1.5, by + 5 - 6.0, UP + 4.2 + 2.4 + 2.5), (0, by + 40, UP - 3.4))], lens=24)

def S01(a, b):  # from the riverbank at the top of the rapids: the long red freighter comes on, the white water drops in front
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(200, 2.2, 30, 170)
    rapids(M, 0.0)
    sh = ship(M); key(sh, 'location', [(0, Vector((0, -112, UP))), (d, Vector((0, -106, UP)))], interp='LINEAR')
    camera([(0, (-30, 22, UP + 3.8), (4, -40, UP + 5)), (d, (-29.5, 20, UP + 3.7), (4, -36, UP + 5))], lens=26)

def S02(a, b):  # high over the upper gates looking down the chamber: the concrete box with gates at both ends; a worker on the wall
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    wat, Gu, Gl = lock(M, UP)
    arm = person('Operator', loc=(W / 2 + 2.4, 14, TOP + 0.25), rot_z=math.radians(-75), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 2.5, STANCES['relax']); pose(arm, 3.6, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    camera([(0, (W / 2 + 6, -26, TOP + 26), (0, LC * 0.55, 0)), (d, (W / 2 + 5, -20, TOP + 31), (0, LC * 0.6, -2))], lens=24)

def S03(a, b):  # on the wall by the upper gates: the ship's stern is inside, the two gate leaves swing shut behind it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    wat, Gu, Gl = lock(M, UP, up_open=1.0)
    key_gates(Gu, [(0, 1.0), (0.4, 1.0), (d - 0.2, 0.0)])
    sh = ship(M); sh.location = (0, 135, UP)
    key(sh, 'location', [(0, Vector((0, 128, UP))), (d, Vector((0, 133, UP)))], interp='LINEAR')
    camera([(0, (W / 2 + 2.0, 16, TOP + 6.0), (-5, -4, UP + 1.0)), (d, (W / 2 + 2.0, 15, TOP + 5.8), (-5, -4, UP + 0.8))], lens=20)

def S04(a, b):  # a lock operator on the wall top next to the closed gate, shrugging at the camera: no pumps
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    wat, Gu, Gl = lock(M, UP)
    sh = ship(M); sh.location = (0, 133, UP)
    # valve machinery housing on the wall (no pump house anywhere)
    box('ValveHouse', (3.0, 4.0, 2.6), (W / 2 + 5.5, 6, TOP + 1.3), M['coping'], bevel=0.05)
    box('Door', (0.05, 1.0, 2.0), (W / 2 + 3.98, 6.4, TOP + 1.0), M['yellow'])
    arm = person('Operator', loc=(W / 2 + 2.2, 3.2, TOP + 0.25), rot_z=math.radians(-20), outfit='worker')
    pose(arm, 0.0, STANCES['relax'])
    pose(arm, 0.8, STANCES['relax']); pose(arm, 1.6, {'neck01': (0, 0, 10)}); pose(arm, 2.2, {'neck01': (0, 0, -10)})
    camera([(0, (W / 2 + 1.0, -3.4, TOP + 1.75), (W / 2 + 2.4, 3.2, TOP + 1.3)), (d, (W / 2 + 1.1, -3.0, TOP + 1.7), (W / 2 + 2.4, 3.2, TOP + 1.3))], lens=32, fstop=2.8)

def S05(a, b):  # studio cut-away through the lock wall: a steel valve slides up and water rushes down the culvert tunnel
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.3, 0, 'studio'); studio_lights(420, 300, 1.4)
    plane('Floor', 40, 40, (0, 0, -1.6), M['studio'])
    con = mat_textured('CutConcrete', ['concrete_floor_worn_001'], 0.6, (0.55, 0.55, 0.52), tint=(0.95, 0.94, 0.9))[0]
    # wall block cut open: tunnel runs along X, we see it from the -Y side (front half removed)
    box('Top', (4.2, 1.2, 0.9), (0, 0.1, 0.95), con)
    box('Bottom', (4.2, 1.2, 1.0), (0, 0.1, -1.0), con)
    box('Back', (4.2, 0.3, 1.1), (0, 0.55, 0.0), con)
    # water in the tunnel: flowing along +X toward the lower lake
    wm = water_mat('TunnelWater', col=(0.015, 0.06, 0.075), rough=0.03, wave=0.9, speed=(3.0, 0, 0), scale=1.5, d=d, stretch=(0.25, 2.5, 2.5))
    wt = box('TunnelWater', (4.1, 0.85, 1.0), (0, 0.0, -0.05), wm)
    key(wt, 'scale', [(0, Vector((1, 1, 0.35))), (0.6, Vector((1, 1, 0.35))), (1.6, Vector((1, 1, 1.0)))])
    key(wt, 'location', [(0, Vector((0, 0, -0.37))), (0.6, Vector((0, 0, -0.37))), (1.6, Vector((0, 0, -0.05)))])
    # steel valve gate in a slot at x = -0.6, lifting up
    vg = box('Valve', (0.18, 1.05, 1.15), (-0.6, 0.05, 0.0), M['gate'])
    key(vg, 'location', [(0, Vector((-0.6, 0.05, 0.0))), (0.5, Vector((-0.6, 0.05, 0.0))), (1.7, Vector((-0.6, 0.05, 1.05)))])
    cyl('Stem', 0.04, 2.2, (-0.6, 0.05, 1.6), M['rail'], verts=16).parent = vg
    camera([(0, (0.7, -3.6, 0.55), (0.1, 0.1, -0.05)), (d, (0.4, -3.3, 0.45), (0.1, 0.1, -0.05))], lens=30, fstop=6)

def S06(a, b):  # on the wall edge looking down the gap beside the ship: water and ship sink together, the wet wall face appears
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    wat, Gu, Gl = lock(M, UP)
    sh = ship(M); sh.location = (0, 135, UP)
    z0, z1 = UP, UP - 2.6
    key(wat, 'location', [(0, Vector((0, LC / 2, z0))), (d, Vector((0, LC / 2, z1)))], interp='LINEAR')
    key(sh, 'location', [(0, Vector((0, 135, z0))), (d, Vector((0, 135, z1)))], interp='LINEAR')
    camera([(0, (W / 2 + 0.6, 52, TOP + 2.0), (W / 2 - 4.0, 80, UP - 3.0)), (d, (W / 2 + 0.6, 53, TOP + 1.9), (W / 2 - 4.0, 81, UP - 3.6))], lens=22)

def S07(a, b):  # low in the drained chamber, from the ship's stern deck: the tall wet upper gate holds back the lake; leaks spray
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    wat, Gu, Gl = lock(M, LO)
    sh = ship(M); sh.location = (0, 118, LO)
    arm = person('GateTender', loc=(-3.0, -1.2, TOP + 0.55), rot_z=math.radians(15), outfit='worker')
    pose(arm, 0.0, STANCES['relax'])
    camera([(0, (2.5, 13, LO + 4.2 + 1.7), (0, -2, UP - 0.5)), (d, (2.2, 12, LO + 4.2 + 1.6), (0, -2, UP + 0.6))], lens=20)

def S08(a, b):  # high above the upper gates: the V of the closed leaves points into the lake, high water above, the low chamber below
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 50, 130)
    wat, Gu, Gl = lock(M, LO)
    sh = ship(M); sh.location = (0, 150, LO)
    camera([(0, (-10, 42, TOP + 44), (0, -6, UP - 2)), (d, (-6, 38, TOP + 40), (0, -6, UP - 2))], lens=24)

def S09(a, b):  # water is level with the river below: the lower gates swing open, a worker on the wall points downstream
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    wat, Gu, Gl = lock(M, LO)
    key_gates(Gl, [(0, 0.0), (0.4, 0.0), (d, 0.85)])
    sh = ship(M); sh.location = (0, LC - 108, LO)
    arm = person('Operator', loc=(W / 2 + 2.4, LC - 9, TOP + 0.25), rot_z=math.radians(-150), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.0, STANCES['relax']); pose(arm, 2.0, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    camera([(0, (W / 2 + 4.5, LC - 26, TOP + 4.2), (0, LC + 12, LO + 1)), (d, (W / 2 + 4.2, LC - 24, TOP + 4.0), (0, LC + 14, LO + 1))], lens=22)

def S10(a, b):  # the empty lock refills fast (time-lapse): boils of white water rise from the floor ports
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(40, 2.3, 34, 130)
    M['water'] = water_mat('Boil', col=(0.012, 0.04, 0.045), rough=0.06, wave=0.9, speed=(0, 0.3, 0), scale=0.1, d=d, foam=0.08)
    wat, Gu, Gl = lock(M, LO)
    key(wat, 'location', [(0, Vector((0, LC / 2, LO))), (d, Vector((0, LC / 2, UP - 0.6)))])
    camera([(0, (-W / 2 - 2.0, 2, TOP + 9), (0, LC * 0.55, LO)), (d, (-W / 2 - 1.5, 6, TOP + 10), (0, LC * 0.6, LO + 2))], lens=22)

def S11(a, b):  # studio: two glass tanks joined by a pipe; water runs from the high one until both levels match; a toy ship sinks with it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.35, 0, 'studio'); studio_lights(380, 120)
    plane('Floor', 30, 30, (0, 0, 0), M['studio'])
    gl = mat_glass('TankGlass')[0]
    wm = mat_simple('TankWater', (0.75, 0.92, 1.0), 0.02, trans=1.0, ior=1.33)[0]
    vol = wm.node_tree.nodes.new('ShaderNodeVolumeAbsorption'); vol.inputs['Color'].default_value = (0.25, 0.62, 0.78, 1); vol.inputs['Density'].default_value = 3.0
    wm.node_tree.links.new(vol.outputs[0], wm.node_tree.nodes['Material Output'].inputs['Volume'])
    for x in (-0.38, 0.38):
        for sx in (-1, 1):
            box('GlassSide', (0.012, 0.36, 0.6), (x + sx * 0.18, 0, 0.3), gl)
        for sy in (-1, 1):
            box('GlassFace', (0.36, 0.012, 0.6), (x, sy * 0.18, 0.3), gl)
        box('GlassBase', (0.38, 0.38, 0.02), (x, 0, 0.01), gl)
    cyl('Pipe', 0.028, 0.42, (0, 0, 0.06), gl, rot=(0, math.radians(90), 0), verts=24)
    cyl('PipeWater', 0.022, 0.42, (0, 0, 0.06), wm, rot=(0, math.radians(90), 0), verts=24)
    hi, lo, mid = 0.5, 0.14, 0.32
    for x, h0 in ((-0.38, hi), (0.38, lo)):
        o = box('Water', (0.345, 0.345, 1.0), (x, 0, 0.02 + h0 / 2), wm); o.scale = (1, 1, h0)
        key(o, 'scale', [(0, Vector((1, 1, h0))), (0.4, Vector((1, 1, h0))), (d - 0.4, Vector((1, 1, mid)))])
        key(o, 'location', [(0, Vector((x, 0, 0.02 + h0 / 2))), (0.4, Vector((x, 0, 0.02 + h0 / 2))), (d - 0.4, Vector((x, 0, 0.02 + mid / 2)))])
    ts = ship(M, name='ToyShip'); ts.scale = (0.0012, 0.0012, 0.0012); ts.rotation_euler = (0, 0, math.radians(90))
    key(ts, 'location', [(0, Vector((-0.38, 0, 0.02 + hi))), (0.4, Vector((-0.38, 0, 0.02 + hi))), (d - 0.4, Vector((-0.38, 0, 0.02 + mid)))])
    camera([(0, (0.12, -1.85, 0.55), (0, 0, 0.2)), (d, (0.06, -1.72, 0.53), (0, 0, 0.19))], lens=30, fstop=5.6)

def S12(a, b):  # dusk, from the riverbank downstream: the freighter steams out of the open lock toward us, lights on
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('qwantani_dusk_2_puresky', 0.7, math.radians(200)); sun(1.2, 5, 200, color=(1, 0.7, 0.45))
    wat, Gu, Gl = lock(M, LO, lamps=True, lo_open=0.85)
    sh = ship(M, lit=6.0); key(sh, 'location', [(0, Vector((0, LC + 70, LO))), (d, Vector((0, LC + 80, LO)))], interp='LINEAR')
    arm = person('Operator', loc=(W / 2 + 2.6, LC + 34, TOP + 0.25), rot_z=math.radians(-150), outfit='worker')
    pose(arm, 0.0, STANCES['relax'])
    camera([(0, (-30, LC + 255, LO + 3.5), (0, LC + 120, LO + 9)), (d, (-29, LC + 252, LO + 3.5), (0, LC + 126, LO + 9))], lens=28)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12]

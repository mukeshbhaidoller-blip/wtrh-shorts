# Shots for "Why Planes Get a Bath Before Winter Flights" (aircraft de-icing / anti-icing, problem -> fix chain).
# Z up, metres. The jet's nose points +Y, fuselage axis on x=0. LEFT wing spans -X (most shots use it).
# Person faces -Y at rot_z=0 (rot_z = theta faces (sin theta, -cos theta)). t = seconds from the shot start.
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

# ---------------------------------------------------------------- airfoil
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

# ---------------------------------------------------------------- materials
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

def _principled(nt, col, rough, coat=0.0, metal=0.0, trans=0.0, emit=None, estr=0.0):
    p = nt.nodes.new('ShaderNodeBsdfPrincipled')
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if coat: inp(p, 'Coat Weight', 'Clearcoat').default_value = coat; inp(p, 'Coat Roughness', 'Clearcoat Roughness').default_value = 0.03
    if trans: inp(p, 'Transmission Weight', 'Transmission').default_value = trans
    if emit: inp(p, 'Emission Color', 'Emission').default_value = (*emit, 1); inp(p, 'Emission Strength').default_value = estr
    return p

def wing_mat(name='WingSkin', frost=None, snow=None, orange=None, green=None, sweep_o=None, sweep_g=None):
    """Grey wing skin with keyed layers on the upper surface: orange Type I (wet), green Type IV gel, frost, snow.
    Each layer: [(t, amount 0..1)]. sweep_*: ('X'|'Y', lo, hi) makes the layer spread along that axis instead of in patches."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(geo.outputs['Normal'], sn.inputs['Vector'])
    upm = nt.nodes.new('ShaderNodeMapRange'); upm.inputs['From Min'].default_value = 0.05; upm.inputs['From Max'].default_value = 0.45
    nt.links.new(sn.outputs['Z'], upm.inputs['Value'])
    # base skin
    base = _principled(nt, (0.62, 0.64, 0.67), 0.33, coat=0.25, metal=0.35)
    nzb = nt.nodes.new('ShaderNodeTexNoise'); nzb.inputs['Scale'].default_value = 0.8; nt.links.new(tc.outputs['Object'], nzb.inputs['Vector'])
    rb = nt.nodes.new('ShaderNodeMapRange'); rb.inputs['To Min'].default_value = 0.26; rb.inputs['To Max'].default_value = 0.42
    nt.links.new(nzb.outputs['Fac'], rb.inputs['Value']); nt.links.new(rb.outputs['Result'], base.inputs['Roughness'])
    # panel lines (thin dark grid along chord/span)
    br = nt.nodes.new('ShaderNodeTexBrick'); br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Brick Width'].default_value = 2.6; br.inputs['Row Height'].default_value = 1.1; br.offset = 0.0
    br.inputs['Color1'].default_value = (0.62, 0.64, 0.67, 1); br.inputs['Color2'].default_value = (0.58, 0.6, 0.63, 1)
    br.inputs['Mortar'].default_value = (0.25, 0.26, 0.28, 1); nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], base.inputs['Base Color'])
    shader = base.outputs['BSDF']
    def noise01(scale, detail=8, seed=0.0):
        n = nt.nodes.new('ShaderNodeTexNoise'); n.noise_dimensions = '4D'; n.inputs['W'].default_value = seed
        n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = 0.6
        nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        r = nt.nodes.new('ShaderNodeMapRange'); r.inputs['From Min'].default_value = 0.3; r.inputs['From Max'].default_value = 0.7
        nt.links.new(n.outputs['Fac'], r.inputs['Value']); return r.outputs['Result']
    def mask(pts, scale, seed, sweep=None, upper=True):
        f = noise01(scale, seed=seed)
        if sweep:
            ax, lo, hi = sweep
            g = nt.nodes.new('ShaderNodeMapRange'); g.inputs['From Min'].default_value = lo; g.inputs['From Max'].default_value = hi
            nt.links.new(sep.outputs[ax], g.inputs['Value'])
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'FLOAT'; mx.inputs['Factor'].default_value = 0.75
            nt.links.new(f, mx.inputs['A']); nt.links.new(g.outputs['Result'], mx.inputs['B']); f = mx.outputs['Result']
        val = nt.nodes.new('ShaderNodeValue')
        for t, v in pts:
            val.outputs[0].default_value = v * 1.12 - 0.04; val.outputs[0].keyframe_insert('default_value', frame=F(t))
        lo = nt.nodes.new('ShaderNodeMath'); lo.operation = 'SUBTRACT'; lo.inputs[1].default_value = 0.07
        nt.links.new(val.outputs[0], lo.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
        nt.links.new(f, mr.inputs['Value']); nt.links.new(lo.outputs['Value'], mr.inputs['From Min']); nt.links.new(val.outputs[0], mr.inputs['From Max'])
        res = mr.outputs['Result']
        if upper:
            mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'
            nt.links.new(res, mu.inputs[0]); nt.links.new(upm.outputs['Result'], mu.inputs[1]); res = mu.outputs['Value']
        return res
    def stack(sh, msk, layer):
        mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(msk, mx.inputs['Fac'])
        nt.links.new(sh, mx.inputs[1]); nt.links.new(layer, mx.inputs[2]); return mx.outputs['Shader']
    if orange:
        po = _principled(nt, (0.95, 0.32, 0.02), 0.06, coat=1.0, emit=(1, 0.3, 0.02), estr=0.04)
        shader = stack(shader, mask(orange, 0.9, 1.0, sweep_o, upper=False), po.outputs['BSDF'])
    if green:
        pg = _principled(nt, (0.04, 0.42, 0.08), 0.04, coat=1.0, emit=(0.05, 0.5, 0.1), estr=0.03)
        nzg = nt.nodes.new('ShaderNodeTexNoise'); nzg.inputs['Scale'].default_value = 6; nt.links.new(tc.outputs['Object'], nzg.inputs['Vector'])
        bg = nt.nodes.new('ShaderNodeBump'); bg.inputs['Strength'].default_value = 0.25; bg.inputs['Distance'].default_value = 0.01
        nt.links.new(nzg.outputs['Fac'], bg.inputs['Height']); nt.links.new(bg.outputs['Normal'], pg.inputs['Normal'])
        shader = stack(shader, mask(green, 0.9, 2.0, sweep_g, upper=False), pg.outputs['BSDF'])
    if frost:
        pf = _principled(nt, (0.82, 0.86, 0.9), 0.5, coat=0.3)
        try: inp(pf, 'Subsurface Weight', 'Subsurface').default_value = 0.1
        except Exception: pass
        vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 260; nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
        vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = 60; nt.links.new(tc.outputs['Object'], vo2.inputs['Vector'])
        ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; nt.links.new(vo.outputs['Distance'], ad.inputs[0]); nt.links.new(vo2.outputs['Distance'], ad.inputs[1])
        bf = nt.nodes.new('ShaderNodeBump'); bf.inputs['Strength'].default_value = 0.9; bf.inputs['Distance'].default_value = 0.004
        nt.links.new(ad.outputs['Value'], bf.inputs['Height']); nt.links.new(bf.outputs['Normal'], pf.inputs['Normal'])
        # sparkle: tiny glints
        rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0.0; rr.inputs['From Max'].default_value = 0.6
        rr.inputs['To Min'].default_value = 0.08; rr.inputs['To Max'].default_value = 0.65
        nt.links.new(vo.outputs['Distance'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], pf.inputs['Roughness'])
        shader = stack(shader, mask(frost, 2.2, 3.0), pf.outputs['BSDF'])
    if snow:
        ps = _principled(nt, (0.9, 0.92, 0.95), 0.75)
        try: inp(ps, 'Subsurface Weight', 'Subsurface').default_value = 0.25
        except Exception: pass
        nzs = nt.nodes.new('ShaderNodeTexNoise'); nzs.inputs['Scale'].default_value = 14; nzs.inputs['Detail'].default_value = 10; nt.links.new(tc.outputs['Object'], nzs.inputs['Vector'])
        bs = nt.nodes.new('ShaderNodeBump'); bs.inputs['Strength'].default_value = 0.5; bs.inputs['Distance'].default_value = 0.02
        nt.links.new(nzs.outputs['Fac'], bs.inputs['Height']); nt.links.new(bs.outputs['Normal'], ps.inputs['Normal'])
        shader = stack(shader, mask(snow, 1.6, 4.0), ps.outputs['BSDF'])
    nt.links.new(shader, out.inputs['Surface'])
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

# ---------------------------------------------------------------- the jet
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

# ---------------------------------------------------------------- the apron / weather
def ground(snow=0.45, size=600, wet=0.35):
    cm, cp = mat_textured('Apron', ['concrete_pavement', 'concrete_floor_02'], 0.18, (0.4, 0.4, 0.4), rough=(0.3, 0.7), tint=(0.62, 0.62, 0.64), wet=wet)
    plane('Apron', size, size, (0, 0, 0), cm)
    # snow patches: snow texture where the noise is high (more at the edges of tyre tracks)
    m = bpy.data.materials.new('SnowPatch'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); tc = nt.nodes.new('ShaderNodeTexCoord')
    ps = nt.nodes.new('ShaderNodeBsdfPrincipled'); ps.inputs['Base Color'].default_value = (0.86, 0.88, 0.92, 1); ps.inputs['Roughness'].default_value = 0.7
    f = tex_file('snow_02', 'Diffuse')
    if f:
        mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.3, 0.3, 0.3); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        im = img_node(nt, f, mp.outputs['Vector']); nt.links.new(im.outputs['Color'], ps.inputs['Base Color'])
        nf = tex_file('snow_02', 'nor_gl')
        if nf:
            nm = img_node(nt, nf, mp.outputs['Vector'], False); nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 1.0
            nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], ps.inputs['Normal'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.08; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.65
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.62 - snow * 0.25; mr.inputs['From Max'].default_value = 0.66 - snow * 0.25
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mr.outputs['Result'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(ps.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], o.inputs['Surface'])
    if snow > 0: plane('Snow', size, size, (0, 0, 0.008), m)
    return cm

SNOW_AVOID = [None]
def snowfall(center, sx, sy, h, n, d, v=1.1, r=(0.012, 0.028), seed=5, glow=0.4, avoid=None):
    avoid = avoid or SNOW_AVOID[0]
    random.seed(seed)
    fm, _ = mat_simple('Flake', (0.95, 0.96, 1.0), 0.6, emit=(0.9, 0.93, 1.0), estr=glow)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=1); proto = bpy.context.active_object; proto.name = 'FlakeProto'
    proto.data.materials.append(fm); proto.location = (0, 0, -50)
    cx, cy, cz = center
    for i in range(n):
        k = random.uniform(*r)
        x = cx + random.uniform(-sx / 2, sx / 2); y = cy + random.uniform(-sy / 2, sy / 2)
        z0 = cz + random.uniform(0, h + v * d)
        if avoid is not None and (Vector((x, y)) - Vector((avoid[0], avoid[1]))).length < 2.2: continue
        fl = dup(proto, (x, y, z0), scale=(k, k, k))
        dx = random.uniform(-0.3, 0.3) * d
        key(fl, 'location', [(0, Vector((x, y, z0))), (d, Vector((x + dx, y + random.uniform(-0.2, 0.2) * d, z0 - v * d)))], interp='LINEAR')

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

def night_world(strength=0.35):
    world_hdri(NIGHT, strength * 1.5, 0.0, 'night')

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

# ---------------------------------------------------------------- de-icing truck
def truck(M, loc, yaw, bucket, beacon_on=True):
    """Boom de-icing truck. loc = rear-axle centre on the ground, yaw = heading (0 = +Y). bucket = world point of the
    bucket floor centre. Returns (bucket_floor, nozzle_tip)."""
    x, y, _ = loc; R = Matrix.Rotation(yaw, 4, 'Z')
    def W(p): v = R @ Vector(p); return Vector((x + v.x, y + v.y, v.z))
    rot = (0, 0, yaw)
    objs = []
    objs.append(box('Frame', (2.3, 8.6, 0.45), W((0, 1.5, 1.0)), M['steel'], rot=rot))
    objs.append(box('Cab', (2.4, 2.2, 2.0), W((0, 5.0, 2.15)), M['yellow'], bevel=0.12, rot=rot))
    objs.append(box('CabGlass', (2.3, 0.08, 0.9), W((0, 6.12, 2.55)), M['glass'], rot=rot))
    for sx in (-1.21, 1.21): objs.append(box('SideGlass', (0.05, 1.3, 0.8), W((sx, 5.2, 2.6)), M['glass'], rot=rot))
    objs.append(box('Tank', (2.3, 4.6, 1.7), W((0, 1.5, 2.1)), M['white'], bevel=0.25, rot=rot))
    for yy in (-1.3, 0.0, 4.6):
        for sx in (-1.1, 1.1):
            objs.append(cyl('TWheel', 0.55, 0.45, W((sx, yy, 0.55)), M['rubber'], rot=(0, math.radians(90), yaw), verts=48, bevel=0.06))
    T = W((0, -1.6, 3.2))
    objs.append(cyl('Turret', 0.7, 0.7, T, M['yellow'], verts=48))
    B = Vector(bucket)
    E = T.lerp(B, 0.45) + Vector((0, 0, 2.2))
    def beam(p, q, w):
        p = Vector(p); q = Vector(q); d = q - p
        o = box('Boom', (w, w, d.length), (0, 0, 0), M['yellow'], bevel=0.03)
        o.location = (p + q) / 2; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); return o
    objs += [beam(T, E, 0.42), beam(E, B + Vector((0, 0, -0.2)), 0.34)]
    objs.append(sphere('Elbow', 0.3, E, M['steel'], sub=2))
    # bucket (open box) around the floor centre B, facing the target direction (yaw)
    bx, by, bz = B
    Rb = Matrix.Rotation(yaw, 4, 'Z')
    def BW(p): v = Rb @ Vector(p); return Vector((bx + v.x, by + v.y, bz + v.z))
    objs.append(box('BFloor', (1.3, 1.1, 0.08), BW((0, 0, 0)), M['yellow'], rot=rot))
    for (px, py, sx, sy) in ((0, 0.55, 1.3, 0.06), (0, -0.55, 1.3, 0.06), (0.65, 0, 0.06, 1.1), (-0.65, 0, 0.06, 1.1)):
        objs.append(box('BWall', (sx, sy, 1.05), BW((px, py, 0.53)), M['yellow'], bevel=0.02, rot=rot))
    objs.append(box('BRail', (1.4, 0.08, 0.08), BW((0, 0.6, 1.1)), M['steel'], rot=rot))
    # mounted nozzle at the front rim
    n0 = BW((0.35, 0.62, 1.1)); n1 = BW((0.35, 1.25, 0.85))
    nd = n1 - n0
    nz = cyl('NozzleGun', 0.06, nd.length, (n0 + n1) / 2, M['steel'], verts=16)
    nz.rotation_mode = 'QUATERNION'; nz.rotation_quaternion = nd.to_track_quat('Z', 'Y')
    if beacon_on:
        bm, bp = mat_simple('TBeacon', (0.6, 0.25, 0.0), 0.3, emit=(1, 0.45, 0.02), estr=0.0)
        objs.append(cyl('TBeacon', 0.14, 0.18, W((0, 5.0, 3.25)), bm, verts=24))
        pts = []
        for k in range(10): pts += [(k * 0.7, 30.0), (k * 0.7 + 0.35, 0.5)]
        key_socket(inp(bp, 'Emission Strength'), pts, 'CONSTANT')
        bl = light('POINT', W((0, 5.0, 3.6)), 0, (1, 0.5, 0.05), 0.2)
        key_light(bl.data, 'energy', [(t, v / 30 * 120) for t, v in pts])
        for fc in fcurves_of(bl.data.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    return B, n1

def spray(p0, p1, col, t_on=0.0, t_off=99.0, r1=0.35, mist=True, seed=1):
    """Fluid jet from p0 to p1: an animated translucent cone + a steam/mist cloud at the impact."""
    p0 = Vector(p0); p1 = Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=r1, depth=d.length, vertices=48, end_fill_type='NOTHING')
    c = bpy.context.active_object; c.name = 'Spray'; bpy.ops.object.shade_smooth()
    c.location = (p0 + p1) / 2; c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = (-d).to_track_quat('Z', 'Y')
    m = bpy.data.materials.new('SprayMat'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (6, 6, 1.5); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    key_socket(mp.inputs['Location'], [(0, Vector((0, 0, 0))), (8, Vector((0, 0, 60)))], 'LINEAR')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 6
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.42; mr.inputs['From Max'].default_value = 0.62
    mr.inputs['To Max'].default_value = 0.85
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    on = nt.nodes.new('ShaderNodeValue')
    for t, v in ((t_on - 0.05, 0.0), (t_on + 0.15, 1.0), (t_off, 1.0), (t_off + 0.2, 0.0)):
        on.outputs[0].default_value = v; on.outputs[0].keyframe_insert('default_value', frame=F(max(0, t)))
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; nt.links.new(mr.outputs['Result'], mu.inputs[0]); nt.links.new(on.outputs[0], mu.inputs[1])
    p = nt.nodes.new('ShaderNodeBsdfPrincipled'); p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = 0.15
    inp(p, 'Transmission Weight', 'Transmission').default_value = 0.4
    inp(p, 'Emission Color', 'Emission').default_value = (*col, 1); inp(p, 'Emission Strength').default_value = 0.25
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mu.outputs['Value'], mx.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(p.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], o.inputs['Surface'])
    c.data.materials.append(m)
    try: c.visible_shadow = False
    except Exception: pass
    if mist:
        vm = bpy.data.materials.new('Mist'); vm.use_nodes = True; vt = vm.node_tree; vt.nodes.clear()
        vo = vt.nodes.new('ShaderNodeOutputMaterial'); vp = vt.nodes.new('ShaderNodeVolumePrincipled')
        vp.inputs['Color'].default_value = (0.95, 0.93, 0.9, 1)
        vn = vt.nodes.new('ShaderNodeTexNoise'); vn.inputs['Scale'].default_value = 1.6; vn.inputs['Detail'].default_value = 3
        vr = vt.nodes.new('ShaderNodeMapRange'); vr.inputs['From Min'].default_value = 0.45; vr.inputs['From Max'].default_value = 0.75; vr.inputs['To Max'].default_value = 0.0
        key_socket(vr.inputs['To Max'], [(t_on, 0.0), (t_on + 1.0, 1.4), (t_off, 1.4), (t_off + 1.0, 0.0)])
        vtc = vt.nodes.new('ShaderNodeTexCoord'); vmp = vt.nodes.new('ShaderNodeMapping'); vt.links.new(vtc.outputs['Object'], vmp.inputs['Vector'])
        key_socket(vmp.inputs['Location'], [(0, Vector((0, 0, 0))), (8, Vector((0, 0, -2.5)))], 'LINEAR')
        vt.links.new(vmp.outputs['Vector'], vn.inputs['Vector'])
        vt.links.new(vn.outputs['Fac'], vr.inputs['Value']); vt.links.new(vr.outputs['Result'], vp.inputs['Density'])
        vt.links.new(vp.outputs['Volume'], vo.inputs['Volume'])
        s = sphere('MistCloud', 1.0, p1 + Vector((0, 0, 0.5)), vm, sub=3); s.scale = (2.2, 2.2, 1.2)
    return c

def text_face(body, loc, size, mat, cam, extrude=0.02):
    bpy.ops.object.text_add(location=loc); t = bpy.context.active_object
    t.data.body = body; t.data.size = size; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'; t.data.extrude = extrude
    d = Vector(cam) - Vector(loc); yaw = math.atan2(-d.x, d.y)
    t.rotation_euler = (math.radians(90), 0, yaw + math.pi)
    t.data.materials.append(mat); return t

def pop_in(o, t0, dt=0.25, s=1.0):
    key(o, 'scale', [(t0 - 0.01, Vector((0.01, 0.01, 0.01))), (t0 + dt, Vector((s * 1.08, s * 1.08, s * 1.08))), (t0 + dt + 0.12, Vector((s, s, s)))])

def guy(name, loc, face, outfit='worker', **kw):
    """face = a world point the person faces (in XY)."""
    d = Vector(face) - Vector(loc); th = math.atan2(d.x, -d.y)
    return person(name, loc=loc, rot_z=th, outfit=outfit, stance='relax', **kw)

def look_up(arm, t, deg=-18):
    pose(arm, t, {'neck01': (deg, 0, 0)})

# ---------------------------------------------------------------- airflow studio diagram
def airflow(a, b, rough):
    sc = new_scene(a, b); d = dur(a, b)
    world_hdri('studio_small_09', 0.05, 0, 'studio')
    bgm, _ = mat_simple('Backdrop', (0.012, 0.014, 0.02), 0.7)
    plane('Back', 60, 60, (0, 6, 0), bgm).rotation_euler = (math.radians(90), 0, 0)
    C = 3.2; ZC = 1.0
    # airfoil slice (profile in the X-Z plane, LE at x=0, chord to +x), extruded along Y
    N = 60; cs = [0.5 * (1 - math.cos(math.pi * i / (N - 1))) for i in range(N)]
    prof = [(c, _yc(c, 0.04) + _yt(c, 0.13)) for c in reversed(cs)] + [(c, _yc(c, 0.04) - _yt(c, 0.13)) for c in cs[1:-1]]
    verts = [(c * C - C * 0.35, yy, ZC + h * C) for yy in (-0.6, 0.6) for c, h in prof]
    n = len(prof); faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    me = bpy.data.meshes.new('Airfoil'); me.from_pydata(verts, [], faces); me.update()
    af = bpy.data.objects.new('Airfoil', me); link(af)
    am = paint_mat('AirfoilGrey', (0.6, 0.62, 0.66), 0.3, 0.5, 0.4); me.materials.append(am)
    def up(xw):  # upper surface z at world x
        c = (xw + C * 0.35) / C
        if c < 0 or c > 1: return ZC
        return ZC + (_yc(c, 0.04) + _yt(c, 0.13)) * C
    def lo(xw):
        c = (xw + C * 0.35) / C
        if c < 0 or c > 1: return ZC
        return ZC + (_yc(c, 0.04) - _yt(c, 0.13)) * C
    light('AREA', (-2, -5, 5), 600, (1, 0.97, 0.92), 4, rot=(math.radians(45), 0, math.radians(-20)))
    light('AREA', (3, -3, -1), 150, (0.6, 0.75, 1.0), 3, rot=(math.radians(110), 0, math.radians(30)))
    cyan, _ = mat_emit('Flow', (0.25, 0.75, 1.0), 4.0)
    bead_m, _ = mat_emit('Bead', (0.7, 0.95, 1.0), 14.0)
    red, _ = mat_emit('Turb', (1.0, 0.35, 0.15), 5.0)
    random.seed(3)
    if rough:   # frost bumps on the front of the upper surface
        fm, _ = mat_simple('FrostBump', (0.9, 0.93, 0.97), 0.5)
        for i in range(140):
            xw = random.uniform(-C * 0.33, C * 0.45); yy = random.uniform(-0.58, 0.58)
            sp = sphere('Frost', random.uniform(0.012, 0.03), (xw, yy, up(xw)), fm, sub=1)
            pop_in(sp, random.uniform(0.0, 0.6), 0.2)
    xs = [-C * 0.35 - 1.6 + i * 0.08 for i in range(int((C + 3.4) / 0.08))]
    paths = []
    for h in (0.12, 0.3, 0.55, 0.85, 1.2, -0.12, -0.32, -0.6, -0.95):
        pts = []
        for xw in xs:
            if h > 0:
                bump = (up(xw) - ZC) * math.exp(-(h - 0.12) / 0.7) * 1.15
                z = ZC + h + bump
                c = (xw + C * 0.35) / C
                if rough and h < 0.6 and c > 0.3:   # flow tumbles and lifts off the rough top
                    k = (c - 0.3) * (1.0 - h)
                    z += k * 0.45 + math.sin(xw * 9 + h * 7) * k * 0.22
            else:
                bump = (lo(xw) - ZC) * math.exp(-(-h - 0.12) / 0.7) * 1.15
                z = ZC + h + bump
            pts.append(Vector((xw, -0.62, z)))
        paths.append((h, pts))
        cu = bpy.data.curves.new('FlowLine', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.008; cu.bevel_resolution = 2
        spl = cu.splines.new('POLY'); spl.points.add(len(pts) - 1)
        for k, p in enumerate(pts): spl.points[k].co = (p.x, p.y, p.z, 1)
        ob = bpy.data.objects.new('FlowLine', cu); link(ob)
        cu.materials.append(red if (rough and 0 < h < 0.6) else cyan)
    # beads that travel along each line
    for h, pts in paths:
        L = len(pts)
        for j in range(4):
            sp = sphere('Bead', 0.03, pts[0], bead_m, sub=2)
            off = j / 4.0; per = 2.2
            ks = []
            for q in range(0, 9):
                tt = q * d / 8.0; u = ((tt / per) + off) % 1.0
                ks.append((tt, pts[min(L - 1, int(u * (L - 1)))]))
            # keep beads on their path: insert per-frame keys
            for fr in range(0, int(d * FPS) + 1, 2):
                tt = fr / FPS; u = ((tt / per) + off) % 1.0
                sp.location = pts[min(L - 1, int(u * (L - 1)))]; sp.keyframe_insert('location', frame=F(tt))
            for fc in fcurves_of(sp.animation_data.action):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    # lift arrow
    ym, _ = mat_emit('LiftArrow', (1.0, 0.8, 0.1) if not rough else (1.0, 0.8, 0.1), 6.0)
    arr = bpy.data.objects.new('Arrow', None); link(arr); arr.location = (C * 0.0, -0.7, up(0.0) + 0.25)
    sh = cyl('Shaft', 0.07, 1.0, (0, 0, 0.5), ym, verts=24); sh.parent = arr
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, radius2=0, depth=0.4, vertices=32, location=(0, 0, 1.2)); hd = bpy.context.active_object; hd.data.materials.append(ym); hd.parent = arr
    tm, _ = mat_emit('Txt', (1, 1, 1), 5.0); rm, _ = mat_emit('TxtRed', (1, 0.2, 0.1), 7.0)
    cam_loc = (0.4, -9.0, 1.1)
    if rough:
        key(arr, 'scale', [(0, Vector((1, 1, 1.25))), (0.8, Vector((1, 1, 1.25))), (d * 0.75, Vector((1, 1, 0.8)))])
        t1 = text_face('LIFT', (0.0, -0.7, 4.35), 0.42, tm, cam_loc); t2 = text_face('-30%', (0.0, -0.7, 3.8), 0.55, rm, cam_loc)
        pop_in(t1, 0.2); pop_in(t2, 1.2)
    else:
        key(arr, 'scale', [(0, Vector((1, 1, 0.2))), (d * 0.7, Vector((1, 1, 1.55)))])
        t1 = text_face('LIFT', (0.0, -0.7, 4.45), 0.5, tm, cam_loc); pop_in(t1, 1.4)
    camera([(0, cam_loc, (0.35, 0, 1.1)), (d, (0.2, -8.4, 1.05), (0.3, 0, 1.1))], lens=35, fstop=8)

# ---------------------------------------------------------------- shots
def night_apron(M, wing_m, snow=0.45, flakes=600, d=4.0, fl_center=(-8, 2, 0), fl_size=(30, 30, 12), lit=True):
    night_world(0.4); ground(snow)
    j = jet(M, wing_m, lit=lit)
    flood((-28, 22, 22), (-6, 0, 2), 14000); flood((20, -26, 22), (-2, -2, 2), 9000, pole=True)
    far_lights(); far_lights(-130, seed=12)
    if flakes: snowfall(fl_center, fl_size[0], fl_size[1], fl_size[2], flakes, d)
    return j

def S00(a, b):  # hook: jet parked at night in falling snow, frost on the wing, a worker with a flashlight walks up
    SNOW_AVOID[0] = (-19.8, 3.2)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(frost=[(0, 0.8), (d, 0.85)])
    night_apron(M, wm, flakes=700, d=d, fl_center=(-16, 8, 0), fl_size=(16, 16, 9))
    arm = guy('Walker', (-13.2, 7.2, 0), (-11.0, 3.0, 0), 'worker')
    if arm:
        walk(arm, 0.0, d * 0.75); pose(arm, d * 0.8, STANCES['relax'])
        key(arm, 'location', [(0, Vector((-13.2, 7.2, 0))), (d * 0.8, Vector((-12.0, 4.9, 0)))])
        look_up(arm, d * 0.85, -20)
    fl = light('SPOT', (-13.0, 6.8, 1.2), 400, (0.9, 0.95, 1.0), 0.05, spot=22, blend=0.4)
    key(fl, 'location', [(0, Vector((-12.9, 6.7, 1.15))), (d * 0.8, Vector((-11.75, 4.45, 1.15)))]);
    tgt = bpy.data.objects.new('FT', None); link(tgt); tgt.location = (-10.3, 0.0, 2.9)
    c = fl.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    camera([(0, (-19.8, 3.2, 6.0), (-8.0, -1.6, 2.6)), (d, (-19.0, 2.4, 5.6), (-8.0, -1.6, 2.6))], lens=24, fstop=6)

def S01(a, b):  # macro: frost crystals grow on the wing skin at dawn
    SNOW_AVOID[0] = None
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('snowy_field', 0.7, 1.2, 'overcast'); sun(2.4, 7, 120, (1.0, 0.78, 0.55), 1.0)
    ground(0.8)
    wm = wing_mat(frost=[(0, 0.7), (d * 0.8, 1.0)])
    jet(M, wm, lit=False, beacon=False)
    s0, c0 = 0.42, 0.10
    P = wing_up(s0, c0); Q = wing_up(s0, 0.28)
    random.seed(11)
    cm = bpy.data.materials.new('Crystal'); cm.use_nodes = True; p = cm.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.92, 0.95, 1.0, 1); p.inputs['Roughness'].default_value = 0.2
    inp(p, 'Subsurface Weight', 'Subsurface').default_value = 0.3; inp(p, 'Coat Weight', 'Clearcoat').default_value = 1.0
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.12, vertices=6); proto = bpy.context.active_object; proto.data.materials.append(cm); proto.location = (0, 0, -60)
    for i in range(900):
        s = s0 + random.uniform(-0.018, 0.018); c = random.uniform(0.06, 0.24)
        p0 = wing_up(s, c)
        k = random.uniform(0.002, 0.007)
        cr = dup(proto, (p0.x, p0.y, p0.z + 0.0005), rot=(random.uniform(-1.2, 1.2), random.uniform(-1.2, 1.2), random.uniform(0, 3.14)))
        t0 = random.uniform(0.0, d * 0.7)
        key(cr, 'scale', [(t0, Vector((0.0001, 0.0001, 0.0001))), (t0 + 0.6, Vector((k, k, k)))])
    cp = P + Vector((0.05, 0.38, 0.09))
    camera([(0, cp, Q + Vector((0, 0, 0.01))), (d, cp + Vector((0.0, -0.08, -0.015)), Q + Vector((0, -0.05, 0.01)))], lens=50, fstop=5.6)

def S02(a, b):  # cut-away: rough frost wrecks the smooth airflow, lift drops ~30%
    SNOW_AVOID[0] = None
    airflow(a, b, rough=True)

def S03(a, b):  # the rule: an inspector checks the wing's leading edge with a flashlight; NO TAKEOFF
    SNOW_AVOID[0] = (-7.4, 8.4)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(frost=[(0, 0.85)], snow=[(0, 0.3)])
    night_apron(M, wm, flakes=500, d=d, fl_center=(-9, 4, 0), fl_size=(12, 12, 8))
    arm = guy('Inspector', (-8.9, 2.5, 0), (-9.2, 0.0, 2.8), 'worker')
    if arm:
        look_up(arm, 0.0, -24); pose(arm, 0.4, STANCES['relax']); pose(arm, 1.3, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    fl = light('SPOT', (-8.6, 2.2, 1.5), 500, (0.9, 0.95, 1.0), 0.05, spot=20, blend=0.4); aim(fl, (-9.6, 0.2, 2.9))
    cam = (-7.4, 8.4, 1.3)
    rm, _ = mat_emit('NoGo', (1.0, 0.12, 0.08), 9.0)
    t = text_face('NO TAKEOFF', (-9.6, 0.6, 5.6), 0.62, rm, cam); pop_in(t, 1.25)
    camera([(0, cam, (-9.0, 0.8, 3.0)), (d, (-7.6, 7.8, 1.35), (-9.0, 0.8, 3.05))], lens=26, fstop=4.5)

def S04(a, b):  # the jet rolls slowly onto the de-icing pad; the truck waits, beacon flashing
    SNOW_AVOID[0] = None
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(frost=[(0, 0.8)], snow=[(0, 0.25)])
    night_world(0.4); ground(0.5)
    j = jet(M, wm)
    key(j, 'location', [(0, Vector((0, -20, 0))), (d * 0.6, Vector((0, -3.0, 0))), (d, Vector((0, 0, 0)))])
    ym, _ = mat_simple('PadLine', (0.85, 0.65, 0.05), 0.5)
    for x in (-21, 21): box('PadEdge', (0.4, 60, 0.01), (x, 0, 0.012), ym)
    for y in (-30, 30): box('PadEnd', (42.4, 0.4, 0.01), (0, y, 0.012), ym)
    box('Center', (0.3, 60, 0.01), (0, 0, 0.012), ym)
    bm, _ = mat_emit('PadBlue', (0.2, 0.45, 1.0), 30)
    for y in range(-30, 25, 6):
        for x in (-21.6, 21.6): sphere('PadLight', 0.12, (x, y, 0.2), bm, sub=1)
    truck(M, (-23.0, -7, 0), math.radians(-12), (-20.5, -2.0, 3.2))
    flood((-32, 26, 22), (-4, 0, 2), 14000); flood((30, -20, 22), (0, 0, 2), 9000)
    far_lights(); far_lights(-130, seed=12)
    snowfall((-16, 22, 0), 22, 22, 10, 600, d)
    camera([(0, (-24.0, 36.0, 2.2), (-3.0, 2.0, 3.0)), (d, (-23.0, 34.5, 2.4), (-3.0, 1.0, 3.0))], lens=26, fstop=8)

BKT = Vector((-10.6, -2.9, 6.6))    # bucket floor centre over the left wing (S05/S06/S08)
def deice_scene(M, wm, d, col, t_on, target, flakes=400, cam=None, person_on=True, lit_extra=True):
    night_world(0.4); ground(0.5)
    jet(M, wm)
    B, nt_ = truck(M, (-11.5, -13.5, 0), math.radians(8), BKT)
    if person_on:
        arm = guy('Sprayer', (BKT.x - 0.15, BKT.y - 0.05, BKT.z + 0.04), target, 'worker')
        if arm:
            pose(arm, 0.0, {'upperarm01.L': (40, 0, -35), 'upperarm01.R': (40, 0, 35), 'lowerarm01.L': (35, 0, 0), 'lowerarm01.R': (35, 0, 0), 'neck01': (16, 0, 0)})
    sp = spray(nt_, target, col, t_on=t_on, t_off=99)
    flood((-28, 18, 22), (-10, -2, 3), 14000); flood((6, -30, 20), (-9, -2, 3), 8000)
    far_lights(); far_lights(-130, seed=12)
    if flakes: snowfall((-11, -2, 0), 16, 16, 10, flakes, d)
    return nt_

def S05(a, b):  # the truck's boom lifts the worker over the wing; hot orange fluid sprays on
    SNOW_AVOID[0] = (-23.5, 3.5)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(frost=[(0, 0.85), (1.0, 0.85), (d, 0.4)], snow=[(0, 0.25), (1.0, 0.25), (d, 0.0)], orange=[(0, 0.0), (0.9, 0.0), (d, 0.6)], sweep_o=('X', -7.5, -12.5))
    tgt = wing_up(0.55, 0.35)
    deice_scene(M, wm, d, (1.0, 0.42, 0.04), 0.8, tgt)
    camera([(0, (-23.5, 3.5, 9.0), (-10.4, -2.4, 4.4)), (d, (-22.8, 2.8, 9.2), (-10.4, -2.4, 4.5))], lens=26, fstop=6)

def S06(a, b):  # close-up: the orange fluid melts the frost right off, steam rises
    SNOW_AVOID[0] = (-8.3, 2.6)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(frost=[(0, 0.75), (d * 0.85, 0.0)], orange=[(0, 0.35), (d * 0.8, 1.0)], sweep_o=('Y', -0.5, -3.5))
    tgt = wing_up(0.55, 0.3)
    deice_scene(M, wm, d, (1.0, 0.42, 0.04), 0.0, tgt, flakes=250, person_on=False)
    camera([(0, (-8.3, 2.6, 4.4), (-10.3, -1.2, 3.1)), (d, (-8.7, 2.1, 4.25), (-10.3, -1.3, 3.1))], lens=32, fstop=3.5)

def S07(a, b):  # snow keeps falling: it starts to stick to the wet wing again
    SNOW_AVOID[0] = None
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(orange=[(0, 1.0)], snow=[(0, 0.0), (0.6, 0.05), (d, 0.62)])
    night_world(0.35); ground(0.6); jet(M, wm)
    flood((-26, 14, 20), (-10, 0, 3), 14000); flood((4, -28, 20), (-9, -2, 3), 8000); far_lights(); far_lights(-130, seed=12)
    snowfall((-9.5, -0.5, 2.5), 7, 7, 5, 1400, d, v=1.3, r=(0.01, 0.024))
    a0 = wing_up(0.3, 0.2); a1 = wing_up(0.75, 0.45)
    camera([(0, a0 + Vector((1.0, 1.6, 0.9)), a1), (d, a0 + Vector((0.8, 1.4, 0.75)), a1 + Vector((0, 0, -0.05)))], lens=30, fstop=4)

def S08(a, b):  # a second coat: thick green gel sprayed over the clean wing
    SNOW_AVOID[0] = (-30.0, -13.0)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(orange=[(0, 1.0)], green=[(0, 0.0), (0.7, 0.0), (d, 0.9)], sweep_g=('X', -7.0, -13.0))
    tgt = wing_up(0.55, 0.4)
    deice_scene(M, wm, d, (0.15, 0.85, 0.2), 0.6, tgt, flakes=400)
    camera([(0, (-30.0, -13.0, 11.0), (-10.4, -2.0, 4.0)), (d, (-29.2, -12.3, 11.1), (-10.4, -2.0, 4.1))], lens=30, fstop=6)

def S09(a, b):  # holdover time: the pilot checks his watch by the nose, a countdown dial ticks
    SNOW_AVOID[0] = (-9.5, 27.5)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(green=[(0, 1.0)])
    night_world(0.4); ground(0.5); jet(M, wm)
    flood((-22, 30, 20), (-2, 12, 2), 12000); flood((14, 26, 18), (0, 14, 2), 6000); far_lights(); far_lights(-130, seed=12)
    snowfall((-4, 17, 0), 12, 12, 8, 500, d)
    arm = guy('Pilot', (-3.4, 17.0, 0), (-6.5, 24.0, 0), 'casual')
    if arm:
        pose(arm, 0.0, STANCES['relax']); look_up(arm, 0.0, -6); look_up(arm, d, -12)
    cam = (-9.5, 27.5, 1.7)
    gm, _ = mat_emit('Dial', (0.2, 1.0, 0.35), 6.0); wmt, _ = mat_emit('DialW', (1, 1, 1), 6.0)
    dc = Vector((-4.2, 15.0, 5.6))
    dial = bpy.data.objects.new('Dial', None); link(dial); dial.location = dc
    dv = Vector(cam) - dc; dial.rotation_euler = (math.radians(90), 0, math.atan2(-dv.x, dv.y) + math.pi)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.8, minor_radius=0.05, major_segments=96, minor_segments=12, rotation=(math.radians(90), 0, 0))
    ring = bpy.context.active_object; ring.data.materials.append(gm); ring.parent = dial; ring.location = (0, 0, 0)
    ring.rotation_euler = (0, 0, 0)
    hand = box('Hand', (0.05, 0.62, 0.03), (0, 0, 0), wmt)
    pv = bpy.data.objects.new('Pivot', None); link(pv); pv.parent = dial; hand.parent = pv; hand.location = (0, 0.28, 0)
    key(pv, 'rotation_euler', [(0, Vector((0, 0, 0))), (d, Vector((0, 0, -math.radians(300))))], interp='LINEAR')
    for k in range(12):
        a_ = k * math.pi / 6
        tk = box('Tick', (0.03, 0.12, 0.03), (0, 0, 0), wmt); tk.parent = dial; tk.location = (math.sin(a_) * 0.66, math.cos(a_) * 0.66, 0); tk.rotation_euler = (0, 0, -a_)
    for o in (dial,): pop_in(o, 0.25, 0.3)
    t = text_face('HOLDOVER TIME', (dc.x, dc.y, dc.z - 1.25), 0.36, wmt, cam); pop_in(t, 0.9)
    camera([(0, cam, (-3.6, 15.5, 2.9)), (d, (-9.1, 26.8, 1.75), (-3.6, 15.5, 3.0))], lens=30, fstop=5)

def S10(a, b):  # green gel drips off the trailing edge; a worker looks up, unsure
    SNOW_AVOID[0] = (-5.6, -11.5)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    wm = wing_mat(green=[(0, 1.0)])
    night_world(0.4); ground(0.5); jet(M, wm)
    flood((-24, -20, 20), (-9, -3, 2), 12000); flood((-20, 16, 20), (-9, -2, 2), 7000, pole=False); far_lights(); far_lights(-130, seed=12)
    gm, _ = mat_simple('Gel', (0.05, 0.5, 0.1), 0.05, emit=(0.05, 0.6, 0.1), estr=0.2, trans=0.4)
    random.seed(8)
    for i in range(22):
        s = random.uniform(0.25, 0.65); p = wing_up(s, 0.985); p.z -= 0.06
        dr = sphere('Drip', 0.035, p, gm, sub=2); dr.scale = (1, 1, 1.6)
        t0 = random.uniform(0, d)
        key(dr, 'location', [(max(0, t0 - 0.6), p), (t0, p), (t0 + 0.65, p - Vector((0, 0, p.z - 0.02)))], interp='LINEAR')
    up_l = light('SPOT', (-6.5, -10.0, 1.4), 2500, (1.0, 0.92, 0.8), 0.3, spot=40, blend=0.5); aim(up_l, (-9.2, -4.2, 2.6))
    arm = guy('Worker', (-9.0, -6.6, 0), (-9.0, -3.0, 0), 'worker')
    if arm:
        look_up(arm, 0.0, -26); pose(arm, d * 0.5, {'neck01': (-30, 0, 0), 'spine02': (-4, 0, 0)})
    snowfall((-9, -5, 0), 10, 10, 6, 300, d)
    camera([(0, (-5.6, -11.5, 1.3), (-9.2, -4.0, 2.7)), (d, (-5.9, -11.0, 1.25), (-9.2, -4.0, 2.75))], lens=26, fstop=4)

def S11(a, b):  # window seat on the takeoff roll: the wind shears the green gel off the wing
    SNOW_AVOID[0] = None
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_overcast_puresky', 0.9, 0, 'overcast'); sun(1.2, 15, 200, (1.0, 0.92, 0.85), 4)
    wm = wing_mat(orange=[(0, 0.6)], green=[(0, 1.0), (0.8, 0.95), (d, 0.08)], sweep_g=('Y', 1.0, -6.0))
    j = jet(M, wm, lit=False, fuselage=False)
    # ground rushes backwards (the jet accelerates along +Y)
    G = bpy.data.objects.new('Ground', None); link(G)
    am, _ = mat_textured('Runway', ['asphalt_02', 'asphalt_04'], 0.3, (0.14, 0.14, 0.15), rough=(0.6, 0.9), wet=0.3)
    r = plane('Runway', 45, 900, (0, -350, 0), am); r.parent = G
    sm = mat_textured('Snowfield', ['snow_02'], 0.15, (0.9, 0.9, 0.92), rough=(0.5, 0.8))[0]
    for s in (-1, 1): plane('SnowField', 600, 900, (s * (22.5 + 300), -350, -0.02), sm).parent = G
    wm2, _ = mat_simple('Marking', (0.85, 0.85, 0.82), 0.5)
    for y in range(-790, 100, 60): box('CL', (0.9, 30, 0.004), (0, y, 0.003), wm2).parent = G
    em, _ = mat_emit('EdgeLight', (1, 0.9, 0.7), 18)
    for y in range(-790, 100, 30): sphere('Edge', 0.14, (-23.5, y, 0.3), em, sub=1).parent = G
    random.seed(4)
    tm_, _ = mat_simple('Hangar', (0.42, 0.43, 0.45), 0.6, 0.3)
    for y in range(-800, 100, 90): box('Hangar', (40, 60, random.uniform(12, 18)), (-320 + random.uniform(-20, 20), y, 7), tm_, bevel=0.5).parent = G
    ks = []
    for q in range(11):
        tt = d * q / 10; ks.append((tt, Vector((0, -(22 * tt + 0.5 * 9.0 * tt * tt), 0))))
    key(G, 'location', ks, interp='LINEAR')
    # gel streaks flying back off the trailing edge
    gm, _ = mat_simple('GelBlob', (0.06, 0.55, 0.12), 0.05, emit=(0.05, 0.6, 0.1), estr=0.15, trans=0.3)
    for i in range(90):
        tb = 0.9 + (d - 1.0) * i / 90
        s = random.uniform(0.2, 0.75); p = wing_up(s, random.uniform(0.6, 1.0))
        bl = sphere('Blob', random.uniform(0.02, 0.05), p, gm, sub=1); bl.scale = (0.6, 3.0, 0.5)
        key(bl, 'scale', [(tb - 0.01, Vector((0.001, 0.001, 0.001))), (tb, Vector((0.6, 3.0, 0.5))), (tb + 0.6, Vector((0.4, 5.0, 0.3)))])
        key(bl, 'location', [(tb, p), (tb + 0.6, p + Vector((random.uniform(-0.3, 0.3), -9.0, random.uniform(0.2, 0.8))))], interp='LINEAR')
    # cabin wall with an oval window right at the camera
    wallm, _ = mat_simple('CabinWall', (0.75, 0.74, 0.71), 0.6)
    wall = box('CabinWall', (0.05, 2.0, 2.0), (-1.62, -1.0, ZF + 0.4), wallm)
    hole = sphere('WinHole', 1.0, (-1.62, -1.0, ZF + 0.45), None, sub=4); hole.scale = (0.3, 0.2, 0.28); hole.hide_render = True; hole.display_type = 'WIRE'
    bo = wall.modifiers.new('w', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = hole
    light('AREA', (-1.3, -1.0, ZF + 0.9), 15, (1, 0.95, 0.9), 1.0, rot=(0, math.radians(-60), 0))
    cp = Vector((-1.18, -0.9, ZF + 0.5))
    tgt = wing_up(0.5, 0.55)
    camera([(0, cp, tgt), (d, cp + Vector((0.0, 0.0, -0.02)), tgt + Vector((0, 0, 0.2)))], lens=24, fstop=4.0)
    sc.camera.data.dof.focus_object = None; sc.camera.data.dof.focus_distance = (tgt - cp).length

def S12(a, b):  # cut-away: clean wing, smooth flow, big lift
    SNOW_AVOID[0] = None
    airflow(a, b, rough=False)

def S13(a, b):  # winter morning: the clean jet lifts off; a de-icing worker (seen from behind) waves it goodbye
    SNOW_AVOID[0] = None
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_overcast_puresky', 1.0, 0.5, 'overcast'); sun(2.2, 10, 150, (1.0, 0.82, 0.62), 2.0)
    wm = wing_mat()
    am, _ = mat_textured('Runway', ['asphalt_02', 'asphalt_04'], 0.3, (0.14, 0.14, 0.15), rough=(0.6, 0.9), wet=0.25)
    plane('Runway', 45, 1400, (0, 400, 0.01), am)
    wm2, _ = mat_simple('Marking', (0.85, 0.85, 0.82), 0.5)
    for y in range(-100, 1000, 60): box('CL', (0.9, 30, 0.004), (0, y, 0.014), wm2)
    sm = mat_textured('Snowfield', ['snow_02'], 0.12, (0.9, 0.9, 0.92), rough=(0.5, 0.8))[0]
    plane('SnowField', 1600, 1800, (0, 400, 0), sm)
    em, _ = mat_emit('EdgeLight', (1, 0.9, 0.7), 12)
    for y in range(-100, 1000, 30):
        for s_ in (-1, 1): sphere('Edge', 0.16, (s_ * 23.5, y, 0.3), em, sub=3)
    tm_, _ = mat_simple('Hangar', (0.42, 0.43, 0.45), 0.6, 0.3)
    random.seed(6)
    for k in range(8): box('Hangar', (60, 40, random.uniform(14, 22)), (random.uniform(-500, 300), 1100 + random.uniform(0, 200), 9), tm_)
    j = jet(M, wm, lit=False)
    ks = []
    for q in range(11):
        tt = (d + 0.5) * q / 10; y = 60 + 50 * tt; z = max(0.0, (tt - 0.9)) ** 1.5 * 2.4
        ks.append((tt, Vector((0, y, z))))
    key(j, 'location', ks, interp='LINEAR')
    key(j, 'rotation_euler', [(0, Vector((0, 0, 0))), (0.6, Vector((0, 0, 0))), (1.8, Vector((math.radians(7), 0, 0))), (d + 0.5, Vector((math.radians(8), 0, 0)))])
    C = Vector((-30.0, -40.0, 1.7))
    arm = guy('Crew', (C.x + 1.56, C.y + 8.86, 0), (-8, 200, 0), 'worker')
    if arm:
        pose(arm, 0.0, STANCES['relax']); pose(arm, 0.7, STANCES['wave_r'])
        for k in range(6):
            pose(arm, 0.9 + k * 0.55, {'upperarm01.R': (75, 0, 18 if k % 2 else 42)})
    path = []
    for tt, jp in ks:
        if tt > d + 0.01: break
        cp = C + Vector((0.3, 1.5, 0.05)) * (tt / d)
        dv = (jp + Vector((0, 0, 1.5)) - cp).normalized()
        path.append((tt, cp, cp + dv * 60 + Vector((-1.2, 0, -0.6))))
    camera(path, lens=70, fstop=8)
    sc.camera.data.dof.focus_object = None; sc.camera.data.dof.focus_distance = 170

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13]

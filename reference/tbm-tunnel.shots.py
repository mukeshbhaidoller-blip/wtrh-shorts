# Shots for "This Machine Builds the Tunnel It Digs" (tunnel boring machine, problem -> fix chain).
# Z up, metres. Tunnel axis = Y; the machine digs toward +Y. Angles around the tunnel axis are measured in the XZ plane
# from +X (90 = crown, 180 = left wall x<0, 270 = invert). Cut-away shots keep only x <= 0 (camera on the +X side).
# Person faces -Y at rot_z=0. t = seconds from the shot start.
import bmesh
from mathutils import Matrix

def dur(a, b): return (b - a) / FPS

R0, R1 = 3.0, 3.3          # segment lining inner / outer radius
RS0, RS1 = 3.34, 3.46      # shield skin
RX = 3.5                   # bored (excavated) radius
W = 1.5                    # ring width
ZC = 3.0                   # tunnel axis height for the inside shots (invert at z=0)
DECK = 0.6                 # walkway deck top
YR0 = -6.0                 # last ring front face (machine at its start position)

# ---------------------------------------------------------------- materials
def _rand_vec(m, amt=7.0):
    """Offset each object's texture by its random value so linked copies don't repeat."""
    nt = m.node_tree
    mp = next((n for n in nt.nodes if n.type == 'MAPPING'), None)
    tc = next((n for n in nt.nodes if n.type == 'TEX_COORD'), None)
    if not mp or not tc: return m
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'SCALE'; mul.inputs['Scale'].default_value = amt
    nt.links.new(oi.outputs['Random'], mul.inputs[0])
    add = nt.nodes.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    nt.links.new(tc.outputs['Object'], add.inputs[0]); nt.links.new(mul.outputs['Vector'], add.inputs[1])
    nt.links.new(add.outputs['Vector'], mp.inputs['Vector'])
    return m

def steel_mat(name, col, rough=0.4, metal=0.6, var=0.18, scale=1.4, coat=0.0):
    """Procedural painted / bare steel: noisy colour + roughness, fine scratches."""
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); oi = nt.nodes.new('ShaderNodeObjectInfo')
    add = nt.nodes.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    nt.links.new(tc.outputs['Object'], add.inputs[0]); nt.links.new(oi.outputs['Location'], add.inputs[1])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    nt.links.new(add.outputs['Vector'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * (1 - var) for c in col], 1); ramp.color_ramp.elements[1].color = (*[min(1, c * (1 + var * 0.5)) for c in col], 1)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough * 0.7; rr.inputs['To Max'].default_value = min(1, rough * 1.5)
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = scale * 6; nt.links.new(add.outputs['Vector'], nz2.inputs['Vector'])
    nt.links.new(nz2.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
    p.inputs['Metallic'].default_value = metal
    if coat: inp(p, 'Coat Weight', 'Clearcoat').default_value = coat
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08
    nt.links.new(nz2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def mats():
    M = {}
    m, p = mat_textured('SegConc', ['concrete_floor_02', 'concrete_pavement'], 0.55, (0.6, 0.6, 0.58), tint=(1.08, 1.07, 1.03), bump=0.35)
    M['conc'] = _rand_vec(m)
    m, p = mat_textured('Invert', ['concrete_floor_worn_001', 'concrete_floor_02'], 0.45, (0.5, 0.5, 0.48), bump=0.5)
    M['invert'] = m
    m, p = mat_textured('PitWall', ['concrete_floor_worn_001', 'concrete_pavement'], 0.12, (0.55, 0.55, 0.52), bump=0.6)
    M['pit'] = m
    M['dirt'] = mat_textured('Dirt', ['brown_mud_02', 'dry_ground_rocks'], 0.45, (0.33, 0.25, 0.18), bump=0.9)[0]
    M['clay'] = mat_textured('Clay', ['brown_mud_02'], 0.3, (0.45, 0.36, 0.26), tint=(1.45, 1.15, 0.85), bump=0.8)[0]
    M['till'] = mat_textured('Till', ['dry_ground_rocks'], 0.1, (0.42, 0.4, 0.37), tint=(0.62, 0.62, 0.62), bump=0.9)[0]
    M['fill'] = mat_textured('Fill', ['brown_mud_02'], 0.25, (0.3, 0.22, 0.15), tint=(0.85, 0.75, 0.62), bump=0.8)[0]
    M['rock'] = mat_textured('Rock', ['concrete_floor_02'], 0.7, (0.45, 0.43, 0.4), tint=(0.72, 0.7, 0.68), bump=1.6)[0]
    M['plate'] = _rand_vec(mat_textured('Diamond', ['metal_plate'], 0.5, (0.45, 0.46, 0.47), tint=(0.9, 0.9, 0.9), bump=0.3)[0])
    M['steel'] = steel_mat('Steel', (0.3, 0.31, 0.32), 0.35, 0.85)
    M['dsteel'] = steel_mat('DarkSteel', (0.07, 0.075, 0.08), 0.5, 0.5)
    m, p = mat_textured('Rust', ['rusty_metal_02'], 0.6, (0.35, 0.2, 0.12), tint=(0.42, 0.4, 0.38), bump=0.4)
    p.inputs['Metallic'].default_value = 0.5; M['rust'] = _rand_vec(m)
    M['shield'] = steel_mat('ShieldPaint', (0.42, 0.48, 0.44), 0.45, 0.2, coat=0.15)
    M['head'] = steel_mat('HeadPaint', (0.34, 0.07, 0.035), 0.42, 0.15, var=0.3, coat=0.2)
    M['newseg'] = _rand_vec(mat_textured('NewSeg', ['concrete_floor_02'], 0.55, (0.7, 0.7, 0.68), tint=(1.12, 1.1, 1.06), bump=0.3)[0])
    M['hole'] = mat_simple('HoleDark', (0.03, 0.025, 0.02), 0.8)[0]
    M['yellow'] = steel_mat('Yellow', (0.8, 0.5, 0.03), 0.45, 0.1, var=0.15, coat=0.2)
    M['orange'] = steel_mat('Orange', (0.8, 0.28, 0.03), 0.4, 0.1, var=0.15, coat=0.3)
    M['grey'] = steel_mat('Cabinet', (0.5, 0.52, 0.53), 0.4, 0.2, var=0.08)
    M['chrome'] = mat_simple('Chrome', (0.92, 0.92, 0.94), 0.08, metal=1.0)[0]
    M['disc'] = mat_simple('DiscSteel', (0.7, 0.7, 0.72), 0.28, metal=1.0)[0]
    M['dark'] = mat_simple('Dark', (0.012, 0.011, 0.01), 0.9)[0]
    M['rubber'] = mat_simple('Belt', (0.025, 0.025, 0.025), 0.75)[0]
    M['duct'] = duct_mat()
    M['led'] = mat_emit('LED', (1.0, 0.93, 0.8), 30)[0]
    M['asphalt'] = mat_textured('Asphalt', ['asphalt_02'], 0.25, (0.08, 0.08, 0.08))[0]
    M['walk'] = mat_textured('Sidewalk', ['concrete_pavement'], 0.4, (0.6, 0.6, 0.58))[0]
    M['brick1'] = mat_textured('Brick1', ['red_brick_03', 'brick_wall_001'], 0.35, (0.5, 0.2, 0.15))[0]
    M['brick2'] = mat_textured('Brick2', ['brick_wall_001', 'red_brick_03'], 0.35, (0.6, 0.5, 0.4), tint=(0.9, 0.85, 0.8))[0]
    M['glass'] = mat_simple('Window', (0.05, 0.07, 0.09), 0.05, metal=0.6)[0]
    M['gravel'] = mat_textured('Gravel', ['gravel_floor_02'], 0.5, (0.4, 0.38, 0.35))[0]
    M['hat'] = mat_simple('HatWhite', (0.86, 0.86, 0.84), 0.35)[0]
    for m in M.values(): m.use_fake_user = True   # MPFB purges unused materials when it builds a person
    return M

def duct_mat():
    m, nt, p = nodes_mat('Duct')
    p.inputs['Base Color'].default_value = (0.82, 0.62, 0.06, 1); p.inputs['Roughness'].default_value = 0.6
    tc = nt.nodes.new('ShaderNodeTexCoord'); wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.inputs['Scale'].default_value = 1.2
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.5
    nt.links.new(wv.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def vol_mat(name, col=(0.55, 0.45, 0.34), dens=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (*col, 1); v.inputs['Density'].default_value = dens
    nt.links.new(v.outputs['Volume'], o.inputs['Volume']); return m, v

# ---------------------------------------------------------------- geometry helpers
def _finish(name, verts, faces, mat, loc=(0, 0, 0), sharp=35):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update(); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for pg in me.polygons: pg.use_smooth = True
    try: me.set_sharp_from_angle(angle=math.radians(sharp))
    except Exception:
        for pg in me.polygons: pg.use_smooth = False
    o = bpy.data.objects.new(name, me); link(o); o.location = loc
    if mat: me.materials.append(mat)
    return o

def arc(name, r0, r1, a0, a1, y0, y1, mat=None, loc=(0, 0, 0), step=3.0):
    """Annular sector around the Y axis (angles in degrees, XZ plane), from y0 to y1."""
    A0, A1 = math.radians(a0), math.radians(a1)
    full = abs(a1 - a0) >= 359.99
    n = max(2, int(abs(a1 - a0) / step))
    cnt = n if full else n + 1
    prof = [(r0, y0), (r1, y0), (r1, y1), (r0, y1)]
    verts, faces = [], []
    for i in range(cnt):
        a = A0 + (A1 - A0) * i / n
        for r, y in prof: verts.append((r * math.cos(a), y, r * math.sin(a)))
    for i in range(cnt if full else cnt - 1):
        j = (i + 1) % cnt
        for k in range(4):
            k2 = (k + 1) % 4; faces.append((i * 4 + k, i * 4 + k2, j * 4 + k2, j * 4 + k))
    if not full:
        faces.append((0, 1, 2, 3)); e = (cnt - 1) * 4; faces.append((e + 3, e + 2, e + 1, e))
    return _finish(name, verts, faces, mat, loc)

def tube(name, r, zc, y0, y1, mat, a0=0, a1=360, na=72, dl=0.25, disp=0.0, dscale=0.6, seed=0, x0=0.0):
    """Rough open tube (single surface) for bored / hand-dug holes."""
    full = abs(a1 - a0) >= 359.99
    n = na if full else na + 1
    nl = max(2, int(abs(y1 - y0) / dl) + 1)
    verts, faces = [], []
    for j in range(nl):
        y = y0 + (y1 - y0) * j / (nl - 1)
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * i / na)
            verts.append((x0 + r * math.cos(a), y, zc + r * math.sin(a)))
    for j in range(nl - 1):
        for i in range(n if full else n - 1):
            i2 = (i + 1) % n; faces.append((j * n + i, j * n + i2, (j + 1) * n + i2, (j + 1) * n + i))
    o = _finish(name, verts, faces, mat, sharp=80)
    if disp:
        tx = bpy.data.textures.new(name + 'N', 'CLOUDS'); tx.noise_scale = dscale; tx.noise_depth = 4
        md = o.modifiers.new('d', 'DISPLACE'); md.texture = tx; md.strength = disp; md.mid_level = 0.5
        md.texture_coords = 'GLOBAL'
    return o

def rotY(o, deg): o.rotation_euler = (0, math.radians(-deg), 0)   # local +X -> angle deg in the XZ plane

def keep(a, half):
    return (not half) or math.cos(math.radians(a)) <= 0.02

# ---------------------------------------------------------------- lining
_SEGME = {}
def segment_obj(M, y, mid, name='Seg', zc=ZC, x0=0.0):
    """One 60-degree precast segment, origin on the tunnel axis, spanning y..y+W."""
    me = bpy.data.meshes.get(_SEGME.get('name', '#none'))
    if me is None:
        t = arc('SegProto', R0, R1, 90 - 29.75, 90 + 29.75, 0.006, W - 0.006, M['conc'], step=2.5)
        me = t.data; me.name = 'SegMesh'; _SEGME['name'] = me.name
        bpy.data.objects.remove(t)
    o = bpy.data.objects.new(name, me); link(o)
    o.location = (x0, y, zc); o.rotation_euler = (0, math.radians(-(mid - 90)), 0)
    return o

def ring(M, y, k=0, half=False, zc=ZC, x0=0.0, objs=None):
    off = 30 if half else (0 if k % 2 == 0 else 30)
    out = []
    for s in range(6):
        mid = 90 + off + 60 * s
        if half and math.cos(math.radians(mid)) > -0.4: continue
        out.append(segment_obj(M, y, mid, zc=zc, x0=x0))
    return out

def lining(M, y0, y1, half=False, zc=ZC, x0=0.0, backing=True):
    """Rings from y0 up to y1 (y1 = front face of the last ring)."""
    rs = []; n = int(round((y1 - y0) / W))
    for k in range(n):
        rs.append(ring(M, y1 - (k + 1) * W, k, half, zc, x0))
    if backing:   # dark grout / ground behind the joints
        b = arc('Backing', R1 + 0.005, R1 + 0.06, 90 if half else 0, 270 if half else 360, y0, y1, M['dark'])
        b.location = (x0, 0, zc)
    return rs

def tunnel_lights(M, y0, y1, every=7.0, zc=ZC, side=-1, power=90, half=False):
    out = []
    y = y0
    while y < y1:
        z = zc + 1.7; x = side * (math.sqrt(R0 ** 2 - 1.7 ** 2) - 0.08)
        box('Lamp', (0.1, 1.2, 0.08), (x, y, z), M['led'])
        L = light('POINT', (x - side * 0.25, y, z - 0.1), power, (1, 0.9, 0.76), 0.3)
        L.data.use_shadow = True; out.append(L)
        y += every
    return out

# ---------------------------------------------------------------- the cutterhead
def cutterhead(M, Rc, half=False, name='Head'):
    """Origin = centre of the front face; front points +Y. Returns the root empty (rotate it about Y)."""
    root = bpy.data.objects.new(name, None); link(root)
    def par(o): o.parent = root; return o
    a0, a1 = (90, 270) if half else (0, 360)
    par(arc('HeadBody', 0.001, Rc - 0.02, a0, a1, -0.9, 0.0, M['rust'], step=3))
    par(arc('HeadRim', Rc - 0.16, Rc, a0, a1, -0.25, 0.14, M['steel'], step=3))
    for rr in (0.3 * Rc, 0.6 * Rc, 0.9 * Rc):
        par(arc('FaceWeld', rr, rr + 0.05, a0, a1, 0.0, 0.025, M['steel'], step=3))
    sw = max(0.36, 0.1 * Rc) if Rc < 5 else 0.55
    for k in range(6):
        a = 90 + 60 * k
        if not keep(a, half): continue
        sp = bpy.data.objects.new('Spoke', None); link(sp); par(sp); rotY(sp, a)
        o = box('SpokeArm', (Rc - 0.5, 0.3, sw), ((Rc - 0.5) / 2 + 0.42, 0.13, 0), M['head'], bevel=0.03); o.parent = sp
        n = int((Rc - 0.9) / 0.48)
        for i in range(n):
            r = 0.75 + i * 0.48 + (0.22 if k % 2 else 0.0)
            if r > Rc - 0.25: break
            d = cyl('Disc', 0.215, 0.07, (r, 0.36, 0), M['disc'], rot=(0, math.pi / 2, 0), verts=40, bevel=0.012); d.parent = sp
            h = box('Saddle', (0.34, 0.18, sw * 0.9), (r, 0.27, 0), M['steel'], bevel=0.02); h.parent = sp
        for i in range(int(Rc / 0.7)):   # scraper teeth along both spoke edges
            r = 0.9 + i * 0.7
            for sgn in (-1, 1):
                tth = box('Scraper', (0.24, 0.16, 0.08), (r, 0.22, sgn * (sw / 2 + 0.05)), M['steel'], bevel=0.015); tth.parent = sp
    for k in range(6):   # muck openings between the spokes
        a = 120 + 60 * k
        if not keep(a, half): continue
        par(arc('Opening', 0.32 * Rc, 0.84 * Rc, a - 6, a + 6, -0.06, 0.012, M['hole'], step=2))
        par(arc('Grill', 0.32 * Rc, 0.84 * Rc, a - 0.8, a + 0.8, -0.02, 0.05, M['steel'], step=1))
    bpy.ops.mesh.primitive_cone_add(radius1=0.55, radius2=0.18, depth=0.55, location=(0, 0.27, 0), rotation=(-math.pi / 2, 0, 0), vertices=48)
    c = bpy.context.active_object; c.name = 'Nose'; c.data.materials.append(M['steel']); par(c)
    if half:   # half cone: hide the +x part with a quick bisect
        bm = bmesh.new(); bm.from_mesh(c.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
        bm.to_mesh(c.data); bm.free()
    return root

def shield(M, r0, r1, y0, y1, half=False, mat=None, seams=True):
    a0, a1 = (90, 270) if half else (0, 360)
    out = [arc('Shield', r0, r1, a0, a1, y0, y1, mat or M['shield'], step=2.5)]
    if seams:
        y = y0 + 2.2
        while y < y1 - 0.5:
            out.append(arc('Seam', r1 - 0.002, r1 + 0.012, a0, a1, y, y + 0.05, M['steel'], step=2.5)); y += 2.6
    return out

# ---------------------------------------------------------------- the machine inside the tunnel
def machine(M, half=False, zc=ZC, rods='world', backup=True, erector=True, head=False, y_last=YR0, back_len=46):
    """Root empty at (0, 0, zc): shield, bulkhead, thrust jacks, erector, trailing gear. Move root.location.y to advance.
    rods='world': rods + shoes stay on the last ring (stretch with key_rods)."""
    root = bpy.data.objects.new('TBM', None); link(root); root.location = (0, 0, zc)
    def par(o):
        o.parent = root; return o
    a0, a1 = (90, 270) if half else (0, 360)
    for o in shield(M, RS0, RS1, -10.0, -0.6, half): par(o)
    par(arc('Bulkhead', 0.001, RS0, a0, a1, -2.3, -2.1, M['dsteel'], step=3))
    par(arc('BulkRing', 2.0, RS0, a0, a1, -2.45, -2.3, M['yellow'], step=3))
    # man-lock door + screw conveyor
    par(cyl('Manlock', 0.62, 1.6, (-1.3, -3.1, 1.05), M['grey'], rot=(math.pi / 2, 0, 0), verts=40))
    sc = cyl('ScrewConv', 0.42, 9.0, (0.6 if not half else -0.6, -6.6, -2.05), M['orange'], rot=(math.pi / 2 - math.radians(7), 0, 0), verts=36)
    par(sc)
    if not half: sc.hide_render = True
    if head:
        h = cutterhead(M, RX - 0.02, half); par(h); h.location = (0, 0.0, 0)
    jacks = []
    for k in range(16):
        a = 11.25 + 22.5 * k
        if 55 < a < 125 or not keep(a, half): continue
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        rj = 3.15
        body = cyl('JackBody', 0.135, 3.0, (rj * ca, -3.9, rj * sa), M['orange'], rot=(math.pi / 2, 0, 0), verts=28)
        par(body)
        cap = cyl('JackCap', 0.17, 0.12, (rj * ca, -5.42, rj * sa), M['steel'], rot=(math.pi / 2, 0, 0), verts=28); par(cap)
        jacks.append((rj * ca, rj * sa, a))
    rodobjs = []
    for (x, z, a) in jacks:
        # rod: origin on the ring face, mesh +Y 1 m, scaled in Y to reach the jack body
        r = cyl('Rod', 0.075, 1.0, (0, 0, 0), M['chrome'], rot=(math.pi / 2, 0, 0), verts=24)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        r.data.transform(Matrix.Translation((0, 0.5, 0)))
        holder = bpy.data.objects.new('RodRoot', None); link(holder)
        r.parent = holder
        shoe = box('Shoe', (0.38, 0.1, 0.26), (0, 0.05, 0), M['steel'], bevel=0.02); shoe.parent = holder
        shoe.rotation_euler = (0, math.radians(-(a - 90)), 0)
        if rods == 'machine':
            holder.parent = root; holder.location = (x, y_last + 0.02, z)
        else:
            holder.location = (x, y_last + 0.02, z + zc)
        rodobjs.append((holder, r))
    E = None
    if erector:
        par(arc('ErectRing', 2.05, 2.3, a0, a1, -4.1, -3.8, M['yellow'], step=3))
        E = bpy.data.objects.new('Erector', None); link(E); par(E); E.location = (0, y_last, 0)
        hub = cyl('Hub', 0.55, 1.2, (0, W / 2, 0), M['yellow'], rot=(math.pi / 2, 0, 0), verts=40); hub.parent = E
    if backup:
        bk = []
        y = -11.0
        while y > -11.0 - back_len:
            for x in ((-1.95,) if half else (-1.95, 2.0)):
                bk.append(box('Post', (0.18, 0.18, 3.8), (x, y, 0.8 + 1.9 - zc), M['yellow']))
            bk.append(box('Beam', (2.0 if half else 4.0, 0.2, 0.22), (-1.0 if half else 0.02, y, 4.6 - zc), M['yellow']))
            bk.append(box('Cabinet', (0.7, 1.4, 1.5), (-1.35, y - 1.4, DECK + 0.75 - zc), M['grey'], bevel=0.02))
            y -= 4.5
        for o in bk: par(o)
        par(box('Deck', (2.6 if not half else 1.8, back_len + 2, 0.1), (-0.35 if not half else -1.0, -11.0 - back_len / 2, DECK - 0.05 - zc), M['plate']))
        for i, (x, z) in enumerate(((-1.55, 4.3), (-1.4, 4.38), (-1.7, 4.15))):
            par(cyl('Hose', 0.05 + 0.02 * i, back_len, (x, -11.0 - back_len / 2, z - zc), M['dark'] if i != 1 else M['orange'], rot=(math.pi / 2, 0, 0), verts=16))
    return dict(root=root, rods=rodobjs, E=E, y_last=y_last)

def key_rods(T, pts):
    """pts: [(t, machine_y)] -> stretch every world rod so it reaches its jack body (body back end at y=-5.4)."""
    for holder, r in T['rods']:
        if holder.parent is not None: continue
        key(r, 'scale', [(t, Vector((1, max(0.02, (my - 5.36) - T['y_last']), 1))) for t, my in pts])

def conveyor(M, y0, y1, zc=ZC, x=1.45, belt_v=2.4, d=4.0, muck=True, parent=None):
    out = []
    zb = 1.85
    L = y1 - y0
    out.append(box('BeltFrameL', (0.08, L, 0.18), (x - 0.42, (y0 + y1) / 2, zb - 0.12), M['yellow']))
    out.append(box('BeltFrameR', (0.08, L, 0.18), (x + 0.42, (y0 + y1) / 2, zb - 0.12), M['yellow']))
    out.append(box('Belt', (0.76, L, 0.03), (x, (y0 + y1) / 2, zb - 0.02), M['rubber']))
    y = y0
    while y < y1:
        out.append(cyl('Roller', 0.06, 0.8, (x, y, zb - 0.1), M['steel'], rot=(0, math.pi / 2, 0), verts=16))
        out.append(box('Leg', (0.06, 0.06, zb - DECK), (x - 0.4, y, (zb + DECK) / 2 - 0.1), M['yellow']))
        y += 1.5
    if muck:
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=8, y_subdivisions=int(L * 5), size=1, location=(x, (y0 + y1) / 2, zb + 0.02))
        g = bpy.context.active_object; g.name = 'Muck'; g.scale = (0.5, L, 1)
        bpy.ops.object.transform_apply(scale=True)
        for v in g.data.vertices:
            v.co.z += 0.09 * (1 - (abs(v.co.x) / 0.25) ** 2) if abs(v.co.x) < 0.25 else 0
        tx = bpy.data.textures.new('MuckN', 'CLOUDS'); tx.noise_scale = 0.12
        emp = bpy.data.objects.new('MuckFlow', None); link(emp)
        md = g.modifiers.new('d', 'DISPLACE'); md.texture = tx; md.strength = 0.12; md.texture_coords = 'OBJECT'; md.texture_coords_object = emp
        g.data.materials.append(M['dirt']); bpy.ops.object.shade_smooth()
        key(emp, 'location', [(0, Vector((0, 0, 0))), (d, Vector((0, -belt_v * d, 0)))], interp='LINEAR')
        out.append(g)
    return out

def vent_duct(M, y0, y1, zc=ZC):
    o = cyl('Duct', 0.42, y1 - y0, (-1.38, (y0 + y1) / 2, zc + 2.15), M['duct'], rot=(math.pi / 2, 0, 0), verts=40)
    return o

# ---------------------------------------------------------------- falling ground
def rock_chunk(M, loc, size, seed, mat=None):
    random.seed(seed)
    o = sphere('Chunk', size, loc, mat or M['dirt'], sub=2)
    o.scale = (random.uniform(0.7, 1.3), random.uniform(0.7, 1.3), random.uniform(0.5, 0.9))
    o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
    tx = bpy.data.textures.new('ChN', 'CLOUDS'); tx.noise_scale = 0.4 * size
    md = o.modifiers.new('d', 'DISPLACE'); md.texture = tx; md.strength = size * 0.45
    return o

def drop(o, t0, zfloor, d, spin=None, drift=(0, 0)):
    p0 = Vector(o.location); r0 = Vector(o.rotation_euler)
    spin = spin or Vector((random.uniform(-4, 4), random.uniform(-4, 4), random.uniform(-2, 2)))
    pts, rots = [(max(0.0, t0 - 0.02), p0.copy())], [(max(0.0, t0 - 0.02), r0.copy())]
    t = 0.0; dt = 1 / 24
    while True:
        t += dt; z = p0.z - 0.5 * 9.81 * t * t
        if z <= zfloor or t0 + t > d + 0.5:
            pts.append((t0 + t, Vector((p0.x + drift[0] * t, p0.y + drift[1] * t, max(z, zfloor)))))
            rots.append((t0 + t, r0 + spin * t)); break
        pts.append((t0 + t, Vector((p0.x + drift[0] * t, p0.y + drift[1] * t, z)))); rots.append((t0 + t, r0 + spin * t))
    key(o, 'location', pts, interp='LINEAR'); key(o, 'rotation_euler', rots, interp='LINEAR')
    return t0 + t

def grains(M, n, x, y, z, zfloor, d, seed=1, spread=0.6, mat=None):
    random.seed(seed)
    proto = sphere('Grain', 0.025, (0, 0, -50), mat or M['dirt'], sub=1)
    for i in range(n):
        g = dup(proto, (x + random.uniform(-spread, spread), y + random.uniform(-spread, spread), z + random.uniform(-0.05, 0.05)))
        s = random.uniform(0.4, 1.6); g.scale = (s, s, s)
        drop(g, random.uniform(0, d * 0.9), zfloor, d)

def dust(M, loc, t0, d, size=1.2, peak=0.35, col=(0.5, 0.42, 0.32)):
    m, v = vol_mat('Dust', col, 0.0)
    o = sphere('DustPuff', 1.0, loc, m, sub=2)
    key(o, 'scale', [(t0, Vector((0.2, 0.2, 0.1)) * size), (t0 + 0.7, Vector((1.0, 1.0, 0.6)) * size), (d, Vector((1.6, 1.6, 0.9)) * size)])
    key_socket(v.inputs['Density'], [(max(0, t0 - 0.01), 0.0), (t0 + 0.4, peak), (d + 0.5, peak * 0.35)])
    return o

# ---------------------------------------------------------------- people
def hardhat(arm, M):
    """White hard hat: a dome + brim. Bone-parented children sit at the bone TAIL (top of the head)."""
    if arm is None: return
    hm = mat_simple('HatWhite', (0.86, 0.86, 0.84), 0.35)[0]
    h = sphere('HardHat', 0.125, (0, 0, 0), hm, sub=3)
    bm = bmesh.new(); bm.from_mesh(h.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
    bm.to_mesh(h.data); bm.free()
    h.scale = (1.0, 1.15, 0.95)
    brim = cyl('Brim', 0.15, 0.012, (0, 0, 0), hm, verts=32); brim.parent = h; brim.location = (0, 0.02, 0.004); brim.scale = (1.0, 1.12, 1.0)
    hold(arm, h, 'head', (0, -0.075, 0.012), (-90, 0, 0))

def guy(M, name, loc, face, outfit='worker', hat=True, **kw):
    dv = Vector(face) - Vector(loc); th = math.atan2(dv.x, -dv.y)
    arm = person(name, loc=loc, rot_z=th, outfit=outfit, stance='relax', **kw)
    if hat and outfit == 'worker': hardhat(arm, M)
    return arm

def look_up(arm, t, deg=-18):
    pose(arm, t, {'neck01': (deg, 0, 0)})

def flashlight(arm, M, target):
    """Spot light + small torch body; the torch is held in the right hand when MPFB is there."""
    L = light('SPOT', (0, 0, 0), 260, (1, 0.93, 0.8), 0.04, spot=30, blend=0.5)
    L.data.use_shadow = True
    tg = bpy.data.objects.new('FlTarget', None); link(tg); tg.location = target
    c = L.constraints.new('TRACK_TO'); c.target = tg; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    if arm is not None:
        t = cyl('Torch', 0.025, 0.2, (0, 0, 0), M['dark'], verts=16); hold(arm, t, 'wrist.R', (0, 0.1, 0.0), (90, 0, 0))
        L.parent = arm; L.parent_type = 'BONE'; L.parent_bone = 'wrist.R'; L.location = (0, 0.22, 0)
    return L, tg

# ---------------------------------------------------------------- scenes
def city_cutaway(M, zc, cutter_r, y0=-45, y1=45, face_y=4.0, bore=None):
    """Earth block x in [-32, 0] cut by the tunnel bore (a hidden cylinder from y0 to face_y), with a street on top."""
    if bore is None:
        bore = cyl('Bore', cutter_r, 1.0, (0, 0, zc), None, rot=(math.pi / 2, 0, 0), verts=96)
        bore.scale = (1, 1, face_y - (y0 - 5)); bore.location = (0, (face_y + y0 - 5) / 2, zc)
    bore.hide_render = True; bore.display_type = 'WIRE'
    layers = [(0.0, -1.6, M['fill']), (-1.6, -6.5, M['clay']), (-6.5, -40, M['till'])]
    for zt, zb, m in layers:
        b = box('Strata', (32, y1 - y0, zt - zb), (-16, (y0 + y1) / 2, (zt + zb) / 2), m)
        md = b.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = bore
        try: md.solver = 'EXACT'
        except Exception: pass
    # street
    box('Road', (8.5, y1 - y0, 0.06), (-4.25, (y0 + y1) / 2, 0.03), M['asphalt'])
    lp = mat_simple('LinePaint', (0.85, 0.72, 0.2), 0.5)[0]
    for yy in range(int(y0), int(y1), 6):
        box('Dash', (0.12, 2.6, 0.01), (-4.2, yy, 0.065), lp)
    box('Curb', (0.25, y1 - y0, 0.2), (-8.6, (y0 + y1) / 2, 0.1), M['walk'])
    box('Sidewalk', (3.2, y1 - y0, 0.16), (-10.3, (y0 + y1) / 2, 0.08), M['walk'])
    random.seed(4)
    y = y0; i = 0
    while y < y1:
        wdt = random.uniform(8, 13); h = random.uniform(9, 22)
        bm = M['brick1'] if i % 2 else M['brick2']
        box('Bldg', (12, wdt - 0.4, h), (-18, y + wdt / 2, h / 2), bm)
        win = box('WinProto', (0.08, 1.2, 1.5), (-11.98, y + 1.6, 3.0), M['glass'])
        fy = y + 1.6
        while fy < y + wdt - 1.4:
            fz = 3.0
            while fz < h - 1.5:
                if not (fy == y + 1.6 and fz == 3.0): dup(win, (-11.98, fy, fz))
                fz += 3.2
            fy += 2.4
        y += wdt; i += 1
    for yy in range(int(y0) + 4, int(y1), 14):
        cyl('LampPole', 0.07, 6.5, (-9.0, yy, 3.25), M['grey'], verts=12)
    return bore

def day_world(rot=40, s=0.85, elev=38, azim=70, e=2.4):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', s, math.radians(rot)); sun(e, elev, azim)

def pit_scene(M, Rc, d, rpm_deg=12.0, L=10.0, pit=(9, 16, 18)):
    """A TBM sitting in its launch shaft, cutterhead facing +Y toward the camera."""
    zc = Rc + 0.55
    px, pb, ph = pit
    box('PitFloor', (2 * px, 3 * pb, 0.4), (0, 0, -0.2), M['pit'])
    box('PitBack', (2 * px, 1.0, ph), (0, -L - 4.5, ph / 2), M['pit'])
    box('PitL', (1.0, 3 * pb, ph), (-px - 0.5, 0, ph / 2), M['pit'])
    box('PitR', (1.0, 3 * pb, ph), (px + 0.5, 0, ph / 2), M['pit'])
    box('PitFront', (2 * px, 1.0, ph), (0, pb + 0.5, ph / 2), M['pit'])
    for z in (ph * 0.62, ph * 0.9):
        cyl('Strut', 0.45 if Rc < 5 else 0.8, 2 * px, (0, -L * 0.35, z), M['yellow'], rot=(0, math.pi / 2, 0), verts=32)
        box('Waler', (0.5, 3 * pb, 0.6 if Rc < 5 else 1.0), (-px + 0.25, 0, z), M['yellow'])
        box('Waler', (0.5, 3 * pb, 0.6 if Rc < 5 else 1.0), (px - 0.25, 0, z), M['yellow'])
    for x in (-0.55 * Rc, 0.55 * Rc):
        top = zc - math.sqrt(Rc ** 2 - x ** 2) + 0.06
        box('Cradle', (0.6 * Rc / 3.5, L + 3, top), (x, -L / 2 - 0.5, top / 2), M['steel'])
    sh = shield(M, Rc - 0.12, Rc - 0.04, -L - 0.9, -0.9)
    for o in sh: o.location = (0, 0, zc)
    stripe = arc('Stripe', Rc - 0.035, Rc - 0.03, 0, 360, -2.4, -1.9, M['orange']); stripe.location = (0, 0, zc)
    h = cutterhead(M, Rc); h.location = (0, 0, zc)
    key(h, 'rotation_euler', [(0, Vector((0, 0, 0))), (d, Vector((0, math.radians(rpm_deg * d), 0)))], interp='LINEAR')
    return zc

def disc_scene(M, d):
    world_hdri('studio_small_09', 0.04, 0, 'studio')
    rk = plane('RockFace', 8, 8, (0, 0, 0), M['rock'], subdiv=6); rk.rotation_euler = (math.radians(-90), 0, 0)
    tx = bpy.data.textures.new('RockN', 'CLOUDS'); tx.noise_scale = 0.35
    md = rk.modifiers.new('d', 'DISPLACE'); md.texture = tx; md.strength = 0.06; md.direction = 'NORMAL'
    sub = rk.modifiers.new('s', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
    rk.modifiers.move(1, 0)
    # earlier kerfs (grooves) left by other cutters: dark concentric lines
    for z in (-0.95, -0.47, 0.47, 0.95):
        box('Kerf', (8, 0.03, 0.05), (0, -0.006, z), M['dark'])
    kerf = box('KerfNew', (1, 0.03, 0.05), (0, -0.004, 0), M['dark'])
    # the disc rolls along +X across the face at z=0
    x0, x1 = -1.6, 1.3
    rig = bpy.data.objects.new('DiscRig', None); link(rig)
    key(rig, 'location', [(0, Vector((x0, 0.24, 0))), (d, Vector((x1, 0.24, 0)))], interp='LINEAR')
    disc = cyl('Disc', 0.23, 0.08, (0, 0, 0), M['disc'], verts=64, bevel=0.015); disc.parent = rig
    hub = cyl('DiscHub', 0.11, 0.2, (0, 0, 0), M['steel'], verts=32); hub.parent = rig
    key(disc, 'rotation_euler', [(0, Vector((0, 0, 0))), (d, Vector((0, 0, -(x1 - x0) / 0.23)))], interp='LINEAR')
    house = box('Housing', (0.62, 0.26, 0.36), (0, 0.5, 0), M['head'], bevel=0.03); house.parent = rig
    for sgn in (-1, 1):
        cheek = box('Cheek', (0.12, 0.3, 0.05), (0, 0.33, sgn * 0.075), M['steel'], bevel=0.01); cheek.parent = rig
    # kerf grows behind the disc
    key(kerf, 'scale', [(0, Vector((0.01, 1, 1))), (d, Vector((x1 - x0, 1, 1)))], interp='LINEAR')
    key(kerf, 'location', [(0, Vector((x0, -0.004, 0))), (d, Vector(((x0 + x1) / 2, -0.004, 0)))], interp='LINEAR')
    # chips break off just behind the contact point
    random.seed(7)
    n = 26
    for i in range(n):
        t0 = 0.1 + i * (d - 0.3) / n
        xc = x0 + (x1 - x0) * t0 / d - 0.05
        c = rock_chunk(M, (xc, 0.03, random.uniform(-0.08, 0.08)), random.uniform(0.018, 0.045), 100 + i, M['rock'])
        drop(c, t0, -1.6, d, drift=(random.uniform(-0.4, 0.1), random.uniform(0.2, 0.9)))
    L = light('SPOT', (-1.8, 1.4, 1.3), 900, (1, 0.9, 0.75), 0.2, spot=55, blend=0.6); aim(L, (0, 0, 0))
    light('AREA', (1.5, 1.8, -0.6), 120, (0.7, 0.8, 1.0), 1.5).rotation_euler = (math.radians(-110), math.radians(40), 0)
    dust(M, (0.2, 0.15, -0.15), 0.2, d, size=0.5, peak=0.25)

# ---------------------------------------------------------------- shots
def S00(a, b):  # hook: cut-away of a city street; a hand-dug side tunnel underneath; its roof caves in on the digger
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(30, 0.85, 36, 65, 2.2)
    zc = -4.5; r = 1.35
    city_cutaway(M, zc, r, y0=-40, y1=40, face_y=2.0)
    t = tube('DugWall', r + 0.02, zc, -40, 2.0, M['dirt'], 90, 270, na=48, dl=0.2, disp=0.22, dscale=0.5)
    floor = box('DugFloor', (2.4, 42, 0.3), (-1.2, -19, zc - 1.05), M['dirt'])
    lamp = light('POINT', (-0.6, -1.0, zc + 0.3), 140, (1, 0.8, 0.55), 0.15)
    random.seed(3)
    for i in range(9):
        c = rock_chunk(M, (random.uniform(-1.1, -0.1), random.uniform(-1.8, 1.2), zc + r - 0.15 - random.uniform(0, 0.3)), random.uniform(0.12, 0.3), 20 + i)
        drop(c, d * 0.32 + i * 0.12, zc - 0.85, d)
    grains(M, 50, -0.6, -0.4, zc + r - 0.1, zc - 0.88, d, seed=5, spread=0.9)
    dust(M, (-0.5, -0.3, zc - 0.6), d * 0.45, d, size=1.1, peak=0.3)
    arm = guy(M, 'Digger', (-0.75, -1.9, zc - 0.9), (-0.6, 2.0, zc), 'worker')
    if arm:
        pose(arm, 0.0, STANCES['work_low']); pose(arm, d * 0.4, STANCES['work_low'])
        pose(arm, d * 0.62, {**STANCES['relax'], 'spine02': (0, 0, 0)}); look_up(arm, d * 0.62, -25)
        key(arm, 'location', [(d * 0.45, Vector((-0.75, -1.9, zc - 0.9))), (d * 0.9, Vector((-0.75, -3.0, zc - 0.9)))])
    camera([(0, (8.2, -3.6, -4.6), (-0.6, -1.2, -5.15)), (d, (7.4, -3.2, -4.7), (-0.6, -1.0, -5.15))], lens=22, fstop=9)

def S01(a, b):  # inside the hand-dug tunnel: chunks of the roof crash down between the camera and the worker
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    r = 1.55; zc = 1.2
    tube('DugWall', r, zc, -14, 1.5, M['dirt'], na=64, dl=0.15, disp=0.28, dscale=0.45)
    f = plane('DigFace', 3.6, 3.6, (0, 1.4, zc), M['dirt']); f.rotation_euler = (math.radians(90), 0, 0)
    tx = bpy.data.textures.new('FaceN', 'CLOUDS'); tx.noise_scale = 0.4
    sub = f.modifiers.new('s', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = sub.render_levels = 5
    md = f.modifiers.new('d', 'DISPLACE'); md.texture = tx; md.strength = 0.25; md.direction = 'Y'
    box('DugFloor', (2.8, 16, 0.3), (0, -6, -0.05), M['dirt'])
    shovel_h = cyl('ShovelHandle', 0.018, 1.1, (0.75, 0.6, 0.55), mat_simple('Wood', (0.45, 0.3, 0.16), 0.6)[0], rot=(math.radians(25), 0, 0), verts=12)
    box('ShovelBlade', (0.24, 0.02, 0.3), (0.75, 0.84, 0.08), M['steel']).rotation_euler = (math.radians(25), 0, 0)
    light('POINT', (0.9, -0.2, 0.25), 90, (1, 0.78, 0.5), 0.1)
    bulb = sphere('Bulb', 0.05, (0.3, -0.6, 2.35), mat_emit('Bulb', (1, 0.8, 0.55), 40)[0], sub=2)
    light('POINT', (0.3, -0.6, 2.3), 110, (1, 0.8, 0.55), 0.05)
    cyl('BulbWire', 0.006, 0.3, (0.3, -0.6, 2.55), M['dark'], verts=8)
    arm = guy(M, 'Digger', (-0.2, 0.2, 0.1), (0.0, -6.0, 1.2), 'worker')
    L, tg = flashlight(arm, M, (0.0, -1.2, 2.2))
    if arm is None: L.location = (-0.35, 0.0, 1.2)
    if arm:
        pose(arm, 0.0, {**STANCES['relax'], 'upperarm01.R': (55, 0, 20), 'lowerarm01.R': (25, 0, 0)}); look_up(arm, 0.0, -22)
        key(arm, 'location', [(d * 0.45, Vector((-0.2, 0.2, 0.1))), (d * 0.85, Vector((-0.2, 0.75, 0.1)))])
    random.seed(9)
    for i in range(7):
        c = rock_chunk(M, (random.uniform(-0.6, 0.6), random.uniform(-1.7, -0.7), zc + r - 0.25), random.uniform(0.12, 0.26), 40 + i)
        drop(c, 0.25 + i * 0.13, 0.25, d)
    grains(M, 60, 0.0, -1.2, zc + r - 0.2, 0.12, d, seed=11, spread=0.8)
    dust(M, (0.0, -1.2, 0.5), 0.8, d, size=1.3, peak=0.35)
    camera([(0, (0.35, -4.6, 1.35), (0.0, -0.4, 1.4)), (d, (0.3, -4.9, 1.3), (0.0, -0.4, 1.45))], lens=24, fstop=4)

def S02(a, b):  # the machine: a tunnel boring machine waits in its launch shaft, the camera sinks down past the struts
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(150, 0.9, 62, 120, 2.6)
    zc = pit_scene(M, 3.5, d, rpm_deg=6.0)
    arm = guy(M, 'Engineer', (2.6, 3.4, 0), (0.0, 0.0, 3.0), 'worker')
    if arm:
        key(arm, 'location', [(0, Vector((3.4, 5.2, 0))), (d * 0.7, Vector((2.4, 3.0, 0)))])
        walk(arm, 0.0, d * 0.65); pose(arm, d * 0.8, STANCES['point_r']); look_up(arm, d * 0.8, -15)
    light('AREA', (0, 9, 7), 2500, (1, 0.97, 0.92), 6).rotation_euler = (math.radians(65), 0, math.radians(180))
    camera([(0, (4.0, 13.5, 11.5), (0.0, -1.0, 3.6)), (d, (3.2, 12.0, 5.2), (0.0, -1.0, 3.6))], lens=24, fstop=8)

def S03(a, b):  # close: the cutterhead slowly turns, a worker stands at its foot for scale
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(150, 0.9, 62, 120, 2.6)
    zc = pit_scene(M, 3.5, d, rpm_deg=18.0)
    arm = guy(M, 'Worker', (1.9, 1.7, 0), (0.6, 0.0, 3.0), 'worker')
    if arm: look_up(arm, 0.0, -20); look_up(arm, d, -26)
    light('AREA', (-2, 7, 6), 2200, (1, 0.97, 0.92), 5).rotation_euler = (math.radians(65), 0, math.radians(195))
    camera([(0, (2.6, 8.0, 1.0), (0.0, 0.0, 3.6)), (d, (1.9, 7.0, 0.9), (0.0, 0.0, 3.8))], lens=22, fstop=5)

def S04(a, b):  # macro: one steel disc cutter rolls across the rock and cracks off chips
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    disc_scene(M, d)
    camera([(0, (-1.35, 0.72, 0.45), (-0.3, 0.08, -0.05)), (d, (-0.6, 0.7, 0.42), (0.45, 0.08, -0.05))], lens=30, fstop=3.5)

def S05(a, b):  # a smooth, round bored hole with no lining: a slab of the roof cracks and falls
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    zc = RX
    tube('Bore', RX, zc, -30, 0.5, M['clay'], na=96, dl=0.3, disp=0.05, dscale=0.8)
    f = plane('Face', 7.4, 7.4, (0, 0.4, zc), M['clay']); f.rotation_euler = (math.radians(90), 0, 0)
    for yy, x in ((-9.0, -1.6), (-2.5, 1.4)):
        box('FloodStand', (0.05, 0.05, 1.6), (x, yy, 0.9), M['grey'])
        fl = box('Flood', (0.4, 0.12, 0.3), (x, yy + 0.05, 1.75), M['led'])
        L = light('SPOT', (x, yy + 0.15, 1.75), 3200, (1, 0.92, 0.8), 0.15, spot=90, blend=0.7); aim(L, (0, yy + 6, 4.5))
    light('POINT', (0.0, -12, 1.0), 200, (1, 0.9, 0.76), 0.3)
    light('POINT', (-1.5, -7.0, 1.2), 250, (1, 0.9, 0.76), 0.3)
    random.seed(21)
    for i in range(10):
        ang = math.radians(random.uniform(70, 110)); rr = RX - 0.12
        c = rock_chunk(M, (rr * math.cos(ang), random.uniform(-8.0, -5.5), zc + rr * math.sin(ang)), random.uniform(0.25, 0.55), 60 + i, M['clay'])
        drop(c, d * 0.35 + i * 0.07, 0.25, d)
    grains(M, 50, 0.0, -5.6, zc + RX - 0.1, 0.05, d, seed=13, spread=1.0, mat=M['clay'])
    dust(M, (0, -5.6, 0.8), d * 0.5, d, size=2.0, peak=0.25, col=(0.6, 0.5, 0.38))
    camera([(0, (0.6, -14.5, 2.0), (0.0, -5.0, 4.0)), (d, (0.5, -13.5, 1.95), (0.0, -5.0, 4.2))], lens=22, fstop=6)

def cut_tbm(M, zc, d, my_pts=None, rings_at=None, wide=False):
    """Cut-away diorama with the TBM in the ground under the street. my_pts: [(t, machine_y)] advance keys."""
    my0 = my_pts[0][1] if my_pts else 0.0
    face0 = my0 + 0.3
    bore = cyl('Bore', RX, 1.0, (0, 0, zc), None, rot=(math.pi / 2, 0, 0), verts=128)
    bore.scale = (1, 1, face0 + 70); bore.location = (0, (face0 - 70) / 2, zc)
    if my_pts:
        key(bore, 'location', [(t, Vector((0, (my + 0.3 - 70) / 2, zc))) for t, my in my_pts])
        key(bore, 'scale', [(t, Vector((1, 1, my + 0.3 + 70))) for t, my in my_pts])
    city_cutaway(M, zc, RX, y0=-60, y1=40, face_y=face0, bore=bore)
    T = machine(M, half=True, zc=zc, rods='machine', backup=True, erector=True, head=True, back_len=36)
    T['root'].location = (0, my0, zc)
    if my_pts: key(T['root'], 'location', [(t, Vector((0, my, zc))) for t, my in my_pts])
    h = [o for o in T['root'].children if o.name.startswith('Head')]
    for o in h: key(o, 'rotation_euler', [(0, Vector((0, 0, 0))), (d, Vector((0, math.radians(30 * d), 0)))], interp='LINEAR')
    # rings: static ones behind, plus optional ones that appear (t, y)
    lining(M, -60, my0 + YR0, half=True, zc=zc)
    for t0, yy in (rings_at or []):
        for o in ring(M, yy, 0, True, zc):
            o.hide_render = True; o.keyframe_insert('hide_render', frame=F(0)); o.keyframe_insert('hide_render', frame=F(t0) - 1)
            o.hide_render = False; o.keyframe_insert('hide_render', frame=F(t0))
    for y in range(-56, int(my0) - 8, 8):
        light('POINT', (-1.8, y, zc + 1.4), 70, (1, 0.86, 0.7), 0.3)
    light('POINT', (-1.2, my0 - 4, zc + 0.6), 160, (1, 0.9, 0.75), 0.3)
    return T

def S06(a, b):  # cut-away close-up: the steel shield right behind the cutterhead holds the soil back
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(30, 0.85, 34, 70, 2.3)
    zc = -11.0
    cut_tbm(M, zc, d)
    grains(M, 40, -1.2, -3.0, zc + RX + 0.4, zc + RS1 + 0.02, d, seed=17, spread=1.6, mat=M['clay'])
    camera([(0, (9.5, 2.5, zc + 1.5), (-1.5, -3.2, zc - 1.5)), (d, (8.6, 0.5, zc + 1.2), (-1.5, -3.6, zc - 1.5))], lens=26, fstop=8)

def S07(a, b):  # inside the shield: the erector arm swings a curved concrete segment up to the crown
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    lining(M, -60, YR0)
    T = machine(M, backup=False)
    E = T['E']
    C = bpy.data.objects.new('ErectSlide', None); link(C); C.parent = E
    seg = arc('NewSeg', R0, R1, 61, 119, 0.006, W - 0.006, M['newseg'], step=2.5); seg.parent = C
    grip = box('Gripper', (0.9, 0.9, 0.22), (0, W / 2, R0 - 0.16), M['yellow'], bevel=0.02); grip.parent = C
    for sx in (-0.45, 0.45):
        arm_ = box('ErArm', (0.18, 0.3, 2.1), (sx, W / 2, 1.75), M['yellow'], bevel=0.02); arm_.parent = C
    key(E, 'rotation_euler', [(0, Vector((0, math.radians(-130), 0))), (d * 0.6, Vector((0, math.radians(-25), 0))), (d * 0.78, Vector((0, 0, 0)))])
    key(C, 'location', [(0, Vector((0, 0, -0.5))), (d * 0.78, Vector((0, 0, -0.5))), (d, Vector((0, 0, -0.02)))])
    tunnel_lights(M, -58, -8, every=7)
    box('Deck', (2.6, 40, 0.1), (-0.35, -28, DECK - 0.05), M['plate'])
    L = light('AREA', (0.8, -9.5, 2.0), 600, (0.9, 0.95, 1.0), 1.2); aim(L, (0, -5.2, 5.2))
    light('POINT', (-1.0, -4.0, 1.4), 200, (1, 0.9, 0.75), 0.3)
    arm = guy(M, 'Operator', (0.7, -8.2, DECK), (0.0, -5.0, 5.5), 'worker')
    if arm:
        pose(arm, 0.0, {**STANCES['relax'], 'upperarm01.L': (40, 0, -30), 'lowerarm01.L': (60, 0, 0), 'upperarm01.R': (40, 0, 30), 'lowerarm01.R': (60, 0, 0)})
        remote = box('Remote', (0.22, 0.14, 0.08), (0, 0, 0), M['yellow']); hold(arm, remote, 'wrist.L', (0, 0.1, 0.05), (0, 0, 0))
        look_up(arm, 0.0, -25); look_up(arm, d, -32)
    camera([(0, (1.1, -13.5, 1.75), (-0.6, -5.2, 3.3)), (d, (1.0, -12.6, 1.8), (-0.4, -5.2, 3.6))], lens=22, fstop=6)

def S08(a, b):  # time-lapse: segments snap in one by one, a full ring, the machine creeps ahead, the next ring
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    lining(M, -60, YR0)
    T = machine(M, rods='machine', backup=False)
    ring_t = (d - 0.3) / 2.2
    my_pts = [(0, 0.0)]
    for k in range(3):
        t0 = 0.1 + k * ring_t
        yy = YR0 + k * W
        segs = ring(M, yy, k + 1)
        for s, o in enumerate(segs):
            ts = t0 + s * ring_t * 0.13
            o.hide_render = True; o.keyframe_insert('hide_render', frame=F(0))
            if ts < d:
                o.keyframe_insert('hide_render', frame=max(F(0), F(ts) - 1)); o.hide_render = False; o.keyframe_insert('hide_render', frame=F(ts))
        tdone = t0 + ring_t * 0.8
        if tdone + 0.2 < d + 0.5:
            my_pts += [(tdone, k * W), (tdone + 0.22, (k + 1) * W)]
    key(T['root'], 'location', [(t, Vector((0, my, ZC))) for t, my in my_pts])
    tunnel_lights(M, -58, -8, every=7)
    box('Deck', (2.6, 40, 0.1), (-0.35, -28, DECK - 0.05), M['plate'])
    L = light('AREA', (0.6, -12, 2.6), 500, (0.9, 0.95, 1.0), 1.5); aim(L, (0, -3, 3))
    camera([(0, (0.9, -17.0, 1.7), (0.0, -3.0, 3.2)), (d, (0.8, -15.8, 1.75), (0.0, -2.0, 3.2))], lens=20, fstop=8)

def S09(a, b):  # question: wide cut-away under the street; the whole machine, heavy, with nothing ahead but soil
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(30, 0.85, 34, 70, 2.3)
    zc = -11.0
    cut_tbm(M, zc, d)
    camera([(0, (30.0, -9.0, -4.0), (-3.0, -7.0, -13.0)), (d, (27.5, -8.0, -4.6), (-3.0, -6.0, -13.2))], lens=26, fstop=14)

def S10(a, b):  # close-up: a thrust jack's chrome rod pushes on the last ring and the whole machine slides ahead
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    lining(M, -40, YR0)
    T = machine(M, backup=False)
    pts = [(0, 0.0), (0.3, 0.0), (d, 1.1)]
    key(T['root'], 'location', [(t, Vector((0, my, ZC))) for t, my in pts], interp='LINEAR')
    key_rods(T, pts)
    tunnel_lights(M, -38, -8, every=7)
    L = light('AREA', (-1.2, YR0 - 1.6, 2.2), 260, (0.95, 0.97, 1.0), 0.8); aim(L, (-3.0, YR0 + 0.6, 2.6))
    light('POINT', (-1.6, YR0 + 2.5, 3.6), 120, (1, 0.88, 0.7), 0.2)
    camera([(0, (-1.75, YR0 - 1.55, 3.55), (-2.95, YR0 + 0.9, 2.55)), (d, (-1.8, YR0 - 1.2, 3.5), (-2.95, YR0 + 1.4, 2.5))], lens=26, fstop=3.2)

def S11(a, b):  # the trailing gear: a conveyor belt carries the dug dirt back out, a worker walks along it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    lining(M, -70, YR0)
    T = machine(M, backup=True, back_len=50)
    conveyor(M, -60, -10, d=d)
    tunnel_lights(M, -68, -8, every=7)
    vent_duct(M, -70, -9)
    L = light('AREA', (0, -28, 3.9), 300, (0.95, 0.97, 1.0), 1.0); aim(L, (0, -28, 0))
    arm = guy(M, 'Walker', (-0.4, -16.0, DECK), (-0.4, -40.0, DECK), 'worker')
    if arm:
        key(arm, 'location', [(0, Vector((-0.4, -16.0, DECK))), (d, Vector((-0.4, -16.0 - 1.2 * d, DECK)))], interp='LINEAR')
        walk(arm, 0.0, d)
    camera([(0, (0.55, -27.5, 2.35), (0.6, -14.0, 1.9)), (d, (0.5, -28.5, 2.3), (0.5, -15.0, 1.9))], lens=26, fstop=4.5)

def S12(a, b):  # scale: the 57-foot cutterhead of a Seattle-size machine, three workers at its foot, camera pulls back
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(150, 0.9, 64, 120, 2.6)
    Rc = 8.75
    zc = pit_scene(M, Rc, d, rpm_deg=5.0, L=16, pit=(17, 34, 34))
    people = [((1.2, 3.2, 0), (0, 0, 9)), ((-1.0, 3.6, 0), (0, 0, 9)), ((3.4, 2.6, 0), (1, 0, 9))]
    for i, (p, f) in enumerate(people):
        arm = guy(M, 'Crew%d' % i, p, f, 'worker')
        if arm:
            look_up(arm, 0.0, -24 - 3 * i)
            if i == 0: pose(arm, d * 0.5, STANCES['point_r'])
    light('AREA', (0, 22, 18), 9000, (1, 0.97, 0.92), 12).rotation_euler = (math.radians(55), 0, math.radians(180))
    camera([(0, (1.6, 10.5, 1.7), (0.6, 0.0, 4.5)), (d, (3.0, 27.0, 4.0), (0.0, 0.0, 9.2))], lens=22, fstop=7)

def S13(a, b):  # cut-away time-lapse: the machine pushes off its newest ring, moves ahead, a new ring appears behind it
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day_world(30, 0.85, 34, 70, 2.3)
    zc = -11.0
    step = d / 3.0
    my_pts = [(0, 0.0)]
    rings_at = []
    for k in range(3):
        t0 = k * step
        my_pts += [(t0 + step * 0.2, k * W), (t0 + step * 0.75, (k + 1) * W)]
        rings_at.append((t0 + step * 0.85, YR0 + k * W))
    cut_tbm(M, zc, d, my_pts=my_pts, rings_at=rings_at)
    camera([(0, (17.0, -4.0, zc + 2.5), (-2.0, -5.0, zc - 1.5)), (d, (16.0, -2.5, zc + 2.2), (-2.0, -3.5, zc - 1.5))], lens=26, fstop=10)

def S14(a, b):  # the finished subway tunnel: ring after ring of concrete, rails, lights, a person walks away
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.01, 0, 'studio')
    lining(M, -40, 90)
    inv = box('Invert', (3.96, 130, 0.75), (0, 25, 0.375), M['invert'])
    random.seed(2)
    tie = box('Tie', (2.3, 0.24, 0.16), (0, -40, 0.82), M['invert'])
    y = -39.2
    while y < 90: dup(tie, (0, y, 0.82)); y += 0.75
    for x in (-0.7175, 0.7175):
        box('Rail', (0.07, 130, 0.15), (x, 25, 0.97), M['chrome' if False else 'steel'])
        box('RailHead', (0.075, 130, 0.035), (x, 25, 1.04), M['chrome'])
    box('Walkway', (0.8, 130, 0.08), (2.05, 25, 1.35), M['grey'])
    for yy in range(-40, 90, 3):
        box('WalkBracket', (0.06, 0.06, 0.55), (1.72, yy, 1.08), M['steel'])
    for i, (x, z) in enumerate(((-2.7, 2.5), (-2.62, 2.3), (-2.78, 2.7))):
        cyl('Cable', 0.035, 130, (x, 25, z), M['dark'], rot=(math.pi / 2, 0, 0), verts=12)
    tunnel_lights(M, -38, 88, every=8, side=-1, power=70)
    tunnel_lights(M, -34, 88, every=8, side=1, power=45)
    arm = guy(M, 'Walker', (2.0, -6.0, 1.39), (2.0, 40.0, 1.39), 'casual', hat=False)
    if arm:
        key(arm, 'location', [(0, Vector((2.0, -6.0, 1.39))), (d, Vector((2.0, -6.0 + 1.25 * d, 1.39)))], interp='LINEAR')
        walk(arm, 0.0, d)
    camera([(0, (0.35, -14.0, 1.45), (0.4, 20.0, 2.6)), (d, (0.35, -11.5, 1.5), (0.4, 22.0, 2.6))], lens=22, fstop=5)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14]

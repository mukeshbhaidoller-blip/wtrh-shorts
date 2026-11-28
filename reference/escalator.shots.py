# Shots for "Why Escalator Stairs Vanish Into the Floor" (steps = carts with 2 wheel pairs on 2 tracks, comb plate,
# endless loop, handrail driven at the same speed, Wheaton station 230 ft).
# Z up, metres. Escalator local frame: travel +Y (up), steps' front wheel axle follows the chain path P.
# Person faces -Y at rot_z=0 (rot_z=pi faces up the escalator, +Y). t = seconds from the shot start.
import numpy as np
from mathutils import Matrix, Euler

def dur(a, b): return (b - a) / FPS
def update(): bpy.context.view_layer.update()

ANG = math.radians(30)
PITCH = 0.40          # step pitch along the chain
TOP = 0.10            # tread top above the front wheel axle
WR = 0.05             # wheel radius
XF, XR = 0.60, 0.52   # front (chain) wheel / rear (trailing) wheel x
RW = (-0.26, -0.12)   # rear wheel axle relative to the front one (y, z)
V = 0.5               # step speed m/s

# ---------------------------------------------------------------- the chain path
class Path:
    """Closed escalator loop. seg 0-4 top run (flat, bend, incline, bend, flat), 5 top turn, 6-10 return, 11 bottom turn."""
    def __init__(s, H=4.0, Llo=2.0, Lhi=2.2, R1=1.0, R2=1.4, Rr=0.35, ds=0.004):
        a = ANG
        Ls = (H - (R1 + R2) * (1 - math.cos(a))) / math.sin(a)
        segs = [(Llo, 0), (R1 * a, 1 / R1), (Ls, 0), (R2 * a, -1 / R2), (Lhi, 0), (math.pi * Rr, -1 / Rr),
                (Lhi, 0), ((R2 - 2 * Rr) * a, 1 / (R2 - 2 * Rr)), (Ls, 0), ((R1 + 2 * Rr) * a, -1 / (R1 + 2 * Rr)), (Llo, 0), (math.pi * Rr, -1 / Rr)]
        ys, zs, th, sg, ss = [0.0], [0.0], [0.0], [0], [0.0]
        y = z = t = S = 0.0
        s.bounds = [0.0]
        for k, (L, c) in enumerate(segs):
            n = max(2, int(L / ds))
            h = L / n
            for i in range(n):
                tm = t + c * h / 2
                y += h * math.cos(tm); z += h * math.sin(tm); t += c * h; S += h
                ys.append(y); zs.append(z); th.append(t); sg.append(k); ss.append(S)
            s.bounds.append(S)
        s.y, s.z, s.th, s.seg, s.s = map(np.array, (ys, zs, th, sg, ss))
        s.L = S; s.H = H; s.Llo, s.Lhi, s.Rr = Llo, Lhi, Rr
        s.top_len = s.bounds[5]
        s.y_top0 = float(np.interp(s.bounds[4], s.s, s.y))      # where the top flat starts
        s.y_end = float(np.interp(s.bounds[5], s.s, s.y))
        s.yb_comb = 0.9                                          # bottom comb edge
        s.yt_comb = s.y_top0 + Lhi - 0.95                        # top comb edge
    def at(s, u):
        u = u % s.L
        y = float(np.interp(u, s.s, s.y)); z = float(np.interp(u, s.s, s.z)); t = float(np.interp(u, s.s, s.th))
        k = int(np.searchsorted(s.bounds, u, side='right') - 1); k = min(max(k, 0), 11)
        return y, z, t, k
    def rot(s, u):
        y, z, t, k = s.at(u)
        if k <= 4: return 0.0
        if k in (6, 7, 8, 9, 10): return -math.pi
        return t
    def top_pts(s, off=(0.0, 0.0), normal=0.0, s0=0.0, s1=None, n=None):
        """Sampled points (y, z) of the top run translated by off and pushed along the up-normal by `normal`."""
        s1 = s.top_len if s1 is None else s1
        n = n or max(8, int((s1 - s0) / 0.03))
        out = []
        for i in range(n + 1):
            u = s0 + (s1 - s0) * i / n
            y, z, t, k = s.at(u)
            out.append((y + off[0] - normal * math.sin(t), z + off[1] + normal * math.cos(t)))
        return out
    def u_at_y_top(s, yq):
        m = s.seg <= 4
        return float(np.interp(yq, s.y[m], s.s[m]))

# ---------------------------------------------------------------- geometry helpers
def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); link(o)
    if mat: me.materials.append(mat)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return o

def strip(name, line_a, line_b, x0, x1, mat, cap=True):
    """Solid between two (y,z) polylines of equal length, from x0 to x1 (a side panel / rail / skirt)."""
    vs, fs = [], []
    n = len(line_a)
    for x in (x0, x1):
        for (y, z) in line_a: vs.append((x, y, z))
        for (y, z) in line_b: vs.append((x, y, z))
    A0, B0, A1, B1 = 0, n, 2 * n, 3 * n
    for i in range(n - 1):
        fs.append((A0 + i, A0 + i + 1, B0 + i + 1, B0 + i))      # x0 face
        fs.append((A1 + i, B1 + i, B1 + i + 1, A1 + i + 1))      # x1 face
        fs.append((A0 + i, A1 + i, A1 + i + 1, A0 + i + 1))      # line a edge
        fs.append((B0 + i, B0 + i + 1, B1 + i + 1, B1 + i))      # line b edge
    if cap:
        fs.append((A0, B0, B1, A1)); fs.append((A0 + n - 1, A1 + n - 1, B1 + n - 1, B0 + n - 1))
    o = mesh_obj(name, vs, fs, mat)
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(o.data); _bm.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o

def child(o, parent, loc=None):
    o.parent = parent
    if loc is not None: o.location = loc
    return o

def tube_curve(name, pts, r, mat, closed=False, flat=1.0):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = r; cu.bevel_resolution = 4; cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); link(o)
    o.data.materials.append(mat)
    return o

def join(objs, name):
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            try: bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception: pass
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    return o

def pop_in(o, t0, dt=0.25, s=1.0):
    key(o, 'scale', [(t0 - 0.01, Vector((0.001, 0.001, 0.001))), (t0 + dt, Vector((s * 1.08,) * 3)), (t0 + dt + 0.12, Vector((s,) * 3))])

# ---------------------------------------------------------------- materials
def mats():
    M = {}
    M['alu'] = mat_simple('StepAlu', (0.62, 0.63, 0.65), 0.3, 1.0)[0]
    M['alu_d'] = mat_simple('StepAluDark', (0.32, 0.33, 0.35), 0.38, 1.0)[0]
    M['yellow'] = mat_simple('Demarcation', (0.95, 0.68, 0.02), 0.45)[0]
    M['black'] = mat_simple('BlackSteel', (0.025, 0.025, 0.028), 0.5, 0.4)[0]
    M['wheel'] = mat_simple('Wheel', (0.05, 0.05, 0.055), 0.55)[0]
    M['hub'] = mat_simple('Hub', (0.7, 0.7, 0.72), 0.25, 1.0)[0]
    M['stain'] = mat_simple('Stainless', (0.72, 0.72, 0.74), 0.16, 1.0)[0]
    M['clad'] = mat_simple('Cladding', (0.8, 0.8, 0.81), 0.24, 1.0)[0]
    M['glass'] = mat_glass('Balustrade', (0.9, 0.97, 0.95), 0.0)[0]
    M['rubber'] = mat_simple('Handrail', (0.012, 0.012, 0.014), 0.42, coat=0.3)[0]
    M['rail'] = mat_simple('TrackSteel', (0.45, 0.46, 0.48), 0.35, 1.0)[0]
    M['chain'] = mat_simple('Chain', (0.2, 0.2, 0.21), 0.35, 1.0)[0]
    M['gear'] = mat_simple('Gear', (0.62, 0.6, 0.55), 0.3, 1.0)[0]
    M['truss'] = mat_simple('Truss', (0.12, 0.2, 0.32), 0.5, 0.2)[0]
    M['floor'] = mat_textured('Floor', ['concrete_floor_02'], 0.35, (0.7, 0.7, 0.68), rough=(0.25, 0.55), tint=(1.05, 1.03, 1.0), wet=0.35)[0]
    M['plate'] = mat_textured('FloorPlate', ['metal_plate'], 0.9, (0.6, 0.6, 0.62), rough=(0.25, 0.5), bump=0.5)[0]
    M['wall'] = mat_textured('Wall', ['concrete_floor_worn_001', 'concrete_pavement'], 0.25, (0.7, 0.7, 0.7), rough=(0.6, 0.9), tint=(0.95, 0.93, 0.9))[0]
    M['ceil'] = mat_simple('Ceiling', (0.85, 0.85, 0.84), 0.8)[0]
    M['lamp'] = mat_emit('LampStrip', (1.0, 0.93, 0.82), 9.0)[0]
    M['glow_b'] = mat_simple('GlowBlue', (0.1, 0.5, 1.0), 0.4, emit=(0.1, 0.55, 1.0), estr=0.0)
    M['glow_o'] = mat_simple('GlowOrange', (1.0, 0.45, 0.05), 0.4, emit=(1.0, 0.45, 0.05), estr=0.0)
    M['glow_r'] = mat_simple('GlowRed', (1.0, 0.06, 0.03), 0.4, emit=(1.0, 0.05, 0.02), estr=0.0)
    M['dot'] = mat_emit('Dot', (1.0, 0.55, 0.08), 14.0)[0]
    M['dot_b'] = mat_emit('DotB', (0.2, 0.7, 1.0), 14.0)[0]
    M['studio'] = mat_simple('StudioFloor', (0.22, 0.225, 0.235), 0.55)[0]
    for v_ in M.values():   # MPFB purges unused materials when it builds a person: keep ours
        m_ = v_[0] if isinstance(v_, tuple) else v_
        m_.use_fake_user = True
    return M

# ---------------------------------------------------------------- one step (a little cart)
def step_proto(M, ribs=True, name='StepProto'):
    """One escalator step, origin = front wheel axle (0,0,0), tread top at z=TOP, tread y -0.38..0.02, width 1.0 m."""
    parts = []
    tz0 = TOP - 0.012
    parts.append(box('TreadBase', (1.0, 0.40, 0.018), (0, -0.18, tz0 - 0.009), M['alu_d']))
    if ribs:
        r = box('Rib', (0.0045, 0.385, 0.012), (-0.459, -0.18, tz0 + 0.006), M['alu'])
        ar = r.modifiers.new('arr', 'ARRAY'); ar.count = 108; ar.use_relative_offset = False; ar.use_constant_offset = True
        ar.constant_offset_displace = (0.0085, 0, 0)
        parts.append(r)
        for sx in (-1, 1):   # yellow side demarcation ribs
            ry = box('RibY', (0.0045, 0.385, 0.012), (sx * 0.493 - (0.0255 if sx > 0 else 0), -0.18, tz0 + 0.006), M['yellow'])
            a2 = ry.modifiers.new('arr', 'ARRAY'); a2.count = 4; a2.use_relative_offset = False; a2.use_constant_offset = True
            a2.constant_offset_displace = (0.0085, 0, 0)
            parts.append(ry)
    else:
        parts.append(box('TreadTop', (1.0, 0.385, 0.012), (0, -0.18, tz0 + 0.006), M['alu']))
    parts.append(box('BackYellow', (1.0, 0.035, 0.013), (0, -0.362, tz0 + 0.0065), M['yellow']))
    # riser (cleated look via ribs is skipped: plain alu, slightly curved feel from a bevel)
    parts.append(box('Riser', (0.99, 0.014, 0.19), (0, -0.373, TOP - 0.11), M['alu'], bevel=0.003))
    # side brackets (yoke) and cross tubes
    for sx in (-1, 1):
        x = sx * 0.497
        vs = []
        poly = [(0.02, TOP - 0.03), (-0.38, TOP - 0.03), (RW[0] - 0.03, RW[1] - 0.03), (0.02, -0.04)]
        for dx in (-0.006, 0.006):
            for (y, z) in poly: vs.append((x + dx, y, z))
        fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        parts.append(mesh_obj('Yoke', vs, fs, M['black']))
    parts.append(cyl('AxleF', 0.012, 2 * XF + 0.04, (0, 0, 0), M['hub'], rot=(0, math.radians(90), 0), verts=16))
    parts.append(cyl('AxleR', 0.012, 2 * XR + 0.02, (0, RW[0], RW[1]), M['hub'], rot=(0, math.radians(90), 0), verts=16))
    for sx in (-1, 1):
        parts.append(cyl('WheelF', WR, 0.03, (sx * XF, 0, 0), M['wheel'], rot=(0, math.radians(90), 0), verts=32, bevel=0.006))
        parts.append(cyl('HubF', 0.022, 0.034, (sx * XF, 0, 0), M['hub'], rot=(0, math.radians(90), 0), verts=16))
        parts.append(cyl('WheelR', WR, 0.03, (sx * XR, RW[0], RW[1]), M['wheel'], rot=(0, math.radians(90), 0), verts=32, bevel=0.006))
        parts.append(cyl('HubR', 0.022, 0.034, (sx * XR, RW[0], RW[1]), M['hub'], rot=(0, math.radians(90), 0), verts=16))
    o = join(parts, name)
    o.location = (0, 0, -300)
    return o

def anim_path(obj, P, u0, d, v=V, off=(0, 0, 0), rot=True, every=2, xrot_extra=0.0, root=None, rotfn=None, u_of_t=None):
    """Keyframe obj along the chain path (local to the escalator root). Straight runs keep only their end keys."""
    nfr = max(1, round(d * FPS))
    frs = list(range(0, nfr + 1, every))
    if frs[-1] != nfr: frs.append(nfr)
    smp = []
    prev = None
    for f in frs:
        t = f / FPS
        u = (u0 + v * t) if u_of_t is None else u_of_t(t)
        y, z, th, k = P.at(u)
        r = (rotfn(u) if rotfn else P.rot(u)) if rot else 0.0
        if prev is not None:
            while r - prev > math.pi: r -= 2 * math.pi
            while prev - r > math.pi: r += 2 * math.pi
        prev = r
        smp.append((t, (off[0], y + off[1], z + off[2]), r, th))
    keep = []
    for i, s_ in enumerate(smp):
        if i in (0, len(smp) - 1): keep.append(s_); continue
        a_, b_ = smp[i - 1], smp[i + 1]
        if abs(a_[3] - b_[3]) < 1e-6 and abs(a_[2] - b_[2]) < 1e-6: continue
        keep.append(s_)
    for t, loc, r, _ in keep:
        obj.location = loc; obj.keyframe_insert('location', frame=F(t))
        if rot:
            obj.rotation_euler = (r + xrot_extra, 0, 0); obj.keyframe_insert('rotation_euler', frame=F(t))
    if obj.animation_data and obj.animation_data.action:
        for fc in fcurves_of(obj.animation_data.action):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------------------------------------------------------------- the escalator
def escalator(M, d, H=4.0, Llo=2.0, Lhi=2.2, loc=(0, 0, 0), yaw=0.0, u0=0.0, cut=False, glass=True, rails=False,
              chain=False, ret=True, ribs_near=None, clad=True, gear=False, handrail=True, floors=True, steps=True, v=V,
              lod_simple=False):
    P = Path(H, Llo, Lhi)
    root = bpy.data.objects.new('Escalator', None); link(root); root.location = loc; root.rotation_euler = (0, 0, yaw)
    E = {'P': P, 'root': root, 'steps': [], 'u0': u0, 'v': v}
    # steps
    if steps:
        proto = step_proto(M, True); protos = step_proto(M, False, 'StepProtoS') if lod_simple else proto
        n = int(P.L / PITCH)
        pitch = P.L / n
        E['pitch'] = pitch
        for i in range(n):
            ui = u0 + i * pitch
            if not ret:
                uu = ui % P.L; uu1 = (ui + v * d) % P.L
                if not (uu < P.top_len + 0.3 or uu1 < P.top_len + 0.3): continue
            use = proto
            if lod_simple and ribs_near is not None and not ribs_near(P.at(ui)[0]): use = protos
            o = use.copy(); link(o); o.parent = root
            anim_path(o, P, ui, d, v)
            E['steps'].append((i, o))
        proto.hide_render = True; protos.hide_render = True
    # tracks (rails) under the front and rear wheels
    if rails:
        for nm, off, x, mat in (('TrackF', (0, 0), XF, M['glow_b'][0]), ('TrackR', RW, XR, M['glow_o'][0])):
            for sx in (-1, 1):
                la = P.top_pts(off, -WR - 0.002); lb = P.top_pts(off, -WR - 0.028)
                r = strip(nm, la, lb, sx * x - 0.022, sx * x + 0.022, mat); r.parent = root
                E.setdefault(nm, []).append(r)
        # return-run guide rails (plain steel)
        for sx in (-1, 1):
            pts = []
            for i in range(160):
                u = P.bounds[6] + (P.bounds[11] - P.bounds[6]) * i / 159
                y, z, t, k = P.at(u); pts.append((y + 0.08 * math.sin(t), z - 0.08 * math.cos(t)))
            la = [(y, z) for (y, z) in pts]; lb = [(y, z - 0.03) for (y, z) in pts]
            r = strip('TrackRet', la, lb, sx * XF - 0.02, sx * XF + 0.02, M['rail']); r.parent = root
    # chain: a link bar between consecutive front axles
    if chain and steps:
        lk = box('Link', (0.012, PITCH, 0.03), (0, 0, 0), M['chain'], bevel=0.004)
        lk.location = (0, 0, -300)
        for i, o in E['steps']:
            for sx in (-1, 1):
                c = lk.copy(); link(c); c.parent = root
                ui = u0 + i * E['pitch']
                # link midpoint follows the path half a pitch behind the axle; rotate with the chain tangent
                def rf(u, P=P): return P.at(u)[2]
                anim_path(c, P, ui - E['pitch'] / 2, d, v, off=(sx * (XF + 0.03), 0, 0), rotfn=rf)
        lk.hide_render = True
    # drive gear (sprocket) at the top turnaround
    if gear:
        cz = P.H - P.Rr; cy = P.y_end
        for sx in (-1, 1):
            g = cyl('Sprocket', P.Rr - 0.02, 0.03, (sx * (XF + 0.06), cy, cz), M['gear'], rot=(0, math.radians(90), 0), verts=64)
            parts = [g]
            for k in range(16):
                a_ = 2 * math.pi * k / 16
                parts.append(box('Tooth', (0.03, 0.06, 0.07), (sx * (XF + 0.06), cy + (P.Rr - 0.0) * math.cos(a_), cz + (P.Rr - 0.0) * math.sin(a_)), M['gear'], rot=(a_, 0, 0)))
            parts.append(cyl('Hub', 0.08, 0.08, (sx * (XF + 0.06), cy, cz), M['hub'], rot=(0, math.radians(90), 0), verts=32))
            G = join(parts, 'Gear'); G.parent = root
            # rotate around its own centre: set origin to centre
            me = G.data
            for vv in me.vertices: vv.co -= Vector((sx * (XF + 0.06), cy, cz))
            G.location = (sx * (XF + 0.06), cy, cz)
            key(G, 'rotation_euler', [(0, Euler((0, 0, 0))), (d, Euler((-v * d / P.Rr, 0, 0)))], interp='LINEAR')
        axle = cyl('MainShaft', 0.05, 2 * XF + 0.3, (0, cy, cz), M['hub'], rot=(0, math.radians(90), 0), verts=24); axle.parent = root
        mot = box('Motor', (0.5, 0.6, 0.45), (0.0, cy + 0.85, cz - 0.3), M['truss'], bevel=0.03); mot.parent = root
        cyl('MotorEnd', 0.2, 0.62, (0.0, cy + 0.85, cz - 0.3), M['gear'], rot=(0, math.radians(90), 0), verts=32).parent = root
    # skirt, deck, glass, handrail, cladding
    sides = (1,) if cut else (-1, 1)
    tread = P.top_pts((0, 0), 0.0)
    tread = [(y, z + TOP) for (y, z) in tread]
    def lift(line, dz): return [(y, z + dz) for (y, z) in line]
    yb, yt = P.yb_comb - 0.6, P.yt_comb + 0.6
    def clip(line): return [(y, z) for (y, z) in line if yb - 0.15 <= y <= yt + 0.15]
    tl = clip(tread)
    for sx in (-1, 1):
        near_cut = cut and sx == -1
        if not near_cut:
            strip('Skirt', lift(tl, -0.06), lift(tl, 0.22), sx * 0.505, sx * 0.515, M['stain']).parent = root
            strip('DeckIn', lift(tl, 0.22), lift(tl, 0.245), sx * 0.505, sx * 0.60, M['stain']).parent = root
        if glass and not near_cut:
            gl = [(y, z) for (y, z) in tl if P.yb_comb - 0.3 <= y <= P.yt_comb + 0.3]
            strip('Glass', lift(gl, 0.245), lift(gl, 0.93), sx * 0.553, sx * 0.565, M['glass']).parent = root
            strip('GlassClamp', lift(gl, 0.245), lift(gl, 0.30), sx * 0.545, sx * 0.573, M['stain']).parent = root
        if handrail and not near_cut:
            hl = [(y, z) for (y, z) in tread if P.yb_comb - 0.55 <= y <= P.yt_comb + 0.55]
            hz = 0.985
            pts = [(sx * 0.56, y, z + hz) for (y, z) in hl]
            # newel loops at both ends (half circles going down), then the return inside the balustrade
            ya, za = hl[0]; yz, zz = hl[-1]
            rr = 0.22
            top_loop = [(sx * 0.56, yz + rr * math.sin(q), zz + hz - rr + rr * math.cos(q)) for q in np.linspace(0, math.pi, 14)[1:]]
            bot_loop = [(sx * 0.56, ya - rr * math.sin(q), za + hz - rr + rr * math.cos(q)) for q in np.linspace(math.pi, 0, 14)[:-1]]
            back = [(sx * 0.56, y, z + hz - 2 * rr) for (y, z) in reversed(hl)]
            loop = pts + top_loop + back + bot_loop
            h = tube_curve('Handrail', loop, 0.036, M['rubber'], closed=True); h.parent = root
            h.scale = (1.0, 1.0, 1.0)
            E.setdefault('handrail', []).append((sx, loop))
        if clad and not (cut and sx == -1):
            hi2 = clip(lift(tread, 0.245)); lo2 = lift(hi2, -1.6)
            strip('Clad', lo2, hi2, sx * 0.74, sx * 0.75, M['clad']).parent = root
            strip('DeckOut', [(y, z) for (y, z) in hi2], [(y, z + 0.02) for (y, z) in hi2], sx * 0.60, sx * 0.75, M['stain']).parent = root
    if clad and not cut:
        lo = lift(clip(lift(tread, 0.245)), -1.6)
        strip('Soffit', lo, [(y, z + 0.01) for (y, z) in lo], -0.75, 0.75, M['clad']).parent = root
    # floors, floor plates and combs
    if floors:
        zt = P.H + TOP; zb = TOP
        plate('FloorLow', 30, 30, (0, P.yb_comb - 0.6 - 15, zb), M['floor']).parent = root
        for sx in (-1, 1):
            plate('FloorLowSide', 14, 40, (sx * (0.75 + 7), P.yb_comb - 0.6 + 20, zb), M['floor']).parent = root
        box('PlateLow', (1.5, 1.6, 0.012), (0, P.yb_comb - 0.8 - 0.0, zb + 0.006), M['plate']).parent = root
        yslab = P.y_end + 0.6
        box('SlabTop', (30, 30, 1.4), (0, yslab + 15, zt - 0.7), M['floor']).parent = root
        for sx in (-1, 1):
            box('SlabTopSide', (14, yslab - P.yt_comb + 0.0, 1.4), (sx * (0.75 + 7), (yslab + P.yt_comb) / 2, zt - 0.7), M['floor']).parent = root
        box('PlateTop', (1.5, yslab - P.yt_comb - 0.02, 0.012), (0, (yslab + P.yt_comb) / 2 + 0.01, zt + 0.006), M['plate']).parent = root
        E['comb_top'] = comb(M, P.yt_comb, zt, -1, root)
        E['comb_bot'] = comb(M, P.yb_comb, zb, +1, root)
    return E

def plate(name, sx, sy, loc, mat):
    return plane(name, sx, sy, loc, mat)

def comb(M, y, z, direction, root):
    """Comb plate at a landing: teeth (pitch 8.5 mm, matching the tread grooves) point toward the steps."""
    base = box('CombBase', (1.0, 0.09, 0.014), (0, y - direction * 0.045, z + 0.008), M['yellow'], bevel=0.002)
    t = box('Tooth', (0.0032, 0.05, 0.008), (-0.459 + 0.00425, y + direction * 0.025, z + 0.002), M['yellow'])
    t.rotation_euler = (math.radians(-12 * direction), 0, 0)
    ar = t.modifiers.new('arr', 'ARRAY'); ar.count = 107; ar.use_relative_offset = False; ar.use_constant_offset = True
    ar.constant_offset_displace = (0.0085, 0, 0)
    base.parent = root; t.parent = root
    return base, t

# ---------------------------------------------------------------- places
def hall(M, P, root_loc=(0, 0, 0), lights=True, strength=0.25):
    world_hdri('studio_small_09', strength, 0.0, 'studio')
    zt = P.H + TOP
    # walls of a mall / station hall
    box('WallBack', (24, 0.3, 14), (0, P.y_end + 18, 6), M['wall'])
    box('WallL', (0.3, 60, 14), (-7.5, 0, 6), M['wall'])
    box('WallR', (0.3, 60, 14), (7.5, 0, 6), M['wall'])
    box('WallFront', (24, 0.3, 14), (0, -16, 6), M['wall'])
    box('Ceiling', (24, 60, 0.3), (0, 0, zt + 4.2), M['ceil'])
    for sx in (-1, 1):   # glass railing along the mezzanine edge
        box('EdgeGlass', (6.7, 0.02, 1.0), (sx * (0.75 + 3.4), P.yt_comb - 0.05, zt + 0.5), M['glass'])
        box('EdgeRail', (6.7, 0.06, 0.05), (sx * (0.75 + 3.4), P.yt_comb - 0.05, zt + 1.02), M['stain'])
    for x in (-3.5, 0, 3.5):
        for y in np.arange(-12, P.y_end + 16, 4.0):
            box('Lamp', (0.18, 2.6, 0.04), (x, y, zt + 4.03), M['lamp'])
    if lights:
        for y in (-4, 2, 8):
            L = light('AREA', (0, y, zt + 3.6), 900, (1.0, 0.93, 0.84), 5.0, rot=(0, 0, 0))
            L.data.shape = 'RECTANGLE'; L.data.size = 6; L.data.size_y = 4

def rider(arm, E, k, d, dy=-0.19, x=0.0, back=False):
    """Make the armature ride on step k (index into E['steps'] order by chain index)."""
    if arm is None: return
    P = E['P']; pitch = E['pitch']
    ui = E['u0'] + k * pitch
    anim_path(arm, P, ui, d, E['v'], off=(x, dy, TOP), rot=False)
    # convert to world if the escalator root is offset (parent it)
    arm.parent = E['root']

def step_index_at(E, t, y_target):
    """Chain index k whose step is at local y = y_target (top run) at shot time t."""
    P = E['P']; u = P.u_at_y_top(y_target)
    k = round((u - E['u0'] - E['v'] * t) / E['pitch'])
    return k

def glow(m_pair, pts):
    key_socket(inp(m_pair[1], 'Emission Strength'), pts)

def dots_along(pts3, n, d, speed, mat, r=0.018, root=None, phase=0.0):
    """Glowing dots moving along a closed or open 3D polyline at `speed` m/s (shows motion / same speed)."""
    P3 = [Vector(p) for p in pts3]
    seg = [0.0]
    for i in range(1, len(P3)): seg.append(seg[-1] + (P3[i] - P3[i - 1]).length)
    Ltot = seg[-1]
    def at(s):
        s = s % Ltot
        j = int(np.searchsorted(seg, s, side='right') - 1); j = min(max(j, 0), len(P3) - 2)
        f = (s - seg[j]) / max(1e-9, seg[j + 1] - seg[j])
        return P3[j].lerp(P3[j + 1], f)
    out = []
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=16, ring_count=8); proto = bpy.context.active_object
    proto.data.materials.append(mat); proto.location = (0, 0, -300)
    for i in range(n):
        o = proto.copy(); link(o)
        if root: o.parent = root
        s0 = phase + Ltot * i / n
        nfr = max(1, round(d * FPS))
        for f in range(0, nfr + 1, 2):
            t = f / FPS; o.location = at(s0 + speed * t); o.keyframe_insert('location', frame=F(t))
        for fc in fcurves_of(o.animation_data.action):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        out.append(o)
    proto.hide_render = True
    return out

def studio(strength=0.5, floor_z=-1.6):
    world_hdri('studio_small_09', strength, 0.0, 'studio')
    M = mats(); plane('Floor', 60, 60, (0, 0, floor_z), M['studio'])
    return M

def keylights(c=(0, 2, 2), s=1.0):
    light('AREA', (c[0] - 4.0, c[1] - 3.0, c[2] + 3.0), 700 * s, (1, 0.96, 0.9), 3.0, rot=(math.radians(50), 0, math.radians(-50)))
    light('AREA', (c[0] + 4.0, c[1] + 2.0, c[2] + 2.5), 380 * s, (0.82, 0.9, 1.0), 3.0, rot=(math.radians(55), 0, math.radians(120)))

def W(E, p):
    """Local escalator point -> world (root has only translation / yaw)."""
    r = E['root']; return r.matrix_world @ Vector(p)

# ================================================================ shots
def S00(a, b):  # hook: top landing, low camera at the comb; stairs rise toward us and vanish into the floor; a rider
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    E = escalator(M, d, u0=0.13); P = E['P']; hall(M, P); update()
    k = step_index_at(E, d * 0.5, P.y_top0 - 2.6)
    arm = person('Rider', rot_z=math.radians(180), outfit='casual')
    rider(arm, E, k, d, x=-0.12)
    yt = P.yt_comb; zt = P.H + TOP
    c0 = W(E, (0.15, yt + 1.35, zt + 1.6)); c1 = W(E, (0.12, yt + 1.05, zt + 1.5))
    camera([(0, c0, W(E, (0.0, yt - 2.6, zt - 2.6))), (d, c1, W(E, (0.0, yt - 2.5, zt - 2.6)))], lens=24, fstop=5.0)

def S01(a, b):  # studio: one step lifted out = a little cart with four wheels; a technician points at it
    sc = new_scene(a, b); d = dur(a, b); M = studio(0.55, 0.0)
    st = step_proto(M, True, 'Step'); st.location = (0, 0, 0.80)
    key(st, 'rotation_euler', [(0, Euler((0, 0, math.radians(-38)))), (d, Euler((0, 0, math.radians(-14))))])
    for sx in (-1, 1):
        for yy in (-0.3, -0.02):
            box('Trestle', (0.04, 0.04, 0.68), (sx * 0.3, yy, 0.34), M['stain'], bevel=0.004)
    box('TrestleBar', (0.66, 0.05, 0.05), (0, -0.16, 0.66), M['stain'], bevel=0.005)
    # wheels glow orange in turn (overlay rings)
    gm = mat_simple('Ring', (1.0, 0.5, 0.08), 0.4, emit=(1.0, 0.5, 0.08), estr=0.0)
    for (x, y, z), t0 in (((XF, 0, 0), 1.3), ((-XF, 0, 0), 1.45), ((XR, RW[0], RW[1]), 1.6), ((-XR, RW[0], RW[1]), 1.75)):
        bpy.ops.mesh.primitive_torus_add(major_radius=WR + 0.012, minor_radius=0.006, location=(x, y, z), rotation=(0, math.radians(90), 0))
        r = bpy.context.active_object; r.data.materials.append(gm[0]); r.parent = st
        pop_in(r, t0)
    key_socket(inp(gm[1], 'Emission Strength'), [(0, 6.0), (d, 6.0)])
    arm = person('Tech', loc=(-0.9, 0.5, 0), rot_z=math.radians(62), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.0, STANCES['relax']); pose(arm, 1.7, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    keylights((0, 0, 0.8), 0.8)
    camera([(0, Vector((1.05, -1.6, 1.2)), Vector((-0.2, 0.0, 0.75))), (d, Vector((0.9, -1.45, 1.12)), Vector((-0.2, 0.0, 0.75)))], lens=30, fstop=5.6)

def cut_scene(a, b, u0=0.0, rails=True, chain=False, gear=False, glow_pts=None, strength=0.45):
    sc = new_scene(a, b); d = dur(a, b); M = studio(strength, -1.4)
    E = escalator(M, d, u0=u0, cut=True, rails=rails, chain=chain, gear=gear, glass=True, floors=False, clad=True)
    keylights((0, 3.5, 2.0), 1.2)
    P = E['P']
    for yy in (P.y_end - 0.9, 0.6 * P.y_top0):
        zz = float(np.interp(yy, P.y[P.seg <= 4], P.z[P.seg <= 4])) + TOP + 0.245 - 1.6
        box('Column', (0.35, 0.35, zz + 1.4), (0.45, yy, (zz - 1.4) / 2), M['clad'])
    box('Backdrop', (0.3, 80, 30), (7.0, 5, 12), M['studio']); box('Backdrop2', (40, 0.3, 30), (0, 18, 12), M['studio']); box('Backdrop3', (40, 0.3, 30), (0, -14, 12), M['studio'])
    return sc, d, M, E

def S02(a, b):  # cut-away: front wheels on the blue track, back wheels on the orange track
    sc, d, M, E = cut_scene(a, b, u0=0.05); P = E['P']
    glow(M['glow_b'], [(0, 0.0), (0.5, 0.0), (0.9, 5.0), (d, 5.0)])
    glow(M['glow_o'], [(0, 0.0), (1.6, 0.0), (2.0, 5.0), (d, 5.0)])
    ym = 3.3; zm = float(np.interp(ym, P.y[P.seg <= 4], P.z[P.seg <= 4]))
    camera([(0, Vector((-2.3, ym - 0.9, zm + 0.55)), Vector((0.45, ym, zm - 0.05))), (d, Vector((-2.1, ym - 0.4, zm + 0.5)), Vector((0.45, ym + 0.3, zm)))], lens=30, fstop=5.0)

def S03(a, b):  # tracks keep every step level while the chain climbs (chain glows)
    sc, d, M, E = cut_scene(a, b, u0=0.21, chain=True); P = E['P']
    glow(M['glow_b'], [(0, 4.0), (d, 4.0)]); glow(M['glow_o'], [(0, 4.0), (d, 4.0)])
    cm = M['chain']
    ym = 4.0; zm = float(np.interp(ym, P.y[P.seg <= 4], P.z[P.seg <= 4]))
    camera([(0, Vector((-2.6, ym + 0.2, zm + 0.25)), Vector((0.5, ym, zm))), (d, Vector((-2.6, ym + 0.9, zm + 0.7)), Vector((0.5, ym + 0.8, zm + 0.45)))], lens=34, fstop=6.0)

def S04(a, b):  # bottom landing: looking up the escalator, the stairs form; a rider goes up (back view)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    E = escalator(M, d, u0=0.31); P = E['P']; hall(M, P); update()
    k = step_index_at(E, d * 0.5, 2.6)
    arm = person('Rider', rot_z=math.radians(180), outfit='casual', male=0.0, hair=('long01', 'ponytail01', 'bob02', 'short02'))
    rider(arm, E, k, d, x=0.1)
    yb = P.yb_comb
    camera([(0, W(E, (-0.35, yb - 2.4, 1.55)), W(E, (0.0, yb + 4.0, 2.4))), (d, W(E, (-0.3, yb - 1.9, 1.5)), W(E, (0.0, yb + 4.3, 2.6)))], lens=26, fstop=6.0)

def S05(a, b):  # cut-away at the top: both tracks flatten out and the stairs fold into a flat floor
    sc, d, M, E = cut_scene(a, b, u0=0.37); P = E['P']
    glow(M['glow_b'], [(0, 3.0), (d * 0.3, 5.0), (d, 5.0)]); glow(M['glow_o'], [(0, 3.0), (d * 0.3, 5.0), (d, 5.0)])
    yt = P.y_top0; zt = P.H
    camera([(0, Vector((-3.3, yt - 0.9, zt + 0.6)), Vector((0.4, yt - 0.3, zt - 0.1))), (d, Vector((-3.1, yt - 0.2, zt + 0.55)), Vector((0.4, yt + 0.2, zt - 0.1)))], lens=30, fstop=6.0)

def S06(a, b):  # top landing, low: a sneaker rides toward the end of the moving floor; the gap glows red
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    E = escalator(M, d, u0=0.45); P = E['P']; hall(M, P); update()
    yt = P.yt_comb; zt = P.H + TOP
    k = step_index_at(E, d, yt - 0.35)
    arm = person('Rider', rot_z=math.radians(180), outfit='casual')
    rider(arm, E, k, d, x=0.08)
    gl = box('GapGlow', (1.0, 0.012, 0.006), (0, yt - 0.03, zt + 0.004), M['glow_r'][0]); gl.parent = E['root']
    glow(M['glow_r'], [(0, 0.0), (0.7, 0.0), (1.1, 8.0), (d, 6.0)])
    c0 = W(E, (0.45, yt + 0.45, zt + 0.16)); c1 = W(E, (0.42, yt + 0.36, zt + 0.15))
    camera([(0, c0, W(E, (0.05, yt - 0.6, zt + 0.08))), (d, c1, W(E, (0.05, yt - 0.5, zt + 0.07)))], lens=30, fstop=3.2)

def S07(a, b):  # macro: the comb's teeth slide into the grooves of the steps
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    E = escalator(M, d, u0=0.52); P = E['P']; hall(M, P, strength=0.35); update()
    yt = P.yt_comb; zt = P.H + TOP
    light('AREA', W(E, (0.6, yt - 0.5, zt + 0.6)), 60, (1, 0.95, 0.9), 0.6, rot=(math.radians(40), 0, math.radians(130)))
    c0 = W(E, (0.2, yt + 0.32, zt + 0.16)); c1 = W(E, (0.17, yt + 0.27, zt + 0.14))
    camera([(0, c0, W(E, (0.05, yt - 0.04, zt))), (d, c1, W(E, (0.04, yt - 0.03, zt)))], lens=55, fstop=11.0)

def S08(a, b):  # cut-away of the top end: steps go round the drive gear, flip upside down and ride back underneath
    sc, d, M, E = cut_scene(a, b, u0=0.6, rails=False, gear=True, chain=True); P = E['P']
    ye = P.y_end; ze = P.H - 0.3
    light('AREA', (-2.0, ye - 0.3, ze + 0.6), 220, (1, 0.96, 0.9), 1.5, rot=(0, math.radians(-70), 0))
    camera([(0, Vector((-4.0, ye - 0.4, ze + 0.6)), Vector((0.3, ye + 0.25, ze - 0.35))), (d, Vector((-3.8, ye - 0.7, ze + 0.5)), Vector((0.3, ye + 0.1, ze - 0.4)))], lens=32, fstop=8.0)

def S09(a, b):  # you hold the handrail as you ride (side view, waist up)
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    E = escalator(M, d, u0=0.68); P = E['P']; hall(M, P); update()
    k = step_index_at(E, d * 0.5, 3.6)
    arm = person('Rider', rot_z=math.radians(180), outfit='office')
    hand = {'upperarm01.R': (18, 0, 30), 'lowerarm01.R': (38, 0, 0), 'upperarm01.L': (0, 0, -55), 'lowerarm01.L': (10, 0, 0)}
    pose(arm, 0.0, hand); pose(arm, d, hand)
    rider(arm, E, k, d, x=0.24)
    u = E['u0'] + k * E['pitch'] + V * d * 0.5
    y, z, t, _ = P.at(u)
    c0 = W(E, (2.35, y - 1.4, z + 1.35)); c1 = W(E, (2.25, y - 1.0, z + 1.55))
    camera([(0, c0, W(E, (0.3, y - 0.2, z + 0.95))), (d, c1, W(E, (0.3, y + 0.25, z + 1.2)))], lens=34, fstop=4.0)

def S10(a, b):  # cut-away: the handrail is one rubber loop; dots on the rail and on the steps move at the same speed
    sc, d, M, E = cut_scene(a, b, u0=0.75, rails=False, chain=False, gear=True); P = E['P']
    sx, loop = E['handrail'][0]
    dots_along(loop, 30, d, V, M['dot'], 0.055, root=E['root'])
    # matching blue dots riding on the step noses
    for i, o in E['steps'][::3]:
        s_ = sphere('NoseDot', 0.05, (0.42, 0.0, TOP + 0.03), M['dot_b'], sub=2); s_.parent = o
    ym = 3.0; zm = 2.0
    camera([(0, Vector((-7.6, ym - 1.5, zm + 1.2)), Vector((0.3, ym, zm))), (d, Vector((-7.2, ym - 0.6, zm + 1.3)), Vector((0.3, ym + 0.3, zm + 0.1)))], lens=26, fstop=8.0)

def wheaton_vault(M, Pq, x_half=3.6, length=None):
    """Long inclined concrete vault (station tunnel) over three escalators, along the incline of path Pq."""
    y2, z2, _, _ = Pq.at(Pq.bounds[2]); y3, z3, _, _ = Pq.at(Pq.bounds[3])
    dy, dz = y3 - y2, z3 - z2; Ln = math.hypot(dy, dz); dy, dz = dy / Ln, dz / Ln
    s0, s1 = -6.0, Ln + 6.0
    nseg = 80; nrad = 28
    vs, fs = [], []
    for i in range(nseg + 1):
        s = s0 + (s1 - s0) * i / nseg
        cy = y2 + s * dy; cz = z2 + TOP + s * dz
        for j in range(nrad + 1):
            q = math.pi * j / nrad
            vs.append((-x_half * math.cos(q), cy, cz + 0.3 + 4.6 * math.sin(q)))
    for i in range(nseg):
        for j in range(nrad):
            p0 = i * (nrad + 1) + j
            fs.append((p0, p0 + nrad + 1, p0 + nrad + 2, p0 + 1))
    o = mesh_obj('Vault', vs, fs, M['wall'], smooth=True)
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.25
    for i in range(1, int((s1 - s0) / 3)):
        s = s0 + 3.0 * i; cy = y2 + s * dy; cz = z2 + TOP + s * dz
        pts = [(-(x_half - 0.08) * math.cos(q), cy, cz + 0.3 + (4.6 - 0.08) * math.sin(q)) for q in np.linspace(0, math.pi, 30)]
        tube_curve('Rib', pts, 0.07, M['wall'])
    return o

def S11(a, b):  # Wheaton station: three very long escalators in a vaulted tunnel; riders far below
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.12, 0.0, 'studio')
    H = 30.0
    Es = []
    for k_, x in enumerate((-1.75, 0.0, 1.75)):
        E = escalator(M, d, H=H, Llo=2.0, Lhi=2.2, loc=(x, 0, 0), u0=0.11 * k_, ret=False, glass=False, floors=False, clad=True,
                      lod_simple=True, ribs_near=lambda y: y > 30.0)
        Es.append(E)
    P = Es[0]['P']
    # median light strips between the escalators (the station's lit balustrade)
    tread = [(y, z + TOP) for (y, z) in P.top_pts((0, 0), 0.0)]
    for x in (-0.875, 0.875, -2.62, 2.62):
        strip('MedianLamp', [(y, z + 0.30) for (y, z) in tread], [(y, z + 0.34) for (y, z) in tread], x - 0.1, x + 0.1, M['lamp'])
        strip('Median', [(y, z + 0.24) for (y, z) in tread], [(y, z + 0.30) for (y, z) in tread], x - 0.13, x + 0.13, M['stain'])
    for sx in (-1, 1):
        strip('Ledge', [(y, z + 0.24) for (y, z) in tread], [(y, z + 0.30) for (y, z) in tread], sx * 2.75, sx * 3.65, M['wall'])
    wheaton_vault(M, P, 3.6)
    plane('Floor', 30, 30, (0, P.y_end + 15, H + TOP), M['floor'])
    plane('FloorLow', 30, 30, (0, -15 + 0.3, TOP), M['floor'])
    for y in np.arange(4, P.y_top0, 7.0):
        z = float(np.interp(y, P.y[P.seg <= 4], P.z[P.seg <= 4]))
        light('POINT', (0, y, z + 4.2), 260, (1.0, 0.9, 0.75), 1.0)
    arm1 = person('Rider1', rot_z=math.radians(180), outfit='casual')
    rider(arm1, Es[1], step_index_at(Es[1], d * 0.5, P.y_top0 - 9.0), d, x=-0.1)
    arm2 = person('Rider2', rot_z=math.radians(180), outfit='office', male=0.0, hair=('long01', 'ponytail01', 'bob02', 'short02'))
    rider(arm2, Es[0], step_index_at(Es[0], d * 0.5, P.y_top0 - 15.0), d, x=0.1)
    yt = P.yt_comb; zt = H + TOP
    camera([(0, Vector((0.0, yt + 1.2, zt + 2.3)), Vector((0.0, yt - 14, zt - 8.6))), (d, Vector((0.0, yt + 0.9, zt + 2.2)), Vector((0.0, yt - 14, zt - 8.9)))], lens=26, fstop=None)

def S12(a, b):  # the whole machine: a chain of little carts going round and round; an engineer watches
    sc, d, M, E = cut_scene(a, b, u0=0.83, rails=True, chain=True, gear=True, strength=0.5); P = E['P']
    glow(M['glow_b'], [(0, 2.5), (d, 2.5)]); glow(M['glow_o'], [(0, 2.5), (d, 2.5)])
    arm = person('Engineer', loc=(-1.7, -0.6, -1.4), rot_z=math.radians(-120), outfit='worker')
    pose(arm, 0.0, STANCES['relax']); pose(arm, 1.2, STANCES['relax']); pose(arm, 2.0, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    camera([(0, Vector((-8.4, -1.6, 2.6)), Vector((0.0, 3.0, 1.4))), (d, Vector((-8.0, -0.4, 2.8)), Vector((0.0, 3.2, 1.5)))], lens=26, fstop=9.0)

def S13(a, b):  # top landing again: the rider arrives, the stairs vanish into the floor
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    E = escalator(M, d, u0=0.91); P = E['P']; hall(M, P); update()
    yt = P.yt_comb; zt = P.H + TOP
    k = step_index_at(E, d, yt - 1.1)
    arm = person('Rider', rot_z=math.radians(180), outfit='casual')
    rider(arm, E, k, d, x=0.1)
    c0 = W(E, (0.3, yt + 0.6, zt + 0.42)); c1 = W(E, (0.26, yt + 0.45, zt + 0.38))
    camera([(0, c0, W(E, (0.0, yt - 2.4, zt + 0.1))), (d, c1, W(E, (0.0, yt - 2.2, zt + 0.1)))], lens=24, fstop=4.0)

def _far(f):
    def g(a, b):
        f(a, b)
        c = bpy.context.scene.camera
        if c: c.data.clip_end = 3000
    return g

SHOTS = [_far(f) for f in (S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13)]

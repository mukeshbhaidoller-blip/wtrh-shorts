# Shots for "This Bridge Hangs From 80,000 Miles of Wire" (how a suspension bridge is built, Golden Gate style).
# Z up, metres. The bridge runs along +Y (south shore -Y, north shore +Y). Towers at y = +-HALF, main cables at x = +-CX.
# Person faces -Y at rot_z=0 (rot_z = theta faces (sin theta, -cos theta)). t = seconds from the shot start.
import bmesh
from mathutils import Matrix

def dur(a, b): return (b - a) / FPS

HALF = 640.0      # half the main span (Golden Gate: 4,200 ft main span)
TOPZ = 227.0      # tower top above the water (746 ft)
SAD = 224.5       # cable centre on the saddle
DZ = 67.0         # road deck top
CX = 18.0         # main cable plane (cables 90 ft apart)
CR = 0.46         # main cable radius (36 3/8 in diameter)
CMIN = DZ + 2.4   # cable centre at mid-span (it comes down to the railing)
SIDE = 343.0      # side span (1,125 ft)
ANCH = HALF + SIDE
ANCHZ = 70.0      # cable enters the anchorage
PANEL = 15.24     # suspender spacing (50 ft)
LAND = 790.0      # shore line |y|

def cz(y):
    ay = abs(y)
    if ay <= HALF: return CMIN + (SAD - CMIN) * (ay / HALF) ** 2
    s = min(1.0, (ay - HALF) / SIDE)
    return SAD + (ANCHZ - SAD) * s - 70.0 * s * (1 - s)

def ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)

def gz(x, y):
    """Ground height (land on both shores, |y| > LAND)."""
    ay = abs(y)
    h = -8.0 + 72.0 * ss(LAND - 10, LAND + 90, ay)
    h += 150.0 * ss(1250, 2600, ay) * (0.55 + 0.45 * math.sin(x / 380.0 + (1.3 if y > 0 else 0.2)))
    h += 5.0 * math.sin(x / 61.0) * math.sin(y / 47.0) * ss(40, 140, abs(x))
    return h

# ---------------------------------------------------------------- materials
def paint_mat(name, col, rough=0.42, grime=0.3, scale=0.08):
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 8
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * (1 - grime) for c in col], 1); ramp.color_ramp.elements[1].color = (*col, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough - 0.1; rr.inputs['To Max'].default_value = rough + 0.15
    nt.links.new(n.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 3.0; nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.08
    nt.links.new(n2.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

def water_mat(name='Water', col=(0.01, 0.035, 0.045), rough=0.04, wave=0.3, scale=0.12, d=6.0, foam=0.0):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    s = inp(p, 'Specular IOR Level', 'Specular')
    if s: s.default_value = 0.6
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale * 0.6, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    key_socket(mp.inputs['Location'], [(0, Vector((0, 0, 0))), (d, Vector((0.3 * d * scale, 0.9 * d * scale, 0.5 * d * scale)))], 'LINEAR')
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 3.0; n.inputs['Detail'].default_value = 10; n.inputs['Roughness'].default_value = 0.62
    nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = wave; bp.inputs['Distance'].default_value = 0.4
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    if foam:
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        e0, e1 = ramp.color_ramp.elements; e0.position = 0.62 - foam * 0.12; e1.position = 0.7
        e0.color = (*col, 1); e1.color = (0.75, 0.8, 0.8, 1)
        nt.links.new(n.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    return m

def rail_mat(name, col):
    """Railing panel: vertical orange bars (wave bands along the panel), see-through between them."""
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = 0.45
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs['Vector'])
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = 1 / 0.42
    nt.links.new(sp.outputs['Y'], mu.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; nt.links.new(mu.outputs['Value'], fr.inputs[0])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.16; nt.links.new(fr.outputs['Value'], lt.inputs[0])
    # solid top/bottom rails
    zt = nt.nodes.new('ShaderNodeMath'); zt.operation = 'GREATER_THAN'; zt.inputs[1].default_value = DZ + 0.75 + 0.6; nt.links.new(sp.outputs['Z'], zt.inputs[0])
    zb = nt.nodes.new('ShaderNodeMath'); zb.operation = 'LESS_THAN'; zb.inputs[1].default_value = DZ + 0.75 - 0.56; nt.links.new(sp.outputs['Z'], zb.inputs[0])
    mx1 = nt.nodes.new('ShaderNodeMath'); mx1.operation = 'MAXIMUM'; nt.links.new(lt.outputs['Value'], mx1.inputs[0]); nt.links.new(zt.outputs['Value'], mx1.inputs[1])
    mx2 = nt.nodes.new('ShaderNodeMath'); mx2.operation = 'MAXIMUM'; nt.links.new(mx1.outputs['Value'], mx2.inputs[0]); nt.links.new(zb.outputs['Value'], mx2.inputs[1])
    out = nt.nodes['Material Output']; tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mx2.outputs['Value'], ms.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], ms.inputs[1]); nt.links.new(p.outputs['BSDF'], ms.inputs[2])
    nt.links.new(ms.outputs['Shader'], out.inputs['Surface'])
    return m

def wires_mat(name='WireFace', cell=0.0049):
    """Cut face of a main cable: thousands of round galvanized wires (voronoi grid), dark gaps."""
    m, nt, p = nodes_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 1.0 / cell
    try: vo.inputs['Randomness'].default_value = 0.08
    except Exception: pass
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.47
    nt.links.new(vo.outputs['Distance'], lt.inputs[0])
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 30; nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.6, 0.61, 0.62, 1); ramp.color_ramp.elements[1].color = (0.85, 0.86, 0.87, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; nt.links.new(lt.outputs['Value'], mx.inputs['Factor'])
    mx.inputs[6].default_value = (0.03, 0.028, 0.026, 1); nt.links.new(ramp.outputs['Color'], mx.inputs[7])
    nt.links.new(mx.outputs[2], p.inputs['Base Color'])
    p.inputs['Metallic'].default_value = 0.55; p.inputs['Roughness'].default_value = 0.4
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.002
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 0.5
    nt.links.new(vo.outputs['Distance'], inv.inputs[1]); nt.links.new(inv.outputs['Value'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    return m

ORANGE = (0.55, 0.075, 0.035)   # International Orange

def mats():
    M = {}
    M['orange'] = paint_mat('BridgeOrange', ORANGE, 0.42, 0.28)
    M['orange_c'] = paint_mat('CableOrange', (0.5, 0.07, 0.035), 0.38, 0.2, scale=0.5)
    M['conc'] = mat_textured('Concrete', ['concrete_floor_worn_001'], 0.08, (0.55, 0.54, 0.52), tint=(0.95, 0.94, 0.9))[0]
    M['conc2'] = mat_textured('Concrete2', ['concrete_floor_02'], 0.3, (0.6, 0.6, 0.58), tint=(1.1, 1.08, 1.04))[0]
    M['asphalt'] = mat_textured('Asphalt', ['asphalt_02'], 0.15, (0.1, 0.1, 0.1), tint=(0.7, 0.7, 0.7))[0]
    M['land'] = mat_textured('Land', ['aerial_grass_rock'], 0.006, (0.3, 0.32, 0.2), rough=(0.85, 1.0), tint=(0.78, 0.74, 0.58))[0]
    M['grass'] = mat_textured('Grass', ['sparse_grass'], 0.25, (0.25, 0.3, 0.12), rough=(0.85, 1.0), bump=0.8, tint=(0.72, 0.7, 0.45))[0]
    M['rock'] = mat_textured('Rock', ['rocky_terrain_02'], 0.06, (0.35, 0.33, 0.3), tint=(0.8, 0.76, 0.7))[0]
    M['shore'] = mat_textured('Shore', ['coast_sand_rocks_02'], 0.2, (0.4, 0.37, 0.33), tint=(0.85, 0.8, 0.74))[0]
    M['steel'] = mat_simple('Steel', (0.5, 0.5, 0.52), 0.3, 1.0)[0]
    M['galv'] = mat_simple('Galvanized', (0.62, 0.63, 0.64), 0.28, 1.0)[0]
    M['dark'] = mat_simple('DarkSteel', (0.05, 0.05, 0.055), 0.5, 0.6)[0]
    M['rust'] = mat_textured('Rust', ['rusty_metal_02'], 1.0, (0.25, 0.13, 0.07), tint=(0.7, 0.55, 0.45))[0]
    M['wood'] = mat_textured('Wood', ['plywood'], 0.5, (0.4, 0.3, 0.2), tint=(0.55, 0.5, 0.45))[0]
    M['rope'] = mat_simple('Rope', (0.12, 0.12, 0.12), 0.5, 0.6)[0]
    M['rail'] = rail_mat('Railing', ORANGE)
    M['water'] = water_mat()
    M['lamp'] = mat_emit('Lamp', (1.0, 0.62, 0.28), 0.0)[0]
    M['white'] = mat_simple('LinePaint', (0.8, 0.8, 0.76), 0.5)[0]
    M['yellow'] = mat_simple('SafetyYellow', (0.85, 0.6, 0.05), 0.45)[0]
    M['studio'] = mat_simple('StudioFloor', (0.05, 0.05, 0.055), 0.55)[0]
    return M

def add_haze(col=(0.62, 0.68, 0.74), d0=1800.0, power=1.0, skip=('Lamp',)):
    """Fake aerial perspective: every material fades toward the haze colour with camera distance."""
    for m in list(bpy.data.materials):
        if not m.use_nodes or m.name.startswith(skip) or m.get('hazed'): continue
        nt = m.node_tree; out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out is None or not out.inputs['Surface'].links: continue
        src = out.inputs['Surface'].links[0].from_socket
        cd = nt.nodes.new('ShaderNodeCameraData')
        dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = d0
        nt.links.new(cd.outputs['View Distance'], dv.inputs[0])
        ng = nt.nodes.new('ShaderNodeMath'); ng.operation = 'MULTIPLY'; ng.inputs[1].default_value = -1.0; nt.links.new(dv.outputs['Value'], ng.inputs[0])
        ex = nt.nodes.new('ShaderNodeMath'); ex.operation = 'EXPONENT'; nt.links.new(ng.outputs['Value'], ex.inputs[0])
        fa = nt.nodes.new('ShaderNodeMath'); fa.operation = 'SUBTRACT'; fa.inputs[0].default_value = 1.0; nt.links.new(ex.outputs['Value'], fa.inputs[1])
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'MULTIPLY'; pw.inputs[1].default_value = power; pw.use_clamp = True
        nt.links.new(fa.outputs['Value'], pw.inputs[0])
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*col, 1); em.inputs['Strength'].default_value = 1.0
        ms = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(pw.outputs['Value'], ms.inputs['Fac'])
        nt.links.new(src, ms.inputs[1]); nt.links.new(em.outputs['Emission'], ms.inputs[2]); nt.links.new(ms.outputs['Shader'], out.inputs['Surface'])
        m['hazed'] = 1

# ---------------------------------------------------------------- mesh helpers
def strut(bm, p, q, r, segs=0):
    p = Vector(p); q = Vector(q); d = q - p; L = d.length
    if L < 1e-6: return
    rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    mtx = Matrix.Translation((p + q) / 2) @ rot
    if segs:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=L, matrix=mtx)
    else:
        bmesh.ops.create_cube(bm, size=1.0, matrix=mtx @ Matrix.Diagonal((2 * r, 2 * r, L, 1)))

def cube(bm, size, loc):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(loc) @ Matrix.Diagonal((*size, 1)))

def bm_obj(name, bm, mat, parent=None, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for pl in me.polygons: pl.use_smooth = True
    o = bpy.data.objects.new(name, me); link(o); o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); link(e); e.location = loc
    if parent: e.parent = parent
    return e

def curve_obj(name, pts, r, mat, res=4):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, q in enumerate(pts): sp.points[i].co = (*q, 1)
    o = bpy.data.objects.new(name, cu); link(o); o.data.materials.append(mat)
    return o

# ---------------------------------------------------------------- scenery
def water(M, mat=None):
    return plane('Sea', 14000, 14000, (0, 0, 0), mat or M['water'])

def terrain(M, sign, x0=-2600, x1=2600, y1=4200, nx=260, ny=110):
    bm = bmesh.new(); V = []
    ys = [LAND - 40 + (y1 - LAND + 40) * (j / (ny - 1)) ** 1.6 for j in range(ny)]
    for j, y in enumerate(ys):
        row = []
        for i in range(nx):
            x = x0 + (x1 - x0) * i / (nx - 1)
            row.append(bm.verts.new((x, sign * y, gz(x, sign * y))))
        V.append(row)
    for j in range(ny - 1):
        for i in range(nx - 1):
            q = [V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]]
            bm.faces.new(q if sign > 0 else q[::-1])
    return bm_obj('Land%+d' % sign, bm, M['land'], smooth=True)

PL = 0.3   # patch lift above gz (covers the coarse terrain mesh)
def gzp(x, y): return gz(x, y) + PL

def patch(M, x0, y0, size=60.0, n=64, mat=None, lift=PL):
    bm = bmesh.new(); V = []
    for j in range(n):
        row = []
        for i in range(n):
            x = x0 - size / 2 + size * i / (n - 1); y = y0 - size / 2 + size * j / (n - 1)
            row.append(bm.verts.new((x, y, gz(x, y) + lift)))
        V.append(row)
    for j in range(n - 1):
        for i in range(n - 1): bm.faces.new([V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]])
    return bm_obj('Patch', bm, mat or M['grass'], smooth=True)

def shores(M):
    terrain(M, 1); terrain(M, -1)

# ---------------------------------------------------------------- bridge parts
TIERS = [(-4.0, DZ - 6.0, 8.0, 12.0), (DZ - 6.0, 128.0, 7.0, 10.8), (128.0, 182.0, 6.4, 9.8), (182.0, TOPZ - 2.0, 5.8, 9.0)]
PORTALS = [(DZ - 9.0, 6.0), (104.0, 7.0), (146.0, 7.0), (186.0, 7.0), (TOPZ - 6.0, 8.0)]

def tower(M, y0, name='Tower'):
    root = empty(name, (0, y0, 0))
    bm = bmesh.new()
    for s in (-1, 1):
        for z0, z1, wx, wy in TIERS:
            cube(bm, (wx, wy, z1 - z0), (s * CX, 0, (z0 + z1) / 2))
            cube(bm, (wx + 0.8, wy + 0.8, 1.2), (s * CX, 0, z1 - 0.6))       # setback ledge
            # vertical fluting on the faces (Art Deco ribs)
            for k in (-1, 1):
                cube(bm, (0.6, 0.5, (z1 - z0) - 2.0), (s * CX + k * wx * 0.28, -wy / 2 - 0.2, (z0 + z1) / 2))
                cube(bm, (0.6, 0.5, (z1 - z0) - 2.0), (s * CX + k * wx * 0.28, wy / 2 + 0.2, (z0 + z1) / 2))
        cube(bm, (6.4, 9.6, 3.5), (s * CX, 0, TOPZ - 0.25))                    # saddle housing
    for zc, h in PORTALS:
        cube(bm, (2 * CX - 4.0, 5.0, h), (0, 0, zc))
        cube(bm, (2 * CX - 4.0, 5.8, 0.8), (0, 0, zc + h / 2))
    o = bm_obj(name + 'Steel', bm, M['orange'], root)
    bm = bmesh.new(); cube(bm, (2 * CX + 30, 46, 14), (0, 0, 2.0))       # concrete pier + fender
    p = bm_obj(name + 'Pier', bm, M['conc'], root)
    return root

def main_cable_pts(x, y0=-ANCH, y1=ANCH, step=6.0, dz=0.0):
    n = int((y1 - y0) / step) + 1; pts = []
    for k in range(n):
        y = y0 + (y1 - y0) * k / (n - 1); pts.append((x, y, cz(y) + dz))
    return pts

def cables(M, y0=-ANCH, y1=ANCH, r=CR, mat=None):
    return [curve_obj('MainCable%+d' % s, main_cable_pts(s * CX, y0, y1), r, mat or M['orange_c'], 4) for s in (-1, 1)]

def hanger_ys(y0=-ANCH + 12, y1=ANCH - 12):
    ys = []; k = -int(ANCH / PANEL)
    while k * PANEL <= ANCH:
        y = k * PANEL
        if y0 <= y <= y1 and abs(abs(y) - HALF) > 8: ys.append(y)
        k += 1
    return ys

def suspenders(M, ys=None, bands=True, per_obj=False, sides=(-1, 1)):
    ys = hanger_ys() if ys is None else ys
    out = []
    if per_obj:
        for s in sides:
            for y in ys:
                top = cz(y) - CR * 0.6; L = top - DZ + 0.4
                if L < 0.4: continue
                bm = bmesh.new()
                for dx in (-0.22, 0.22): strut(bm, (s * CX + dx, y, 0), (s * CX + dx, y, -L), 0.045, 8)
                o = bm_obj('Hanger', bm, M['orange_c']); o.location = (0, 0, top); out.append((o, s, y))
    else:
        bm = bmesh.new()
        for s in sides:
            for y in ys:
                top = cz(y) - CR * 0.6
                if top - DZ < 0.4: continue
                for dx in (-0.22, 0.22): strut(bm, (s * CX + dx, y, top), (s * CX + dx, y, DZ - 0.4), 0.045, 6)
        out.append(bm_obj('Hangers', bm, M['orange_c']))
    if bands:
        bm = bmesh.new()
        for s in sides:
            for y in ys:
                d = (cz(y + 0.5) - cz(y - 0.5)); ang = math.atan2(d, 1.0)
                mtx = Matrix.Translation((s * CX, y, cz(y))) @ Matrix.Rotation(-math.pi / 2 + ang, 4, 'X')
                bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=CR + 0.07, radius2=CR + 0.07, depth=1.1, matrix=mtx)
        bm_obj('CableBands', bm, M['orange_c'], smooth=True)
    return out

def deck_segment(M, y0, y1, name='Deck', lamps=False, truss=True):
    root = empty(name, (0, (y0 + y1) / 2, 0)); L = y1 - y0; h = L / 2
    bm = bmesh.new()
    cube(bm, (2 * CX - 1.0, L, 0.5), (0, 0, DZ - 0.25))                  # road slab
    o = bm_obj(name + 'Road', bm, M['asphalt'], root)
    bm = bmesh.new()
    for s in (-1, 1):
        cube(bm, (3.2, L, 0.35), (s * (CX + 1.9), 0, DZ - 0.05))              # sidewalk (outside the cable plane)
        cube(bm, (0.35, L, 0.25), (s * (CX - 0.7), 0, DZ + 0.12))            # curb
    cube(bm, (0.8, L, 0.8), (0, 0, DZ + 0.4))                               # median barrier
    bm_obj(name + 'Walk', bm, M['conc2'], root)
    bm = bmesh.new()
    for s in (-1, 1):
        cube(bm, (0.08, L, 1.3), (s * (CX + 3.55), 0, DZ + 0.75))
    bm_obj(name + 'Rail', bm, M['rail'], root)
    if truss:
        bm = bmesh.new(); D = 7.6; zt = DZ - 0.6; zb = DZ - D
        nb = max(1, int(round(L / 7.62)))
        for s in (-1, 1):
            x = s * CX
            strut(bm, (x, -h, zt), (x, h, zt), 0.38); strut(bm, (x, -h, zb), (x, h, zb), 0.38)
            for k in range(nb + 1):
                y = -h + L * k / nb
                strut(bm, (x, y, zb), (x, y, zt), 0.18)
                if k < nb:
                    yn = -h + L * (k + 1) / nb
                    if k % 2 == 0: strut(bm, (x, y, zb), (x, yn, zt), 0.16)
                    else: strut(bm, (x, y, zt), (x, yn, zb), 0.16)
        for k in range(nb + 1):
            y = -h + L * k / nb
            strut(bm, (-CX, y, zb), (CX, y, zb), 0.22); strut(bm, (-CX, y, zt - 0.3), (CX, y, zt - 0.3), 0.3)
        for k in range(nb):
            y = -h + L * k / nb; yn = -h + L * (k + 1) / nb
            strut(bm, (-CX, y, zb), (CX, yn, zb), 0.1); strut(bm, (CX, y, zb), (-CX, yn, zb), 0.1)
        bm_obj(name + 'Truss', bm, M['orange'], root)
    if lamps:
        bm = bmesh.new(); bh = bmesh.new()
        n = max(1, int(L // 50))
        for k in range(n):
            y = -h + (k + 0.5) * L / n
            for s in (-1, 1):
                x = s * (CX - 1.1)
                strut(bm, (x, y, DZ), (x, y, DZ + 8.5), 0.09, 8); strut(bm, (x, y, DZ + 8.5), (x - s * 1.6, y, DZ + 8.9), 0.06, 6)
                cube(bh, (0.7, 0.35, 0.18), (x - s * 1.7, y, DZ + 8.82))
        bm_obj(name + 'Poles', bm, M['orange'], root); bm_obj(name + 'Heads', bh, M['lamp'], root)
    return root

def deck(M, y0=-ANCH - 300, y1=ANCH + 300, seg=60.96, lamps=False):
    out = []; y = y0
    while y < y1 - 1e-6:
        yn = min(y1, y + seg); onland = abs((y + yn) / 2) > ANCH + 10
        out.append(deck_segment(M, y, yn, f'Deck{len(out):03d}', lamps=lamps, truss=not onland)); y = yn
    return out

def anchorage(M, sign, name='Anchorage'):
    y = sign * (ANCH + 28)
    bm = bmesh.new(); W = CX + 14
    yf = sign * (ANCH - 2.0); yb = sign * (ANCH + 70.0)
    pts = [(-W, yf, 40.0), (W, yf, 40.0), (-W, yf, ANCHZ + 4.0), (W, yf, ANCHZ + 4.0),
           (-W, yb, 40.0), (W, yb, 40.0), (-W, yb, 104.0), (W, yb, 104.0)]
    vs = [bm.verts.new(q) for q in pts]; bmesh.ops.convex_hull(bm, input=vs)
    cm = mat_textured('AnchorConc', ['concrete_floor_worn_001'], 0.35, (0.55, 0.54, 0.52), tint=(0.92, 0.91, 0.88))[0]
    o = bm_obj(name, bm, cm)
    # cable splay: strands fan out where they enter the block
    bm = bmesh.new()
    for s in (-1, 1):
        p0 = Vector((s * CX, sign * (ANCH - 28), cz(sign * (ANCH - 28))))
        for i in range(-3, 4):
            for j in range(-2, 3):
                strut(bm, p0, (s * CX + i * 0.9, sign * (ANCH + 0.5), ANCHZ - 1.5 + j * 1.0), 0.09, 6)
    bm_obj(name + 'Splay', bm, M['galv'])
    return o

def catwalk(M, x, y0, y1, step=6.0, dz=-1.05, name='Catwalk'):
    bm = bmesh.new(); br = bmesh.new(); n = int((y1 - y0) / step)
    for k in range(n):
        ya = y0 + k * step; yb = ya + step
        pa = Vector((x, ya, cz(ya) + dz)); pb = Vector((x, yb, cz(yb) + dz)); d = pb - pa
        rot = d.to_track_quat('Y', 'Z').to_matrix().to_4x4()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((pa + pb) / 2) @ rot @ Matrix.Diagonal((3.0, d.length, 0.06, 1)))
        for c in range(1, 6):   # cross cleats
            q = pa + d * (c / 6)
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(q + Vector((0, 0, 0.05))) @ rot @ Matrix.Diagonal((3.0, 0.06, 0.05, 1)))
        for s in (-1, 1):       # posts + hand ropes
            strut(br, (x + s * 1.5, ya, cz(ya) + dz), (x + s * 1.5, ya, cz(ya) + dz + 1.1), 0.03, 6)
    bm_obj(name, bm, M['wood'])
    for s in (-1, 1):
        curve_obj(name + 'Rope', [(x + s * 1.5, y, cz(y) + dz + 1.1) for y in [y0 + i * step for i in range(n + 1)]], 0.022, M['rope'], 2)
    bm_obj(name + 'Posts', br, M['rope'])

def bridge(M, lamps=False, deck_on=True, hang=True, cab=True):
    T = [tower(M, -HALF, 'TowerS'), tower(M, HALF, 'TowerN')]
    if cab: cables(M); anchorage(M, 1); anchorage(M, -1)
    if hang: suspenders(M)
    D = deck(M, lamps=lamps) if deck_on else []
    return T, D

def day(rot=30, sun_e=2.3, elev=34, azim=140, s=0.8):
    world_hdri('kloofendal_48d_partly_cloudy_puresky', s, math.radians(rot)); sun(sun_e, elev, azim)

def dusk(rot=190, s=0.8):
    world_hdri('qwantani_dusk_2_puresky', s, math.radians(rot)); sun(1.4, 5, 250, color=(1, 0.62, 0.38))

def big_cam(path, lens=24, fstop=None):
    cam, tgt = camera(path, lens=lens, fstop=fstop); cam.data.clip_end = 9000; return cam, tgt

def hardhat(arm, col=(0.86, 0.86, 0.84)):
    if arm is None: return
    hm = mat_simple('HatWhite', col, 0.35)[0]
    h = sphere('HardHat', 0.135, (0, 0, 0), hm, sub=3); h.scale = (1.0, 1.12, 0.72)
    brim = cyl('Brim', 0.17, 0.012, (0, 0, 0), hm, verts=32); brim.parent = h; brim.location = (0, 0, -0.06)
    hold(arm, h, 'head', (0, 0.17, 0.02), (0, 0, 0))

def worker(name, loc, rot_deg, outfit='worker', hat=False):
    arm = person(name, loc=loc, rot_z=math.radians(rot_deg), outfit=outfit, stance='relax')
    if hat and outfit == 'worker': hardhat(arm)
    return arm

# ---------------------------------------------------------------- shots
def S00(a, b):  # hook: on the sidewalk at mid-span, the huge orange main cable sweeps up past a walker toward the tower top
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(250, 2.4, 30, 115)
    water(M); shores(M); bridge(M)
    arm = person('Walker', loc=(CX + 2.2, -15.0, DZ + 0.13), rot_z=math.radians(0), outfit='casual')
    if arm: key(arm, 'location', [(0, Vector((CX + 2.2, -15.0, DZ + 0.13))), (d, Vector((CX + 2.2, -15.0 - 1.25 * d, DZ + 0.13)))], interp='LINEAR')
    walk(arm, 0.0, d); pose(arm, 0.0, {'neck01': (-14, 0, 0)})
    camera_pts = [(0, (CX + 1.7, -6.0, DZ + 1.0), (CX - 1.0, -200.0, 125.0)), (d, (CX + 1.7, -4.5, DZ + 0.9), (CX - 1.0, -220.0, 140.0))]
    big_cam(camera_pts, lens=24)
    add_haze((0.62, 0.68, 0.76), 2600, 0.8)

def S01(a, b):  # deep rough water: a line of skinny posts across the strait gets swallowed by the waves; no bridge
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('kloofendal_overcast_puresky', 0.9, math.radians(60)); sun(0.8, 25, 160)
    rough = water_mat('RoughSea', (0.012, 0.03, 0.036), 0.08, 0.9, 0.25, d, foam=1.0)
    water(M, rough); shores(M)
    bm = bmesh.new()
    for k in range(14):
        y = -LAND + 25 + k * 55.0
        lean = 0.0 if k < 3 else (k % 3 - 1) * 0.35
        strut(bm, (lean * 2, y, -2.0), (lean * 7, y, 11.0 - k * 0.15), 0.55, 16)
    bm_obj('Posts', bm, M['conc'], smooth=True)
    big_cam([(0, (14.0, -LAND - 10.0, 3.2), (0.0, -LAND + 260.0, 4.0)), (d, (12.0, -LAND + 4.0, 2.8), (0.0, -LAND + 260.0, 3.6))], lens=30)
    add_haze((0.56, 0.6, 0.64), 900, 0.95)

def S02(a, b):  # from the south shore: the two orange towers rise out of the water, one near each shore; a worker watches
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(10, 2.4, 30, 120)
    water(M); shores(M)
    for i, y0 in enumerate((-HALF, HALF)):
        root = tower(M, y0, 'Tower%d' % i)
        t0 = 0.0 if i == 0 else 0.35
        key(root, 'scale', [(t0, Vector((1, 1, 0.25))), (t0 + d * 0.85, Vector((1, 1, 1.0)))])
    y = -LAND - 140.0; x = 120.0
    patch(M, x, y - 10, 120.0)
    arm = worker('Worker', (x - 4.5, y + 0.0, gzp(x - 4.5, y + 0.0)), 200)
    pose(arm, 0.0, {'neck01': (-12, 0, 0)})
    zc = gzp(x, y)
    big_cam([(0, (x - 3.0, y - 9.0, zc + 1.7), (0.0, -HALF + 60, 110.0)), (d, (x - 4.0, y - 10.5, zc + 1.8), (0.0, -HALF + 60, 125.0))], lens=26)
    add_haze((0.62, 0.68, 0.76), 2200, 0.85)

def S03(a, b):  # one tight cable strung between the tower tops pulls both towers in toward each other
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(10, 2.4, 30, 120)
    water(M); shores(M)
    T = [tower(M, -HALF, 'TowerS'), tower(M, HALF, 'TowerN')]
    th = [(0, 0.0), (d * 0.2, 0.0), (d, 6.5)]
    key(T[0], 'rotation_euler', [(t, Vector((-math.radians(v), 0, 0))) for t, v in th])
    key(T[1], 'rotation_euler', [(t, Vector((math.radians(v), 0, 0))) for t, v in th])
    for s in (-1, 1):
        c = cyl('Cable%+d' % s, 0.6, 1.0, (s * CX, 0, SAD), M['steel'], rot=(math.radians(90), 0, 0), verts=16)
        pts = []
        for t, v in th:
            r = math.radians(v); L = 2 * (HALF - SAD * math.sin(r)); pts.append((t, Vector((1, 1, L))))
        key(c, 'scale', pts)
        key(c, 'location', [(t, Vector((s * CX, 0, SAD * math.cos(math.radians(v))))) for t, v in th])
    big_cam([(0, (520.0, -1300.0, 150.0), (0.0, 0.0, 120.0)), (d, (500.0, -1250.0, 150.0), (0.0, 0.0, 118.0))], lens=30)
    add_haze((0.62, 0.68, 0.76), 2400, 0.85)

def S04(a, b):  # on the north headland: the cable dives into a giant concrete anchorage block; worker in a hard hat points
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(20, 2.4, 32, 40)
    water(M); shores(M)
    T = [tower(M, -HALF, 'TowerS'), tower(M, HALF, 'TowerN')]
    cables(M); anchorage(M, 1)
    x = CX + 34.0; y = ANCH - 40.0
    patch(M, x, y - 8, 120.0)
    arm = worker('Worker', (x + 5.9, y - 13.6, gzp(x + 5.9, y - 13.6)), 215)
    pose(arm, 0.2, STANCES['relax']); pose(arm, 1.0, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    zc = gzp(x, y)
    big_cam([(0, (x + 9.0, y - 20.0, zc + 4.5), (CX - 8.0, ANCH + 6.0, 64.0)), (d, (x + 8.0, y - 17.0, zc + 4.3), (CX - 8.0, ANCH + 6.0, 66.0))], lens=22)
    add_haze((0.62, 0.68, 0.76), 2400, 0.85)

def S05(a, b):  # studio: one steel wire with a slab of road hanging from it sags, then snaps; the slab drops with a thud
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    world_hdri('studio_small_09', 0.5, 0, 'studio')
    k1 = light('AREA', (-2.5, -3.0, 3.2), 520, (1, 0.95, 0.88), 2.5); aim(k1, (0, 0, 1.0))
    k2 = light('AREA', (3.0, 2.0, 2.5), 260, (0.85, 0.9, 1.0), 2.0); aim(k2, (0, 0, 1.2))
    plane('Floor', 30, 30, (0, 0, 0), M['studio'])
    for s in (-1, 1):
        box('Stand%+d' % s, (0.2, 0.2, 2.2), (s * 1.0, 0, 1.1), M['steel'], bevel=0.01)
        box('Base%+d' % s, (0.6, 0.6, 0.08), (s * 1.0, 0, 0.04), M['dark'])
    snap = d * 0.62; ztop = 2.15
    halves = []
    for s in (-1, 1):
        h = empty('Half%+d' % s, (s * 1.0, 0, ztop))
        w = cyl('Wire%+d' % s, 0.006, 1.0, (-s * 0.5, 0, 0), M['galv'], rot=(0, math.radians(90), 0), verts=8); w.parent = h
        sag = lambda deg, s=s: Vector((0, -s * math.radians(deg), 0))
        key(h, 'rotation_euler', [(0, sag(4)), (snap - 0.02, sag(13)), (snap + 0.35, sag(80)), (d, sag(88))])
        halves.append(h)
    zmid = lambda deg: ztop - 1.0 * math.sin(math.radians(deg))
    slab = box('Slab', (0.7, 0.36, 0.16), (0, 0, zmid(4) - 0.38), M['conc2'], bevel=0.01)
    hook = cyl('Hook', 0.006, 0.28, (0, 0, zmid(4) - 0.15), M['galv'], verts=8)
    for o, off in ((slab, -0.38), (hook, -0.15)):
        key(o, 'location', [(0, Vector((0, 0, zmid(4) + off))), (snap - 0.02, Vector((0, 0, zmid(13) + off))),
                            (snap + 0.32, Vector((0, 0, 0.09 + (0 if o is slab else 0.2)))), (d, Vector((0, 0, 0.09 + (0 if o is slab else 0.2))))])
    camera([(0, (0.4, -3.3, 1.45), (0, 0, 1.2)), (d, (0.35, -3.1, 1.4), (0, 0, 1.1))], lens=28, fstop=5.6)

def S06(a, b):  # high on the catwalk: a spinning wheel runs along overhead, laying wire after wire; worker on the catwalk
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(300, 2.4, 30, 100)
    water(M); shores(M)
    T = [tower(M, -HALF, 'TowerS'), tower(M, HALF, 'TowerN')]; anchorage(M, 1); anchorage(M, -1)
    for s in (-1, 1): catwalk(M, s * CX, -ANCH + 10, ANCH - 10, 6.0)
    # half-spun cable: loose bundles of wire (strands) along the cable line
    for s in (-1, 1):
        for i in range(7):
            ang = i * 2 * math.pi / 7
            curve_obj('Strand%d%+d' % (i, s), main_cable_pts(s * CX + 0.16 * math.cos(ang), -ANCH, ANCH, 8.0, 0.16 * math.sin(ang)), 0.07, M['galv'], 2)
    # spinning wheel riding a haul rope above the near cable
    yw0, yw1 = -137.0, -137.0 + 1.3 * d
    rig = empty('WheelRig', (CX, yw0, cz(yw0) + 2.2))
    key(rig, 'location', [(0, Vector((CX, yw0, cz(yw0) + 2.2))), (d, Vector((CX, yw1, cz(yw1) + 2.2)))], interp='LINEAR')
    wh = cyl('Wheel', 0.85, 0.16, (0, 0, 0), M['steel'], verts=48); wh.parent = rig; wh.rotation_mode = 'ZYX'
    key(wh, 'rotation_euler', [(0, Vector((0, math.radians(90), 0))), (d, Vector((0, math.radians(90), 1.3 * d / 0.85)))], interp='LINEAR')
    for k in range(6):
        sp = box('Spoke%d' % k, (0.05, 1.6, 0.06), (0, 0, 0), M['dark']); sp.parent = wh; sp.rotation_euler = (0, 0, k * math.pi / 6)
    hub = box('Hanger', (0.12, 0.12, 2.0), (0, 0, 1.0), M['dark']); hub.parent = rig
    curve_obj('HaulRope', main_cable_pts(CX, -ANCH, ANCH, 8.0, 3.2), 0.03, M['rope'], 2)
    for k, dy in enumerate((-0.05, 0.05)):   # two fresh wires trailing behind the wheel
        w = curve_obj('NewWire%d' % k, [(CX + dy, -ANCH + 30, cz(-ANCH + 30) + 0.5), (CX + dy, -300, cz(-300) + 0.9), (CX + dy, -200, cz(-200) + 1.4)], 0.012, M['galv'], 1)
    yp = -128.0
    arm = worker('Worker', (CX - 0.9, yp, cz(yp) - 1.02), 0)
    pose(arm, 0.0, {'neck01': (-10, 0, 0)}); pose(arm, d * 0.5, STANCES['point_r'])
    big_cam([(0, (CX - 1.4, yp + 8.0, cz(yp + 8.0) + 0.9), (CX + 0.1, yp - 9.0, cz(yp - 9.0) + 1.6)),
             (d, (CX - 1.3, yp + 7.0, cz(yp + 7.0) + 0.9), (CX + 0.1, yp - 6.0, cz(yp - 6.0) + 1.8))], lens=24, fstop=8)
    add_haze((0.62, 0.68, 0.76), 2600, 0.8)

def pencil(loc, rotz=0.0):
    pm = paint_mat('PencilYellow', (0.85, 0.55, 0.03), 0.35, 0.05, 40)
    root = empty('Pencil', loc); root.rotation_euler = (0, 0, rotz)
    b = cyl('PencilBody', 0.0036, 0.16, (0, 0, 0), pm, rot=(0, math.radians(90), 0), verts=6); b.parent = root
    wd = mat_simple('PencilWood', (0.75, 0.55, 0.35), 0.6)[0]; gr = mat_simple('Graphite', (0.05, 0.05, 0.05), 0.3, 0.6)[0]
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.0036, radius2=0.0008, depth=0.018, location=(0.089, 0, 0), rotation=(0, math.radians(90), 0))
    c = bpy.context.active_object; c.data.materials.append(wd); c.parent = root
    tip = sphere('Lead', 0.0009, (0.098, 0, 0), gr, sub=2); tip.parent = root
    fe = cyl('Ferrule', 0.0039, 0.012, (-0.086, 0, 0), M_galv(), rot=(0, math.radians(90), 0), verts=24); fe.parent = root
    er = cyl('Eraser', 0.0037, 0.01, (-0.097, 0, 0), mat_simple('Eraser', (0.85, 0.35, 0.35), 0.8)[0], rot=(0, math.radians(90), 0), verts=24); er.parent = root
    return root

def M_galv(): return mat_simple('FerruleMetal', (0.75, 0.72, 0.6), 0.25, 1.0)[0]

def S07(a, b):  # a cut piece of main cable on a plinth at the bridge: thousands of wires, a pencil on the face; pull back to a visitor
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(160, 2.6, 36, 200)
    water(M); shores(M); bridge(M)
    x0, y0 = 70.0, -LAND - 120.0; zg = gz(x0, y0)
    box('Plaza', (40, 40, 0.4), (x0, y0, zg + 0.1), M['conc2'])
    zp = zg + 0.3
    box('Plinth', (1.4, 1.4, 0.45), (x0, y0, zp + 0.225), M['conc'], bevel=0.02)
    H = 0.62; ztop = zp + 0.45 + H
    cy = cyl('CableCut', CR, H, (x0, y0, zp + 0.45 + H / 2), M['orange_c'], verts=96)
    face = cyl('CableFace', CR - 0.012, 0.004, (x0, y0, ztop + 0.001), wires_mat(), verts=96)
    ring = cyl('Band', CR + 0.04, 0.12, (x0, y0, ztop - 0.12), M['orange_c'], verts=96)
    pencil((x0 + 0.05, y0 - 0.06, ztop + 0.0075), math.radians(25))
    arm = person('Visitor', loc=(x0 + 0.95, y0 + 0.35, zp), rot_z=math.radians(-70), outfit='casual')
    pose(arm, 0.0, STANCES['relax']); pose(arm, d * 0.55, STANCES['relax']); pose(arm, d * 0.8, STANCES['point_r']); pose(arm, d, STANCES['point_r'])
    pc = Vector((x0 + 0.05, y0 - 0.06, ztop))
    big_cam([(0, (pc.x + 0.02, pc.y - 0.2, ztop + 0.26), (pc.x, pc.y, ztop)),
             (d * 0.3, (pc.x + 0.03, pc.y - 0.3, ztop + 0.36), (pc.x, pc.y + 0.02, ztop)),
             (d, (x0 - 0.4, y0 - 3.6, ztop + 0.35), (x0 + 0.3, y0 + 0.2, ztop - 0.05))], lens=40, fstop=4)
    add_haze((0.62, 0.68, 0.76), 2600, 0.8)

def S08(a, b):  # from the catwalk: suspender ropes are lowered one after another from the finished cable; no road yet
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(300, 2.4, 30, 100)
    water(M); shores(M)
    T = [tower(M, -HALF, 'TowerS'), tower(M, HALF, 'TowerN')]; cables(M); anchorage(M, 1); anchorage(M, -1)
    catwalk(M, CX, -ANCH + 10, ANCH - 10, 6.0)
    ys = [y for y in hanger_ys(-HALF + 10, HALF - 10)]
    H = suspenders(M, ys, bands=True, per_obj=True)
    for o, s, y in H:
        dist = abs(y - (-60.0)); t0 = 0.2 + dist / 260.0
        key(o, 'scale', [(min(t0, d), Vector((1, 1, 0.0 if t0 > 0.05 else 1.0))), (min(t0 + 1.4, d + 2), Vector((1, 1, 1.0)))])
    yp = -84.0
    arm = worker('Worker', (CX - 0.8, yp, cz(yp) - 1.02), 10)
    pose(arm, 0.0, {'neck01': (12, 0, 0), 'spine02': (8, 0, 0)})
    big_cam([(0, (CX - 2.2, yp + 7.5, cz(yp + 7.5) + 1.2), (CX + 4.0, yp - 70.0, DZ - 8.0)),
             (d, (CX - 2.0, yp + 6.5, cz(yp + 6.5) + 1.3), (CX + 4.0, yp - 80.0, DZ - 10.0))], lens=20)
    add_haze((0.62, 0.68, 0.76), 2600, 0.8)

def S09(a, b):  # wide from the water: road pieces are lifted up from barges and hung, out from the tower in both directions
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(20, 2.4, 30, 120)
    water(M); shores(M)
    T = [tower(M, -HALF, 'TowerS'), tower(M, HALF, 'TowerN')]; cables(M); anchorage(M, 1); anchorage(M, -1); suspenders(M)
    seg = 30.48; done0 = 5; nmax = 11
    for sgn in (-1, 1):            # around each tower: toward mid-span (+) and toward the shore (-)
        for ty in (-HALF, HALF):
            for k in range(nmax):
                y0 = ty + sgn * (6.0 + k * seg); y1 = y0 + sgn * seg
                lo, hi = min(y0, y1), max(y0, y1)
                if abs(lo) > ANCH or abs(hi) > ANCH: continue
                s = deck_segment(M, lo, hi, f'Seg{ty:+.0f}{sgn:+d}{k:02d}')
                if k < done0: continue
                t0 = (k - done0) * d / (nmax - done0 + 0.5)
                zl = -DZ + 4.0
                key(s, 'location', [(0, Vector((0, (lo + hi) / 2, zl))), (t0, Vector((0, (lo + hi) / 2, zl))),
                                    (t0 + 0.9, Vector((0, (lo + hi) / 2, 0)))])
                if t0 > 0.04:
                    for ch in s.children:
                        ch.hide_render = True; ch.keyframe_insert('hide_render', frame=F(0))
                        ch.hide_render = False; ch.keyframe_insert('hide_render', frame=F(t0))
    big_cam([(0, (330.0, -HALF - 110.0, 18.0), (0.0, -HALF + 60.0, 85.0)), (d, (320.0, -HALF - 100.0, 19.0), (0.0, -HALF + 60.0, 86.0))], lens=24)
    add_haze((0.62, 0.68, 0.76), 2400, 0.85)

def S10(a, b):  # under the bridge on the water: the road hangs from the ropes; tilt up the tower that only pushes down
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    day(60, 2.4, 34, 150)
    water(M); shores(M); bridge(M)
    big_cam([(0, (30.0, -380.0, 6.0), (0.0, -330.0, DZ - 6.0)), (d, (34.0, -420.0, 6.0), (0.0, -HALF, 170.0))], lens=20)
    add_haze((0.62, 0.68, 0.76), 2600, 0.8)

def S11(a, b):  # golden dusk from the north headland: a man at the lookout rail, the finished bridge with its lamps glowing
    sc = new_scene(a, b); d = dur(a, b); M = mats()
    dusk(195, 0.85)
    M['lamp'].node_tree.nodes['Emission'].inputs['Strength'].default_value = 40.0
    water(M); shores(M); bridge(M, lamps=True)
    x, y = -150.0, LAND + 82.0; zg = gz(x, y)
    patch(M, x, y + 20, 60.0)
    box('Lookout', (12, 6, 0.4), (x, y, zg + 0.1), M['conc2'])
    box('LookRail', (12, 0.06, 0.06), (x, y - 3.0, zg + 1.25), M['dark'])
    arm = person('Man', loc=(x + 0.8, y - 2.2, zg + 0.3), rot_z=math.radians(12), outfit='casual')
    pose(arm, 0.0, STANCES['relax'])
    big_cam([(0, (x - 1.2, y + 3.2, zg + 2.1), (10.0, 300.0, 135.0)), (d, (x - 0.8, y + 2.8, zg + 2.05), (10.0, 300.0, 131.0))], lens=24)
    add_haze((0.85, 0.6, 0.45), 2400, 0.75)

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11]

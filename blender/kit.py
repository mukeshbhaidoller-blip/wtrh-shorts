# Realistic Blender (Cycles) kit for "Wait, That Really Happened" Shorts.
# Usage:  blender -b --factory-startup -P kit.py -- --proj DIR --assets DIR [--samples 48] [--shots 0,3] [--test] [--redo 0,14]
# DIR must hold timing.json (= data/lines.json from the voice step) and shots.py (defines S00.. and SHOTS = [...]).
# shots.py is exec'd inside this module, so it can use every helper below directly.
import bpy, sys, os, json, math, random, argparse
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--proj', required=True)
ap.add_argument('--assets', default='')
ap.add_argument('--scale', type=float, default=1.0)
ap.add_argument('--samples', type=int, default=64)
ap.add_argument('--shots', default='')
ap.add_argument('--test', action='store_true')          # one still per shot (middle frame)
ap.add_argument('--cpu', action='store_true')
ap.add_argument('--overwrite', action='store_true')
ap.add_argument('--redo', default='')
A = ap.parse_args(argv)

FPS = 24
T = json.load(open(os.path.join(A.proj, 'timing.json')))
LINES = T['lines']; DUR = T['duration']
starts = [0.0] + [max(0.0, l['start'] - 0.12) for l in LINES[1:]]
ends = starts[1:] + [DUR]
FR = [(round(s * FPS), round(e * FPS)) for s, e in zip(starts, ends)]   # global frame ranges per shot [a, b)
OUT = os.path.join(A.proj, 'frames'); os.makedirs(OUT, exist_ok=True)
ASSETS = A.assets

def asset(*p):
    f = os.path.join(ASSETS, *p)
    return f if ASSETS and os.path.exists(f) else None

def tex_file(tid, kind):
    d = os.path.join(ASSETS, tid) if ASSETS else ''
    if not d or not os.path.isdir(d): return None
    for f in os.listdir(d):
        if f.lower().startswith(kind.lower() + '.'): return os.path.join(d, f)
    return None

# ---------------------------------------------------------------- scene / render
GPU = None
def setup_gpu():
    # read_factory_settings() resets the Cycles device prefs, so this must run for EVERY shot
    global GPU
    if A.cpu: return False
    GPU = False
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL'):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                devs = [d for d in prefs.devices if d.type == t]
                if devs:
                    for d in prefs.devices: d.use = (d.type == t)
                    GPU = t; print('GPU device:', t, [d.name for d in devs]); break
            except Exception as e:
                pass
    except Exception as e:
        print('gpu setup failed', e)
    return GPU

def new_scene(a, b):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    g = setup_gpu()
    sc.cycles.device = 'GPU' if g else 'CPU'
    sc.cycles.samples = A.samples if not A.test else max(8, A.samples // 2)
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    try: sc.cycles.denoising_use_gpu = bool(g)
    except Exception: pass
    sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 4; sc.cycles.transmission_bounces = 8
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    try: sc.render.use_persistent_data = True
    except Exception: pass
    sc.render.resolution_x = 1080; sc.render.resolution_y = 1920
    sc.render.resolution_percentage = int(100 * A.scale)
    sc.render.fps = FPS
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 93
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    sc.frame_start = a; sc.frame_end = b - 1
    sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
    return sc

# ---------------------------------------------------------------- animation helpers
SHOT_A = 0
def F(t): return SHOT_A + round(t * FPS)
def key(obj, path, pts, idx=None, interp='BEZIER'):
    """pts: [(t_sec_local, value)]"""
    for t, v in pts:
        if idx is None:
            setattr_path(obj, path, v); obj.keyframe_insert(path, frame=F(t))
        else:
            getattr(obj, path)[idx] = v; obj.keyframe_insert(path, index=idx, frame=F(t))
    ad = obj.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for k in fc.keyframe_points: k.interpolation = interp
def setattr_path(obj, path, v):
    if path in ('location', 'rotation_euler', 'scale'): setattr(obj, path, v)
    else: setattr(obj, path, v)
def fcurves_of(action):
    try: return list(action.fcurves)
    except Exception:
        out = []
        try:
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags: out += list(bag.fcurves)
        except Exception: pass
        return out
def key_socket(sock, pts, interp='BEZIER'):
    for t, v in pts:
        sock.default_value = v; sock.keyframe_insert('default_value', frame=F(t))
def key_light(light, attr, pts):
    for t, v in pts:
        setattr(light, attr, v); light.keyframe_insert(attr, frame=F(t))

# ---------------------------------------------------------------- world
def world_hdri(name, strength=1.0, rot=0.0, fallback='day'):
    w = bpy.context.scene.world; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    f = asset(name + '.hdr') if name else None
    if f:
        env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(f)
        mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord')
        mp.inputs['Rotation'].default_value[2] = rot
        nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
        nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    else:
        if fallback == 'night':
            bg.inputs['Color'].default_value = (0.004, 0.006, 0.012, 1)
        elif fallback == 'studio':
            bg.inputs['Color'].default_value = (0.02, 0.02, 0.022, 1)
        else:
            sky = nt.nodes.new('ShaderNodeTexSky')
            try:
                sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(38 if fallback == 'day' else 4)
                sky.sun_rotation = math.radians(140); sky.altitude = 0
                if fallback == 'overcast': sky.air_density = 6; sky.dust_density = 8
            except Exception: pass
            nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
            bg.inputs['Strength'].default_value = strength * (0.25 if fallback != 'overcast' else 0.12)
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return bg

def sun(energy=3.0, elev=40, azim=140, color=(1, 0.96, 0.9), angle=1.5):
    d = bpy.data.lights.new('Sun', 'SUN'); d.energy = energy; d.color = color; d.angle = math.radians(angle)
    o = bpy.data.objects.new('Sun', d); bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim)); return o

def light(kind, loc, energy, color=(1, 1, 1), size=0.5, rot=None, spot=None, blend=0.3):
    d = bpy.data.lights.new('L', kind); d.energy = energy; d.color = color
    if kind in ('POINT', 'SPOT'): d.shadow_soft_size = size
    if kind == 'AREA': d.size = size
    if kind == 'SPOT' and spot: d.spot_size = math.radians(spot); d.spot_blend = blend
    o = bpy.data.objects.new('L', d); bpy.context.scene.collection.objects.link(o); o.location = loc
    if rot: o.rotation_euler = rot
    return o

def aim(o, target):
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# ---------------------------------------------------------------- camera
def camera(path, lens=35, fstop=None, focus=None, interp='BEZIER'):
    """path: [(t, (x,y,z), (tx,ty,tz))]"""
    cd = bpy.data.cameras.new('Cam'); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 0.01; cd.clip_end = 2000
    cam = bpy.data.objects.new('Cam', cd); bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
    tgt = bpy.data.objects.new('CamTarget', None); bpy.context.scene.collection.objects.link(tgt)
    c = cam.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    for t, p, q in path:
        cam.location = p; cam.keyframe_insert('location', frame=F(t))
        tgt.location = q; tgt.keyframe_insert('location', frame=F(t))
    for o in (cam, tgt):
        for fc in fcurves_of(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = interp
    if fstop:
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
        if focus is None: cd.dof.focus_object = tgt
        else: cd.dof.focus_distance = focus
    return cam, tgt

# ---------------------------------------------------------------- materials
def nodes_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes['Principled BSDF']; return m, nt, p

def inp(p, *names):
    for n in names:
        if n in p.inputs: return p.inputs[n]
    return None

def coord_box(nt, scale):
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); return mp.outputs['Vector']

def img_node(nt, f, vec, color=True):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f, check_existing=True)
    if not color: n.image.colorspace_settings.name = 'Non-Color'
    n.projection = 'BOX'; n.projection_blend = 0.3
    nt.links.new(vec, n.inputs['Vector']); return n

def mat_textured(name, tids, scale, fallback_col, rough=(0.7, 0.95), bump=0.6, tint=None, wet=None, emit=None):
    """PBR from a Poly Haven texture folder, else procedural noise."""
    m, nt, p = nodes_mat(name)
    tid = next((t for t in tids if tex_file(t, 'Diffuse')), None)
    vec = coord_box(nt, scale)
    if tid:
        dif = img_node(nt, tex_file(tid, 'Diffuse'), vec)
        col = dif.outputs['Color']
        if tint is not None:
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            nt.links.new(col, mix.inputs[6]); mix.inputs[7].default_value = (*tint, 1); col = mix.outputs[2]
        nt.links.new(col, p.inputs['Base Color'])
        rf = tex_file(tid, 'Rough')
        if rf:
            r = img_node(nt, rf, vec, False); nt.links.new(r.outputs['Color'], p.inputs['Roughness'])
        nf = tex_file(tid, 'nor_gl')
        if nf:
            nm = img_node(nt, nf, vec, False); nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump * 1.5
            nt.links.new(nm.outputs['Color'], nmap.inputs['Color']); nt.links.new(nmap.outputs['Normal'], p.inputs['Normal'])
    else:
        n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 40; n1.inputs['Detail'].default_value = 12
        nt.links.new(vec, n1.inputs['Vector'])
        vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 220; nt.links.new(vec, vo.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*[c * 0.55 for c in fallback_col], 1); ramp.color_ramp.elements[1].color = (*fallback_col, 1)
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MULTIPLY'
        nt.links.new(n1.outputs['Fac'], mx.inputs[0]); nt.links.new(vo.outputs['Distance'], mx.inputs[1])
        nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
        rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = rough[0]; rr.inputs['To Max'].default_value = rough[1]
        nt.links.new(n1.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.02
        nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    if wet is not None:
        cw = inp(p, 'Coat Weight', 'Clearcoat'); cr = inp(p, 'Coat Roughness', 'Clearcoat Roughness')
        if cw: cw.default_value = wet
        if cr: cr.default_value = 0.03
    return m, p

def mat_simple(name, col, rough=0.5, metal=0.0, coat=0.0, emit=None, estr=0.0, trans=0.0, ior=1.45, sss=0.0, spec=0.5):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    if coat: inp(p, 'Coat Weight', 'Clearcoat').default_value = coat
    if emit:
        inp(p, 'Emission Color', 'Emission').default_value = (*emit, 1); inp(p, 'Emission Strength').default_value = estr
    if trans:
        inp(p, 'Transmission Weight', 'Transmission').default_value = trans; p.inputs['IOR'].default_value = ior
    if sss:
        s = inp(p, 'Subsurface Weight', 'Subsurface'); s.default_value = sss
    return m, p

def mat_paint(name='Paint', col=(0.86, 0.86, 0.82), rough=0.45, worn=0.0, beads=False, glow_col=(1, 0.97, 0.9)):
    """Thermoplastic stripe. 'Emission Strength' doubles as fake retroreflection (keyframed per shot)."""
    m, nt, p = nodes_mat(name)
    vec = coord_box(nt, 1.0)
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 9; n.inputs['Detail'].default_value = 10; n.inputs['Roughness'].default_value = 0.65
    nt.links.new(vec, n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'EASE'
    e0, e1 = ramp.color_ramp.elements; e0.position = 0.45; e1.position = 0.62
    e0.color = (0.11, 0.11, 0.11, 1); e1.color = (*col, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs['Fac'])
    # wear: shift the ramp via a math add on noise
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'; add.inputs[1].default_value = 0.35 - worn
    nt.links.new(n.outputs['Fac'], add.inputs[0]); nt.links.new(add.outputs['Value'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 600 if beads else 160; nt.links.new(vec, vo.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35 if beads else 0.25; bp.inputs['Distance'].default_value = 0.004
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], p.inputs['Normal'])
    inp(p, 'Emission Color', 'Emission').default_value = (*glow_col, 1); inp(p, 'Emission Strength').default_value = 0.0
    m['wear_add'] = add.name
    return m, p, add

def mat_glass(name='Glass', col=(0.95, 0.98, 1.0), rough=0.0):
    m, nt, p = nodes_mat(name)
    p.inputs['Base Color'].default_value = (*col, 1); p.inputs['Roughness'].default_value = rough
    inp(p, 'Transmission Weight', 'Transmission').default_value = 1.0; p.inputs['IOR'].default_value = 1.52
    return m, p

def mat_emit(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], o.inputs['Surface']); return m, e

def mat_rain(name='Rain', strength=0.6, speed=30.0, dur=4.0):
    """Transparent plane with falling streaks (animated noise stretched along z)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    try: m.blend_method = 'BLEND'
    except Exception: pass
    o = nt.nodes.new('ShaderNodeOutputMaterial'); tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (90, 1.6, 1)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    key_socket(mp.inputs['Location'], [(0, Vector((0, 0, 0))), (dur, Vector((0, speed * dur / 10, 0)))], 'LINEAR')
    for fc in []: pass
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.voronoi_dimensions = '2D'; vo.inputs['Scale'].default_value = 1.0
    try: vo.inputs['Randomness'].default_value = 1.0
    except Exception: pass
    nt.links.new(mp.outputs['Vector'], vo.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[1].position = 0.06
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1); ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(vo.outputs['Distance'], ramp.inputs['Fac'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = strength
    em.inputs['Color'].default_value = (0.8, 0.85, 0.95, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(ramp.outputs['Color'], mix.inputs['Fac']); nt.links.new(tr.outputs['BSDF'], mix.inputs[1]); nt.links.new(em.outputs['Emission'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], o.inputs['Surface'])
    return m

# ---------------------------------------------------------------- geometry helpers
def link(o): bpy.context.scene.collection.objects.link(o); return o

def box(name, size, loc, mat=None, bevel=0.0, rot=(0, 0, 0), segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'
    if mat: o.data.materials.append(mat)
    bpy.ops.object.shade_smooth() if bevel else None
    return o

def plane(name, sx, sy, loc, mat=None, subdiv=0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if subdiv:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=subdiv); bpy.ops.object.mode_set(mode='OBJECT')
    if mat: o.data.materials.append(mat)
    return o

def sphere(name, r, loc, mat=None, sub=3, ico=True):
    if ico: bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=sub, location=loc)
    else: bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object; o.name = name; bpy.ops.object.shade_smooth()
    if mat: o.data.materials.append(mat)
    return o

def cyl(name, r, depth, loc, mat=None, rot=(0, 0, 0), verts=64, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name
    if bevel:
        b = o.modifiers.new('bev', 'BEVEL'); b.width = bevel; b.segments = 4; b.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth()
    try: o.data.shade_smooth()
    except Exception: pass
    if mat: o.data.materials.append(mat)
    return o

def dup(o, loc, rot=None, scale=None):
    n = o.copy(); link(n); n.location = loc
    if rot: n.rotation_euler = rot
    if scale: n.scale = scale
    return n

# ---------------------------------------------------------------- road kit
ASPHALT = ['asphalt_02', 'asphalt_04', 'rough_asphalt', 'asphalt_track']
GRASS = ['aerial_grass_rock']
def road(length=400, y0=-60, wet=None, dash_glow=False, lanes=2, worn=0.05, edge=True, shoulder=True, beads=True, dash_every=12.0, dash_len=3.0, grass_scale=0.12):
    am, ap_ = mat_textured('Asphalt', ASPHALT, 0.35, (0.16, 0.16, 0.165), wet=wet)
    W = 3.7 * lanes
    r = plane('Road', W + 1.6, length, (0, y0 + length / 2, 0), am)
    pm, pp, padd = mat_paint('Paint', worn=worn, beads=beads)
    objs = []
    # lane dashes between lanes (x=0 for 2 lanes)
    y = y0
    proto = box('Dash', (0.15, dash_len, 0.004), (0, y, 0.002), pm)
    objs.append(proto)
    while y < y0 + length:
        y += dash_every; objs.append(dup(proto, (0, y, 0.002)))
    if edge:
        for x in (-W / 2, W / 2):
            objs.append(box('Edge', (0.15, length, 0.004), (x, y0 + length / 2, 0.002), pm))
    if shoulder:
        gm, gp = mat_textured('Grass', GRASS, grass_scale, (0.18, 0.26, 0.09), rough=(0.85, 1.0), bump=0.8, tint=(0.55, 0.85, 0.45))
        for s in (-1, 1):
            plane('Grass', 120, length, (s * (W / 2 + 0.8 + 60), y0 + length / 2, -0.03), gm)
    return dict(road=r, paint=(pm, pp, padd), asphalt=(am, ap_), dashes=objs, W=W)

def trees(n=40, xr=(14, 60), yr=(-40, 300), seed=3):
    random.seed(seed)
    fm, fp = mat_textured('Foliage', [], 2.0, (0.09, 0.17, 0.05), rough=(0.6, 0.9), bump=1.0)
    trunk_m, _ = mat_simple('Bark', (0.12, 0.08, 0.05), 0.9)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=4); proto = bpy.context.active_object; proto.name = 'Crown'
    tex = bpy.data.textures.new('crownN', 'CLOUDS'); tex.noise_scale = 0.45
    d = proto.modifiers.new('disp', 'DISPLACE'); d.texture = tex; d.strength = 0.55
    proto.data.materials.append(fm); bpy.ops.object.shade_smooth()
    tr = cyl('Trunk', 0.18, 3, (0, 0, 1.5), trunk_m)
    out = []
    for i in range(n):
        s = random.choice((-1, 1)); x = s * random.uniform(*xr); y = random.uniform(*yr); k = random.uniform(2.2, 4.2)
        c = dup(proto, (x, y, 2.8 + k * 0.8), scale=(k, k, k * 1.15)); t = dup(tr, (x, y, 1.5))
        out += [c, t]
    proto.location = (0, -999, 0); tr.location = (0, -999, 0)
    return out

def car_lights(loc, yaw=0, on=True, strength=900, body=True, color=(0.08, 0.09, 0.1)):
    """A dark car silhouette with two headlights (spot) and tail lights."""
    grp = []
    x, y, z = loc
    if body:
        bm, _ = mat_simple('CarPaint', color, 0.25, 0.6, coat=1.0)
        gm, _ = mat_simple('CarGlass', (0.02, 0.02, 0.025), 0.05, 0.0, coat=1.0)
        b = box('CarBody', (1.85, 4.5, 0.75), (x, y, z + 0.62), bm, bevel=0.18, segs=4)
        c = box('Cabin', (1.6, 2.3, 0.6), (x, y - 0.3, z + 1.25), gm, bevel=0.2, segs=4)
        grp += [b, c]
        tm, _ = mat_simple('Tire', (0.02, 0.02, 0.02), 0.8)
        for dx in (-0.85, 0.85):
            for dy in (-1.4, 1.45):
                grp.append(cyl('Wheel', 0.34, 0.24, (x + dx, y + dy, z + 0.34), tm, rot=(0, math.radians(90), 0)))
        tlm, _ = mat_emit('Tail', (1, 0.05, 0.02), 6)
        for dx in (-0.7, 0.7): grp.append(box('TailL', (0.35, 0.05, 0.12), (x + dx, y - 2.26, z + 0.8), tlm))
        hm, _ = mat_emit('Head', (1, 0.95, 0.85), 30 if on else 0)
        for dx in (-0.68, 0.68): grp.append(box('HeadL', (0.32, 0.05, 0.12), (x + dx, y + 2.26, z + 0.72), hm))
    for dx in (-0.68, 0.68):
        s = light('SPOT', (x + dx, y + 2.3, z + 0.72), strength if on else 0, (1, 0.95, 0.86), 0.06, spot=48, blend=0.5)
        s.rotation_euler = (math.radians(83), 0, 0)   # forward (+y) and slightly down
        try: s.visible_glossy = False; s.visible_diffuse = True
        except Exception: pass
        grp.append(s)
    return grp

def parent_all(objs, name='Rig'):
    e = bpy.data.objects.new(name, None); link(e)
    for o in objs: o.parent = e
    return e

def rpm(loc, face=(1, 0.75, 0.1), glow=0.0, name='RPM'):
    """Raised pavement marker (Botts-style reflector): rounded white body with two reflective faces."""
    bm, _ = mat_simple('RPMBody', (0.85, 0.85, 0.82), 0.4)
    o = box(name, (0.10, 0.10, 0.018), loc, bm, bevel=0.008, segs=3)
    fm, fp = mat_simple('RPMFace', face, 0.15, emit=face, estr=glow)
    fp.inputs['Roughness'].default_value = 0.1
    f1 = box(name + 'F', (0.07, 0.006, 0.012), (loc[0], loc[1] - 0.05, loc[2] + 0.003), fm, rot=(math.radians(-25), 0, 0)); f1.parent = o
    f1.location = (0, -0.05, 0.003)
    return o, fp


def import_model(path, loc=(0, 0, 0), scale=1.0, rot=(0, 0, 0), name='Model'):
    """Import a .glb/.gltf/.fbx/.obj (e.g. a free NASA or Poly Haven model in the assets folder) and parent it to one empty."""
    f = path if os.path.isabs(path) else asset(path)
    if not f: print('MODEL MISSING', path); return None
    before = set(bpy.data.objects)
    ext = os.path.splitext(f)[1].lower()
    if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=f)
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=f)
    elif ext == '.obj': bpy.ops.wm.obj_import(filepath=f)
    elif ext == '.blend':
        with bpy.data.libraries.load(f) as (src, dst): dst.objects = src.objects
        for o in dst.objects:
            if o: link(o)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name, None); link(root)
    for o in new:
        if o.parent is None: o.parent = root
    root.location = loc; root.scale = (scale, scale, scale); root.rotation_euler = rot
    return root

def main():
    global SHOT_A
    pick = [int(x) for x in A.shots.split(',')] if A.shots else list(range(len(SHOTS)))
    redo = [int(x) for x in A.redo.split(',')] if A.redo else []
    for f in os.listdir(OUT):   # drop empty placeholders left by an interrupted run
        fp = os.path.join(OUT, f)
        try:
            n = int(os.path.splitext(f)[0])
        except ValueError:
            continue
        if os.path.getsize(fp) == 0 or any(FR[r][0] <= n < FR[r][1] for r in redo):
            os.remove(fp)
    for i in pick:
        a, b = FR[i]; SHOT_A = a
        print(f'=== SHOT {i:02d} frames {a}-{b - 1} ({(b - a) / FPS:.2f}s) ===', flush=True)
        SHOTS[i](a, b)
        sc = bpy.context.scene
        if A.test:
            sc.frame_set((a + b) // 2)
            sc.render.filepath = os.path.join(A.proj, 'test', f'shot{i:02d}.jpg'); os.makedirs(os.path.dirname(sc.render.filepath), exist_ok=True)
            bpy.ops.render.render(write_still=True)
        else:
            sc.render.filepath = os.path.join(OUT, '#####')
            sc.render.use_overwrite = A.overwrite; sc.render.use_placeholder = not A.overwrite
            bpy.ops.render.render(animation=True)
        print(f'=== SHOT {i:02d} DONE ===', flush=True)

SHOTS = []
exec(compile(open(os.path.join(A.proj, 'shots.py'), encoding='utf-8').read(), 'shots.py', 'exec'), globals())
assert len(SHOTS) == len(LINES), f'need one shot per line: {len(SHOTS)} shots vs {len(LINES)} lines'
main()

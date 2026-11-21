# Shots for the road-lines Short (approved by the owner, 2026-11-21). One function per script line.
# Each S##(a, b) builds a fresh scene for global frames [a, b); use F(t)/key()/camera() with t in seconds from the shot start.
# ---------------------------------------------------------------- shots
def S00(a, b):  # low, cinematic glide over a day highway (shallow focus)
    sc = new_scene(a, b); world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, 1.2, 'day'); sun(2.2, 28, 150)
    road(900, -40, grass_scale=0.45)
    d = (b - a) / FPS
    camera([(0, (-1.2, -6, 1.6), (0.4, 30, 0.2)), (d, (-0.4, 6, 1.1), (0.4, 42, 0.0))], lens=32, fstop=2.0, focus=9.0, interp='LINEAR')

def S01(a, b):  # tire rolls over the stripe, paint wears
    sc = new_scene(a, b); world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, 0.5, 'day'); sun(2.2, 30, 120)
    R = road(60, -30, edge=False, shoulder=False)
    pm, pp, padd = R['paint']
    for o in R['dashes']: o.hide_render = True
    stripe = box('Stripe', (0.15, 40, 0.004), (0, 0, 0.002), pm)
    d = (b - a) / FPS
    key_socket(padd.inputs[1], [(0, 0.35 - 0.02), (d, 0.35 - 0.33)])
    tm, tp = mat_textured('Rubber', ['rubber_tiles'], 3.0, (0.03, 0.03, 0.032), rough=(0.6, 0.85), bump=0.9)
    tire = cyl('Tire', 0.34, 0.24, (0, 0, 0.34), tm, rot=(0, math.radians(90), 0), bevel=0.06)
    rim_m, _ = mat_simple('Rim', (0.6, 0.6, 0.62), 0.25, 1.0)
    rim = cyl('Rim', 0.2, 0.25, (0, 0, 0.34), rim_m, rot=(0, math.radians(90), 0), bevel=0.02); rim.parent = tire; rim.location = (0, 0, 0); rim.rotation_euler = (0, 0, 0)
    # tire rolls along +y across camera view, twice
    key(tire, 'location', [(0, Vector((0, -2.2, 0.34))), (d * 0.5, Vector((0, 2.2, 0.34)))], interp='LINEAR')
    key(tire, 'rotation_euler', [(0, Vector((0, math.radians(90), 0))), (d * 0.5, Vector((-4.4 / 0.34, math.radians(90), 0)))], interp='LINEAR')
    tire2 = tire.copy(); link(tire2); tire2.animation_data_clear()
    key(tire2, 'location', [(d * 0.45, Vector((0.05, -2.4, 0.34))), (d, Vector((0.05, 2.4, 0.34)))], interp='LINEAR')
    key(tire2, 'rotation_euler', [(d * 0.45, Vector((0, math.radians(90), 0))), (d, Vector((-4.8 / 0.34, math.radians(90), 0)))], interp='LINEAR')
    rim2 = rim.copy(); link(rim2); rim2.parent = tire2
    camera([(0, (1.25, -0.9, 0.32), (0, 0.15, 0.05)), (d, (1.15, -0.5, 0.28), (0, 0.3, 0.04))], lens=32, fstop=2.8)

def S02(a, b):  # kettle of molten thermoplastic, pellets melting (~400F)
    sc = new_scene(a, b); world_hdri('kloofendal_overcast_puresky', 0.6, 0, 'overcast')
    d = (b - a) / FPS
    steel, _ = mat_simple('Steel', (0.55, 0.55, 0.56), 0.28, 1.0)
    pot = cyl('Pot', 0.6, 0.7, (0, 0, 0.35), steel, verts=96)
    sol = pot.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.03
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for poly in pot.data.polygons:
        if poly.normal.z > 0.9: poly.select = True
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='FACE'); bpy.ops.object.mode_set(mode='OBJECT')
    lm, lp = mat_simple('Molten', (0.92, 0.9, 0.84), 0.12, sss=0.3)
    liq = plane('Liquid', 1.18, 1.18, (0, 0, 0.55), lm, subdiv=60)
    tex = bpy.data.textures.new('bub', 'VORONOI'); tex.noise_scale = 0.08
    dm = liq.modifiers.new('d', 'DISPLACE'); dm.texture = tex; dm.strength = 0.012; dm.texture_coords = 'OBJECT'
    em = bpy.data.objects.new('BubDrv', None); link(em); dm.texture_coords_object = em
    key(em, 'location', [(0, Vector((0, 0, 0))), (d, Vector((0.05, 0.03, 0.4)))], interp='LINEAR')
    cut = liq.modifiers.new('c', 'BOOLEAN')   # keep liquid inside pot
    cutter = cyl('Cutter', 0.57, 1, (0, 0, 0.55), None, verts=96); cutter.hide_render = True; cutter.display_type = 'WIRE'
    cut.operation = 'INTERSECT'; cut.object = cutter
    pel_m, _ = mat_simple('Pellet', (0.95, 0.95, 0.92), 0.5)
    random.seed(7)
    for i in range(36):
        x, y = random.uniform(-0.42, 0.42), random.uniform(-0.42, 0.42)
        if x * x + y * y > 0.17: continue
        t0 = random.uniform(0, d * 0.6)
        p = box('Pellet', (0.035, 0.035, 0.02), (x, y, 1.4), pel_m, bevel=0.006, rot=(random.random(), random.random(), random.random()))
        key(p, 'location', [(t0, Vector((x, y, 1.3))), (t0 + 0.45, Vector((x, y, 0.56))), (t0 + 1.4, Vector((x, y, 0.53)))])
        key(p, 'scale', [(t0 + 0.45, Vector((1, 1, 1))), (t0 + 1.6, Vector((0.2, 0.2, 0.2)))])
    glow = light('POINT', (0, 0, 0.1), 60, (1, 0.45, 0.15), 0.4)
    light('AREA', (-1.2, -1.0, 2.2), 260, (1, 0.97, 0.92), 1.6, rot=(math.radians(40), 0, math.radians(-50)))
    ground = plane('Ground', 8, 8, (0, 0, 0), mat_textured('Asphalt', ASPHALT, 0.35, (0.16, 0.16, 0.165))[0])
    camera([(0, (0.95, -1.05, 1.35), (0, 0, 0.5)), (d, (0.7, -0.85, 1.15), (0, 0, 0.52))], lens=34, fstop=4)

def S03(a, b):  # hot stripe laid down behind a moving shoe
    sc = new_scene(a, b); world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, 2.0, 'day'); sun(2.2, 35, 100)
    R = road(60, -30, edge=False, shoulder=False)
    for o in R['dashes']: o.hide_render = True
    d = (b - a) / FPS
    hm, hp, _ = mat_paint('HotPaint', rough=0.12)
    inp(hp, 'Coat Weight', 'Clearcoat').default_value = 0.6
    L = 7.0
    st = box('Stripe', (0.15, 1.0, 0.006), (0, 0, 0.003), hm)
    # origin at the start so scaling along y grows it forward
    st.data.transform(__import__('mathutils').Matrix.Translation((0, 0.5, 0))); st.location = (0, -L / 2, 0.003)
    key(st, 'scale', [(0, Vector((1, 0.01, 1))), (d, Vector((1, L, 1)))], interp='LINEAR')
    steel, _ = mat_simple('Steel', (0.6, 0.6, 0.6), 0.3, 1.0)
    shoe = box('Shoe', (0.34, 0.5, 0.22), (0, 0, 0.12), steel, bevel=0.02)
    arm = cyl('Arm', 0.03, 1.2, (0.45, 0, 0.75), steel, rot=(0, math.radians(35), 0)); arm.parent = shoe; arm.location = (0.3, 0, 0.5)
    key(shoe, 'location', [(0, Vector((0, -L / 2 + 0.25, 0.12))), (d, Vector((0, L / 2 + 0.25, 0.12)))], interp='LINEAR')
    camera([(0, (1.5, -3.6, 0.55), (0, -2.6, 0.05)), (d, (1.5, 2.4, 0.55), (0, 3.4, 0.05))], lens=30, fstop=3.5, interp='LINEAR')

def night_road(wet=None, worn=0.05, beads=True):
    world_hdri('dikhololo_night', 0.22, 0, 'night')
    R = road(220, -40, wet=wet, worn=worn, beads=beads, shoulder=True)
    moon = sun(0.08, 30, 200, (0.6, 0.7, 1.0))
    try: moon.visible_glossy = False
    except Exception: pass
    return R

def S04(a, b):  # night: headlights hit the line, it looks gray
    sc = new_scene(a, b); R = night_road()
    pm, pp, padd = R['paint']; pp.inputs['Base Color'].default_value = (0.4, 0.4, 0.4, 1)
    padd.inputs[1].default_value = 0.0
    d = (b - a) / FPS
    rig = parent_all(car_lights((1.85, 0, 0), body=True, strength=1400), 'Car')
    key(rig, 'location', [(0, Vector((0, -6, 0))), (d, Vector((0, 22, 0)))], interp='LINEAR')
    camera([(0, (2.6, -14, 2.1), (1.2, 8, 0.2)), (d, (2.4, 6, 1.9), (1.0, 30, 0.2))], lens=30, interp='LINEAR')

def S05(a, b):  # glass beads sprinkled onto the soft stripe
    sc = new_scene(a, b); world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, 1.0, 'day'); sun(2.2, 40, 120)
    R = road(20, -10, edge=False, shoulder=False)
    for o in R['dashes']: o.hide_render = True
    hm, hp, _ = mat_paint('HotPaint', rough=0.2)
    st = box('Stripe', (0.15, 6, 0.006), (0, 0, 0.003), hm)
    gm, _ = mat_glass('Bead')
    d = (b - a) / FPS
    random.seed(11)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.0035, subdivisions=2); proto = bpy.context.active_object; bpy.ops.object.shade_smooth(); proto.data.materials.append(gm)
    for i in range(420):
        x = random.gauss(0, 0.05); y = random.uniform(-0.45, 0.45); t0 = random.uniform(0, d * 0.75)
        bb = dup(proto, (x, y, 0.5))
        land = 0.0062 if abs(x) < 0.075 else 0.0035
        key(bb, 'location', [(max(0, t0 - 0.01), Vector((x * 0.3, y, 0.42))), (t0 + 0.38, Vector((x, y, land)))], interp='LINEAR')
        key(bb, 'location', [(t0 + 0.38, Vector((x, y, land))), (d + 1, Vector((x, y, land)))], interp='CONSTANT')
    proto.location = (0, 0, -5)
    steel, _ = mat_simple('Steel', (0.6, 0.6, 0.6), 0.3, 1.0)
    noz = cyl('Nozzle', 0.04, 0.3, (0, 0, 0.6), steel, verts=48)
    camera([(0, (0.42, -0.62, 0.22), (0, 0, 0.02)), (d, (0.34, -0.5, 0.17), (0, 0.04, 0.01))], lens=50, fstop=2.2)

def bead_macro(a, b, refract=False):
    sc = new_scene(a, b); world_hdri('studio_small_09', 0.15, 0, 'studio')
    d = (b - a) / FPS
    # cross-section slab: asphalt below, stripe layer, half-embedded glass beads
    am, _ = mat_textured('Asphalt', ASPHALT, 3.0, (0.12, 0.12, 0.125))
    box('AsphaltSlab', (6, 3, 1.0), (0, 0, -0.5), am)
    pm, pp, _ = mat_paint('PaintX', rough=0.5); pp.inputs['Base Color'].default_value = (0.85, 0.85, 0.82, 1)
    box('PaintLayer', (6, 3, 0.3), (0, 0, 0.15), pm)
    gm, _ = mat_glass('BeadGlass')
    hero = sphere('Hero', 0.42, (0, 0, 0.3), gm, ico=False)
    random.seed(5)
    for i in range(16):
        x = random.uniform(-2.8, 2.8); y = random.uniform(-1.3, 1.3)
        if abs(x) < 0.7 and abs(y) < 0.7: continue
        r = random.uniform(0.12, 0.3); sphere('B', r, (x, y, 0.3 + r * random.uniform(-0.2, 0.25)), gm, ico=False)
    # light rays (emissive tubes)
    rin, ein = mat_emit('RayIn', (1, 0.92, 0.7), 14)
    rout, eout = mat_emit('RayOut', (1, 0.92, 0.7), 14)
    def ray(p0, p1, mat, t0, t1):
        p0 = Vector(p0); p1 = Vector(p1); v = p1 - p0
        c = cyl('Ray', 0.025, 1.0, (0, 0, 0), mat, verts=16)
        c.data.transform(__import__('mathutils').Matrix.Translation((0, 0, 0.5)))
        c.location = p0; c.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
        key(c, 'scale', [(t0, Vector((1, 1, 0.001))), (t1, Vector((1, 1, v.length)))])
        return c
    src = (-3.2, -0.6, 3.4)
    if not refract:
        ray(src, (-0.12, -0.02, 0.66), rin, 0.1, 0.9)
        ray((-0.12, -0.02, 0.66), (-3.0, -0.55, 3.55), rout, 1.0, 1.9)
    else:
        ray(src, (-0.25, 0, 0.58), rin, 0.1, 0.8)
        ray((-0.25, 0, 0.58), (0.12, 0, 0.0), rin, 0.8, 1.3)
        ray((0.12, 0, 0.0), (0.3, 0, 0.52), rout, 1.3, 1.8)
        ray((0.3, 0, 0.52), (-2.9, -0.5, 3.6), rout, 1.8, 2.6)
    light('AREA', (-2.5, -2.5, 4.0), 900, (1, 0.98, 0.95), 2.5, rot=(math.radians(35), 0, math.radians(-45)))
    light('AREA', (3, 2.0, 2.0), 250, (0.7, 0.8, 1.0), 2.0, rot=(math.radians(55), 0, math.radians(125)))
    spot = light('SPOT', src, 2500, (1, 0.9, 0.7), 0.1, spot=8, blend=0.4); aim(spot, (0, 0, 0.5))
    if not refract:
        camera([(0, (1.3, -3.2, 1.2), (0, 0, 0.4)), (d, (0.6, -2.7, 1.0), (0, 0, 0.42))], lens=45, fstop=5)
    else:
        camera([(0, (-0.9, -3.0, 0.9), (0, 0, 0.35)), (d, (0.3, -2.6, 0.75), (0, 0, 0.35))], lens=50, fstop=6)

def S06(a, b): bead_macro(a, b, False)
def S13(a, b): bead_macro(a, b, True)

def rain_layers(cam_y=0, d=4.0, n=3, dist=(4, 9, 16)):
    m = mat_rain('Rain', 0.5, 30, d)
    for k in range(n):
        p = plane('RainSheet', 30, 18, (0, cam_y + dist[k], 6), m); p.rotation_euler = (math.radians(90), 0, 0)
        try: p.visible_shadow = False
        except Exception: pass

def S07(a, b):  # rain, water film covers beads
    sc = new_scene(a, b); R = night_road(wet=1.0)
    pm, pp, padd = R['paint']; d = (b - a) / FPS
    key_socket(inp(pp, 'Emission Strength'), [(0, 1.6), (d, 0.2)])
    rig = parent_all(car_lights((1.85, 0, 0), body=True, strength=1500), 'Car')
    key(rig, 'location', [(0, Vector((0, -2, 0))), (d, Vector((0, 10, 0)))], interp='LINEAR')
    rain_layers(-8, d)
    camera([(0, (2.3, -9, 1.7), (1.2, 10, 0.2)), (d, (2.2, -1, 1.5), (1.0, 18, 0.2))], lens=30, interp='LINEAR')

def S08(a, b):  # line disappears in the wet
    sc = new_scene(a, b); R = night_road(wet=1.0)
    pm, pp, padd = R['paint']; d = (b - a) / FPS
    key_socket(inp(pp, 'Emission Strength'), [(0, 0.25), (d * 0.7, 0.0)])
    key_socket(pp.inputs['Base Color'], [(0, (0.5, 0.5, 0.5, 1)), (d * 0.8, (0.12, 0.12, 0.12, 1))])
    for s in car_lights((1.85, -3, 0), body=False, strength=1700): pass
    rain_layers(-2, d)
    camera([(0, (1.85, -2.6, 1.15), (0.6, 12, 0.0)), (d, (1.85, -2.0, 1.1), (0.4, 14, 0.0))], lens=28, interp='LINEAR')

def S09(a, b):  # California glues raised reflectors between the lanes
    sc = new_scene(a, b); world_hdri('kloofendal_48d_partly_cloudy_puresky', 0.8, 2.6, 'day'); sun(2.2, 50, 110)
    R = road(80, -20, shoulder=True); d = (b - a) / FPS
    for o in R['dashes']: o.hide_render = True
    glue, _ = mat_simple('Glue', (0.02, 0.02, 0.02), 0.25)
    for i in range(9):
        y = -0.6 + i * 1.2; t0 = 0.15 + i * 0.32
        blob = cyl('Glue', 0.07, 0.006, (0, y, 0.003), glue, verts=32)
        key(blob, 'scale', [(t0 - 0.2, Vector((0.01, 0.01, 1))), (t0, Vector((1, 1, 1)))])
        o, fp = rpm((0, y, 0.6), (1, 0.72, 0.08))
        key(o, 'location', [(t0, Vector((0, y, 0.45))), (t0 + 0.25, Vector((0, y, 0.016)))])
    camera([(0, (0.7, -2.4, 0.42), (0, 1.5, 0)), (d, (0.6, -1.4, 0.36), (0, 3.0, 0))], lens=35, fstop=3.2)

def S10(a, b):  # reflectors stick up above the water, glowing
    sc = new_scene(a, b); R = night_road(wet=1.0); d = (b - a) / FPS
    for o in R['dashes']: o.hide_render = True
    pm, pp, padd = R['paint']; pp.inputs['Base Color'].default_value = (0.2, 0.2, 0.2, 1)
    faces = []
    for i in range(30):
        o, fp = rpm((0, -1 + i * 2.4, 0.016), (1, 0.72, 0.08), glow=0.0); faces.append(fp)
    for fp in faces[:1]: pass
    fm = faces[0]
    for k, fp in enumerate(faces):
        key_socket(inp(fp, 'Emission Strength'), [(0, 0.0), (0.4, 0.0), (0.9, 25.0)])
    car_lights((1.85, -6, 0), body=False, strength=1700)
    rain_layers(-4, d)
    camera([(0, (1.0, -4.5, 0.55), (0, 8, 0)), (d, (0.9, -2.5, 0.5), (0, 10, 0))], lens=32, fstop=2.8, interp='LINEAR')

def S11(a, b):  # snowplow blade scrapes a reflector off
    sc = new_scene(a, b); world_hdri('snowy_field', 0.9, 0, 'overcast'); sun(1.0, 25, 60, (0.9, 0.95, 1.0), 8)
    d = (b - a) / FPS
    am, _ = mat_textured('Asphalt', ASPHALT, 0.35, (0.16, 0.16, 0.165), wet=0.4)
    plane('Road', 9, 80, (0, 10, 0), am)
    sm, sp = mat_textured('Snow', ['snow_02'], 0.6, (0.92, 0.94, 0.98), rough=(0.35, 0.6), bump=0.8)
    s2 = inp(sp, 'Subsurface Weight', 'Subsurface')
    if s2: s2.default_value = 0.3
    for x in (-6.5, 6.5):
        bank = plane('SnowBank', 5, 80, (x, 10, 0.1), sm, subdiv=40)
        tx = bpy.data.textures.new('sn', 'CLOUDS'); tx.noise_scale = 0.8
        dm = bank.modifiers.new('d', 'DISPLACE'); dm.texture = tx; dm.strength = 0.5
    # thin snow on road with a scraped lane
    pm, pp, _ = mat_paint('Paint', worn=0.15)
    box('Edge', (0.15, 80, 0.004), (0, 10, 0.002), pm)
    o, fp = rpm((0, 3.0, 0.016), (1, 0.72, 0.08), name='Victim')
    for i in range(1, 6): rpm((0, 3.0 + i * 2.4, 0.016), (1, 0.72, 0.08))
    ym, _ = mat_simple('PlowYellow', (0.85, 0.55, 0.02), 0.35, 0.2, coat=0.6)
    blade = box('Blade', (3.6, 0.12, 0.9), (0, 0, 0.47), ym, bevel=0.04)
    steel, _ = mat_simple('Edge', (0.4, 0.4, 0.42), 0.3, 1.0)
    edge = box('CutEdge', (3.6, 0.14, 0.06), (0, 0.02, 0.03), steel); edge.parent = blade; edge.location = (0, 0.02, -0.44)
    hit = d * 0.48
    key(blade, 'location', [(0, Vector((0.2, -4.0, 0.47))), (d, Vector((0.2, 5.5, 0.47)))], interp='LINEAR')
    key(o, 'location', [(hit, Vector((0, 3.0, 0.016))), (hit + 0.7, Vector((-1.6, 5.8, 1.1))), (hit + 1.3, Vector((-2.8, 7.2, 0.05)))])
    key(o, 'rotation_euler', [(hit, Vector((0, 0, 0))), (hit + 1.3, Vector((5.5, 2.0, 3.0)))])
    # flying snow clumps
    snow_m, _ = mat_simple('SnowClump', (0.95, 0.96, 1.0), 0.6, sss=0.2)
    random.seed(2)
    for i in range(60):
        t0 = random.uniform(0, d); x = random.uniform(-1.7, 1.7)
        yb = -4.0 + 9.5 * t0 / d
        c = sphere('Clump', random.uniform(0.02, 0.06), (x, yb, 0.3), snow_m, sub=1)
        key(c, 'location', [(t0, Vector((x, yb + 0.1, 0.3))), (t0 + 0.8, Vector((x + random.choice((-1, 1)) * random.uniform(1.5, 3), yb + 1.2, 0.05)))])
    camera([(0, (5.2, -5.5, 1.7), (0, 2.0, 0.3)), (d, (4.8, -1.5, 1.5), (0, 4.5, 0.3))], lens=32, fstop=5, interp='LINEAR')

def S12(a, b):  # pocket cut into the road, reflector tucked inside, blade passes over
    sc = new_scene(a, b); world_hdri('studio_small_09', 0.35, 0, 'studio')
    d = (b - a) / FPS
    am, _ = mat_textured('Asphalt', ASPHALT, 1.2, (0.15, 0.15, 0.155))
    slab = box('Slab', (2.4, 2.4, 0.5), (0, 0, -0.25), am)
    cutter = box('Pocket', (0.2, 0.62, 0.2), (0, 0, 0.0), None, bevel=0.06); cutter.hide_render = True; cutter.display_type = 'WIRE'
    bo = slab.modifiers.new('b', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cutter
    pm, pp, _ = mat_paint('Paint', worn=0.05); box('Line', (0.15, 2.4, 0.004), (0.32, 0, 0.002), pm)
    o, fp = rpm((0, 0, 0.6), (1, 0.72, 0.08), glow=0.0, name='Inset')
    o.scale = (1.6, 3.2, 2.0)
    key(o, 'location', [(0.2, Vector((0, 0, 0.5))), (1.0, Vector((0, 0, -0.03)))])
    ym, _ = mat_simple('PlowYellow', (0.85, 0.55, 0.02), 0.35, 0.2, coat=0.6)
    blade = box('Blade', (2.8, 0.1, 0.5), (0, -2.5, 0.27), ym, bevel=0.03)
    key(blade, 'location', [(1.6, Vector((0, -2.5, 0.27))), (d, Vector((0, 2.5, 0.27)))], interp='LINEAR')
    key_socket(inp(fp, 'Emission Strength'), [(d * 0.75, 0.0), (d, 12.0)])
    light('AREA', (-2, -2, 3), 500, (1, 0.98, 0.95), 2.5, rot=(math.radians(40), 0, math.radians(-45)))
    light('AREA', (2.5, 1, 1.5), 150, (0.75, 0.85, 1.0), 2.0, rot=(math.radians(60), 0, math.radians(110)))
    camera([(0, (1.9, -2.4, 1.6), (0, 0, -0.05)), (d, (1.5, -2.0, 1.25), (0, 0, -0.05))], lens=38, fstop=5)

def S14(a, b):  # aerial: night lines glow, then daylight
    sc = new_scene(a, b); d = (b - a) / FPS
    w = sc.world; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld'); mix = nt.nodes.new('ShaderNodeMixShader')
    bn = nt.nodes.new('ShaderNodeBackground'); bn.inputs['Color'].default_value = (0.003, 0.005, 0.01, 1)
    bd = nt.nodes.new('ShaderNodeBackground')
    fd = asset('kloofendal_48d_partly_cloudy_puresky.hdr')
    if fd:
        env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(fd); nt.links.new(env.outputs['Color'], bd.inputs['Color'])
    else:
        sky = nt.nodes.new('ShaderNodeTexSky')
        try: sky.sky_type = 'NISHITA'; sky.sun_elevation = math.radians(38)
        except Exception: pass
        nt.links.new(sky.outputs['Color'], bd.inputs['Color']); bd.inputs['Strength'].default_value = 0.25
    nt.links.new(bn.outputs['Background'], mix.inputs[1]); nt.links.new(bd.outputs['Background'], mix.inputs[2]); nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    tsw = d * 0.55
    key_socket(mix.inputs['Fac'], [(tsw - 0.25, 0.0), (tsw + 0.35, 1.0)])
    sn = sun(0.0, 42, 150)
    key_light(sn.data, 'energy', [(tsw - 0.25, 0.0), (tsw + 0.35, 3.2)])
    R = road(900, -60, grass_scale=0.45)
    pm, pp, padd = R['paint']
    key_socket(inp(pp, 'Emission Strength'), [(0, 3.0), (tsw - 0.25, 3.0), (tsw + 0.35, 0.0)])
    for k in range(3):
        rig = parent_all(car_lights((1.85, 0, 0), body=True, strength=1500), 'Car%d' % k)
        key(rig, 'location', [(0, Vector((0, 5 + k * 25, 0))), (d, Vector((0, 5 + k * 25 + 60, 0)))], interp='LINEAR')
    camera([(0, (3.5, -14, 7), (0.5, 30, 0)), (d, (2.0, 6, 4.5), (0.5, 45, 0))], lens=28, interp='LINEAR')

SHOTS = [S00, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14]


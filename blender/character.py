# Realistic people for the Blender kit, made with MPFB (MakeHuman for Blender, CC0 assets) on the owner's PC.
# exec'd by kit.py after the kit helpers; needs the MPFB extension + asset packs installed in the PC's Blender
# (jobs/004-mpfb-setup). Not available in the cloud test venv: person() returns None there, so test stills show no one.
import addon_utils, glob
from importlib import import_module

_MP = {}


def _mpfb():
    """Enable MPFB (read_factory_settings() disables add-ons, so do it for every scene) and return its services."""
    mods = [m.__name__ for m in addon_utils.modules() if m.__name__.split('.')[-1] == 'mpfb']
    if not mods: return None
    for m in mods:
        try: addon_utils.enable(m, default_set=False)
        except Exception as e: print('MPFB enable failed', m, e)
    pkg = mods[0]
    if pkg not in _MP:
        _MP[pkg] = dict(HS=import_module(pkg + '.services.humanservice').HumanService,
                        LS=import_module(pkg + '.services.locationservice').LocationService)
    return _MP[pkg]


def _pick(LS, sub, keys, ext):
    """First asset file (basename) under user data/<sub> whose name contains one of keys (tried in order)."""
    files = glob.glob(os.path.join(LS.get_user_data(sub), '**', '*' + ext), recursive=True)
    files += glob.glob(os.path.join(LS.get_mpfb_data(sub), '**', '*' + ext), recursive=True)
    names = [os.path.basename(f) for f in files]
    for k in keys:
        for n in names:
            if k.lower() in n.lower(): return n
    return None


# Outfits that looked right in the PC test (2026-11-21). Keywords are matched against installed .mhclo names.
OUTFITS = dict(
    casual=dict(clothes=(('namuhekam_male_polo_shirt',), ('toigo_wool_pants', 'cortu_cargo_pants'), ('toigo_ankle_boots_male', 'shoes02')), extra=(('jujube_newsboy_cap',),)),
    worker=dict(clothes=(('male_worksuit01',), ('toigo_ankle_boots_male', 'shoes02')), extra=()),
    office=dict(clothes=(('male_casualsuit02', 'male_casualsuit01'), ('shoes01', 'shoes02')), extra=()),
)
# Bone rotations (degrees, local XYZ) learned from the PC tests on the MPFB 'default' rig:
#   upperarm01.L: Z- lowers the arm to the side, X+ raises it forward/up.  upperarm01.R: mirrored Z (Z+ lowers).
#   lowerarm01.*: X+ bends the elbow.  upperleg01.*: X- swings the leg forward, X+ back.  lowerleg01.*: X+ bends the knee.
#   spine02: X+ bends forward.  neck01: Z turns/tilts the head.  A BVH pose ('standing02') gives the most natural idle.
STANCES = dict(
    relax={'upperarm01.L': (0, 0, -55), 'upperarm01.R': (0, 0, 55), 'lowerarm01.L': (10, 0, 0), 'lowerarm01.R': (10, 0, 0)},
    point_r={'upperarm01.L': (0, 0, -55), 'upperarm01.R': (45, 0, 25), 'lowerarm01.R': (5, 0, 0), 'lowerarm01.L': (10, 0, 0)},
    wave_r={'upperarm01.L': (0, 0, -55), 'upperarm01.R': (75, 0, 30), 'lowerarm01.R': (5, 0, 0)},
    work_low={'spine02': (22, 0, 0), 'upperarm01.L': (55, 0, -30), 'upperarm01.R': (45, 0, 30), 'lowerarm01.L': (40, 0, 0), 'lowerarm01.R': (40, 0, 0)},
    step_a={'upperleg01.L': (-22, 0, 0), 'upperleg01.R': (16, 0, 0), 'lowerleg01.R': (28, 0, 0), 'upperarm01.L': (-12, 0, -58), 'upperarm01.R': (16, 0, 58)},
    step_b={'upperleg01.R': (-22, 0, 0), 'upperleg01.L': (16, 0, 0), 'lowerleg01.L': (28, 0, 0), 'upperarm01.R': (-12, 0, 58), 'upperarm01.L': (16, 0, -58)},
)


def bvh_pose(arm, name='standing02'):
    """Apply one of the installed MakeHuman BVH poses (standing01-06, sit01, run01, fight01..) as the base pose.
    Note: it rewrites bone rolls, so add STANCES on top only after checking a test still."""
    mp = _mpfb()
    if not mp or arm is None: return False
    try:
        pkg = next(k for k in _MP)
        AS = import_module(pkg + '.services.animationservice').AnimationService
        f = glob.glob(os.path.join(mp['LS'].get_user_data('poses'), '**', name + '.bvh'), recursive=True)[0]
        AS.import_bvh_file_as_pose(arm, f); return True
    except Exception as e:
        print('BVH POSE FAILED', name, e); return False


def walk(arm, t0, t1, step=0.55):
    """Simple keyframed walk cycle between shot times t0..t1 (move the armature's location yourself)."""
    t, k = t0, 0
    while t <= t1:
        pose(arm, t, STANCES['step_a' if k % 2 == 0 else 'step_b']); t += step; k += 1


def person(name='Person', loc=(0, 0, 0), rot_z=0.0, outfit='casual', male=1.0, age=0.5, muscle=0.62, weight=0.58, height=0.55,
           race=(0.2, 0.7, 0.1), skin=('middleage_caucasian_male', 'young_caucasian_male2', 'young_caucasian_male'),
           hair=('short02', 'short04', 'short'), clothes=None, extra=None, eyebrows=('eyebrow001',), subdiv=1, stance='relax'):
    """Make a rigged realistic human (MPFB 'default' rig). Returns the armature object (or None if MPFB is missing).
    clothes/extra: tuples of keyword alternatives, e.g. ('cap', 'hat'). race = (african, caucasian, asian)."""
    mp = _mpfb()
    if not mp:
        print('MPFB not available: person() skipped'); return None
    o = OUTFITS.get(outfit, OUTFITS['casual'])
    clothes = o['clothes'] if clothes is None else clothes
    extra = o['extra'] if extra is None else extra
    HS, LS = mp['HS'], mp['LS']
    info = HS._create_default_human_info_dict()
    info['phenotype'].update(gender=male, age=age, muscle=muscle, weight=weight, height=height, proportions=0.6)
    info['phenotype']['race'] = dict(african=race[0], caucasian=race[1], asian=race[2])
    info['rig'] = 'default'
    info['eyes'] = _pick(LS, 'eyes', ('high-poly', 'low-poly'), '.mhclo') or ''
    info['eyebrows'] = _pick(LS, 'eyebrows', eyebrows, '.mhclo') or ''
    info['eyelashes'] = _pick(LS, 'eyelashes', ('eyelashes01', 'eyelashes'), '.mhclo') or ''
    info['teeth'] = _pick(LS, 'teeth', ('teeth_base', 'teeth'), '.mhclo') or ''
    info['hair'] = (_pick(LS, 'hair', hair, '.mhclo') or '') if hair else ''
    info['skin_mhmat'] = _pick(LS, 'skins', skin, '.mhmat') or ''
    info['skin_material_type'] = 'ENHANCED_SSS'
    info['eyes_material_type'] = 'PROCEDURAL_EYES'
    info['clothes'] = [c for c in (_pick(LS, 'clothes', k, '.mhclo') for k in list(clothes) + list(extra)) if c]
    info.setdefault('alternative_materials', {})
    print('PERSON', name, {k: info[k] for k in ('eyes', 'hair', 'skin_mhmat', 'clothes')})
    st = HS.get_default_deserialization_settings(); st['subdiv_levels'] = subdiv
    basemesh = HS.deserialize_from_dict(info, st)
    arm = basemesh.parent if basemesh.parent and basemesh.parent.type == 'ARMATURE' else None
    if arm is None:
        arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE' and basemesh in o.children), None)
    root = arm or basemesh
    root.name = name; root.location = loc; root.rotation_euler = (0, 0, rot_z)
    if arm:
        for b in arm.pose.bones: b.rotation_mode = 'XYZ'
        if stance in STANCES: pose(arm, 0.0, STANCES[stance])
    return root


def pose(arm, t, bones, interp='BEZIER'):
    """Keyframe bone rotations (degrees, XYZ euler in the bone's local space) at shot time t.
    bones: {'upperarm01.L': (x, y, z), ...}. Unlisted bones keep their previous keys."""
    if arm is None: return
    for bn, deg in bones.items():
        pb = arm.pose.bones.get(bn)
        if pb is None: print('no bone', bn); continue
        pb.rotation_euler = tuple(math.radians(v) for v in deg)
        pb.keyframe_insert('rotation_euler', frame=F(t))
    if arm.animation_data and arm.animation_data.action:
        for fc in fcurves_of(arm.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = interp


def hold(arm, obj, bone='wrist.R', offset=(0, 0, 0), rot=(0, 0, 0)):
    """Parent a prop (shovel, phone, tool) to a hand bone so it moves with the hand."""
    if arm is None or obj is None: return
    obj.parent = arm; obj.parent_type = 'BONE'; obj.parent_bone = bone
    obj.location = offset; obj.rotation_euler = tuple(math.radians(v) for v in rot)

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


def person(name='Person', loc=(0, 0, 0), rot_z=0.0, male=1.0, age=0.45, muscle=0.6, weight=0.55, height=0.55,
           race=(0.2, 0.7, 0.1), skin=('young_caucasian_male', 'middleage_caucasian_male', 'caucasian_male', 'male'),
           hair=('short02', 'short04', 'short'), clothes=(('tshirt', 'shirt'), ('jeans', 'pants', 'trouser'), ('shoes', 'boots', 'sneaker')),
           extra=(), eyebrows=('eyebrow001',), subdiv=1):
    """Make a rigged realistic human (MPFB 'default' rig). Returns the armature object (or None if MPFB is missing).
    clothes/extra: tuples of keyword alternatives, e.g. ('cap', 'hat'). race = (african, caucasian, asian)."""
    mp = _mpfb()
    if not mp:
        print('MPFB not available: person() skipped'); return None
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

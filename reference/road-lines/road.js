// Road world for "If you paint a line on a road...": one highway scene that switches between day / night / rain /
// snow, plus vehicles (car, line-striping truck, snowplow) and a macro scene (glass beads, recessed reflector).
import * as THREE from 'three';
import { rbox, ellipsoid, capsule, smin, ssub, sphere, mesh, rgb, noise3 } from './sdf.js';
import { lightRig } from './engine.js';
import { Human } from './human.js';

const std = (color, rough = 0.7, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, ...extra });
const sh = (m) => { m.castShadow = true; m.receiveShadow = true; return m; };
const box = (w, h, d, m, x = 0, y = 0, z = 0, parent) => { const b = sh(new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m)); b.position.set(x, y, z); if (parent) parent.add(b); return b; };
const cyl = (r1, r2, h, m, x, y, z, parent, seg = 24) => { const c = sh(new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, seg), m)); c.position.set(x, y, z); if (parent) parent.add(c); return c; };
const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
function tex(w, h, draw, rep = [1, 1]) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); t.anisotropy = 8; return t; }

const asphaltTex = (rep) => tex(512, 512, (g, w, h) => { g.fillStyle = '#4A4B4F'; g.fillRect(0, 0, w, h); for (let i = 0; i < 9000; i++) { const l = 50 + rnd(i) * 60; g.fillStyle = `rgba(${l},${l},${l + 4},0.55)`; g.fillRect(rnd(i * 3) * w, rnd(i * 7) * h, 1 + rnd(i * 5) * 2.5, 1 + rnd(i * 11) * 2.5); } g.fillStyle = 'rgba(30,30,32,0.25)'; for (let i = 0; i < 30; i++) { g.beginPath(); g.ellipse(rnd(i * 13) * w, rnd(i * 17) * h, 30 + rnd(i) * 60, 10 + rnd(i * 2) * 25, rnd(i * 19) * 3, 0, 7); g.fill(); } }, rep);
const grassTex = (rep) => tex(512, 512, (g, w, h) => { g.fillStyle = '#6E9A45'; g.fillRect(0, 0, w, h); for (let i = 0; i < 7000; i++) { const k = rnd(i); g.fillStyle = k > 0.5 ? 'rgba(95,140,55,0.7)' : 'rgba(130,165,75,0.6)'; g.fillRect(rnd(i * 3) * w, rnd(i * 7) * h, 2, 4 + rnd(i) * 5); } }, rep);
/** paint texture: fresh = solid white; worn = white with tire-worn gaps showing asphalt */
const paintTex = (worn) => tex(64, 512, (g, w, h) => { g.fillStyle = '#F4F4F0'; g.fillRect(0, 0, w, h); if (!worn) return; for (let i = 0; i < 260; i++) { const l = 60 + rnd(i) * 40; g.fillStyle = `rgba(${l},${l},${l},${0.55 + rnd(i * 3) * 0.45})`; g.beginPath(); g.ellipse(rnd(i * 5) * w, rnd(i * 7) * h, 3 + rnd(i * 9) * 14, 4 + rnd(i * 11) * 30, 0, 0, 7); g.fill(); } });

/** a little sedan, facing -z (drives toward -z), wheels on y = 0 */
export function car(color = '#B83A3A') {
  const g = new THREE.Group();
  const paint = new THREE.MeshPhysicalMaterial({ color, roughness: 0.35, metalness: 0.4, clearcoat: 1, clearcoatRoughness: 0.15 });
  const body = sh(new THREE.Mesh(mesh((p) => smin(rbox(p, [0, 0.42, 0], [0.86, 0.22, 2.1], 0.14), rbox(p, [0, 0.78, 0.15], [0.74, 0.22, 1.05], 0.18), 0.12), [[-1, 0.1, -2.3], [1, 1.1, 2.3]], 0.035), paint)); g.add(body);
  const glass = std('#1C2633', 0.1, { metalness: 0.6 }); box(1.42, 0.3, 0.06, glass, 0, 0.8, -0.86, g).rotation.x = -0.55; box(1.42, 0.3, 0.06, glass, 0, 0.82, 1.18, g).rotation.x = 0.5;
  [-1, 1].forEach((s) => box(0.04, 0.3, 1.6, glass, s * 0.75, 0.82, 0.15, g));
  const tire = std('#161616', 0.9), rim = std('#BFC3C7', 0.3, { metalness: 0.8 });
  g.wheels = [];
  for (const [x, z] of [[-0.8, -1.35], [0.8, -1.35], [-0.8, 1.35], [0.8, 1.35]]) { const w = new THREE.Group(); w.position.set(x, 0.34, z); const t = cyl(0.34, 0.34, 0.24, tire, 0, 0, 0, w, 28); t.rotation.z = Math.PI / 2; const r = cyl(0.2, 0.2, 0.25, rim, 0, 0, 0, w, 16); r.rotation.z = Math.PI / 2; g.add(w); g.wheels.push(w); }
  const lampM = new THREE.MeshStandardMaterial({ color: '#FFFFFF', emissive: '#FFF6DA', emissiveIntensity: 0 });
  [-1, 1].forEach((s) => box(0.34, 0.1, 0.05, lampM, s * 0.58, 0.5, -2.1, g));
  const tailM = new THREE.MeshStandardMaterial({ color: '#7A1010', emissive: '#FF2020', emissiveIntensity: 0 });
  [-1, 1].forEach((s) => box(0.3, 0.09, 0.05, tailM, s * 0.6, 0.55, 2.1, g));
  g.lights = [];
  [-1, 1].forEach((s) => { const L = new THREE.SpotLight('#FFF2D8', 0, 60, 0.42, 0.5, 1.2); L.position.set(s * 0.58, 0.55, -2.15); L.target.position.set(s * 0.4, 0, -14); g.add(L, L.target); g.lights.push(L); });
  g.headlights = (on) => { lampM.emissiveIntensity = on ? 6 : 0; tailM.emissiveIntensity = on ? 2 : 0; g.lights.forEach((l) => (l.intensity = on ? 180 : 0)); };
  g.roll = (dist) => g.wheels.forEach((w) => (w.rotation.x = -dist / 0.34));
  return g;
}

/** line-striping truck facing -z: white cab, flatbed with a big orange melting kettle; g.shoe = where the line comes out */
export function stripeTruck() {
  const g = new THREE.Group();
  const white = std('#F2F2EE', 0.45), orange = std('#E8732E', 0.5), steel = std('#8E959C', 0.35, { metalness: 0.7 }), dark = std('#2A2D31', 0.6);
  { const cab = sh(new THREE.Mesh(mesh((p) => rbox(p, [0, 1.25, 0], [1.05, 0.75, 0.85], 0.16), [[-1.2, 0.4, -1], [1.2, 2.1, 1]], 0.04), white)); cab.position.set(0, 0, -2.6); g.add(cab); }
  box(2.0, 0.55, 0.06, std('#1C2633', 0.1, { metalness: 0.6 }), 0, 1.55, -3.47, g);
  box(2.1, 0.3, 5.4, dark, 0, 0.75, 0.6, g);                                        // chassis
  const kettle = cyl(0.75, 0.75, 1.6, orange, 0, 1.75, 0.2, g, 32); kettle.rotation.x = Math.PI / 2;
  cyl(0.18, 0.18, 0.6, steel, 0.3, 2.6, 0.5, g, 12); cyl(0.12, 0.12, 0.5, steel, -0.35, 2.55, -0.2, g, 12);
  box(1.6, 0.9, 1.4, std('#D8D8D2', 0.5), 0, 1.4, 2.4, g);                              // bead hopper box
  box(0.18, 0.55, 0.5, steel, 1.12, 0.5, 1.2, g);                                     // applicator shoe arm
  g.shoe = new THREE.Vector3(1.12, 0.02, 1.35);
  const tire = std('#161616', 0.9);
  for (const [x, z] of [[-0.95, -2.5], [0.95, -2.5], [-0.95, 1.9], [0.95, 1.9], [-0.95, 2.9], [0.95, 2.9]]) { const t = cyl(0.45, 0.45, 0.35, tire, x, 0.45, z, g, 24); t.rotation.z = Math.PI / 2; }
  const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.1, 12, 8), new THREE.MeshStandardMaterial({ color: '#FFB020', emissive: '#FF9A10', emissiveIntensity: 4 })); beacon.position.set(0, 2.05, -2.6); g.add(beacon);
  return g;
}

/** snowplow truck facing -z with an angled orange blade in front */
export function snowplow() {
  const g = new THREE.Group();
  const orange = std('#E8732E', 0.5), dark = std('#2A2D31', 0.6), yellow = std('#F2B422', 0.45, { metalness: 0.3 });
  { const cab = sh(new THREE.Mesh(mesh((p) => rbox(p, [0, 1.35, 0], [1.1, 0.8, 0.9], 0.16), [[-1.25, 0.45, -1.05], [1.25, 2.3, 1.05]], 0.04), orange)); cab.position.set(0, 0, -1.6); g.add(cab); }
  box(2.0, 0.55, 0.06, std('#1C2633', 0.1, { metalness: 0.6 }), 0, 1.7, -2.52, g);
  box(2.2, 1.3, 3.6, orange, 0, 1.45, 1.6, g); box(2.2, 0.3, 5.6, dark, 0, 0.7, 0.4, g);
  const blade = box(3.4, 0.9, 0.12, yellow, 0, 0.5, -3.3, g); blade.rotation.y = 0.32; blade.rotation.x = -0.15; g.blade = blade;
  const tire = std('#161616', 0.9);
  for (const [x, z] of [[-1, -1.6], [1, -1.6], [-1, 2.2], [1, 2.2]]) { const t = cyl(0.5, 0.5, 0.4, tire, x, 0.5, z, g, 24); t.rotation.z = Math.PI / 2; }
  const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 8), new THREE.MeshStandardMaterial({ color: '#FFB020', emissive: '#FF9A10', emissiveIntensity: 5 })); beacon.position.set(0, 2.25, -1.6); g.add(beacon);
  return g;
}

/** the highway: 2 lanes each way-ish; dashed lane line at x = 0, solid edge lines at x = ±3.55. Road runs along z. */
export function highway(E) {
  const scene = new THREE.Scene(); scene.environment = E.envMap; scene.environmentIntensity = 0.35;
  const sky = new THREE.Color('#9CCBF0'); scene.background = sky.clone(); scene.fog = new THREE.Fog(sky.clone(), 30, 140);
  const LEN = 260, Z0 = 40;
  const asphalt = std('#FFFFFF', 0.85, { map: asphaltTex([3, 90]) });
  const road = new THREE.Mesh(new THREE.PlaneGeometry(8.4, LEN), asphalt); road.rotation.x = -Math.PI / 2; road.position.set(0, 0, Z0 - LEN / 2); road.receiveShadow = true; scene.add(road);
  const grassM = std('#FFFFFF', 0.95, { map: grassTex([30, 120]) });
  const grass = new THREE.Mesh(new THREE.PlaneGeometry(240, LEN), grassM); grass.rotation.x = -Math.PI / 2; grass.position.set(0, -0.02, Z0 - LEN / 2); grass.receiveShadow = true; scene.add(grass);
  // trees + hills for depth
  const treeM = std('#4E7A35', 0.9), trunkM = std('#6B4A30', 0.9);
  for (let i = 0; i < 90; i++) { const s = i % 2 ? 1 : -1, x = s * (9 + rnd(i) * 40), z = Z0 - rnd(i * 3) * LEN, r = 1.4 + rnd(i * 5) * 2.2; const t = new THREE.Group(); cyl(0.18, 0.25, 1.6, trunkM, 0, 0.8, 0, t, 8); const c = sh(new THREE.Mesh(new THREE.IcosahedronGeometry(r, 1), treeM)); c.position.y = 1.6 + r * 0.8; c.scale.y = 1.3; t.add(c); t.position.set(x, 0, z); scene.add(t); }
  for (let i = 0; i < 8; i++) { const h = new THREE.Mesh(new THREE.SphereGeometry(40 + rnd(i) * 30, 24, 12), std('#7FA05A', 1)); h.scale.y = 0.25; h.position.set((i - 4) * 50, -4, Z0 - LEN - 20 - rnd(i) * 30); scene.add(h); }
  // markings
  const lineM = new THREE.MeshStandardMaterial({ color: '#FFFFFF', roughness: 0.6, map: paintTex(false), emissive: '#FFFFFF', emissiveIntensity: 0 });
  const wornMap = paintTex(true), freshMap = lineM.map;
  const dashes = [];
  for (let z = Z0 - 2; z > Z0 - LEN; z -= 12) { const d = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.012, 3.05), lineM); d.position.set(0, 0.006, z); d.receiveShadow = true; scene.add(d); dashes.push(d); }
  [-1, 1].forEach((s) => { const e = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.012, LEN), lineM); e.position.set(s * 3.55, 0.006, Z0 - LEN / 2); e.receiveShadow = true; scene.add(e); });
  // raised reflectors (in the dash gaps) — white body, amber/white glowing faces
  const rpmBody = std('#EDEDE6', 0.4), rpmGlow = new THREE.MeshStandardMaterial({ color: '#FFE9B0', emissive: '#FFD27A', emissiveIntensity: 0 });
  const reflectors = [];
  for (let z = Z0 - 8; z > Z0 - LEN; z -= 12) { const r = new THREE.Group(); box(0.12, 0.022, 0.12, rpmBody, 0, 0.012, 0, r); const f = box(0.1, 0.016, 0.012, rpmGlow, 0, 0.014, 0.062, r); f.rotation.x = 0.5; r.position.set(0, 0, z); r.visible = false; scene.add(r); reflectors.push(r); }
  // water film over the road (rain)
  const waterM = new THREE.MeshPhysicalMaterial({ color: '#6F8796', roughness: 0.04, metalness: 0.2, transparent: true, opacity: 0, clearcoat: 1 });
  const water = new THREE.Mesh(new THREE.PlaneGeometry(8.4, LEN), waterM); water.rotation.x = -Math.PI / 2; water.position.set(0, 0.016, Z0 - LEN / 2); scene.add(water);
  // snow on the road and verges
  const snowM = std('#F4F7FA', 0.9, { transparent: true, opacity: 0 });
  const snowRoad = new THREE.Mesh(new THREE.PlaneGeometry(260, LEN), snowM); snowRoad.rotation.x = -Math.PI / 2; snowRoad.position.set(0, 0.03, Z0 - LEN / 2); scene.add(snowRoad);
  // rain streaks + snowflakes (instanced, placed around a centre each frame)
  const N = 900, streak = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.006, 0.006, 0.55, 3), new THREE.MeshBasicMaterial({ color: '#C9D6E2', transparent: true, opacity: 0.55 }), N); streak.visible = false; scene.add(streak);
  const flakes = new THREE.InstancedMesh(new THREE.SphereGeometry(0.03, 5, 4), new THREE.MeshBasicMaterial({ color: '#FFFFFF' }), N); flakes.visible = false; scene.add(flakes);
  const m4 = new THREE.Matrix4();
  const precip = (t, c, snow) => { const M = snow ? flakes : streak; M.visible = true; (snow ? streak : flakes).visible = false;
    for (let i = 0; i < N; i++) { const x = c.x + (rnd(i) - 0.5) * 12, z = c.z - rnd(i * 3) * 18 + 2, sp = snow ? 1.2 : 14, y = 6 - ((t * sp + rnd(i * 7) * 6) % 6) + (snow ? 0 : 0.2); m4.makeTranslation(x + (snow ? Math.sin(t + i) * 0.3 : 0), y, z); M.setMatrixAt(i, m4); } M.instanceMatrix.needsUpdate = true; };
  const L = lightRig(scene, { key: '#FFE6C4', keyI: 3.4, keyPos: [8, 14, 10], target: [0, 0, -4], rimCol: '#CFE0FF', rimI: 1.0, sky: '#EAF4FF', ground: '#7C8A5A', hemiI: 1.0, shadowBox: 14 });
  L.key.shadow.camera.far = 60; L.key.shadow.camera.updateProjectionMatrix();
  const hemi = L.group.children.find((c) => c.isHemisphereLight);
  const MODES = {
    day: { sky: '#9CCBF0', fog: [30, 140], key: 3.4, hemi: 1.0, rim: 1.0, env: 0.35 },
    dusk: { sky: '#F2B48A', fog: [25, 120], key: 2.2, hemi: 0.7, rim: 0.8, env: 0.3, keyCol: '#FFB070' },
    night: { sky: '#0B1628', fog: [10, 70], key: 0.12, hemi: 0.07, rim: 0.15, env: 0.04, keyCol: '#9DB8FF' },
    snow: { sky: '#BFCAD4', fog: [18, 95], key: 1.6, hemi: 1.1, rim: 0.6, env: 0.4, keyCol: '#E8F0FF' },
  };
  return {
    scene, lineM, dashes, reflectors, water, waterM, snowM, L,
    paint(worn) { lineM.map = worn ? wornMap : freshMap; lineM.needsUpdate = true; },
    /** mode: day | dusk | night | snow; wet 0..1 (rain film + darker shiny road); glow 0..1 line retro-glow */
    set({ mode = 'day', wet = 0, glow = 0, rpm = 0, rpmGlow: rg = 0, snow = 0, t = 0, center = new THREE.Vector3(), precip: pr = null } = {}) {
      const M = MODES[mode]; scene.background.set(M.sky); scene.fog.color.set(M.sky); scene.fog.near = M.fog[0]; scene.fog.far = M.fog[1];
      L.key.intensity = M.key; L.key.color.set(M.keyCol || '#FFE6C4'); hemi.intensity = M.hemi; L.rim.intensity = M.rim; scene.environmentIntensity = M.env;
      asphalt.roughness = 0.85 - wet * 0.7; asphalt.color.set(wet > 0 ? '#C8C8C8' : '#FFFFFF');
      waterM.opacity = wet * 0.6; water.visible = wet > 0;
      lineM.emissiveIntensity = glow * 1.6; lineM.color.set(mode === 'night' ? '#9A9A98' : '#FFFFFF');
      reflectors.forEach((r) => (r.visible = rpm > 0)); rpmGlow.emissiveIntensity = rg * 9;
      snowM.opacity = snow; snowRoad.visible = snow > 0;
      if (pr) precip(t, center, pr === 'snow'); else { streak.visible = false; flakes.visible = false; }
    },
  };
}

/** a road worker in hi-vis */
export const worker = (o = {}) => new Human({ skin: '#C98E6B', shirt: '#C8F04A', pants: '#33405A', shoes: '#5A4636', hair: '#2A1C12', ...o });

// ═════════════════ MACRO: a cut-away slab of road with a white stripe, glass beads, and a recessed reflector ═════════
export function macro(E) {
  const scene = new THREE.Scene(); scene.environment = E.envMap; scene.environmentIntensity = 0.12;
  scene.background = new THREE.Color('#10141C');
  const asphalt = std('#FFFFFF', 0.85, { map: asphaltTex([2, 2]) });
  const slab = sh(new THREE.Mesh(new THREE.BoxGeometry(3, 0.6, 3), asphalt)); slab.position.y = -0.3; scene.add(slab);
  // a thick white stripe on top (thermoplastic) — beads sit half-embedded in it
  const stripeM = std('#CFCFC9', 0.6);
  const stripe = sh(new THREE.Mesh(mesh((p) => rbox(p, [0, 0.03, 0], [0.55, 0.03, 1.4], 0.025) + noise3(p[0] * 9, p[1] * 9, p[2] * 9) * 0.004, [[-0.6, -0.01, -1.45], [0.6, 0.08, 1.45]], 0.012), stripeM)); scene.add(stripe);
  const beadM = new THREE.MeshPhysicalMaterial({ color: '#F2FAFF', roughness: 0.02, metalness: 0, transmission: 0.7, thickness: 0.05, ior: 1.5, clearcoat: 1, envMapIntensity: 1.1, transparent: true });
  const beads = [];
  for (let i = 0; i < 70; i++) { const r = 0.045 + rnd(i) * 0.03; const b = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 16), beadM); b.position.set((rnd(i * 3) - 0.5) * 1.0, 0.055, (rnd(i * 7) - 0.5) * 2.6); b.userData.r = r; scene.add(b); beads.push(b); }
  const hero = new THREE.Mesh(new THREE.SphereGeometry(0.28, 48, 32), beadM); hero.position.set(0, 0.07, 0.2); scene.add(hero);
  // light ray in and back out (glowing tubes)
  const rayM = new THREE.MeshBasicMaterial({ color: '#FFE7A8', transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
  const ray = (a, b) => { const d = b.clone().sub(a), m = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, d.length(), 8), rayM); m.position.copy(a).addScaledVector(d, 0.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize()); scene.add(m); return m; };
  const src = new THREE.Vector3(-1.6, 1.4, 1.6), hit = new THREE.Vector3(0, 0.12, 0.2), back = new THREE.Vector3(-1.55, 1.48, 1.52);
  const rayIn = ray(src, hit), rayOut = ray(hit.clone().add(new THREE.Vector3(0.03, 0.04, 0)), back);
  // recessed reflector: a pocket cut in a second slab, reflector inside
  const pocket = new THREE.Group(); pocket.position.set(6, 0, 0); scene.add(pocket);
  const cut = sh(new THREE.Mesh(mesh((p) => ssub(rbox(p, [0, -0.3, 0], [1.5, 0.3, 1.5], 0.01), rbox(p, [0, 0, 0], [0.32, 0.07, 0.22], 0.03), 0.02), [[-1.55, -0.62, -1.55], [1.55, 0.02, 1.55]], 0.02), asphalt)); pocket.add(cut);
  const rpm = new THREE.Group(); box(0.42, 0.06, 0.24, std('#EDEDE6', 0.4), 0, -0.035, 0, rpm); const face = box(0.36, 0.045, 0.02, new THREE.MeshStandardMaterial({ color: '#FFE9B0', emissive: '#FFC860', emissiveIntensity: 2.5 }), 0, -0.03, 0.125, rpm); face.rotation.x = 0.45; pocket.add(rpm);
  const snowM = std('#F6F9FC', 0.9); const snowPile = sh(new THREE.Mesh(new THREE.BoxGeometry(3, 0.06, 1.2), snowM)); snowPile.position.set(0, 0.03, -0.9); pocket.add(snowPile);
  const blade = box(2.6, 0.5, 0.08, std('#F2B422', 0.45, { metalness: 0.3 }), 0, 0.3, 0, pocket); blade.rotation.y = 0.25;
  const lightA = new THREE.SpotLight('#FFF0D2', 25, 12, 0.35, 0.6, 1.5); lightA.position.copy(src); lightA.target.position.copy(hit); scene.add(lightA, lightA.target);
  const L = lightRig(scene, { key: '#DDE8FF', keyI: 1.4, keyPos: [3, 5, 4], target: [0, 0, 0], rimCol: '#9DB8FF', rimI: 0.8, sky: '#AFC4E8', ground: '#202430', hemiI: 0.2, shadowBox: 4 });
  const L2 = lightRig(scene, { key: '#DDE8FF', keyI: 1.4, keyPos: [9, 5, 4], target: [6, 0, 0], rimI: 0, hemiI: 0, shadowBox: 3 });
  return { scene, beads, hero, rayM, rayIn, rayOut, pocket, rpm, blade, snowPile, stripe, lightA, L, beadM };
}

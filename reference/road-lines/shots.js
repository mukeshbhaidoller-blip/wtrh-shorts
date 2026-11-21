// IF YOU PAINT A LINE ON A ROAD... : the shot list (Deep Dive 3D engine, "If you..." problem → "But" → "So" chain).
import * as THREE from 'three';
import { ctx, W, H, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { L, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import { pill, label } from './core/look2d.js';
import * as RD from './core/road.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const lerpV = (a, b, k) => a.clone().lerp(b, k);
function screen(p, cam) { const v = p.clone().project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; }

export function buildShots(E) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.08);
  const cam = camera(40);
  const DLOOK = { aperture: 0.0012, maxblur: 0.008, bloom: 0.2, bloomThreshold: 0.9 };
  const NLOOK = { aperture: 0.0008, maxblur: 0.006, bloom: 0.55, bloomThreshold: 0.7, exposure: 1.1, vignette: 0.45 };
  const MLOOK = { aperture: 0.0015, maxblur: 0.008, bloom: 0.35, bloomThreshold: 0.85, vignette: 0.45 };
  const shoot = (scene, from, to, at, at2, k, look, fov = 40, focus) => {
    if (cam.fov !== fov) { cam.fov = fov; cam.updateProjectionMatrix(); }
    cam.position.copy(lerpV(from, to, k)); const tgt = at2 ? lerpV(at, at2, k) : at; cam.lookAt(tgt);
    E.render(scene, cam, { ...look, focus: focus ?? cam.position.distanceTo(tgt) });
  };

  // ── the world ──
  const R = RD.highway(E), sc = R.scene;
  const carA = RD.car('#B83A3A'), carB = RD.car('#2F5FA8'); sc.add(carA, carB);
  const truck = RD.stripeTruck(); sc.add(truck);
  const plow = RD.snowplow(); sc.add(plow);
  const crew = RD.worker(); sc.add(crew.group);
  const M = RD.macro(E);
  // hot fresh stripe that the truck lays down (S03-S06)
  const hotM = new THREE.MeshStandardMaterial({ color: '#FFFFFF', roughness: 0.5, emissive: '#FFB070', emissiveIntensity: 0 });
  const hot = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.016, 1), hotM); hot.receiveShadow = true; sc.add(hot);
  // falling glass beads (S06)
  const NB = 160, beadsI = new THREE.InstancedMesh(new THREE.SphereGeometry(0.012, 8, 6), new THREE.MeshStandardMaterial({ color: '#F4FBFF', roughness: 0.05, metalness: 0.2, emissive: '#FFFFFF', emissiveIntensity: 0.1 }), NB); sc.add(beadsI);
  const m4 = new THREE.Matrix4(), rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  // steam puffs over the kettle (S03)
  const steamM = new THREE.MeshStandardMaterial({ color: '#FFFFFF', transparent: true, opacity: 0.35, roughness: 1, depthWrite: false });
  const steam = Array.from({ length: 10 }, () => { const s = new THREE.Mesh(new THREE.SphereGeometry(0.3, 12, 8), steamM); sc.add(s); return s; });

  const reset = () => {
    R.paint(false); R.dashes.forEach((d) => (d.visible = true)); hot.visible = false; beadsI.visible = false; steam.forEach((s) => (s.visible = false));
    [carA, carB].forEach((c) => { c.visible = false; c.headlights(false); c.rotation.y = 0; }); truck.visible = false; plow.visible = false; crew.group.visible = false; crew.pose({}); crew.hips.position.y = 0.93;
    R.reflectors.forEach((r) => { r.position.y = 0; r.position.x = 0; r.rotation.set(0, 0, 0); });
  };
  const driveCar = (c, x, z, dist) => { c.visible = true; c.position.set(x, 0, z); c.roll(dist); };

  // ═══ 1 · "If you paint a white line on a road, you get a lane." — drone over a sunny highway
  { const st = cut(0);
    add({ id: 'S01', at: st, note: 'drone glides down over a sunny highway; fresh white lines; a red car drives in its lane', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'day' }); const cz = 6 - lt * 14; driveCar(carA, 1.8, cz, lt * 14);
      shoot(sc, V3(7, 11, 16), V3(3.2, 4.2, cz + 14), V3(0.6, 0, -18), V3(1.4, 0.5, cz - 6), eio(clamp(lt / d)), DLOOK, 50); blit();
    } });
    cue(st + 0.05, 'whoosh', { gain: 0.6 }); }

  // ═══ 2 · "But tires grind regular paint away in a few months." — tire rolls over the dash; the paint wears
  { const st = cut(1), wa = Wd('away', 1);
    add({ id: 'S02', at: st, note: 'low close-up: car tires roll over a dash; on "away" the paint turns patchy and worn', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'day' }); R.paint(t > wa - 0.1);
      const cz = 12 - lt * 7.5; driveCar(carA, 0.8, cz, lt * 7.5);
      shoot(sc, V3(-1.5, 0.5, 5.6), V3(-1.2, 0.42, 4.6), V3(0.15, 0.1, 2.2), null, eio(clamp(lt / d)), { ...DLOOK, aperture: 0.002 }, 40); blit();
      pill('A FEW MONTHS', 540, 330, eob(seg(t, wa, wa + 0.3)), '#FFFFFF', 'rgba(12,14,20,0.72)', 54);
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(st + 0.6, 'slide', { dur: 1.6, gain: 0.35 }); }

  // ═══ 3 · "So, crews melt plastic to about four hundred degrees," — the striping truck's orange melting kettle
  const TZ = -24;
  { const st = cut(2), wd = Wd('degrees', 2);
    add({ id: 'S03', at: st, note: 'striping truck with an orange kettle, steam rising; a crew member in hi-vis; 400°F pill on "degrees"', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'day' }); truck.visible = true; truck.position.set(-1.12, 0, TZ);
      crew.group.visible = true; crew.group.position.set(0.75, 0, TZ + 0.6); crew.group.rotation.y = -0.6; crew.pose({ head: [-8, -20, 0], shR: [40, 0, 10], elR: 60 });
      steam.forEach((s, i) => { const u = (lt * 0.5 + i / steam.length) % 1; s.visible = true; s.position.set(-1.12 + 0.3 + Math.sin(i * 2 + lt) * 0.15, 2.7 + u * 2.2, TZ + 0.5); s.scale.setScalar(0.4 + u * 1.4); });
      steamM.opacity = 0.3;
      shoot(sc, V3(3.2, 2.6, TZ + 6.5), V3(2.4, 2.4, TZ + 4.6), V3(-0.8, 1.7, TZ + 0.2), null, eio(clamp(lt / d)), DLOOK, 40); blit();
      pill('400°F', 540, 360, eob(seg(t, wd - 0.25, wd + 0.1)), '#FFB070', 'rgba(12,14,20,0.75)', 90);
    } });
    cue(st, 'whoosh'); cue(st + 0.2, 'bubbles', { dur: 3.0, gain: 0.45 }); cue(Wd('degrees', 2) - 0.2, 'pop', { gain: 0.6 }); }

  // ═══ 4 · "and lay it down hot, so it lasts for years." — the shoe lays a fresh stripe as the truck rolls
  { const st = cut(3), wy = Wd('years', 3);
    add({ id: 'S04', at: st, note: 'low shot behind the applicator shoe: the truck rolls forward laying a fresh hot white stripe; "3-6 YEARS" pill', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'day' }); R.dashes.forEach((dd) => (dd.visible = Math.abs(dd.position.z - (TZ - 6)) > 14));
      const tz = TZ - lt * 1.6; truck.visible = true; truck.position.set(-1.12, 0, tz);
      const z0 = TZ + 1.35, z1 = tz + 1.35; hot.visible = true; hot.position.set(0, 0.008, (z0 + z1) / 2 + 0.6); hot.scale.z = Math.max(0.05, z0 - z1 + 1.2); hotM.emissiveIntensity = 0.25;
      shoot(sc, V3(0.9, 0.55, TZ + 4.2), V3(0.6, 0.6, tz + 4.6), V3(0, 0.15, tz + 1.3), null, eio(clamp(lt / d)), { ...DLOOK, aperture: 0.002 }, 40); blit();
      pill('LASTS 3-6 YEARS', 540, 330, eob(seg(t, wy - 0.2, wy + 0.15)), '#FFFFFF', 'rgba(12,14,20,0.72)', 58);
    } });
    cue(st, 'sizzle', { dur: 2.6, gain: 0.4 }); cue(Wd('years', 3) - 0.15, 'ding', { gain: 0.5 }); }

  // ═══ 5 · "But at night, your headlights hit the line, and it looks gray." — night, headlights, the line stays dull
  { const st = cut(4);
    add({ id: 'S05', at: st, note: 'night: chase cam behind a car with headlights on; the painted dashes stay dull gray', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'night', glow: 0.02 }); const cz = 10 - lt * 12; driveCar(carA, 1.8, cz, lt * 12); carA.headlights(true);
      shoot(sc, V3(2.6, 1.7, cz + 6.2), V3(1.9, 1.45, cz + 5.2), V3(0.6, 0.2, cz - 12), null, eio(clamp(lt / d)), NLOOK, 46); blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(st + 0.1, 'slide', { dur: 2.8, gain: 0.25 }); }

  // ═══ 6 · "So, while it's still soft, they sprinkle tiny glass beads on top." — beads rain onto the hot stripe
  { const st = cut(5), ws = Wd('sprinkle', 5);
    add({ id: 'S06', at: st, note: 'close-up: tiny glass beads shower from the truck onto the soft white stripe and glint in the sun', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'day' }); R.dashes.forEach((dd) => (dd.visible = Math.abs(dd.position.z - (TZ - 6)) > 14));
      const tz = TZ - 2 - lt * 0.6; truck.visible = true; truck.position.set(-1.12, 0, tz); hot.visible = true; hot.position.set(0, 0.008, tz + 4); hot.scale.z = 6; hotM.emissiveIntensity = 0.15;
      const on = clamp((t - ws + 0.2) / 0.3); beadsI.visible = on > 0;
      for (let i = 0; i < NB; i++) { const u = (lt * 1.6 + rnd(i)) % 1, x = (rnd(i * 3) - 0.5) * 0.14, z = tz + 2.1 + rnd(i * 5) * 0.8 + u * 0.15, y = 0.7 * (1 - u) + 0.02; m4.makeTranslation(x, i / NB < on ? y : -1, z); beadsI.setMatrixAt(i, m4); } beadsI.instanceMatrix.needsUpdate = true;
      shoot(sc, V3(1.5, 0.75, tz + 4.6), V3(1.2, 0.6, tz + 4.1), V3(0, 0.15, tz + 2.4), null, eio(clamp(lt / d)), { ...DLOOK, aperture: 0.0012, bloom: 0.3, bloomThreshold: 0.85 }, 40); blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(Wd('sprinkle', 5) - 0.1, 'sparkle', { dur: 2.2, gain: 0.7 }); }

  // ═══ 7a · "Each bead catches your headlight and sends it…" — macro: one glass bead, a light ray goes in and back
  const wStraight = Wd('straight', 6);
  { const st = cut(6), wc = Wd('catches', 6), wsd = Wd('sends', 6);
    add({ id: 'S07', at: st, note: 'macro: a glass bead half-sunk in the white stripe; a headlight ray goes in on "catches" and comes back out on "sends"', draw(lt, d, t, blit) {
      M.rayIn.visible = true; M.rayOut.visible = t > wsd - 0.1; M.rayM.opacity = 0.85 * clamp((t - wc + 0.2) / 0.3);
      M.pocket.visible = false; M.lightA.intensity = 25;
      const a = lerp(0.9, 0.5, eio(clamp(lt / d)));
      shoot(M.scene, V3(Math.sin(a) * 3.0, 1.3, 0.2 + Math.cos(a) * 3.0), V3(Math.sin(a) * 2.5, 1.05, 0.2 + Math.cos(a) * 2.5), V3(0, 0.12, 0.2), null, 0, MLOOK, 45);
      blit(); const [lx, ly] = screen(V3(0, 0.3, 0.2), cam); label('GLASS BEAD', 760, 420, lx, ly, eob(seg(lt, 0.3, 0.6)));
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(Wd('catches', 6), 'sparkle', { dur: 1.0, gain: 0.6 }); }
  // ═══ 7b · "…straight back to you." — driver's view at night: now the lines glow
  { const st = wStraight - 0.1;
    add({ id: 'S07b', at: st, note: "driver's view at night: the beaded lines now glow bright white in the headlights", draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'night', glow: 1 }); const cz = 0 - lt * 14; driveCar(carA, 1.8, cz, lt * 14); carA.headlights(true); carA.visible = false;
      shoot(sc, V3(1.6, 1.25, cz - 1.4), V3(1.6, 1.25, cz - 2.2), V3(0.9, 0.0, cz - 22), null, 0, NLOOK, 46); blit();
    } });
    cue(st, 'ding', { gain: 0.5 }); }

  // ═══ 8 · "But in the rain, a thin film of water covers the beads," — night rain, wet road, glow fading
  { const st = cut(7), wf = Wd('film', 7);
    add({ id: 'S08', at: st, note: 'night rain: streaks, shiny wet road, the glowing dashes fade as the water film spreads', draw(lt, d, t, blit) {
      reset(); const fade = clamp((t - wf) / 1.6); R.set({ mode: 'night', wet: 0.4 + fade * 0.6, glow: 1 - fade * 0.85, precip: 'rain', t, center: V3(1.5, 0, 2 - lt * 6) });
      const cz = 4 - lt * 6; driveCar(carA, 1.8, cz, lt * 6); carA.headlights(true);
      shoot(sc, V3(3.0, 1.6, cz + 6.5), V3(2.4, 1.4, cz + 5.5), V3(0.4, 0.1, cz - 10), null, eio(clamp(lt / d)), NLOOK, 46); blit();
    } });
    cue(st, 'slide', { dur: 3.4, gain: 0.45 }); cue(st + 0.2, 'bubbles', { dur: 3.2, gain: 0.2 }); }

  // ═══ 9 · "and the line disappears." — low rain close-up: the dash vanishes under the water
  { const st = cut(8), wd = Wd('disappears', 8);
    add({ id: 'S09', at: st, note: 'low close-up in the rain: the dash under the water film goes dark and disappears', draw(lt, d, t, blit) {
      reset(); const k = clamp((t - wd + 0.3) / 0.6); R.set({ mode: 'night', wet: 1, glow: 0.15 * (1 - k), precip: 'rain', t, center: V3(0, 0, 4) });
      R.lineM.color.set(new THREE.Color('#9A9A98').lerp(new THREE.Color('#3A3B3F'), k));
      driveCar(carA, 1.8, 16, 0); carA.headlights(true);
      shoot(sc, V3(-0.6, 0.45, 5.3), V3(-0.4, 0.4, 4.7), V3(0, 0.02, 2), null, eio(clamp(lt / d)), NLOOK, 40); blit();
    } });
    cue(Wd('disappears', 8), 'plop', { gain: 0.5 }); }

  // ═══ 10 · "So, California started gluing raised reflectors between the lanes," — a crew glues markers one by one
  { const st = cut(9);
    add({ id: 'S10', at: st, note: 'dusk: a crew member kneels and glues raised reflectors along the lane line; they pop into place one by one', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'dusk', rpm: 1 }); const n = Math.floor(lt * 2.2);
      const near = R.reflectors.filter((r) => r.position.z < 34 && r.position.z > -40).sort((a, b) => b.position.z - a.position.z);
      R.reflectors.forEach((r) => (r.visible = false)); near.forEach((r, i) => (r.visible = i <= n));
      const cur = near[Math.min(n, near.length - 1)], wz = cur.position.z;
      crew.group.visible = true; crew.group.position.set(0.55, 0, wz + 0.15); crew.group.rotation.y = -1.2; crew.hips.position.y = 0.5;
      crew.pose({ spine: [35, 0, 0], head: [20, 0, 0], hipL: [95, 0, 4], knL: 125, hipR: [60, 0, 4], knR: 120, shR: [70, 0, 10], elR: 30, shL: [50, 0, 10], elL: 40 });
      shoot(sc, V3(2.6, 1.4, wz + 3.6), V3(2.2, 1.2, wz + 2.8), V3(0.2, 0.3, wz), null, eio(clamp((lt % (1 / 2.2)) * 2.2)) * 0.3, DLOOK, 40); blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); for (let i = 1; i < 9; i++) cue(st + i / 2.2, 'tock', { gain: 0.5 }); }

  // ═══ 11 · "and they stick up above the water." — night rain: the reflectors glow above the flooded line
  { const st = cut(10);
    add({ id: 'S11', at: st, note: 'night rain, low angle: the painted line is lost, but the raised reflectors shine above the water', draw(lt, d, t, blit) {
      reset(); R.set({ mode: 'night', wet: 1, glow: 0.05, rpm: 1, rpmGlow: 1, precip: 'rain', t, center: V3(0.5, 0, 0) });
      const cz = 14 - lt * 4; driveCar(carA, 1.8, cz, lt * 4); carA.headlights(true); carA.visible = false;
      shoot(sc, V3(0.45, 0.32, cz - 2), V3(0.4, 0.3, cz - 3), V3(0.0, 0.0, cz - 34), null, eio(clamp(lt / d)), { ...NLOOK, aperture: 0.0004 }, 40); blit();
    } });
    cue(st, 'sparkle', { dur: 1.4, gain: 0.5 }); }

  // ═══ 12 · "But up north, snowplows scrape them right off the road." — a plow barrels toward camera, markers fly
  { const st = cut(11);
    add({ id: 'S12', at: st, note: 'snowy road: an orange snowplow drives at the camera; its blade knocks the reflectors flying', draw(lt, d, t, blit) {
      reset(); const pz = 30 - lt * 9; R.set({ mode: 'snow', snow: 0.55, rpm: 1, precip: 'snow', t, center: V3(0, 0, pz - 6) });
      plow.visible = true; plow.position.set(0.6, 0, pz);
      R.reflectors.forEach((r) => { const bz = pz - 3.3; if (r.position.z > bz && r.position.z < bz + 30) { const u = clamp((r.position.z - bz) / 2.5); r.position.y = u * 1.2 - u * u * 0.6; r.rotation.set(u * 6, u * 3, u * 4); r.position.x = -u * 1.5; r.visible = u < 1; } });
      shoot(sc, V3(-1.6, 1.3, pz - 14), V3(-1.2, 1.1, pz - 11.5), V3(0.4, 0.6, pz - 2), null, eio(clamp(lt / d)), { ...DLOOK, aperture: 0.0015 }, 42); blit();
    } });
    cue(st, 'slide', { dur: 3.2, gain: 0.35 }); cue(Wd('scrape', 11), 'zip', { gain: 0.6 }); cue(Wd('scrape', 11) + 0.4, 'pop', { gain: 0.5 }); }

  // ═══ 13 · "So, they cut a little pocket into the road and tuck the reflector inside." — the recessed marker
  { const st = cut(12), wp = Wd('pocket', 12), wt = Wd('tuck', 12);
    add({ id: 'S13', at: st, note: 'macro cut-away: a pocket in the asphalt; the reflector drops in on "tuck"; a plow blade sweeps safely over it', draw(lt, d, t, blit) {
      M.pocket.visible = true; M.rayIn.visible = false; M.rayOut.visible = false; M.lightA.intensity = 0;
      const drop = eo(clamp((t - wt + 0.1) / 0.5)); M.rpm.position.y = lerp(0.6, 0, drop);
      const sw = clamp((lt - (wt - st) - 0.6) / 1.6); M.blade.position.set(0, 0.22, lerp(-1.6, 1.6, sw)); M.blade.visible = sw > 0 && sw < 1;
      const a = lerp(0.7, 0.35, eio(clamp(lt / d)));
      shoot(M.scene, V3(6 + Math.sin(a) * 3.2, 1.7, Math.cos(a) * 3.2), V3(6 + Math.sin(a) * 2.6, 1.35, Math.cos(a) * 2.6), V3(6, 0, 0), null, 0, MLOOK, 45);
      blit(); const [lx, ly] = screen(V3(6, -0.05, 0), cam); label('POCKET', 300, 430, lx, ly, eob(seg(t, wp, wp + 0.3)) * (1 - seg(t, wt, wt + 0.3)));
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(Wd('tuck', 12), 'thud', { gain: 0.6 }); cue(Wd('tuck', 12) + 0.9, 'slide', { dur: 1.4, gain: 0.4 }); }

  // ═══ 14 · "You see, every bead is a tiny glass ball that bends light back where it came from." — back in the bead
  { const st = cut(13), wb = Wd('bends', 13);
    add({ id: 'S14', at: st, note: 'macro: slow orbit around the glass bead; the light ray enters and returns along the same path', draw(lt, d, t, blit) {
      M.pocket.visible = false; M.rayIn.visible = true; M.rayOut.visible = t > wb; M.rayM.opacity = 0.9; M.lightA.intensity = 25;
      const a = lerp(-0.2, 0.6, eio(clamp(lt / d)));
      shoot(M.scene, V3(Math.sin(a) * 2.2, 0.85, 0.2 + Math.cos(a) * 2.2), V3(Math.sin(a) * 1.8, 0.7, 0.2 + Math.cos(a) * 1.8), V3(0, 0.1, 0.2), null, 0, { ...MLOOK, aperture: 0.002 }, 45); blit();
    } });
    cue(st, 'whoosh', { gain: 0.4 }); cue(Wd('bends', 13), 'sparkle', { dur: 1.2, gain: 0.6 }); }

  // ═══ 15 · "That's why road lines glow at night, but look like plain paint all day." — aerial: night glow → day
  { const st = cut(14), wp = Wd('plain', 14);
    add({ id: 'S15', at: st, note: 'aerial highway at night: lines + reflectors glow in the headlights; on "plain" the same view turns to plain daylight', draw(lt, d, t, blit) {
      reset(); const day = t > wp - 0.1;
      R.set(day ? { mode: 'day', rpm: 1 } : { mode: 'night', glow: 0.55, rpm: 1, rpmGlow: 1 });
      const cz = 4 - lt * 12; driveCar(carA, 1.8, cz, lt * 12); driveCar(carB, -1.8, -30 + lt * 12, lt * 12); carB.rotation.y = Math.PI; carA.headlights(!day); carB.headlights(!day);
      shoot(sc, V3(5.5, 9, cz + 14), V3(4, 12, cz + 6), V3(0.2, 0, cz - 10), V3(0.2, 0, cz - 26), eio(clamp(lt / d)), day ? DLOOK : NLOOK, 46); blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(Wd('plain', 14) - 0.1, 'whoosh', { gain: 0.7 }); }

  return { shots: S, cues: CUES };
}

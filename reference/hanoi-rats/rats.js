// Kit additions for "The City That Paid People To Farm Rats" (Tall Tale look: flat 2D ink cut-outs in a 3D world).
//   new Rat({ size, tail, baby }) .at(x,y,z) .face(cam) .set({ tail, frame, flip, mood }) — a 2D cartoon rat cut-out
//   drawRat(g, x, y, s, o)  — the 2D rat drawing (also used by hand props)
//   RPROPS.coin / net / scissors / magnifier / ratByTail / tailOnly / coins  — props held in a Toon's hand
//   sewer(E) · toilet() · tailPile(n) · heart() · pen(w, d)  — sets and 3D props
import * as THREE from 'three';
import { INK } from './toon.js';
import { T, mat, canvasTex } from './world.js';

const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const box = (w, h, d, m, x = 0, y = 0, z = 0, parent) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); b.castShadow = b.receiveShadow = true; if (parent) parent.add(b); return b; };
const cyl = (r1, r2, h, m, x, y, z, parent, seg = 24) => { const c = new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, seg), m); c.position.set(x, y, z); c.castShadow = c.receiveShadow = true; if (parent) parent.add(c); return c; };

const FUR = '#9A93A8', FUR2 = '#C9C3D4', PINK = '#F2A7B4';

/** a cartoon rat facing right, feet on y, about 400*s px long. o = { tail, frame, mood: happy|shock|sly|neutral, rot } */
export function drawRat(g, x, y, s = 1, o = {}) {
  const { tail = true, frame = 0, mood = 'happy', rot = 0 } = o;
  g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, s); g.lineJoin = 'round'; g.lineCap = 'round';
  // tail (ink under-stroke, then pink)
  if (tail) {
    const tp = () => { g.beginPath(); g.moveTo(-120, -60); g.bezierCurveTo(-200, -40, -210, -150, -290, -120); };
    g.strokeStyle = INK; g.lineWidth = 22; tp(); g.stroke(); g.strokeStyle = PINK; g.lineWidth = 11; tp(); g.stroke();
  } else { g.fillStyle = PINK; g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.arc(-128, -62, 10, 0, 7); g.fill(); g.stroke(); }
  // feet
  const fx = frame ? [-60, 40] : [-90, 70];
  g.fillStyle = PINK; g.strokeStyle = INK; g.lineWidth = 7;
  fx.forEach((f) => { g.beginPath(); g.ellipse(f, -10, 26, 13, 0, 0, 7); g.fill(); g.stroke(); });
  // body + head + snout as one inked silhouette
  const shapes = [() => g.ellipse(-20, -80, 120, 70, -0.05, 0, 7), () => g.ellipse(105, -105, 66, 56, 0.15, 0, 7), () => g.ellipse(160, -88, 42, 30, 0.25, 0, 7)];
  g.strokeStyle = INK; g.lineWidth = 16; shapes.forEach((sh) => { g.beginPath(); sh(); g.stroke(); });
  g.fillStyle = FUR; shapes.forEach((sh) => { g.beginPath(); sh(); g.fill(); });
  g.fillStyle = FUR2; g.beginPath(); g.ellipse(-10, -50, 85, 30, -0.05, 0, 7); g.fill();
  // ear
  g.fillStyle = FUR; g.lineWidth = 8; g.beginPath(); g.arc(70, -165, 38, 0, 7); g.fill(); g.stroke();
  g.fillStyle = PINK; g.beginPath(); g.arc(72, -163, 22, 0, 7); g.fill();
  // nose + whiskers
  g.fillStyle = '#E36D86'; g.lineWidth = 6; g.beginPath(); g.arc(200, -96, 13, 0, 7); g.fill(); g.stroke();
  g.lineWidth = 4; [[-14, -6], [0, 0], [12, 7]].forEach(([dy, k]) => { g.beginPath(); g.moveTo(178, -86 + dy * 0.3); g.lineTo(240, -84 + dy + k); g.stroke(); });
  // eye + mouth by mood
  g.fillStyle = INK;
  if (mood === 'shock') { g.fillStyle = '#FFFFFF'; g.lineWidth = 5; g.beginPath(); g.arc(120, -122, 19, 0, 7); g.fill(); g.stroke(); g.fillStyle = INK; g.beginPath(); g.arc(124, -122, 8, 0, 7); g.fill(); g.beginPath(); g.ellipse(160, -70, 9, 12, 0, 0, 7); g.fill(); }
  else if (mood === 'sly') { g.lineWidth = 7; g.beginPath(); g.moveTo(104, -124); g.lineTo(140, -124); g.stroke(); g.beginPath(); g.arc(124, -119, 7, 0, Math.PI); g.fill(); g.beginPath(); g.moveTo(140, -72); g.quadraticCurveTo(158, -64, 174, -76); g.stroke(); }
  else {
    g.beginPath(); g.ellipse(122, -122, 11, 14, 0, 0, 7); g.fill(); g.fillStyle = '#FFFFFF'; g.beginPath(); g.arc(126, -128, 4.5, 0, 7); g.fill();
    if (mood === 'happy') { g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.moveTo(142, -74); g.quadraticCurveTo(160, -60, 178, -76); g.stroke(); }
    g.fillStyle = 'rgba(240,120,140,0.55)'; g.beginPath(); g.ellipse(110, -88, 16, 10, 0, 0, 7); g.fill();
  }
  // teeth
  g.fillStyle = '#FFFFFF'; g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.rect(176, -76, 12, 14); g.fill(); g.stroke();
  g.restore();
}

const RTEX = {};
function ratTex(key, o) {
  if (RTEX[key]) return RTEX[key];
  const c = document.createElement('canvas'); c.width = 640; c.height = 320; const g = c.getContext('2d');
  drawRat(g, 330, 300, 1, o);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; RTEX[key] = t; return t;
}

export class Rat {
  constructor({ size = 0.62, tail = true, mood = 'happy', castShadow = true } = {}) {
    const W = size, H = size / 2;
    const geo = new THREE.PlaneGeometry(W, H); geo.translate(0, H / 2 - H * (20 / 320), 0);
    this.mat = new THREE.MeshBasicMaterial({ transparent: true, alphaTest: 0.05, side: THREE.DoubleSide, toneMapped: false });
    this.mesh = new THREE.Mesh(geo, this.mat); this.mesh.castShadow = castShadow;
    this.depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, alphaTest: 0.5 }); this.mesh.customDepthMaterial = this.depth;
    this.pivot = new THREE.Group(); this.pivot.add(this.mesh); this.group = new THREE.Group(); this.group.add(this.pivot);
    this.st = {}; this.set({ tail, mood, frame: 0, flip: false });
  }
  set(st = {}) {
    const s = { ...this.st, ...st }; const key = `${s.tail ? 1 : 0}${s.frame ? 1 : 0}${s.mood}`;
    if (key !== this.key) { this.key = key; const t = ratTex(key, s); this.mat.map = t; this.depth.map = t; this.mat.needsUpdate = this.depth.needsUpdate = true; }
    this.mesh.scale.x = s.flip ? -1 : 1; this.st = s; return this;
  }
  /** run cycle: hop + swap feet */
  run(t, speed = 14, off = 0) { const p = Math.sin(t * speed + off); this.set({ frame: p > 0 ? 1 : 0 }); this.mesh.position.y = Math.abs(p) * 0.05; this.mesh.rotation.z = p * 0.05; return this; }
  still() { this.mesh.position.y = 0; this.mesh.rotation.z = 0; return this; }
  face(cam) { const p = new THREE.Vector3(); this.group.getWorldPosition(p); this.pivot.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z) - this.group.rotation.y; return this; }
  at(x, y, z) { this.group.position.set(x, y, z); return this; }
}

// ---------- hand props (Toon canvas space, hand at x,y) ----------
const coinAt = (g, x, y, r = 34) => { g.fillStyle = '#F2C230'; g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.stroke(); g.strokeStyle = '#C9962A'; g.lineWidth = 4; g.beginPath(); g.arc(x, y, r - 9, 0, 7); g.stroke(); g.fillStyle = '#8A5A1A'; g.font = `900 ${r * 0.9}px Inter`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('1¢', x, y + 2); };
export const RPROPS = {
  coin: (g, x, y) => coinAt(g, x, y - 46, 40),
  coins: (g, x, y) => { [[-30, -20], [20, -36], [-6, -70], [34, -84]].forEach(([dx, dy]) => coinAt(g, x + dx, y + dy, 30)); },
  net: (g, x, y) => { g.strokeStyle = '#8A5A36'; g.lineWidth = 12; g.lineCap = 'round'; g.beginPath(); g.moveTo(x, y + 40); g.lineTo(x + 40, y - 190); g.stroke(); g.strokeStyle = INK; g.lineWidth = 6; g.fillStyle = 'rgba(240,235,220,0.55)'; g.beginPath(); g.ellipse(x + 52, y - 250, 62, 70, 0.15, 0, 7); g.fill(); g.stroke(); g.lineWidth = 2.5; for (let i = -3; i <= 3; i++) { g.beginPath(); g.moveTo(x + 52 + i * 16, y - 316); g.lineTo(x + 52 + i * 16, y - 184); g.stroke(); g.beginPath(); g.moveTo(x - 6, y - 250 + i * 18); g.lineTo(x + 110, y - 250 + i * 18); g.stroke(); } },
  scissors: (g, x, y) => { g.save(); g.translate(x, y - 40); g.rotate(-0.5); g.strokeStyle = INK; g.lineWidth = 6; g.fillStyle = '#D8343F'; [-1, 1].forEach((s) => { g.beginPath(); g.ellipse(-28, s * 18, 20, 14, 0, 0, 7); g.fill(); g.stroke(); }); g.fillStyle = '#C9D2DA'; [-1, 1].forEach((s) => { g.beginPath(); g.moveTo(-10, s * 12); g.lineTo(70, -s * 10); g.lineTo(66, -s * 2); g.closePath(); g.fill(); g.stroke(); }); g.restore(); },
  magnifier: (g, x, y) => { g.strokeStyle = '#7A4A2A'; g.lineWidth = 14; g.lineCap = 'round'; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 26, y - 60); g.stroke(); g.fillStyle = 'rgba(190,230,245,0.75)'; g.strokeStyle = INK; g.lineWidth = 7; g.beginPath(); g.arc(x + 46, y - 112, 52, 0, 7); g.fill(); g.stroke(); g.strokeStyle = '#C9A13B'; g.lineWidth = 6; g.beginPath(); g.arc(x + 46, y - 112, 46, 0, 7); g.stroke(); g.fillStyle = 'rgba(255,255,255,0.85)'; g.beginPath(); g.ellipse(x + 28, y - 130, 9, 18, 0.6, 0, 7); g.fill(); },
  ratByTail: (g, x, y) => { g.strokeStyle = INK; g.lineWidth = 16; g.lineCap = 'round'; g.beginPath(); g.moveTo(x, y - 6); g.quadraticCurveTo(x + 14, y + 36, x, y + 70); g.stroke(); g.strokeStyle = PINK; g.lineWidth = 8; g.stroke(); drawRat(g, x - 25, y + 120, 0.42, { tail: false, mood: 'shock', rot: Math.PI / 2 }); },
  tailOnly: (g, x, y) => { g.strokeStyle = INK; g.lineWidth = 16; g.lineCap = 'round'; g.beginPath(); g.moveTo(x, y - 6); g.quadraticCurveTo(x + 22, y + 40, x + 2, y + 84); g.stroke(); g.strokeStyle = PINK; g.lineWidth = 8; g.stroke(); },
  cashFan: (g, x, y) => { for (let i = 0; i < 5; i++) { g.save(); g.translate(x, y - 20); g.rotate(-0.6 + i * 0.3); g.fillStyle = i % 2 ? '#7FBF7A' : '#8FD08A'; g.strokeStyle = INK; g.lineWidth = 5; g.beginPath(); g.roundRect(-18, -130, 36, 120, 4); g.fill(); g.stroke(); g.restore(); } },
};

// ---------- sets + 3D props ----------
/** a shiny new brick sewer running along -z: walkways at y 0 (x ±0.9..3), water channel in the middle. */
export function sewer(E, { len = 46 } = {}) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#120F14');
  scene.environment = E.envMap; scene.environmentIntensity = 0.5;
  const tube = new THREE.Mesh(new THREE.CylinderGeometry(3.3, 3.3, len, 40, 1, true), mat({ map: T.brick('#C27A55', [10, len / 2.2]), side: THREE.BackSide, roughness: 0.6 }));
  tube.rotation.x = Math.PI / 2; tube.position.set(0, 0.7, -len / 2 + 4); tube.receiveShadow = true; scene.add(tube);
  const stone = mat({ map: T.planks('#9C9488', [1, len / 3]), roughness: 0.7 }); stone.map.rotation = Math.PI / 2;
  [-1, 1].forEach((s) => { box(2.4, 0.4, len, stone, s * 2.1, -0.2, -len / 2 + 4, scene); box(0.12, 0.1, len, mat({ color: '#D8C9A8' }), s * 0.92, 0.02, -len / 2 + 4, scene); });
  const water = new THREE.Mesh(new THREE.PlaneGeometry(1.84, len), new THREE.MeshStandardMaterial({ color: '#2F7C78', roughness: 0.08, metalness: 0.35 })); water.rotation.x = -Math.PI / 2; water.position.set(0, -0.26, -len / 2 + 4); water.receiveShadow = true; scene.add(water);
  const bulbs = [];
  for (let z = 2; z > -len + 4; z -= 5.5) [-1, 1].forEach((s, i) => {
    const b = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 8), new THREE.MeshStandardMaterial({ color: '#FFF3C8', emissive: '#FFD27A', emissiveIntensity: 3 })); b.position.set(s * 2.95, 2.3, z - i * 2.7); scene.add(b); bulbs.push(b);
    cyl(0.05, 0.05, 0.5, mat({ color: '#C9A13B', metalness: 0.7, roughness: 0.3 }), s * 3.15, 2.3, z - i * 2.7, scene, 8).rotation.z = Math.PI / 2;
    const pl = new THREE.PointLight('#FFC98A', 7, 9, 1.5); pl.position.set(s * 2.6, 2.2, z - i * 2.7); scene.add(pl);
  });
  // brass pipe along the wall (the "shiny new" part)
  [-1, 1].forEach((s) => { const p = cyl(0.12, 0.12, len, mat({ color: '#D9A441', metalness: 0.85, roughness: 0.25 }), s * 3.0, 1.1, -len / 2 + 4, scene, 16); p.rotation.x = Math.PI / 2; });
  const key = new THREE.DirectionalLight('#FFE0B0', 1.6); key.position.set(1.5, 8, 2); key.target.position.set(0, 0, -3); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -6, right: 6, top: 8, bottom: -8, near: 0.5, far: 30 }); key.shadow.bias = -0.0006; key.shadow.camera.updateProjectionMatrix();
  scene.add(key, key.target); scene.add(new THREE.HemisphereLight('#FFE2C0', '#3A2A2A', 0.9));
  return { scene, sun: { key }, water };
}

/** a fancy porcelain toilet facing +z, bowl centre at (0, 0.42, 0.05). g.water = the water disc height */
export function toilet() {
  const g = new THREE.Group(), por = mat({ color: '#FBF8F2', roughness: 0.25, metalness: 0.05 }), gold = mat({ color: '#D9A441', metalness: 0.85, roughness: 0.25 });
  const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.27, 0.17, 0.4, 32, 1, true), por); bowl.position.set(0, 0.22, 0.05); bowl.castShadow = true; g.add(bowl);
  cyl(0.17, 0.2, 0.06, por, 0, 0.03, 0.05, g, 24);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.045, 12, 40), por); rim.rotation.x = Math.PI / 2; rim.position.set(0, 0.43, 0.05); rim.castShadow = true; g.add(rim);
  const water = new THREE.Mesh(new THREE.CircleGeometry(0.24, 32), new THREE.MeshStandardMaterial({ color: '#7FC4D6', roughness: 0.05, metalness: 0.2 })); water.rotation.x = -Math.PI / 2; water.position.set(0, 0.34, 0.05); g.add(water);
  const lid = box(0.56, 0.03, 0.08, por, 0, 0.75, -0.18, g); lid.rotation.x = -0.25;
  box(0.6, 0.55, 0.22, por, 0, 0.78, -0.3, g); box(0.64, 0.05, 0.26, por, 0, 1.07, -0.3, g);
  const h = cyl(0.025, 0.025, 0.14, gold, -0.22, 0.98, -0.17, g, 8); h.rotation.z = Math.PI / 2;
  cyl(0.04, 0.04, 0.03, gold, -0.29, 0.98, -0.18, g, 12).rotation.x = Math.PI / 2;
  g.water = 0.34; return g;
}

/** a heap of pink tails (3D tubes) in a basket; g.show(k) reveals 0..1 of them */
export function tailBasket(n = 40) {
  const g = new THREE.Group();
  const wood = mat({ map: T.planks('#C08A50', [0.6, 0.4]) });
  const bk = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.32, 0.38, 24, 1, true), wood); bk.position.y = 0.19; bk.material.side = THREE.DoubleSide; bk.castShadow = true; g.add(bk);
  cyl(0.32, 0.32, 0.03, wood, 0, 0.015, 0, g);
  const pm = mat({ color: PINK, roughness: 0.5 }); const tails = [];
  for (let i = 0; i < n; i++) {
    const a = rnd(i) * 6.28, r = rnd(i * 3) * 0.3, lvl = i / n;
    const p0 = new THREE.Vector3(Math.cos(a) * r, 0.08 + lvl * 0.45, Math.sin(a) * r);
    const pts = [0, 1, 2, 3].map((k) => p0.clone().add(new THREE.Vector3(Math.cos(a + k * 1.3) * k * 0.09, Math.sin(k * 2.1 + i) * 0.03, Math.sin(a + k * 1.1) * k * 0.09)));
    const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 12, 0.018, 6), pm); m.castShadow = true; g.add(m); tails.push(m);
  }
  g.show = (k) => tails.forEach((t, i) => (t.visible = i < Math.round(k * n)));
  g.show(0); return g;
}

/** a floating heart sprite (2D) */
export function heart(s = 0.28) {
  const t = canvasTex('heart', 128, 128, (c) => { c.save(); c.translate(64, 70); c.beginPath(); c.moveTo(0, 36); c.bezierCurveTo(-60, -6, -36, -58, 0, -26); c.bezierCurveTo(36, -58, 60, -6, 0, 36); c.lineWidth = 8; c.strokeStyle = INK; c.fillStyle = '#F0506E'; c.fill(); c.stroke(); c.fillStyle = 'rgba(255,255,255,0.7)'; c.beginPath(); c.ellipse(-18, -20, 8, 5, -0.6, 0, 7); c.fill(); c.restore(); });
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, toneMapped: false, depthWrite: false })); sp.scale.set(s, s, 1); return sp;
}

/** a square fenced pen centred on the origin */
export function pen(w = 6, d = 4, col = '#E9DCC0') {
  const g = new THREE.Group(), m = mat({ color: col });
  const side = (len, x, z, ry) => { const s = new THREE.Group(); for (let k = 0; k <= len; k += 1) box(0.1, 0.8, 0.1, m, k, 0.4, 0, s); [0.3, 0.65].forEach((y) => box(len, 0.07, 0.05, m, len / 2, y, 0, s)); s.position.set(x, 0, z); s.rotation.y = ry; g.add(s); };
  side(w, -w / 2, d / 2, 0); side(w, -w / 2, -d / 2, 0); side(d, -w / 2, d / 2, Math.PI / 2); side(d, w / 2, d / 2, Math.PI / 2);
  const dirt = new THREE.Mesh(new THREE.PlaneGeometry(w, d), mat({ map: T.dirt('#B8834F', [2, 2], false) })); dirt.rotation.x = -Math.PI / 2; dirt.position.y = 0.012; dirt.receiveShadow = true; g.add(dirt);
  return g;
}

// THE CITY THAT PAID PEOPLE TO FARM RATS: the shot list (Tall Tale 3D).
// Hanoi, 1902: new sewers → rats → hired catchers → 1 cent per tail → tailless rats → rat farms → deal cancelled.
import * as THREE from 'three';
import { ctx, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { L, Wd } from './core/timing.js';
import { camera } from './core/engine.js';
import * as WD from './core/world.js';
import * as PR from './core/props.js';
import { Toon, PROPS } from './core/toon.js';
import { Rat, RPROPS, sewer, toilet, tailBasket, heart, pen } from './core/rats.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const mix = (a, b, k) => a.clone().lerp(b, k);
const talk = (t, on = 1) => (on ? 0.25 + 0.75 * Math.abs(Math.sin(t * 13)) * (0.6 + 0.4 * Math.sin(t * 5.3)) : 0);
const blink = (t, off = 0) => (((t + off) % 3.3) < 0.12 ? 1 : 0);
const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// the cast (original characters)
const LOOK = {
  boss: { body: '#3E5FA8', hat: 'tophat', hatCol: '#2A2638', neck: 'bowtie', neckCol: '#D8343F', pattern: 'vest', patCol: '#2A2638', extra: ['mustache', 'monocle'] },
  catcher: { body: '#E8734A', pattern: 'overalls', patCol: '#3E5FA8', hat: 'cap', hatCol: '#6E8A4F' },
  catcher2: { body: '#9BC46A', pattern: 'overalls', patCol: '#7A5236', hat: 'beanie', hatCol: '#D8343F' },
  catcher3: { body: '#F2C230', pattern: 'stripes', patCol: '#E8A23A', hat: 'cap', hatCol: '#3B3346' },
  lady: { body: '#F2B8C6', hat: 'flower', hatCol: '#F29BB5', pattern: 'apron', patCol: '#FFF4E0', extra: ['blush'] },
  sly: { body: '#4FB3A9', hat: 'boater', hatCol: '#E8C77A', band: '#B5372E', neck: 'scarf', neckCol: '#F2C230', extra: ['freckles'] },
  man: { body: '#B98ACF', hat: 'bowler', hatCol: '#3B3346', neck: 'tie', neckCol: '#F2C230' },
  farmer: { body: '#D8584A', pattern: 'overalls', patCol: '#3C6FB6', hat: 'boater', hatCol: '#E8C77A', band: '#3C6FB6', extra: ['freckles'] },
};
const person = (k, opts) => new Toon({ ...LOOK[k], extra: [...(LOOK[k].extra || [])] }, opts);

// ── 2D overlays ──────────────────────────────────────────────────────────
function rew(lt) {          // the "rewind" badge on "See,"
  if (lt > 0.9) return;
  const a = lt < 0.7 ? 1 : 1 - (lt - 0.7) / 0.2;
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(255,255,255,0.10)'; for (let y = (lt * 900) % 40; y < 1920; y += 40) ctx.fillRect(0, y, 1080, 3);
  ctx.translate(90, 210); ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = '#0B0B10'; ctx.lineWidth = 10; ctx.lineJoin = 'round';
  [0, 52].forEach((dx) => { ctx.beginPath(); ctx.moveTo(dx + 50, -32); ctx.lineTo(dx, 0); ctx.lineTo(dx + 50, 32); ctx.closePath(); ctx.stroke(); ctx.fill(); });
  ctx.font = '900 76px Inter'; ctx.textBaseline = 'middle'; ctx.strokeText('REW', 125, 4); ctx.fillText('REW', 125, 4);
  ctx.restore();
}
function card(lines, pop, { x = 540, y = 560, rot = -0.06, w = 560, h = 600 } = {}) {   // a paper notice slapped on screen
  if (pop <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(lerp(-0.4, rot, eo(pop))); const sc = lerp(1.8, 1, eo(pop)); ctx.scale(sc, sc); ctx.globalAlpha = Math.min(1, pop * 2);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(-w / 2 + 18, -h / 2 + 18, w, h); ctx.fillStyle = '#F4EBD6'; ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.strokeStyle = '#1F1C33'; ctx.lineWidth = 8; ctx.strokeRect(-w / 2 + 20, -h / 2 + 20, w - 40, h - 40);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; let yy = -h / 2 + 110;
  lines.forEach(([txt, size, col]) => { ctx.fillStyle = col || '#1F1C33'; ctx.font = `900 ${size}px Inter`; ctx.fillText(txt, 0, yy); yy += size * 1.3; });
  ctx.restore();
}
function stamp(text, sp, { x = 540, y = 620, col = '#C8283A', rot = -0.16, size = 120 } = {}) {
  if (sp <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); const s = lerp(2.6, 1, eo(sp)); ctx.scale(s, s); ctx.globalAlpha = Math.min(1, sp * 1.5);
  ctx.font = `900 ${size}px Inter`; const w = ctx.measureText(text).width + 90;
  ctx.strokeStyle = col; ctx.lineWidth = 14; ctx.beginPath(); ctx.roundRect(-w / 2, -size * 0.75, w, size * 1.5, 22); ctx.stroke();
  ctx.fillStyle = col; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, 6);
  ctx.restore();
}
function counter(n, label, pop, { y = 430 } = {}) {
  ctx.save(); ctx.translate(540, y); const s = lerp(0.6, 1, eob(clamp(pop))); ctx.scale(s, s);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const txt = Math.round(n).toLocaleString('en-US');
  ctx.font = '900 170px Inter'; ctx.lineWidth = 22; ctx.strokeStyle = '#0B0B10'; ctx.strokeText(txt, 0, 0); ctx.fillStyle = '#FFD43B'; ctx.fillText(txt, 0, 0);
  ctx.font = '900 70px Inter'; ctx.lineWidth = 14; ctx.strokeText(label, 0, 130); ctx.fillStyle = '#FFFFFF'; ctx.fillText(label, 0, 130);
  ctx.restore();
}
function qmark(pop, x = 820, y = 420) {
  if (pop <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(0.12); const s = eob(clamp(pop)); ctx.scale(s, s);
  ctx.font = '900 260px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  ctx.lineWidth = 26; ctx.strokeStyle = '#0B0B10'; ctx.strokeText('?', 0, 0); ctx.fillStyle = '#FFD43B'; ctx.fillText('?', 0, 0); ctx.restore();
}
function yearTag(pop) {     // "HANOI 1902" title tag on the hook
  if (pop <= 0) return;
  ctx.save(); ctx.translate(540, 300); const s = eob(clamp(pop)); ctx.scale(s, s);
  ctx.fillStyle = '#F4EBD6'; ctx.strokeStyle = '#1F1C33'; ctx.lineWidth = 8; ctx.beginPath(); ctx.roundRect(-280, -70, 560, 140, 18); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#B5372E'; ctx.font = '900 84px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('HANOI 1902', 0, 6);
  ctx.restore();
}
const TAIL_CARD = [['RAT TAILS', 104], ['1¢ EACH', 128, '#B5372E'], ['BRING THEM TO', 52], ['CITY HALL', 60]];

export function buildShots(E) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.06);
  const cam = camera(36);
  const LOOKS = { street: { bloom: 0.15, aperture: 0.0012, maxblur: 0.008 }, room: { bloom: 0.3, aperture: 0.001, maxblur: 0.008 }, field: { bloom: 0.25, aperture: 0.001, maxblur: 0.007 }, sewer: { bloom: 0.55, bloomThreshold: 0.7, aperture: 0.0012, maxblur: 0.008, vignette: 0.32 } };
  const shoot = (scene, people, from, to, at, at2, k, look, focus) => {
    if (cam.fov !== (look.fov || 36)) { cam.fov = look.fov || 36; cam.updateProjectionMatrix(); }
    cam.position.copy(mix(from, to, k)); cam.lookAt(at2 ? mix(at, at2, k) : at);
    people.forEach((p) => p.face(cam));
    E.render(scene, cam, { ...look, focus: focus ?? cam.position.distanceTo(at2 ? mix(at, at2, k) : at) });
  };
  const show = (list, on) => list.forEach((o) => ((o.group || o).visible = on));

  // ── MAIN STREET (Hanoi, 1902; city hall on the left) ──
  const SHOPS = [['BAKERY', '#C9603F', 'brick', '#D8343F'], ['TEA HOUSE', '#6FA3B8', 'wood', '#2E4E3F'], ['BARBER', '#E3C16F', 'wood', '#3C6FB6'], ['GRAND HOTEL', '#9E4A3A', 'brick', null],
    ['TAILOR', '#B98ACF', 'wood', '#2E4E3F'], ['CITY HALL', '#E6D3A3', 'brick', '#2E4E8A'], ['PHARMACY', '#5FA39A', 'wood', '#D8343F'], ['CAFE', '#E58A6A', 'wood', '#2E4E3F'],
    ['BANK', '#C7B79A', 'brick', null], ['NOODLES', '#D9A34A', 'wood', '#D8343F'], ['SHOES', '#7FA36A', 'wood', null], ['THEATER', '#A3485A', 'brick', '#F2C230']];
  const ST = WD.mainStreet(E, { shops: SHOPS });
  ST.sun.key.target.position.set(-3, 0, 0); ST.sun.key.position.set(5, 13, 6);
  const CH = ST.buildings.find((b) => b.name === 'CITY HALL'); const z0 = CH.z;
  const plague = PR.poster(['WARNING', '!PLAGUE', 'WASH HANDS', 'AVOID RATS'], { w: 1.2, h: 1.5 }); plague.position.set(-6.1, 2.0, z0 - 4.2); plague.rotation.y = Math.PI / 2; ST.scene.add(plague);
  const stBoss = person('boss'), stMan = person('man'), stLady = person('lady'), stC1 = person('catcher'), stC2 = person('catcher2'), stC3 = person('catcher3'), stSly = person('sly');
  const stCast = [stBoss, stMan, stLady, stC1, stC2, stC3, stSly]; stCast.forEach((p) => ST.scene.add(p.group));
  const stRats = []; for (let i = 0; i < 16; i++) { const r = new Rat({ tail: i % 3 !== 0 }); ST.scene.add(r.group); stRats.push(r); }
  const babies = []; for (let i = 0; i < 5; i++) { const r = new Rat({ size: 0.32, mood: 'happy' }); ST.scene.add(r.group); babies.push(r); }
  const stTailless = new Rat({ tail: false, mood: 'happy' }); ST.scene.add(stTailless.group);
  const streetAll = () => [...ST.people, ...stCast, ...stRats, ...babies, stTailless];
  const streetReset = () => { show(stCast, false); show(stRats, false); show(babies, false); show([stTailless], false); };
  const ratRun = (r, t, x0, x1, z, speed, off, period) => {        // a rat that loops across the road
    const u = ((t * speed + off) % period) / period; r.at(lerp(x0, x1, u), 0, z); r.set({ flip: x1 < x0 }); r.run(t, 16, off * 3); r.group.visible = true;
  };

  // ── CITY HALL OFFICE ──
  const view = (scene, from, look, people = []) => { const c = new THREE.PerspectiveCamera(42, 4 / 3, 0.1, 800); c.position.copy(from); c.lookAt(look); people.forEach((p) => p.face(c)); const t = WD.snapshot(E, scene, c); t.wrapS = THREE.RepeatWrapping; return t; };
  streetReset();
  const OF = WD.interior(E, { w: 7, depth: 6, wall: '#2E4E8A', motif: '#3A5E9C', ceiling: '#2A2638', floor: '#7A3E24', signText: null, counterOn: false, litter: false, view: view(ST.scene, V3(0, 6, 6), V3(0, 3, -40), ST.people) });
  const dk = PR.desk(2.4); dk.position.set(0.4, 0, -3.2); OF.scene.add(dk);
  const tailPoster = PR.poster(['RAT TAILS', '!1¢ EACH', 'BRING THEM', 'TO CITY HALL'], { w: 1.3, h: 1.7 }); tailPoster.position.set(-2.3, 2.1, -5.87); OF.scene.add(tailPoster);
  { const fl = WD.signBoard('CITY HALL', { w: 2.2, h: 0.42, bg: '#2A2638', fg: '#E2B33C' }); fl.position.set(0.4, 3.55, -5.88); OF.scene.add(fl); }
  const basket = tailBasket(44); basket.position.set(1.25, 0.88, -3.05); OF.scene.add(basket);
  const ofBoss = person('boss'); ofBoss.at(0.4, 0, -3.95); OF.scene.add(ofBoss.group);
  const ofQ = [person('sly'), person('lady'), person('man'), person('catcher2')]; ofQ.forEach((p) => OF.scene.add(p.group));
  const ofPeople = [ofBoss, ...ofQ];

  // ── FANCY BATHROOM ──
  const BR = WD.interior(E, { w: 6, depth: 5.5, wall: '#E58FA8', motif: '#F2B3C4', floor: '#E6D2B0', ceiling: '#F2E6CF', signText: null, counterOn: false, litter: false, picture: true, view: view(ST.scene, V3(-2, 2.5, -14), V3(2, 2.6, 10), ST.people) });
  const loo = toilet(); loo.position.set(1.0, 0, -4.7); BR.scene.add(loo);
  { const mirror = new THREE.Mesh(new THREE.CircleGeometry(0.45, 40), new THREE.MeshStandardMaterial({ color: '#CFE8F2', roughness: 0.05, metalness: 0.6 })); mirror.position.set(-1.4, 2.0, -5.38); BR.scene.add(mirror);
    const fr = new THREE.Mesh(new THREE.TorusGeometry(0.47, 0.05, 10, 40), WD.mat({ color: '#D9A441', metalness: 0.85, roughness: 0.25 })); fr.position.copy(mirror.position); BR.scene.add(fr); }
  const brRat = new Rat({ mood: 'happy', size: 0.5 }); BR.scene.add(brRat.group);
  const brLady = person('lady'); brLady.at(0.25, 0, -3.2); BR.scene.add(brLady.group);

  // ── THE SEWER ──
  const SW = sewer(E);
  const swRats = []; for (let i = 0; i < 18; i++) { const r = new Rat({ mood: i % 4 === 0 ? 'sly' : 'happy' }); SW.scene.add(r.group); swRats.push(r); }
  const hearts = []; for (let i = 0; i < 6; i++) { const h = heart(0.26); SW.scene.add(h); hearts.push(h); }
  const swC = person('catcher'); SW.scene.add(swC.group);
  const sacks = []; for (let i = 0; i < 7; i++) { const s = PR.mailSack(0.75 + (i % 3) * 0.08, '#B8A27A'); s.position.set(-2.3 + (i % 2) * 0.55, 0, -3.2 - Math.floor(i / 2) * 0.55 - (i % 2) * 0.2); s.rotation.y = i; SW.scene.add(s); sacks.push(s); }
  const swAll = () => [...swRats, swC];

  // ── THE RAT FARM (meadow outside town), day + sunset ──
  const farm = (sunset) => {
    const M = WD.meadow(E, { sunset, fenceOn: false }); M.sun.key.target.position.set(0, 0, -4); M.sun.key.position.set(sunset ? -10 : 7, sunset ? 6 : 12, sunset ? -6 : 8);
    const p = pen(6, 4); p.position.set(0, 0, -4.5); M.scene.add(p);
    const post = new THREE.Group(); { const m = WD.mat({ color: '#7A5236' }); const pl = new THREE.Mesh(new THREE.BoxGeometry(0.12, 1.6, 0.12), m); pl.position.y = 0.8; pl.castShadow = true; post.add(pl); const sb = WD.signBoard('RAT FARM', { w: 1.5, h: 0.5, bg: '#B5372E', fg: '#F4EBD6' }); sb.position.y = 1.65; post.add(sb); }
    post.position.set(-3.4, 0, -2.2); post.rotation.y = 0.35; M.scene.add(post);
    const barn = PR.house({ wall: '#C0503E', roof: '#5A3A2A', door: '#F2E6CF', trim: '#F4EFE4' }); barn.position.set(5.5, 0, -11); barn.rotation.y = -0.4; M.scene.add(barn);
    const rats = []; for (let i = 0; i < 22; i++) { const r = new Rat({ size: i % 5 === 0 ? 0.36 : 0.56, tail: i % 4 !== 1, mood: i % 3 === 0 ? 'sly' : 'happy' }); r.at(-2.6 + rnd(i) * 5.2, 0, -6.2 + rnd(i * 7) * 3.4); r.set({ flip: i % 2 === 0 }); M.scene.add(r.group); rats.push(r); }
    const farmer = person('farmer'); farmer.at(2.1, 0, -1.6); M.scene.add(farmer.group);
    return { ...M, rats, farmer };
  };
  const FD = farm(false), FS = farm(true);
  const fsBoss = person('boss'); FS.scene.add(fsBoss.group);

  // ════════════════ SHOTS ════════════════
  // 1 · "In 1902, the city of Hanoi" — crane down the street to city hall, the official on the boardwalk
  const wPaid = Wd('paid', 0);
  { const st = cut(0);
    add({ id: 'S01', at: st, note: 'crane down the busy street to CITY HALL; the official waits on the boardwalk; HANOI 1902 tag', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); stBoss.group.visible = true;
      stBoss.at(-5.0, 0.18, z0 - 1.6); stBoss.set({ mood: 'proud', armL: [20, 10], armR: [30, -40], blink: blink(t) });
      shoot(ST.scene, streetAll(), V3(0.5, 6.5, z0 - 22), V3(-2.0, 1.8, z0 - 6.6), V3(-2.5, 3.2, z0), V3(-4.8, 1.3, z0 - 1.6), k, { ...LOOKS.street, fov: 44 });
      blit(); yearTag(clamp((t - Wd('1902', 0)) / 0.3));
    } });
    cue(st + 0.05, 'whoosh', { gain: 0.6 }); cue(Wd('1902', 0), 'ding', { gain: 0.7 }); }

  // 2 · "paid people to get rid of rats," — the official holds up a coin; a rat dashes through
  { const st = wPaid - 0.1, wr = Wd('rats', 0);
    add({ id: 'S02', at: st, note: 'close: the official holds up a 1¢ coin, townsman grins; a rat dashes across on "rats"', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); show([stBoss, stMan], true);
      stBoss.at(-5.0, 0.18, z0 - 1.6); stMan.at(-4.2, 0.18, z0 - 2.4);
      stBoss.set({ mood: 'smug', armR: [125, -20], holdR: RPROPS.coin, armL: [20, 10], blink: blink(t) });
      stMan.set({ mood: t > wr ? 'shock' : 'happy', look: [-0.5, -0.3], armL: [60, -40], armR: [20, 10] });
      const r = stRats[0]; const u = clamp((t - wr + 0.25) / 0.7); r.group.visible = u > 0 && u < 1; r.at(lerp(-3.4, -6.0, u), 0.18, z0 - 1.9); r.set({ flip: true, tail: true }); r.run(t);
      shoot(ST.scene, streetAll(), V3(-2.3, 1.9, z0 - 6.4), V3(-2.9, 1.75, z0 - 5.6), V3(-4.6, 1.5, z0 - 1.9), null, k, LOOKS.street);
      blit();
    } });
    cue(st, 'whoosh'); cue(st + 0.2, 'ding', { gain: 0.5 }); cue(wr - 0.1, 'zip', { gain: 0.5 }); }

  // 3 · "and somehow made the problem even worse." — the street floods with rats
  { const st = cut(1), ww = Wd('worse', 1);
    add({ id: 'S03', at: st, note: 'wide: rats pour across the street both ways, townsfolk jump in shock; punch-in on "worse"', draw(lt, d, t, blit) {
      streetReset(); show([stBoss, stLady, stMan], true);
      stBoss.at(-4.9, 0.18, z0 - 3.0); stLady.at(-4.3, 0.18, z0 - 3.6); stMan.at(-3.4, 0, z0 - 3.2);
      const n = Math.min(16, 4 + Math.floor(lt * 7));
      stRats.forEach((r, i) => { if (i >= n) { r.group.visible = false; return; } const dir = i % 2 ? 1 : -1; ratRun(r, t, dir > 0 ? -5.4 : -0.6, dir > 0 ? -0.6 : -5.4, z0 - 4.2 - (i % 8) * 0.45, 1.6 + (i % 3) * 0.4, i * 1.37, 4.8); if (r.group.position.x < -4) r.group.position.y = 0.18; });
      [stBoss, stLady, stMan].forEach((p, i) => p.set({ mood: 'shock', legs: Math.sin(t * 9 + i * 2) > 0.2 ? 'jump' : 'stand', armL: [140, 20], armR: [140, 20], sweat: 1 }));
      const punch = eo(clamp((t - ww + 0.05) / 0.3));
      shoot(ST.scene, streetAll(), V3(-1.4, 1.6, z0 - 10.6), V3(-3.2, 1.45, z0 - 6.6), V3(-3.4, 0.9, z0 - 4.0), V3(-4.4, 1.2, z0 - 3.3), Math.max(eio(clamp(lt / d)) * 0.4, punch), { ...LOOKS.street, fov: 50 });
      blit();
    } });
    cue(st, 'whoosh'); for (let i = 0; i < 6; i++) cue(st + 0.15 + i * 0.28, 'pop', { gain: 0.45 }); cue(ww, 'boing', { gain: 0.8 }); }

  // 4 · "See, the city had just built shiny new sewers," — REW, glide down the gleaming sewer
  { const st = cut(2);
    add({ id: 'S04', at: st, note: 'REW badge, then a slow glide down a brand-new brick sewer: brass pipes, warm lamps, shiny water', draw(lt, d, t, blit) {
      const k = clamp(lt / d); show(swAll(), false); sacks.forEach((s) => (s.visible = false)); hearts.forEach((h) => (h.visible = false));
      shoot(SW.scene, [], V3(0.4, 1.5, 3.5 - k * 6), V3(0.2, 1.4, 1.0 - k * 6), V3(0, 1.2, -10 - k * 6), null, eio(k), { ...LOOKS.sewer, aperture: 0.0006 }, 8);
      blit(); rew(lt);
    } });
    cue(st, 'rewind', { gain: 0.8 }); cue(st + 0.75, 'sparkle', { gain: 0.6 }); cue(st + 0.6, 'bubbles', { dur: 2.2, gain: 0.35 }); }

  // 5 · "and the rats loved them." — rats move in, hearts float up
  { const st = cut(3), wl = Wd('loved', 3);
    add({ id: 'S05', at: st, note: 'rats scamper in along the walkways and settle; on "loved" hearts float up over them', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show([swC], false); sacks.forEach((s) => (s.visible = false));
      const RX = (i) => -1.35 - (i % 3) * 0.32 - Math.floor(i / 2) * 0.12, RZ = (i) => -1.6 - i * 0.62;
      swRats.forEach((r, i) => { if (i >= 9) { r.group.visible = false; return; } const arrive = clamp((lt - i * 0.06) / 0.5);
        r.group.visible = true; r.at(lerp(-3.0, RX(i), eo(arrive)), 0, RZ(i)); r.set({ flip: i % 2 === 0, mood: 'happy', tail: true }); if (arrive < 1) r.run(t, 16, i); else r.still(); });
      hearts.forEach((h, i) => { const u = clamp((t - wl + 0.05 - i * 0.07) / 1.0); h.visible = u > 0; h.position.set(RX(i), 0.45 + u * 0.8, RZ(i)); h.material.opacity = 1 - clamp((u - 0.75) / 0.25); h.scale.setScalar(0.26 * (eob(clamp(u * 3)) || 0.01)); });
      shoot(SW.scene, swAll(), V3(-0.5, 1.05, 1.4), V3(-0.6, 0.95, 0.7), V3(-2.0, 0.35, -4.0), null, k, { ...LOOKS.sewer, fov: 44 });
      blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); for (let i = 0; i < 4; i++) cue(st + 0.05 + i * 0.12, 'pop', { gain: 0.35 }); cue(wl, 'sparkle', { gain: 0.8 }); }

  // 6 · "They popped out of fancy toilets," — a rat pops out of a gold-trimmed toilet, a lady leaps
  { const st = cut(4), wp = Wd('popped', 4);
    add({ id: 'S06', at: st, note: 'fancy pink bathroom: a rat pops up out of the toilet on "popped", the lady leaps in shock', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); const u = eob(clamp((t - wp + 0.05) / 0.28));
      brRat.at(1.0, loo.water - 0.24 + u * 0.36, -4.62); brRat.set({ mood: u > 0.5 ? 'happy' : 'shock', tail: true });
      const sh = t > wp + 0.12;
      brLady.set({ mood: sh ? 'shock' : 'happy', legs: sh && lt < 1.2 ? 'jump' : 'stand', armL: sh ? [150, 30] : [20, 10], armR: sh ? [150, 30] : [40, -60], sweat: sh ? 1 : 0, look: [0.7, 0.3], blink: blink(t) });
      shoot(BR.scene, [brRat, brLady], V3(-0.5, 1.45, 0.3), V3(-0.3, 1.35, -0.5), V3(0.75, 0.9, -4.2), null, k, { ...LOOKS.room, fov: 44 });
      blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(wp, 'plop', { gain: 0.9 }); cue(wp + 0.15, 'boing', { gain: 0.6 }); }

  // 7 · "and people feared the plague." — worried townsfolk in front of a PLAGUE poster
  { const st = cut(5);
    add({ id: 'S07', at: st, note: 'two townsfolk sweat in front of a WARNING: PLAGUE poster; camera pushes in on the poster', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); show([stLady, stMan], true);
      stLady.at(-4.7, 0.18, z0 - 3.5); stMan.at(-4.4, 0.18, z0 - 5.0);
      stLady.set({ mood: 'worried', sweat: 1, armL: [60, -110], armR: [20, 10], look: [-0.6, -0.2], blink: blink(t) });
      stMan.set({ mood: 'worried', sweat: 1, armR: [50, -100], armL: [20, 10], look: [-0.7, -0.3], lean: Math.sin(t * 3) * 2 });
      shoot(ST.scene, streetAll(), V3(-1.4, 1.9, z0 - 8.0), V3(-2.8, 1.85, z0 - 6.6), V3(-5.2, 1.6, z0 - 4.2), V3(-5.6, 1.9, z0 - 4.2), k, LOOKS.street);
      blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(st + 0.35, 'heartbeat', { gain: 0.6 }); }

  // 8 · "So the city hired rat catchers," — three catchers march along the boardwalk with nets
  { const st = cut(6);
    add({ id: 'S08', at: st, note: 'three proud rat catchers with nets march along the boardwalk toward camera', draw(lt, d, t, blit) {
      const k = clamp(lt / d); streetReset(); show([stC1, stC2, stC3], true);
      const zz = z0 - 1.0 - k * 3.0;
      [stC1, stC2, stC3].forEach((p, i) => { p.at(-5.3 + i * 0.6, 0.18, zz + i * 0.9); p.set({ legs: 'walk', phase: t * 7 + i * 1.3, mood: 'proud', armR: [100, -20], holdR: RPROPS.net, armL: [30, 0], blink: blink(t, i) }); });
      shoot(ST.scene, streetAll(), V3(-2.2, 1.7, zz - 5.6), V3(-2.6, 1.6, zz - 4.4), V3(-4.8, 1.4, zz + 0.6), null, eio(k), LOOKS.street);
      blit();
    } });
    cue(st, 'whoosh'); for (let i = 0; i < 4; i++) cue(st + 0.3 + i * 0.42, 'tock', { gain: 0.5 }); }

  // 9 · "who caught over twenty thousand rats in one day." — sacks pile up, a counter rolls to 20,000
  { const st = cut(7), wt = Wd('thousand', 7);
    add({ id: 'S09', at: st, note: 'sewer: catcher swings his net, sacks pile up; counter rolls to 20,000 landing on "thousand"', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show(swRats, false); hearts.forEach((h) => (h.visible = false)); swC.group.visible = true;
      swC.at(-1.75, 0, -2.4); const sw = Math.sin(t * 7);
      swC.set({ mood: 'proud', armR: [lerp(70, 150, (sw + 1) / 2), -20], holdR: RPROPS.net, armL: [40, -40], sweat: 1, lean: sw * 3 });
      const n = Math.min(7, 1 + Math.floor(lt / 0.38)); sacks.forEach((s, i) => { s.visible = i < n; s.scale.setScalar(i === n - 1 && n < 7 ? (eob(clamp(((lt / 0.38) % 1) * 2.5)) || 0.01) : 1); });
      swRats.slice(0, 4).forEach((r, i) => { r.group.visible = true; const u = ((t * 0.7 + i * 0.25) % 1); r.at(lerp(-0.95, -2.9, u), 0, -1.5 - i * 0.18); r.set({ flip: true, mood: 'shock', tail: true }); r.run(t, 16, i); });
      shoot(SW.scene, swAll(), V3(0.3, 1.5, 1.2), V3(0.0, 1.45, 0.4), V3(-1.6, 1.0, -2.6), null, k, LOOKS.sewer);
      blit();
      const u = clamp((t - st - 0.15) / (wt - st - 0.15)); counter(20000 * eo(u), 'RATS IN ONE DAY', clamp((t - st) / 0.25));
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', { dur: wt - st - 0.1, gain: 0.5 }); cue(wt, 'ding', { gain: 0.9 }); for (let i = 1; i < 7; i++) cue(st + i * 0.38, 'thud', { gain: 0.35 }); }

  // 10 · "But the rats kept coming." — a wave of rats runs straight at camera past the exhausted catcher
  { const st = cut(8);
    add({ id: 'S10', at: st, note: 'low sewer shot: a wave of rats charges toward camera; the catcher droops, tired and sweating', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); hearts.forEach((h) => (h.visible = false)); sacks.forEach((s) => { s.visible = true; s.scale.setScalar(1); });
      swC.group.visible = true; swC.at(-1.9, 0, -3.4); swC.set({ mood: 'tired', sweat: 1, armR: [10, 0], holdR: RPROPS.net, armL: [8, 6], lean: -4 });
      swRats.forEach((r, i) => { const s = i % 2 ? 1 : -1; const z = -14 + ((t * (3.2 + (i % 4) * 0.5) + i * 1.7) % 15); r.group.visible = true; r.at(s * (1.3 + (i % 3) * 0.45), 0, z); r.set({ mood: i % 3 ? 'happy' : 'sly', tail: true, flip: s > 0 }); r.run(t, 16, i); });
      shoot(SW.scene, swAll(), V3(0.3, 0.55, 1.8), V3(0.2, 0.6, 1.2), V3(0, 0.5, -6), null, k, { ...LOOKS.sewer, fov: 48 }, 4);
      blit();
    } });
    cue(st, 'whoosh'); cue(st + 0.1, 'slide', { dur: 1.2, gain: 0.4 }); for (let i = 0; i < 6; i++) cue(st + 0.1 + i * 0.2, 'pop', { gain: 0.3 }); }

  // 11 · "So the city made everyone a deal." — the official at his desk, smug, pointing
  { const st = cut(9);
    add({ id: 'S11', at: st, note: 'city hall office: the official behind his desk, smug, pointing at us', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show(ofQ, false); basket.show(0);
      ofBoss.set({ mood: 'smug', talk: talk(t), armR: [80, -10], armL: [20, 10], blink: blink(t), lean: 2 });
      shoot(OF.scene, ofPeople, V3(0.6, 1.75, 0.9), V3(0.5, 1.7, -0.6), V3(0.4, 1.5, -4), null, k, LOOKS.room);
      blit();
    } });
    cue(st, 'whoosh'); cue(st + 0.3, 'ding', { gain: 0.5 }); }

  // 12 · "Bring us a rat's tail, and we'll pay you one cent." — coin up, RAT TAILS 1¢ EACH notice slaps on
  { const st = cut(10), wc = Wd('cent', 10), wt = Wd('tail', 10);
    add({ id: 'S12', at: st, note: 'close-up: official holds up a 1¢ coin; on "cent" the RAT TAILS · 1¢ EACH notice slaps onto the screen', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show(ofQ, false); basket.show(0);
      ofBoss.set({ mood: t > wc ? 'proud' : 'smug', talk: talk(t), armR: [130, -20], holdR: RPROPS.coin, armL: t > wt ? [70, -60] : [20, 10], blink: blink(t) });
      shoot(OF.scene, ofPeople, V3(0.8, 1.7, -0.9), V3(0.65, 1.65, -1.7), V3(0.45, 1.55, -3.95), null, k, LOOKS.room, 2.2);
      blit();
      card(TAIL_CARD, clamp((t - wc + 0.05) / 0.22), { y: 560 });
    } });
    cue(st, 'whoosh'); cue(wt, 'pop', { gain: 0.5 }); cue(wc, 'stamp', { gain: 0.9 }); cue(wc + 0.05, 'ding', { gain: 0.6 }); }

  // 13 · "Just the tail, so nobody had to carry dead rats." — TAILS ONLY stamp, the official waves off a whole sack
  { const st = cut(11), wn = Wd('nobody', 11);
    add({ id: 'S13', at: st, note: 'a townsman offers a pile of boxes; the official waves it off, worried; TAILS ONLY stamp', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show(ofQ, false); ofQ[2].group.visible = true; basket.show(0);
      ofQ[2].at(-0.2, 0, -2.4); ofQ[2].set({ mood: 'happy', armR: [70, -40], armL: [70, -40], holdR: PROPS.parcels, v: 'p' });
      const wave = Math.sin(t * 12);
      ofBoss.set({ mood: t > wn ? 'worried' : 'neutral', sweat: t > wn ? 1 : 0, armR: [100 + wave * 18, -40], armL: [20, 10], look: [-0.7, 0.1] });
      shoot(OF.scene, ofPeople, V3(1.1, 1.7, 0.9), V3(1.0, 1.65, 0.3), V3(0.1, 1.35, -3.2), null, k, { ...LOOKS.room, fov: 44 });
      blit(); stamp('TAILS ONLY!', clamp((t - st - 0.25) / 0.2), { y: 430, size: 104 });
    } });
    cue(st + 0.25, 'stamp', { gain: 1 }); cue(st + 0.28, 'slam', { gain: 0.5 }); }

  // 14 · "And the tails came pouring in." — a queue at the desk, the basket fills, coins fly
  { const st = cut(12);
    add({ id: 'S14', at: st, note: 'side view: a queue of townsfolk holds up tails, the basket fills; the official hands out coins, laughing', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show(ofQ, true); ofQ[3].group.visible = false; basket.show(clamp(0.1 + lt / d));
      ofQ.forEach((p, i) => { p.at(0.55 + i * 0.25, 0, -2.2 + i * 0.5); p.set({ mood: i === 0 ? 'happy' : 'neutral', armL: i === 0 ? [80, -30] : [30, -50], holdL: RPROPS.tailOnly, bob: Math.abs(Math.sin(t * 6 + i)) * 6, look: [-0.8, 0], blink: blink(t, i) }); });
      ofBoss.set({ mood: 'laugh', armR: [90 + Math.sin(t * 10) * 15, -30], holdR: RPROPS.coin, armL: [40, -20] });
      shoot(OF.scene, ofPeople, V3(2.7, 1.8, 1.3), V3(2.5, 1.75, 0.9), V3(0.75, 1.2, -2.8), null, k, { ...LOOKS.room, fov: 40 });
      blit();
    } });
    cue(st, 'whoosh'); for (let i = 0; i < 6; i++) cue(st + 0.15 + i * 0.24, i % 2 ? 'ding' : 'plop', { gain: 0.45 }); }

  // 15 · "But then, officials noticed something weird." — the official on the street with a magnifier
  { const st = cut(13), ww = Wd('weird', 13);
    add({ id: 'S15', at: st, note: 'the official strolls the boardwalk with a magnifying glass, squints down; "?" pops on "weird"', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); stBoss.group.visible = true;
      const zz = z0 - 3 - k * 1.6; stBoss.at(-4.8, 0.18, zz);
      stBoss.set({ mood: t > ww ? 'worried' : 'neutral', legs: lt < d * 0.7 ? 'walk' : 'stand', phase: t * 6, armR: [95, -30], holdR: RPROPS.magnifier, armL: [20, 10], look: [0.3, 0.8], lean: 4 });
      shoot(ST.scene, streetAll(), V3(-2.3, 1.7, zz - 4.2), V3(-2.9, 1.6, zz - 3.2), V3(-4.7, 1.4, zz), null, k, LOOKS.street);
      blit(); qmark(clamp((t - ww) / 0.25));
    } });
    cue(st, 'whoosh'); cue(ww, 'boing', { gain: 0.7 }); }

  // 16 · "Rats running around with no tails." — ground-level: tailless rats scurry past
  { const st = cut(14), wn = Wd('tails', 14);
    add({ id: 'S16', at: st, note: 'rat-eye view on the road: TAILLESS rats scurry past; the official in the back, shocked', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); stBoss.group.visible = true; stBoss.at(-2.2, 0, z0 - 4.6);
      stBoss.set({ mood: 'shock', armR: [150, 20], holdR: RPROPS.magnifier, armL: [140, 20], sweat: 1, legs: Math.sin(t * 8) > 0.5 ? 'jump' : 'stand' });
      stRats.forEach((r, i) => { if (i > 8) { r.group.visible = false; return; } r.set({ tail: false, mood: i % 2 ? 'happy' : 'sly' }); const dir = i % 2 ? 1 : -1; ratRun(r, t, dir > 0 ? -3.4 : 0.4, dir > 0 ? 0.4 : -3.4, z0 - 7.0 - (i % 4) * 0.4, 1.3 + (i % 3) * 0.4, i * 1.9, 3.8); });
      shoot(ST.scene, streetAll(), V3(-0.9, 0.42, z0 - 10.2), V3(-1.1, 0.45, z0 - 9.7), V3(-1.5, 0.5, z0 - 6.5), V3(-1.8, 0.6, z0 - 5.5), k, { ...LOOKS.street, fov: 50 }, 2.8);
      blit();
    } });
    cue(st, 'whoosh'); for (let i = 0; i < 7; i++) cue(st + 0.1 + i * 0.25, 'pop', { gain: 0.35 }); cue(wn, 'boing', { gain: 0.6 }); }

  // 17 · "See, people caught a rat, snipped off the tail," — REW; a sly man holds a rat by the tail, snip
  { const st = cut(15), ws = Wd('snipped', 15);
    add({ id: 'S17', at: st, note: 'REW; on the far boardwalk a sly man dangles a rat by its tail and snips it on "snipped"', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); stSly.group.visible = true; stSly.at(5.0, 0.18, z0 - 9.0);
      const snipped = t > ws + 0.15;
      stSly.set({ mood: 'sly', armL: [70, -60], holdL: snipped ? RPROPS.tailOnly : RPROPS.ratByTail, armR: [90, -60], holdR: RPROPS.scissors, look: [-0.4, -0.2], blink: blink(t) });
      const r = stTailless; r.group.visible = snipped; const fall = clamp((t - ws - 0.15) / 0.3); r.at(4.75, lerp(0.95, 0.18, eo(fall)), z0 - 8.85); r.set({ tail: false, mood: 'shock', flip: true }); r.still();
      shoot(ST.scene, streetAll(), V3(2.8, 1.6, z0 - 12.4), V3(3.2, 1.5, z0 - 11.6), V3(4.9, 1.2, z0 - 9.0), null, k, LOOKS.street);
      blit(); rew(lt);
    } });
    cue(st, 'rewind', { gain: 0.7 }); cue(ws, 'zip', { gain: 0.8 }); cue(ws + 0.4, 'plop', { gain: 0.5 }); }

  // 18 · "and let it go, to make more baby rats," — the tailless rat scampers off; babies pop up beside it
  { const st = cut(16), wb = Wd('baby', 16);
    add({ id: 'S18', at: st, note: 'the tailless rat scampers away down the road; on "baby" five baby rats pop up around it', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); show([stSly, stTailless], true); stSly.at(5.0, 0.18, z0 - 9.0);
      stSly.set({ mood: 'smug', armL: [150, 10], holdL: RPROPS.tailOnly, armR: [20, 10], blink: blink(t) });
      const run = clamp(lt / 1.2); stTailless.at(lerp(4.6, 2.2, eo(run)), 0, z0 - 9.6); stTailless.set({ tail: false, mood: 'happy', flip: true }); if (run < 1) stTailless.run(t); else stTailless.still();
      babies.forEach((b, i) => { const u = clamp((t - wb + 0.1 - i * 0.08) / 0.25); b.group.visible = u > 0; b.at(2.2 - 0.36 + i * 0.18, 0, z0 - 9.2 - (i % 2) * 0.4); b.set({ tail: true, mood: 'happy', flip: i % 2 === 0 }); b.mesh.scale.y = eob(u) || 0.01; b.mesh.position.y = Math.abs(Math.sin(t * 8 + i)) * 0.04; });
      const rp = stTailless.group.position; shoot(ST.scene, streetAll(), V3(rp.x + 0.5, 0.75, z0 - 11.5), V3(rp.x + 0.3, 0.65, z0 - 11.3), V3(rp.x + 0.25, 0.02, z0 - 9.4), null, clamp(lt / d), { ...LOOKS.street, fov: 46 }, 2.1);
      blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); for (let i = 0; i < 5; i++) cue(wb - 0.1 + i * 0.08, 'pop', { gain: 0.6 }); }

  // 19 · "with brand new tails." — close-up on the babies, tails sparkle
  { const st = cut(17), wt = Wd('tails', 17);
    add({ id: 'S19', at: st, note: 'low close-up: the five babies wag their brand-new tails; sparkle on "tails"', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); show([stTailless, stSly], true); stSly.at(5.0, 0.18, z0 - 9.0); stSly.set({ mood: 'laugh', armL: [150, 10], armR: [150, 10] });
      stTailless.at(2.2, 0, z0 - 9.6); stTailless.set({ tail: false, mood: 'happy', flip: true }); stTailless.still();
      babies.forEach((b, i) => { b.group.visible = true; b.at(2.2 - 0.36 + i * 0.18, 0, z0 - 9.2 - (i % 2) * 0.4); b.set({ tail: true, mood: 'happy', flip: i % 2 === 0 }); b.mesh.scale.y = 1; b.mesh.position.y = Math.abs(Math.sin(t * 9 + i)) * 0.05; b.mesh.rotation.z = Math.sin(t * 10 + i) * 0.08; });
      shoot(ST.scene, streetAll(), V3(2.0, 0.55, z0 - 11.8), V3(2.1, 0.45, z0 - 11.3), V3(2.2, 0.25, z0 - 9.3), null, k, { ...LOOKS.street, aperture: 0.002, fov: 44 }, 2.1);
      blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(wt, 'sparkle', { gain: 0.9 }); }

  // 20 · "Some even started rat farms outside of town." — the RAT FARM pen, farmer proud
  { const st = cut(18), wf = Wd('farms', 18);
    add({ id: 'S20', at: st, note: 'crane down over a fenced RAT FARM full of rats outside town; the farmer waves proudly', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d));
      FD.rats.forEach((r, i) => { if (i % 3 === 0) r.run(t, 10, i); else r.still(); });
      FD.farmer.set({ mood: t > wf ? 'proud' : 'happy', armR: [150 + Math.sin(t * 9) * 15, 10], armL: [20, 10], blink: blink(t) });
      shoot(FD.scene, [...FD.rats, FD.farmer], V3(1.5, 6.5, 6.0), V3(1.0, 2.2, 3.0), V3(0, 0, -5), V3(0.6, 0.8, -3.6), k, { ...LOOKS.field, fov: 46 });
      blit();
    } });
    cue(st, 'whoosh'); cue(st + 0.3, 'chirp', { dur: 1.6, gain: 0.25 }); cue(wf, 'ding', { gain: 0.7 }); }

  // 21 · "So the city canceled the deal," — stamp slam, CANCELED
  { const st = cut(19), wc = Wd('canceled', 19);
    add({ id: 'S21', at: st, note: 'office: the official slams his rubber stamp on "canceled"; red CANCELED stamp over the notice', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); show(ofQ, false); basket.show(1);
      const hit = clamp((t - wc + 0.2) / 0.2);
      ofBoss.set({ mood: t > wc ? 'angry' : 'neutral', armR: [lerp(40, 140, eo(seg(lt, 0, Math.max(0.2, wc - st - 0.2)))) - hit * 110, -20], holdR: PROPS.rubberStamp, armL: [20, 10], v: 'rs' });
      shoot(OF.scene, ofPeople, V3(0.6, 1.7, 0.4), V3(0.5, 1.65, -0.5), V3(0.4, 1.45, -4), null, k, LOOKS.room);
      blit();
      card(TAIL_CARD, 1, { y: 560 });
      stamp('CANCELED', clamp((t - wc) / 0.2), { y: 560, size: 120 });
    } });
    cue(st, 'whoosh'); cue(wc, 'stamp', { gain: 1 }); cue(wc + 0.05, 'slam', { gain: 0.6 }); }

  // 22 · "because it wasn't getting rid of rats." — the street, rats everywhere, official sad
  { const st = cut(20);
    add({ id: 'S22', at: st, note: 'the official sits on the boardwalk, sad, tears; rats (with and without tails) scurry all around him', draw(lt, d, t, blit) {
      const k = eio(clamp(lt / d)); streetReset(); stBoss.group.visible = true; stBoss.at(-4.6, 0.18, z0 - 3.6);
      stBoss.set({ mood: 'sad', tears: 1, legs: 'sit', armL: [20, 10], armR: [20, 10], look: [0, 0.5] });
      stRats.forEach((r, i) => { r.set({ tail: i % 2 === 0, mood: 'happy' }); const dir = i % 2 ? 1 : -1; ratRun(r, t, dir > 0 ? -4.2 : 3.0, dir > 0 ? 3.0 : -4.2, z0 - 2.6 - (i % 6) * 0.5, 1.8 + (i % 4) * 0.5, i * 2.3, 7.2); });
      shoot(ST.scene, streetAll(), V3(-0.8, 1.6, z0 - 8.4), V3(-1.6, 1.4, z0 - 7.2), V3(-4.2, 0.9, z0 - 3.6), null, k, LOOKS.street);
      blit();
    } });
    cue(st, 'whoosh', { gain: 0.5 }); cue(st + 0.3, 'slide', { dur: 1.0, gain: 0.35 }); }

  // 23 · "It was paying people to farm them." — sunset at the rat farm: farmer laughing with cash, official sad
  { const st = cut(21), wf = Wd('farm', 21);
    add({ id: 'S23', at: st, note: 'pink sunset over the rat farm: the farmer laughs fanning cash, the official slumps; punch-in on "farm"', draw(lt, d, t, blit) {
      const kk = clamp(lt / Math.min(d, 2.4));
      FS.rats.forEach((r, i) => { if (i % 2 === 0) r.run(t, 10, i); else r.still(); });
      FS.farmer.at(1.0, 0, -1.4); FS.farmer.set({ mood: 'laugh', armR: [130 + Math.sin(t * 8) * 10, -20], holdR: RPROPS.cashFan, armL: [60, -40], bob: Math.abs(Math.sin(t * 9)) * 8 });
      fsBoss.at(-0.4, 0, -2.2); fsBoss.set({ mood: 'sad', tears: 1, armL: [10, 0], armR: [10, 0], look: [0.6, 0] });
      const punch = eo(clamp((t - wf) / 0.35));
      shoot(FS.scene, [...FS.rats, FS.farmer, fsBoss], V3(-0.4, 1.7, 5.2), V3(0.6, 1.6, 1.4), V3(0, 1.0, -2.6), V3(0.9, 1.3, -1.4), Math.max(eio(kk) * 0.5, punch), { ...LOOKS.field, fov: 44 });
      blit();
    } });
    cue(st, 'whoosh'); cue(wf, 'boing', { gain: 0.7 }); cue(wf + 0.3, 'sparkle', { gain: 0.6 }); }

  return { shots: S, cues: CUES };
}

// Video QA on the owner's PC, after the render and before the upload. $0, no Claude usage.
//   node qa.mjs "<job dir>" [--test]
// 1. Hard checks without AI (ffmpeg): black stretches, silent audio, wrong length.  -> qa-block.txt = do NOT upload
// 2. Qwen3-VL-8B (local Ollama) looks at one frame per narration line and reports what it sees and what looks broken.
//    Its findings are advice only (they never stop an upload): they go into the Telegram caption and into
//    jobs\_uploaded\<job>-qa.json so the next Claude run can fix recurring problems in kit.py / character.py.
// --test: write the report only (no qa-block.txt, no meta.json change).
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync, spawnSync } from 'node:child_process';

const FF = 'C:\\Users\\Mukesh\\.clip-studio\\ffmpeg\\bin\\ffmpeg.exe';
const OLLAMA = 'E:\\Ollama\\ollama.exe', MODEL = 'qwen3-vl:8b', API = 'http://127.0.0.1:11434';
const dir = path.resolve(process.argv[2] || '.'), TEST = process.argv.includes('--test');
const job = path.basename(dir), video = fs.existsSync(path.join(dir, 'final.mp4')) ? path.join(dir, 'final.mp4') : path.join(dir, 'share.mp4');
const report = { job, video: path.basename(video), at: new Date().toISOString(), hard: {}, frames: [], ai: 'skipped' };
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

// ---------- 1. hard checks ----------
function ff(args) { const r = spawnSync(FF, args, { encoding: 'utf8', maxBuffer: 64 << 20 }); return (r.stderr || '') + (r.stdout || ''); }
const probe = ff(['-hide_banner', '-i', video, '-af', 'volumedetect', '-vf', 'blackdetect=d=0.6:pix_th=0.06', '-f', 'null', '-']);
const dur = (() => { const m = /Duration: (\d+):(\d+):([\d.]+)/.exec(probe); return m ? +m[1] * 3600 + +m[2] * 60 + +m[3] : 0; })();
const blacks = [...probe.matchAll(/black_start:([\d.]+) black_end:([\d.]+)/g)].map(m => [+m[1], +m[2]]);
const blackSec = blacks.reduce((s, [a, b]) => s + (b - a), 0);
const meanVol = (() => { const m = /mean_volume: (-?[\d.]+) dB/.exec(probe); return m ? +m[1] : -99; })();
report.hard = { duration: +dur.toFixed(2), black_seconds: +blackSec.toFixed(2), black_parts: blacks, mean_volume_db: meanVol };
const hardFail = [];
if (dur < 10 || dur > 180) hardFail.push(`length ${dur.toFixed(1)} s`);
if (blackSec > 1.5) hardFail.push(`${blackSec.toFixed(1)} s black screen`);
if (meanVol < -45) hardFail.push(`no sound (mean ${meanVol} dB)`);
report.hard.fail = hardFail;
log('hard checks', JSON.stringify(report.hard));

// ---------- 2. Qwen3-VL looks at the frames ----------
async function up() { try { const r = await fetch(API + '/api/version', { signal: AbortSignal.timeout(3000) }); return r.ok; } catch { return false; } }
async function ensureServer() {
  if (await up()) return true;
  if (!fs.existsSync(OLLAMA)) return false;
  // start it outside this job's process tree, so the render queue never waits on it
  spawnSync('powershell', ['-NoProfile', '-Command', `Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='cmd.exe /c set OLLAMA_MODELS=E:\\Ollama\\models&& "${OLLAMA}" serve'} | Out-Null`]);
  for (let i = 0; i < 30; i++) { await new Promise(r => setTimeout(r, 2000)); if (await up()) return true; }
  return false;
}
const PROMPT = (line) => `You are checking one frame of a realistic 3D animated YouTube Short (how-it-works explainer, rendered in Blender).
The narrator says at this moment: "${line}"
Look carefully and answer ONLY with JSON:
{"describe": "<one sentence: what is in the picture>",
 "matches_narration": "yes" | "partly" | "no",
 "problems": ["<short problem>", ...],
 "severity": "none" | "minor" | "serious"}
Problems to look for: picture black, blank or almost all one colour; very dark or blown out; a human body that looks broken
(arms or legs through the body or through objects, twisted joints, missing head or hands, person floating or sunk into the ground);
objects floating, cutting through each other, or missing textures (bright pink/magenta, checkerboard); caption text cut off,
overlapping or hard to read; the main subject hard to see. Do not invent problems: if it looks fine, "problems": [] and "severity": "none".`;

async function ask(jpg, line, last) {
  const body = { model: MODEL, stream: false, think: false, format: 'json', keep_alive: last ? 0 : '5m',
    options: { temperature: 0, num_ctx: 4096 },
    messages: [{ role: 'user', content: PROMPT(line), images: [fs.readFileSync(jpg).toString('base64')] }] };
  const r = await fetch(API + '/api/chat', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), signal: AbortSignal.timeout(240000) });
  const j = await r.json(); const txt = (j.message && j.message.content) || '';
  try { return JSON.parse(txt.slice(txt.indexOf('{'), txt.lastIndexOf('}') + 1)); } catch { return { describe: txt.slice(0, 200), problems: [], severity: 'unknown' }; }
}

async function aiCheck() {
  let lines = [];
  try { lines = JSON.parse(fs.readFileSync(path.join(dir, 'timing.json'), 'utf8')).lines || []; } catch {}
  if (!lines.length) lines = Array.from({ length: 8 }, (_, i) => ({ text: '', start: dur * i / 8, end: dur * (i + 1) / 8 }));
  // one frame per line (max 12, evenly picked), at 60% of the line so the cut has happened
  const pick = lines.length <= 12 ? lines : Array.from({ length: 12 }, (_, i) => lines[Math.round(i * (lines.length - 1) / 11)]);
  if (!(await ensureServer())) return 'ollama not running';
  const fdir = path.join(dir, 'qa-frames'); fs.mkdirSync(fdir, { recursive: true });
  const t0 = Date.now();
  for (let k = 0; k < pick.length; k++) {
    const L = pick[k], t = Math.min(dur - 0.1, L.start + 0.6 * (L.end - L.start));
    const jpg = path.join(fdir, `f${String(k).padStart(2, '0')}.jpg`);
    ff(['-v', 'error', '-y', '-ss', t.toFixed(2), '-i', video, '-frames:v', '1', '-vf', 'scale=576:-2', '-q:v', '3', jpg]);
    if (!fs.existsSync(jpg)) continue;
    try {
      const a = await ask(jpg, L.text || '', k === pick.length - 1);
      report.frames.push({ t: +t.toFixed(1), line: L.text, ...a }); log(`t=${t.toFixed(1)}`, a.severity, JSON.stringify(a.problems || []), '|', a.describe);
    } catch (e) { report.frames.push({ t: +t.toFixed(1), line: L.text, error: String(e.message || e).slice(0, 120) }); log('frame error', e.message); }
    if (Date.now() - t0 > 12 * 60000) { log('time budget reached'); break; }
  }
  fs.rmSync(fdir, { recursive: true, force: true });
  return 'done';
}

try { report.ai = await aiCheck(); } catch (e) { report.ai = 'error: ' + String(e.message || e).slice(0, 150); }

// ---------- 3. summary, record, gate ----------
const serious = report.frames.filter(f => f.severity === 'serious'), minor = report.frames.filter(f => f.severity === 'minor');
const off = report.frames.filter(f => f.matches_narration === 'no');
report.summary = report.ai !== 'done' ? `AI check ${report.ai}` :
  `${report.frames.length - serious.length - minor.length}/${report.frames.length} frames OK` +
  (serious.length ? `; serious: ${serious.map(f => `${f.t}s ${(f.problems || []).join(', ')}`).join(' | ')}` : '') +
  (minor.length ? `; minor: ${minor.length}` : '') + (off.length ? `; picture off-topic at ${off.map(f => f.t + 's').join(', ')}` : '');
if (hardFail.length) report.summary = `BLOCKED (${hardFail.join(', ')}); ` + report.summary;
fs.writeFileSync(path.join(dir, 'qa.json'), JSON.stringify(report, null, 1));
const rec = path.join(path.dirname(dir), '_uploaded'); fs.mkdirSync(rec, { recursive: true });
fs.writeFileSync(path.join(rec, job + '-qa.json'), JSON.stringify(report, null, 1));
log('SUMMARY', report.summary);

if (!TEST) {
  if (hardFail.length) {
    fs.writeFileSync(path.join(dir, 'qa-block.txt'), hardFail.join('\n'));
    try { execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\\Ai Video Edit\\_claude\\send-telegram-text.ps1', '-Text', `QA BLOCKED upload of ${job}: ${hardFail.join(', ')}`]); } catch {}
  } else {
    const mp = path.join(dir, 'meta.json');
    try { const m = JSON.parse(fs.readFileSync(mp, 'utf8')); m.telegram_caption = (m.telegram_caption || m.title) + `\nQA (Qwen): ${report.summary}`.slice(0, 700); fs.writeFileSync(mp, JSON.stringify(m, null, 1)); } catch {}
  }
}

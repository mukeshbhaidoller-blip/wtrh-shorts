"""Build a PC render job for the Blender pipeline.

  python3 blender/build_job.py cues  --proj <faceless project>            -> data/cues.json (soft whoosh per cut + script "sfx")
  python3 blender/build_job.py job   --proj <faceless project> --shots <shots.py> --name <job-name> --out <dir>

`job` writes <dir>/ with: kit.py, shots.py, timing.json, mix.wav, caps/cNN.png, job.bat.
Commit every file of <dir> to D:\\Ai Video Edit\\jobs\\<job-name>\\ and LAST of all a file ready.txt; the PC helper then runs
job.bat (Blender render on the RTX GPU -> captions + audio -> final.mp4 + share.mp4) and writes done.txt.
Optional per-line sound in script.json: "sfx": [{"at": 0.4, "type": "pop", "gain": 0.5}]  (at = seconds after line start).
"""
import argparse, json, os, re, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
BLENDER = r'D:\Ai Video Edit\_tools\blender\blender-4.5.16-windows-x64\blender.exe'
FFMPEG = r'C:\Users\Mukesh\.clip-studio\ffmpeg\bin\ffmpeg.exe'
ASSETS = r'D:\Ai Video Edit\assets'


def load(proj):
    S = json.load(open(f'{proj}/script.json'))
    L = json.load(open(f'{proj}/data/lines.json'))
    W = json.load(open(f'{proj}/data/words.json'))
    return S, L, W


def cues(proj):
    S, L, _ = load(proj)
    out = [{'t': 0.05, 'type': 'whoosh', 'gain': 0.45}]
    for i, ln in enumerate(L['lines']):
        if i: out.append({'t': round(max(0, ln['start'] - 0.12), 3), 'type': 'whoosh', 'gain': 0.32})
        for c in S['lines'][i].get('sfx', []):
            e = {'t': round(ln['start'] + float(c.get('at', 0)), 3), 'type': c['type'], 'gain': c.get('gain', 0.45)}
            if 'dur' in c: e['dur'] = c['dur']
            out.append(e)
    st = S.get('style', 'classic')
    if st in ('pops', 'nomusic'):
        W = json.load(open(f'{proj}/data/words.json'))
        for c in caption_list(S, L, W):
            if c.get('kt') is not None and c.get('kw'): out.append({'t': round(c['kt'], 3), 'type': 'pop', 'gain': 0.8 if st == 'pops' else 0.6})
            elif st == 'nomusic': out.append({'t': round(c['s'] + 0.04, 3), 'type': 'tock', 'gain': 0.5})
    if st == 'hud':
        for stp in (S.get('hud') or {}).get('steps', []):
            out.append({'t': round(L['lines'][min(int(stp[1]), len(L['lines']) - 1)]['start'], 3), 'type': 'sparkle', 'gain': 0.5, 'dur': 0.6})
    if st == 'nomusic' and S.get('music') != 'none': print('NOTE style nomusic: set script.json "music": "none" before mix.py')
    json.dump({'duration': L['duration'], 'cues': sorted(out, key=lambda c: c['t'])}, open(f'{proj}/data/cues.json', 'w'), indent=1)
    print(len(out), 'cues')


def caption_list(S, L, W):
    nm = lambda w: re.sub(r"[^a-z0-9']+", '', str(w).lower())
    caps = []
    for i, ln in enumerate(S['lines']):
        chunks = [c.strip() for c in (ln.get('caps') or ln['text']).split('|') if c.strip()]
        ws = [w for w in W if w['line'] == i]
        if not ws: continue
        counts = [len(c.split()) for c in chunks]; N = sum(counts); acc = 0; frm = 0
        for j, c in enumerate(chunks):
            first = nm(c.split()[0]); idx = 0
            if j:
                idx = next((k for k, w in enumerate(ws) if k > frm and first and (nm(w['w']) == first or (len(first) > 2 and nm(w['w']).startswith(first)))), -1)
                if idx < 0: idx = max(frm + 1, min(len(ws) - 1, round(acc * len(ws) / N)))
            acc += counts[j]; frm = idx
            kw = next((x for x in c.split() if x.startswith('*')), None); kt = None
            if kw:
                kn = nm(kw); kt = next((w['s'] for w in ws[idx:] if kn and nm(w['w']).startswith(kn[:4])), ws[idx]['s'])
            caps.append(dict(line=i, s=max(0.0, ws[idx]['s'] - 0.05), txt=c.replace('*', ''), raw=c, kw=(kw or '').lstrip('*'), kt=kt))
    for k, c in enumerate(caps):
        nxt = caps[k + 1] if k + 1 < len(caps) else None; le = L['lines'][c['line']]['end']
        c['e'] = (le + 0.35 if nxt['s'] - le > 0.7 and nxt['line'] != c['line'] else nxt['s']) if nxt else L['duration']
    return caps


YELLOW = (255, 212, 0, 255)
# script.json "style" (A/B test, see reference/experiments.md):
#   "classic" (default) captions low (y 1300), all white · "mid" captions in the middle (y 960), *keyword yellow
#   "pops" classic captions + a big yellow keyword label on the *word with a pop SFX · "nomusic" classic look, no music bed,
#   extra SFX, loud mix · "hud" classic captions + a progress checklist (script.json "hud") top-left
def draw_caps(caps, outdir, style='classic'):
    font = ImageFont.truetype(FONT, 66); os.makedirs(outdir, exist_ok=True)
    cy = 960 if style == 'mid' else 1300
    for k, c in enumerate(caps):
        words = c['txt'].split(); full = ' '.join(words)
        kwl = c.get('kw', '').lower()
        im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        tw = lambda t: d.textlength(t, font=font)
        lines = [full]
        if tw(full) > 700 and len(words) > 1:
            lines = min(((max(tw(' '.join(words[:i])), tw(' '.join(words[i:]))), [' '.join(words[:i]), ' '.join(words[i:])]) for i in range(1, len(words))), key=lambda x: x[0])[1]
        lh = 66 * 1.12; y0 = cy - (len(lines) - 1) * lh / 2
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        for i, t in enumerate(lines):
            sd.text((540, y0 + i * lh + 3), t, font=font, anchor='mm', fill=(0, 0, 0, 200), stroke_width=4, stroke_fill=(0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        for i, t in enumerate(lines):
            if style == 'mid' and kwl:   # word by word, the keyword in yellow
                x = 540 - tw(t) / 2; sp = tw(' ')
                for w in t.split():
                    col = YELLOW if w.lower().strip('.,!?;:') == kwl.strip('.,!?;:') else (255, 255, 255, 255)
                    d.text((x, y0 + i * lh), w, font=font, anchor='lm', fill=col, stroke_width=3, stroke_fill=(0, 0, 0, 140)); x += tw(w) + sp
            else:
                d.text((540, y0 + i * lh), t, font=font, anchor='mm', fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 110))
        Image.alpha_composite(sh, im).save(f'{outdir}/c{k:02d}.png', optimize=True)


def draw_pops(caps, outdir):
    """style "pops": one big tilted yellow label per *keyword, shown 1.1 s from the moment the word is said"""
    font = ImageFont.truetype(FONT, 132); out = []
    for c in caps:
        if not c.get('kw') or c.get('kt') is None: continue
        word = c['kw'].strip('.,!?;:').upper(); k = len(out)
        f = font
        while ImageDraw.Draw(Image.new('L', (1, 1))).textlength(word, font=f) > 900 and f.size > 60: f = ImageFont.truetype(FONT, f.size - 8)
        lab = Image.new('RGBA', (1080, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(lab)
        d.text((540, 200), word, font=f, anchor='mm', fill=YELLOW, stroke_width=10, stroke_fill=(0, 0, 0, 255))
        lab = lab.rotate(-4, resample=Image.BICUBIC)
        im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); im.alpha_composite(lab, (0, 560))
        im.save(f'{outdir}/p{k:02d}.png', optimize=True); out.append(dict(s=c['kt'], e=c['kt'] + 1.1))
    return out


def draw_hud(S, L, outdir):
    """style "hud": script.json "hud": {"title": "SINK BUILD", "steps": [["U-bend", 3], ["Vent pipe", 7], ...]}
    (step label, line index where it gets its tick). Top-left checklist like a build log."""
    h = S.get('hud') or {}; steps = h.get('steps') or []
    if not steps: return []
    ft = ImageFont.truetype(FONT, 40); fr = ImageFont.truetype(FONT, 32); n = len(steps); out = []
    times = [L['lines'][min(int(st[1]), len(L['lines']) - 1)]['start'] for st in steps]
    for k in range(n + 1):       # state k = k steps done
        im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        x0, y0, w = 44, 150, 430; hh = 70 + 46 * n
        d.rounded_rectangle((x0, y0, x0 + w, y0 + hh), 18, fill=(10, 14, 20, 175))
        d.text((x0 + 22, y0 + 36), str(h.get('title', 'BUILD')).upper(), font=ft, anchor='lm', fill=(255, 255, 255, 255))
        d.text((x0 + w - 22, y0 + 36), f'{k}/{n}', font=ft, anchor='rm', fill=YELLOW)
        for i, st in enumerate(steps):
            y = y0 + 88 + i * 46; done = i < k
            d.rounded_rectangle((x0 + 22, y - 14, x0 + 50, y + 14), 6, outline=(255, 255, 255, 200), width=3, fill=(60, 200, 90, 255) if done else None)
            if done: d.line((x0 + 28, y, x0 + 35, y + 8, x0 + 46, y - 9), fill=(255, 255, 255, 255), width=4)
            d.text((x0 + 64, y), str(st[0]), font=fr, anchor='lm', fill=(255, 255, 255, 255 if done or i == k else 150))
        im.save(f'{outdir}/h{k:02d}.png', optimize=True)
        out.append(dict(s=0.0 if k == 0 else times[k - 1], e=(times[k] if k < n else L['duration'] + 1)))
    return out


def job(proj, shots, name, out, samples, meta_path=None):
    S, L, W = load(proj)
    os.makedirs(out, exist_ok=True)
    if meta_path:
        m = json.load(open(meta_path, encoding='utf-8'))
        for k in ('title', 'description', 'tags', 'date', 'time'):
            if k not in m: raise SystemExit(f'meta needs {k}')
        jd = f'D:\\Ai Video Edit\\jobs\\{name}'
        m.update(video=f'{jd}\\final.mp4', telegram_file=f'{jd}\\share.mp4', channel='UCEbKzlOb63pBdElUTl9wRvg')
        json.dump(m, open(f'{out}/meta.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    shutil.copy(f'{HERE}/kit.py', f'{out}/kit.py'); shutil.copy(f'{HERE}/character.py', f'{out}/character.py'); shutil.copy(shots, f'{out}/shots.py')
    shutil.copy(f'{proj}/data/lines.json', f'{out}/timing.json'); shutil.copy(f'{proj}/data/mix.wav', f'{out}/mix.wav')
    style = S.get('style', 'classic'); print('style:', style)
    if style == 'nomusic':   # loud voice + SFX mix like the references (about -15 LUFS)
        import subprocess
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{proj}/data/mix.wav', '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11', '-ar', '48000', f'{out}/mix.wav'], check=True)
    caps = caption_list(S, L, W); draw_caps(caps, f'{out}/caps', style)
    layers = [(f'caps\\c{k:02d}.png', c['s'], c['e']) for k, c in enumerate(caps)]
    if style == 'pops':
        layers += [(f'caps\\p{k:02d}.png', p['s'], p['e']) for k, p in enumerate(draw_pops(caps, f'{out}/caps'))]
    if style == 'hud':
        layers += [(f'caps\\h{k:02d}.png', h['s'], h['e']) for k, h in enumerate(draw_hud(S, L, f'{out}/caps'))]
    filt = []; prev = '0:v'
    for k, (_, a, b) in enumerate(layers):
        filt.append(f"[{prev}][{k + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{b - 0.001:.3f})'[v{k}]"); prev = f'v{k}'
    filt.append(f'[{prev}]format=yuv420p[vout]')
    ins = ' '.join(f'-i "{f}"' for f, _, _ in layers)
    bat = f'''@echo off
title Claude render job {name}
cd /d "%~dp0"
set "BL={BLENDER}"
set "FF={FFMPEG}"
echo === BLENDER START %DATE% %TIME% === > "job-log.txt"
"%BL%" -b -P kit.py -- --proj "%~dp0." --assets "{ASSETS}" --samples {samples} 2>&1 | findstr /C:"=== " /C:"GPU device" /C:"Error" /C:"Traceback" /C:"line " >> "job-log.txt"
echo === BLENDER END %TIME% === >> "job-log.txt"
"%FF%" -v error -y -framerate 24 -i "frames\\%%05d.jpg" -i "mix.wav" {ins} -filter_complex "{';'.join(filt)}" -map "[vout]" -map 1:a -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k -shortest -movflags +faststart "final.mp4" >> "job-log.txt" 2>&1
"%FF%" -v error -y -i "final.mp4" -c:v libx264 -crf 23 -maxrate 5M -bufsize 10M -preset medium -c:a aac -b:a 160k -movflags +faststart "share.mp4" >> "job-log.txt" 2>&1
if exist share.mp4 (echo RENDER_OK > result.txt) else (echo RENDER_FAILED > result.txt)
rem keep the D: drive clean: drop this job's frames once the video exists, and job folders older than 10 days
if exist share.mp4 rd /s /q frames
rem QA: ffmpeg hard checks + Qwen3-VL (local Ollama) frame review; qa-block.txt stops the upload
if exist share.mp4 if exist "D:\\Ai Video Edit\\_claude\\qa\\qa.mjs" node "D:\\Ai Video Edit\\_claude\\qa\\qa.mjs" "%~dp0." > qa-log.txt 2>&1
if exist share.mp4 if exist meta.json if not exist qa-block.txt node "D:\\Ai Video Edit\\_claude\\uploader\\upload.mjs" "%~dp0meta.json" > upload-log.txt 2>&1
for /d %%D in ("D:\\Ai Video Edit\\jobs\\*") do if exist "%%D\\delete-me.txt" if exist "%%D\\done.txt" rd /s /q "%%D"
forfiles /p "D:\\Ai Video Edit\\jobs" /d -10 /c "cmd /c if @isdir==TRUE rd /s /q @path" > nul 2>&1
echo === JOB END %TIME% === >> "job-log.txt"
'''
    if len(bat) > 7800: raise SystemExit('job.bat too long for cmd.exe: use fewer caption chunks')
    open(f'{out}/job.bat', 'w', newline='').write(bat.replace('\n', '\r\n'))
    files = sorted(os.path.relpath(os.path.join(r, f), out) for r, _, fs in os.walk(out) for f in fs)
    print(len(caps), 'captions;', len(files), 'files ->', out)
    print(json.dumps([{'devicePath': f'D:\\Ai Video Edit\\jobs\\{name}\\' + f.replace('/', '\\'), 'stagedPath': f'{out}/{f}'} for f in files]))


def stills_job(proj, shots, name, out, shots_sel=''):
    """Test stills ON THE PC (needed for shots with people: MPFB only exists there). Writes test/shotNN.jpg."""
    os.makedirs(out, exist_ok=True)
    for f in ('kit.py', 'character.py'): shutil.copy(f'{HERE}/{f}', f'{out}/{f}')
    shutil.copy(shots, f'{out}/shots.py'); shutil.copy(f'{proj}/data/lines.json', f'{out}/timing.json')
    sel = f' --shots {shots_sel}' if shots_sel else ''
    bat = f'''@echo off
cd /d "%~dp0"
"{BLENDER}" -b -P kit.py -- --proj "%~dp0." --assets "{ASSETS}" --samples 24 --scale 0.5 --test{sel} > blender-out.txt 2>&1
echo done > result.txt
'''
    open(f'{out}/job.bat', 'w', newline='').write(bat.replace('\n', '\r\n'))
    files = ['kit.py', 'character.py', 'shots.py', 'timing.json', 'job.bat']
    print(json.dumps([{'devicePath': f'D:\\Ai Video Edit\\jobs\\{name}\\{f}', 'stagedPath': f'{out}/{f}'} for f in files]))


def tg_job(name, render_job, caption, out):
    """A tiny job that sends <render_job>\\share.mp4 to the owner's Telegram with caption.txt (UTF-8)."""
    os.makedirs(out, exist_ok=True)
    open(f'{out}/caption.txt', 'w', encoding='utf-8').write(caption)
    bat = f'''@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\\Ai Video Edit\\_claude\\send-telegram.ps1" -File "D:\\Ai Video Edit\\jobs\\{render_job}\\share.mp4" -CaptionFile "%~dp0caption.txt" > result.txt 2>&1
'''
    open(f'{out}/job.bat', 'w', newline='').write(bat.replace('\n', '\r\n'))
    print(json.dumps([{'devicePath': f'D:\\Ai Video Edit\\jobs\\{name}\\{f}', 'stagedPath': f'{out}/{f}'} for f in ('caption.txt', 'job.bat')]))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['cues', 'job', 'tg', 'stills'])
    ap.add_argument('--proj'); ap.add_argument('--shots'); ap.add_argument('--name'); ap.add_argument('--out')
    ap.add_argument('--samples', type=int, default=48); ap.add_argument('--sel', default=''); ap.add_argument('--meta'); ap.add_argument('--render-job'); ap.add_argument('--caption')
    a = ap.parse_args()
    if a.cmd == 'cues': cues(a.proj)
    elif a.cmd == 'job': job(a.proj, a.shots, a.name, a.out, a.samples, a.meta)
    elif a.cmd == 'stills': stills_job(a.proj, a.shots, a.name, a.out, a.sel)
    else: tg_job(a.name, a.render_job, a.caption, a.out)

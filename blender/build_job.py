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
            caps.append(dict(line=i, s=max(0.0, ws[idx]['s'] - 0.05), txt=c.replace('*', '')))
    for k, c in enumerate(caps):
        nxt = caps[k + 1] if k + 1 < len(caps) else None; le = L['lines'][c['line']]['end']
        c['e'] = (le + 0.35 if nxt['s'] - le > 0.7 and nxt['line'] != c['line'] else nxt['s']) if nxt else L['duration']
    return caps


def draw_caps(caps, outdir):
    font = ImageFont.truetype(FONT, 66); os.makedirs(outdir, exist_ok=True)
    for k, c in enumerate(caps):
        words = c['txt'].split(); full = ' '.join(words)
        im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        tw = lambda t: d.textlength(t, font=font)
        lines = [full]
        if tw(full) > 700 and len(words) > 1:
            lines = min(((max(tw(' '.join(words[:i])), tw(' '.join(words[i:]))), [' '.join(words[:i]), ' '.join(words[i:])]) for i in range(1, len(words))), key=lambda x: x[0])[1]
        lh = 66 * 1.12; y0 = 1300 - (len(lines) - 1) * lh / 2
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        for i, t in enumerate(lines):
            sd.text((540, y0 + i * lh + 3), t, font=font, anchor='mm', fill=(0, 0, 0, 200), stroke_width=4, stroke_fill=(0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        for i, t in enumerate(lines):
            d.text((540, y0 + i * lh), t, font=font, anchor='mm', fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 110))
        Image.alpha_composite(sh, im).save(f'{outdir}/c{k:02d}.png', optimize=True)


def job(proj, shots, name, out, samples):
    S, L, W = load(proj)
    os.makedirs(out, exist_ok=True)
    shutil.copy(f'{HERE}/kit.py', f'{out}/kit.py'); shutil.copy(f'{HERE}/character.py', f'{out}/character.py'); shutil.copy(shots, f'{out}/shots.py')
    shutil.copy(f'{proj}/data/lines.json', f'{out}/timing.json'); shutil.copy(f'{proj}/data/mix.wav', f'{out}/mix.wav')
    caps = caption_list(S, L, W); draw_caps(caps, f'{out}/caps')
    filt = []; prev = '0:v'
    for k, c in enumerate(caps):
        filt.append(f"[{prev}][{k + 2}:v]overlay=0:0:enable='between(t,{c['s']:.3f},{c['e'] - 0.001:.3f})'[v{k}]"); prev = f'v{k}'
    filt.append(f'[{prev}]format=yuv420p[vout]')
    ins = ' '.join(f'-i "caps\\c{k:02d}.png"' for k in range(len(caps)))
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
    ap.add_argument('--samples', type=int, default=48); ap.add_argument('--sel', default=''); ap.add_argument('--render-job'); ap.add_argument('--caption')
    a = ap.parse_args()
    if a.cmd == 'cues': cues(a.proj)
    elif a.cmd == 'job': job(a.proj, a.shots, a.name, a.out, a.samples)
    elif a.cmd == 'stills': stills_job(a.proj, a.shots, a.name, a.out, a.sel)
    else: tg_job(a.name, a.render_job, a.caption, a.out)

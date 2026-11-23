# RUNBOOK: one new Short for "Wait, That Really Happened"

Each scheduled run makes ONE brand-new Short from start to finish and uploads it. Follow every step in order.
Do not ask the owner anything during a run: nobody is watching (runs happen at night while he sleeps).

**NEVER use any tool that waits for a human approval.** In particular: NEVER call WebFetch (every new website asks the
owner for permission and the run would hang all night). Check facts with **WebSearch only** (use `mode: "extended"`
when the standard results are thin); the search snippets are your sources. Do not use computer-use / screen tools or
browsers either: the PC is reached only through the `mcp__remote-devices__` file tools and the jobs folder. If some
tool still asks for approval, skip that step and use another way. If a step fails in a way you cannot fix, do NOT
upload; finish with a short note (in Hindi written in Roman letters) saying what failed.

## Fixed facts (never change these)

- Channel: **Wait, That Really Happened**, handle `@WaitThatReallyHappenedUS`, channel ID `UCEbKzlOb63pBdElUTl9wRvg`.
- Zapier YouTube connection for this channel: `connection_id = 02322a7b-7e7d-8a1a-9aad-6c9bc6a79dc3`.
  ALWAYS pass this connection_id. The Zapier default YouTube connection is a DIFFERENT channel (The Fandom Room):
  never upload without the connection_id.
- File host: this repo, branch `upload` (force-pushed, holds only the current video). Public URL:
  `https://raw.githubusercontent.com/mukeshbhaidoller-blip/wtrh-shorts/upload/video.mp4`
- Log of everything already uploaded: `topics.md` on branch `main`.

## 1. Setup (videos are RENDERED ON THE OWNER'S PC in Blender, since 2026-11-21)

1. Attach the repo with push access (`add_repo` owner `mukeshbhaidoller-blip`, repo `wtrh-shorts`, access `push`), clone it to
   `/home/claude/wtrh-shorts` (`git clone --depth 1 ...`, long timeout), set git user.name `mukeshbhaidoller-blip`,
   user.email `mukeshbhaidoller-blip@users.noreply.github.com`.
2. **Check the PC first.** Load the `mcp__remote-devices__` tools (ToolSearch "device"). `device_list_dir`
   `D:\Ai Video Edit\jobs` must work and `heartbeat.txt` there must be < 3 minutes old (the PC render helper writes it every
   20 s). If the PC can't be reached or the heartbeat is old: STOP, upload nothing, report "PC band hai / helper nahi chal
   raha" in the Hindi report. Never try to render the full video in the cloud (no GPU here: it would take days).
   If `device_list_dir` says the folder is not connected (or get_device_info shows no connected folders) it is often only
   the link waking up: run `sleep 90` in Bash, ToolSearch "device" again, retry — up to 4 tries (~6 min) before giving up.
   Never call device_request_folder_access in a scheduled run (nobody is there to approve it).
3. Load the `anthropic-skills:faceless-shorts` skill and run its `scripts/setup.sh` (only the Kokoro voice, ffmpeg and
   Python are needed; Whisper may fail to download, that is fine).
4. For test stills: `python3.11 -m venv ~/bvenv && ~/bvenv/bin/pip install bpy==4.5.16` (Blender as a Python module, same
   version as the PC's Blender 4.5.16).
5. Disks (2026-11-22): heavy AI things live on the new **E: "AI NVMe 1TB"** (931 GB). `D:\FreeVideo`, `D:\AI-Cache`,
   `D:\VoiceClone`, `D:\Ai Video Edit\_tools` (Blender) and `D:\Ai Video Edit\engines` are junctions to `E:\...`, so the
   old paths still work. Anything NEW and big (models, tools, caches, downloads) goes straight to `E:\` (via a job;
   E: is not a connected folder). `jobs`, `_claude` and `assets` stay real folders on D: (connected folder).
6. PC layout (all under `D:\Ai Video Edit`): Blender `_tools\blender\blender-4.5.16-windows-x64\blender.exe`; ffmpeg
   `C:\Users\Mukesh\.clip-studio\ffmpeg\bin\ffmpeg.exe`; CC0 textures/HDRIs in `assets\` (one folder per texture with
   Diffuse/nor_gl/Rough jpgs, HDRIs as `<id>.hdr`; `device_list_dir` it to see what is there); helper scripts in `_claude\`;
   jobs in `jobs\<name>\`. GPU: RTX 5060 8 GB (OptiX), Cycles ≈ 1.1-2.5 s per 1080x1920 frame at 48 samples.

## 1a. Check the earlier auto-uploads first (cheap)

The PC uploads and sends to Telegram BY ITSELF after each render (section 4), so earlier runs log their video in
`topics.md` as `PENDING-PC <job>`. For each such line: stage `D:\Ai Video Edit\jobs\_uploaded\<job>.json` (the PC writes it
after a good upload + Telegram and then DELETES the whole job folder to save disk space, owner's wish); if there is no
such record, stage `D:\Ai Video Edit\jobs\<job>\upload-result.json`.
- `"ok": true` → replace PENDING-PC in that line with its `url`, push.
- `"ok": false` (or `result.txt` says RENDER_FAILED) → read `error` / `job-log.txt`. If `final.mp4` exists, give it the
  earliest free slot (1b), edit `date`/`time` in that job's `meta.json` (commit a new copy), and run a small job whose
  `job.bat` is just `node "D:\Ai Video Edit\_claude\uploader\upload.mjs" "D:\Ai Video Edit\jobs\<job>\meta.json" > upload-log2.txt 2>&1`.
  If the video itself is missing/bad, mark the line `FAILED` and move on. `NOT_LOGGED_IN` → report that the owner must
  run `D:\Ai Video Edit\_claude\uploader\login.bat` once; still make today's video.
- no result file yet → the PC is still rendering/uploading; leave it.
- `jobs\_uploaded\<job>-qa.json` (the PC's QA report, section 4a) → read its `summary` and the `frames` with
  `severity: serious`. A problem that shows up in 2+ videos (e.g. "arm through body", "very dark", "pink texture") is a
  kit/character/shots bug: fix it in `blender/` before making today's shots, and note the fix in your report.
  `QA BLOCKED` (qa-block.txt in the job folder, nothing uploaded) → read `qa.json` `hard`; re-render with `--redo` for the bad
  shots if it is a render problem, then upload as in the `"ok": false` case.
Older lines marked `NOT UPLOADED` with a `pending/*.json`: same idea (their MP4 is on the git branch named there).

## 1b. Pick the publish slot (videos are made ONE DAY AHEAD and scheduled on YouTube)

- TWO videos per day. **Owner's publish times (2026-11-22): 19:00 (7 PM) and 01:00 (1 AM) India time (Asia/Kolkata, IST)**,
  every day. (While the US is on EST: 19:00 IST = 08:30 ET, 01:00 IST = 14:30 ET the day before.)
- Take the earliest of these IST slots that is at least **20 hours after now** and is not already taken in
  `topics.md` (no other video within 2 hours of it; older lines are in ET: ET + 10:30 h = IST while the US is on EST,
  + 9:30 h during US daylight time).
- Log new lines with the IST slot, e.g. `- 2026-11-27 01:00 IST · <title> · ...`.
- meta.json `date`/`time` are exactly this IST slot (e.g. "27 Nov 2026", "01:00"); Studio's time zone is IST.

## 2. Pick the topic ("how machines and big things work", realistic 3D)

The owner approved the realistic Blender road-lines Short (`reference/road-lines-blender/`). Make more like it.
- **Owner's topic wish (most videos):** cars and trucks, engines, brakes, tires; machines (cranes, excavators, elevators,
  escalators, tunnel boring machines, combine harvesters); AIRPLANES (wings, jet engines, landing gear, tires, de-icing,
  runways, air traffic); trains; ships and locks; HOW HOUSES AND BUILDINGS ARE BUILT (foundations, framing, concrete,
  roofs, plumbing, skyscrapers, bridges, dams). Use your own judgment for more topics in that spirit; set it in the USA
  when there is a place.
- **The hook is everything.** Line 1 must make a viewer stop scrolling in under 2 seconds: a simple action with a
  surprising problem coming, e.g. "If you put wings on a metal tube, it still won't fly." / "If you build a house on dirt,
  it slowly sinks." / "This engine explodes three thousand times a minute, on purpose."
- Shapes:
  - **A. "If you…" chain (45-58 s, main).** "If you <simple thing>, you get <result>." then 4-6 rounds of
    "But <problem>." → "So, <real fix>." Finish with "You see, <hidden science>." + "That's why <everyday thing>."
  - **B. "This <machine> just <amazing thing>" (25-35 s).** Wow line, 4-6 how-it-works lines, one surprising number.
- Read `topics.md`: never repeat a topic, no two on the same theme back to back.
- Use WebSearch ONLY (never WebFetch): confirm every fact and number on at least 2 reliable sources (.gov,
  manufacturers, engineering references, encyclopedias, major outlets) from the search results. List them in `script.json` "sources". Original script only.
- **Pick topics you can SHOW realistically in Blender**: things built from simple strong shapes with great materials
  (concrete, steel, glass, rubber, asphalt, wood, water, snow, light). Very complex hero objects (a whole car, a whole
  airliner) only if a free model exists (see 3.4) or the shot can be close-up / part-only / silhouette at night.
- Skip: gore, crashes played for drama, tragedies, politics, living private people, brands as characters.

## 3. Make the video (Blender on the owner's PC)

Reference (approved, copy its approach): `reference/road-lines-blender/` (`script.json`, `shots.py`, `test-stills.jpg`)
and the kit `blender/kit.py` (helpers: `new_scene`, `world_hdri`, `sun`, `light`, `aim`, `camera` (keyframed path, DOF),
`mat_textured` (Poly Haven PBR with procedural fallback), `mat_simple`, `mat_paint`, `mat_glass`, `mat_emit`, `mat_rain`,
`box`, `plane`, `sphere`, `cyl`, `dup`, `road`, `trees`, `car_lights`, `rpm`, `parent_all`, `import_model`, `key`,
`key_socket`, `key_light`; time `t` is seconds from the shot start).

1. Voice and timing: `bash <skill>/scripts/new_video.sh deep-dive <slug>` (only for its voice/mix tools), write
   `script.json` (voice `am_michael`, speed 1.0, music `bed`, gap 0.16, every line with `caps` chunks of 3-6 words split
   by `|`, numbers spoken in `text`, digits in `caps`; optional `"sfx": [{"at": 0.4, "type": "pop"}]` per line), run
   `<skill>/scripts/py <skill>/scripts/voice.py <proj>`, then `words.py <proj>`. Then
   `python3 blender/build_job.py cues --proj <proj>` and `<skill>/scripts/py <proj>/tools/mix.py <proj>` → `data/mix.wav`.
   Valid sfx types: whoosh slide pop plop gulp boing bubbles sizzle sparkle thud slam tock zip alarm.
2. Write `<proj>/shots.py`: one function `S00(a, b)`, `S01(a, b)` … per script line and `SHOTS = [...]` (the kit checks the
   count). Each shot builds its own scene: realistic materials, an HDRI world (`kloofendal_48d_partly_cloudy_puresky` day,
   `kloofendal_overcast_puresky`, `dikhololo_night` night, `snowy_field`, `studio_small_09` for cut-away/macro studio
   shots, `qwantani_dusk_2_puresky`, `moonless_golf`), a sun at ~2.2 (the puresky HDRIs already contain a sun: keep the
   HDRI ~0.8), slow camera moves, shallow focus for close-ups (fstop 2-4).
   Lessons learned (road-lines):
   - Frame is 9:16 and narrow: keep the subject near the camera's line of sight; low, close cameras look most real.
   - Wide aerial shots of fields with blob trees look like a game: prefer low cinematic angles, close-ups, macro, night.
   - Lights mounted near the camera reflect in wet roads as bright blobs: set `light.visible_glossy = False`.
   - Spot lights point along their local -Z: rotation X=+83° aims them forward (+Y) and slightly down.
   - Keep the caption band (y 1230-1380 of 1920) free of the key subject.
   - Avoid huge object counts with glass (slow); a few hundred small instances is fine.
2b. **A person in the video (owner's wish, 2026-11-21): the viewer should feel he is the one there.** Put a realistic
   human (`blender/character.py`, MPFB/MakeHuman, CC0) in at least 3-5 shots, doing what the line says: standing by the
   machine, pointing at the part being explained, holding or using the tool, walking up to it, looking at it. Like the
   Mildly Elsewhere references (a worker with a cap and a shovel on the beach).
   - `arm = person('Worker', loc=(x, y, 0), rot_z=math.radians(a), outfit='worker'|'casual'|'office', stance='relax')`
     (faces -Y at rot_z 0). Then `pose(arm, t, STANCES['point_r'])` / `pose(arm, t, {...bone: (x, y, z)})` to animate,
     `walk(arm, t0, t1)` while you keyframe `arm.location` yourself, `hold(arm, prop, 'wrist.R', offset, rot)` for tools.
     Bone axes are documented at the top of `STANCES` in character.py. Keep moves slow and small: big fast limb moves
     look robotic. Medium/wide framing (full body or waist up) looks most real; avoid face close-ups.
   - People exist ONLY on the PC (MPFB is installed in the PC's Blender, not in the cloud venv: `person()` returns None
     here). So for shots with people, after the cloud stills, check them ON THE PC:
     `python3 blender/build_job.py stills --proj <proj> --shots <proj>/shots.py --name <job>-stills --out /mnt/user-data/outputs/jobs/<job>-stills --sel 2,5`
     → commit the printed files + `ready.txt` → wait for `done.txt` (~1-2 min) → stage `test/shotNN.jpg` and look
     (hands not inside the body or props, feet on the ground, clothes OK, face not creepy). Fix and repeat once.
3. Test stills in the cloud, ALWAYS before sending a job: stage the textures/HDRIs you use from `D:\Ai Video Edit\assets`
   with `device_stage_files` (they land in `/mnt/user-data/uploads/Ai Video Edit/assets`), copy `data/lines.json` to
   `<proj>/timing.json`, then
   `~/bvenv/bin/python blender/kit.py -- --proj <proj> --assets "/mnt/user-data/uploads/Ai Video Edit/assets" --scale 0.25 --samples 16 --test --cpu`
   → `<proj>/test/shotNN.jpg` (middle frame of each shot). Tile them into one sheet and LOOK: realistic? subject in frame?
   matches the line? nothing blown out or black? Fix and re-test only the changed shots (`--shots 3,7`).
4. New assets: textures/HDRIs from Poly Haven (CC0) are downloaded ON THE PC: make a small job whose `job.bat` runs
   `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Ai Video Edit\_claude\fetch-assets.ps1" -Tex "id1,id2" -Hdri "id3" > result.txt`
   (see job mechanics below), wait for `done.txt`, then stage them for tests. Free 3D models (NASA 3D Resources on GitHub
   = public domain .glb; check the license of anything else; CC0/public domain only) can be downloaded here and committed
   to `D:\Ai Video Edit\assets\models\`; load with `import_model('models/x.glb', ...)`.
5. Job mechanics (the PC helper runs any `D:\Ai Video Edit\jobs\<name>\job.bat` once a `ready.txt` exists, then writes
   `done.txt`). First write `<proj>/meta.json` (UTF-8):
   `{"title": "...", "description": "...", "tags": [...], "date": "<D Mon YYYY in IST, e.g. 25 Nov 2026>", "time": "<HH:MM IST, 15-min step>", "telegram_caption": "<title>\nYouTube par publish: <IST> IST (<ET> ET)"}`
   (title ≤ 60 chars, curiosity hook, max 1 emoji; description = 2-3 sentence teaser, Sources line, subscribe line with
   @WaitThatReallyHappenedUS, then `#shorts` + 4-6 hashtags; 8-12 tags; `date`/`time` = the IST slot from 1b, e.g. "27 Nov 2026"
   + "19:00" or "01:00"). Then
   `python3 blender/build_job.py job --proj <proj> --shots <proj>/shots.py --name <job> --out /mnt/user-data/outputs/jobs/<job> --meta <proj>/meta.json`
   (job name e.g. `2026-11-23-1200-<slug>`). It prints the JSON file list: `device_commit_files` it (≤ 40 files per call is
   fine), check sizes with `device_list_dir`, then commit `ready.txt` LAST (any small file). Staged files must live under
   `/mnt/user-data/outputs`. If a commit seems to write an old version, copy the file to a NEW name and commit that.
6. **Do NOT wait for the render** (that waiting used most of the owner's usage). The PC renders (25-50 min), then by
   itself uploads to YouTube Studio with the schedule (section 4) and sends the video + link to the owner's Telegram.
   Right after `ready.txt` is committed, append to `topics.md` on main:
   `- <slot IST> · <title> · PENDING-PC <job> · <one-line topic> · <main source>`, pull --rebase, push, report, END.
   The next run checks the result (1a).
7. So the quality gate is BEFORE the job: the cloud test stills (step 3) and, for shots with people, the PC stills job
   (2b) must look right. Only send a job you would be happy to see published.
8. Usage: don't re-read big files, keep sheets small, look only at changed frames, never poll a render.

## 4. Upload — FREE and automatic, done by the PC itself (since 2026-11-22)

No Zapier (trial ends 2026-12-03, owner can't pay) and no own Google API project (that would lock uploads to private).
`D:\Ai Video Edit\_claude\uploader\upload.mjs` (Playwright + the PC's Chrome, own profile `_claude\yt-profile`, signed in
by the owner once with `login.bat`) opens YouTube Studio for channel UCEbKzlOb63pBdElUTl9wRvg (it checks the channel id
and stops if different), uploads `final.mp4`, fills title/description/not-made-for-kids/tags, schedules at
meta `date` + `time` (IST, Studio's local time zone), confirms ("will be set to public on ..."), writes
`upload-result.json` {ok, id, url, telegram} and sends `share.mp4` + caption + link to the owner's Telegram. On failure it
sends a Telegram text "UPLOAD FAILED ...". The render job's `job.bat` calls it automatically when `meta.json` is in the
job folder. Step screenshots: `jobs\<job>\upload-shots\`.
After a good upload AND `TELEGRAM OK` it writes `jobs\_uploaded\<job>.json` and deletes the job folder ~90 s later (the
video lives on YouTube + Telegram; nothing of it stays on the PC). A failed job keeps its folder for a retry. Proven 2026-11-22 (road-lines, xoWM3B7zIRo).

### 4a. QA before the upload — Qwen3-VL-8B on the PC (since 2026-11-22, $0, no Claude usage)
`job.bat` runs `D:\Ai Video Edit\_claude\qa\qa.mjs <job>` between the render and the upload:
1. ffmpeg hard checks: length 10-180 s, black screen > 1.5 s, no sound (mean < -45 dB). Any of these → `qa-block.txt`,
   NO upload, Telegram text "QA BLOCKED ...".
2. Qwen3-VL-8B (Ollama, `E:\Ollama`, model `qwen3-vl:8b-instruct` (the plain `qwen3-vl:8b` tag is the Thinking one: it ignores think:false and returns nothing, so it was removed)) looks at one frame per narration line (max 12)
   with that line's words, and returns `describe / matches_narration / problems / severity`. Advice only — it never stops
   the upload (an 8B model has false alarms); its one-line summary is added to the Telegram caption and the full report
   is kept in `jobs\_uploaded\<job>-qa.json` for section 1a.
Owner's teaching: `_claude\qa\channel-rules.txt` (his rules, plain text, sent with every frame — never overwrite it
without asking; you may ADD a line for a recurring problem you fixed) and `_claude\qa\examples\*.jpg` (max 2 "good look"
pictures sent as style reference).
Ollama is started outside the job's process tree (WMI) and the model is unloaded after the last frame (`keep_alive 0`), so
the GPU is free again. Repo copy: `blender/pc-helper/qa/qa.mjs`.

Fallbacks, only if the PC uploader keeps failing: YouTube Studio through the built-in browser by hand (studio.youtube.com
is allowed; file via `ytcp-uploads-file-picker input[type=file]` + fetched raw URL), or Zapier while its trial lasts.

## 5. Report

End with a short message in Hindi written in Roman letters: the title, the planned publish time (IST), that the PC will upload it and send it on Telegram by itself after the render (~25-50 min), what 1a found about
earlier videos, and anything that went wrong.

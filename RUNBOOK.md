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
3. Load the `anthropic-skills:faceless-shorts` skill and run its `scripts/setup.sh` (only the Kokoro voice, ffmpeg and
   Python are needed; Whisper may fail to download, that is fine).
4. For test stills: `python3.11 -m venv ~/bvenv && ~/bvenv/bin/pip install bpy==4.5.16` (Blender as a Python module, same
   version as the PC's Blender 4.5.16).
5. PC layout (all under `D:\Ai Video Edit`): Blender `_tools\blender\blender-4.5.16-windows-x64\blender.exe`; ffmpeg
   `C:\Users\Mukesh\.clip-studio\ffmpeg\bin\ffmpeg.exe`; CC0 textures/HDRIs in `assets\` (one folder per texture with
   Diffuse/nor_gl/Rough jpgs, HDRIs as `<id>.hdr`; `device_list_dir` it to see what is there); helper scripts in `_claude\`;
   jobs in `jobs\<name>\`. GPU: RTX 5060 8 GB (OptiX), Cycles ≈ 1.1-2.5 s per 1080x1920 frame at 48 samples.

## 1a. Pending uploads first

If `pending/*.json` exists (a finished video whose upload failed, e.g. Zapier "throttled" = YouTube's daily upload
quota, which resets at midnight Pacific = 13:30 IST), handle the oldest one BEFORE making a new video: its MP4 is on the
git branch named in the file (and on the PC). Give it the earliest free slot (section 1b, must be >= 2 h ahead), upload
it exactly like section 4 (use that branch's raw URL) (same metadata), send it to Telegram (4b), log it in topics.md (replace its NOT UPLOADED line),
delete the pending json, push. If the upload is throttled again, stop the run (don't make a new video), report it.
Then continue with a new video only if this run still has time.

## 1b. Pick the publish slot (videos are made ONE DAY AHEAD and scheduled on YouTube)

- TWO videos per day. Publish slots are 12:00 and 19:00 **America/New_York** time, every day.
- Take the earliest slot that is at least **20 hours after now** and is not already used by a line in `topics.md`.
  (Runs start at about 06:15 and 12:15 New York time, so the pipeline always stays about one day ahead.)
- Convert the slot to UTC (`TZ=America/New_York date -d ... -u +%Y-%m-%dT%H:%M:%SZ`, mind daylight saving time).
  That UTC time is `PUBLISH_AT`.

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
   `done.txt`): `python3 blender/build_job.py job --proj <proj> --shots <proj>/shots.py --name <job> --out /mnt/user-data/outputs/jobs/<job>`
   (job name e.g. `2026-11-23-1200-<slug>`). It prints the JSON file list: `device_commit_files` it (≤ 40 files per call is
   fine), check sizes with `device_list_dir`, then commit `ready.txt` LAST (any small file). Staged files must live under
   `/mnt/user-data/outputs`. If a commit seems to write an old version, copy the file to a NEW name and commit that.
6. Wait: poll `device_list_dir D:\Ai Video Edit\jobs\<job>` with foreground `sleep 540` between checks until `done.txt`
   exists (≈ 25-50 min). Never end the turn while it runs. `job-log.txt` there shows progress; `result.txt` says
   `RENDER_OK`. If it failed: read `job-log.txt`, fix, make a new job name, run again (once).
7. QA: `device_stage_files` `jobs\<job>\final.mp4`, ffprobe it (1080x1920, ≤ 59 s, audio), make a contact sheet every
   2 s and LOOK. One bad shot: fix it, re-test it, and send a NEW job with a new name (the job deletes its frames after a good
   render, so the whole video is rendered again; ~25-50 min).
8. Usage: don't re-read big files, keep sheets small, look only at changed frames.

## 4. Upload — FREE, through YouTube Studio in the PC's built-in browser (since 2026-11-22)

Zapier's trial ends 2026-12-03 and the owner can't pay, and an own Google API project would lock every upload to
private. So upload exactly like a person would, in YouTube Studio inside the Claude desktop app's built-in browser on
the owner's PC (already signed in to the owner's Google account; studio.youtube.com is allowed for the browser pane
permanently). Proven on 2026-11-22 with the jet-tires Short (https://youtube.com/shorts/nXDqd75z3fM).

1. Host the MP4: copy the staged `final.mp4` to `video.mp4`, `git checkout --orphan upload-tmp`, remove everything from
   the index, add only `video.mp4`, commit, `git push -f origin upload-tmp:upload`, `curl -sSI` the raw URL
   `https://raw.githubusercontent.com/mukeshbhaidoller-blip/wtrh-shorts/upload/video.mp4` (200, right size).
2. Load the browser tools (ToolSearch `mcp__remote-devices__Claude_Browser__`, max 30). `preview_start`
   `https://studio.youtube.com/channel/UCEbKzlOb63pBdElUTl9wRvg/videos/upload`. With `javascript_tool` check
   `ytcfg.get('CHANNEL_ID') === 'UCEbKzlOb63pBdElUTl9wRvg'` and that the page text contains "Wait, That Really Happened".
   If not: STOP, upload nothing.
3. `find` "Upload videos" → click it (ref). Then `javascript_tool`:
   ```js
   await new Promise(r=>setTimeout(r,2000));
   const inp = document.querySelector('ytcp-uploads-file-picker input[type=file]');
   const b = await (await fetch('<raw URL>?v=' + Date.now())).blob();
   const dt = new DataTransfer(); dt.items.add(new File([b], '<title>.mp4', {type: 'video/mp4'}));
   inp.files = dt.files; inp.dispatchEvent(new Event('change', {bubbles: true})); b.size
   ```
   (Only ONE upload: never run this twice. The details form appears after a few seconds; `read_page` filter
   interactive shows it.)
4. Details: title textbox ("Add a title that describes your video") → click, `ctrl+a`, type the title (≤ 60 chars,
   curiosity hook, 1 emoji max). Description textbox ("Tell viewers about your video") → click, `ctrl+a`, type it
   (2-3 sentence teaser, Sources line, subscribe line with @WaitThatReallyHappenedUS, `#shorts` + 4-6 hashtags).
   `find` "not made for kids" → `scroll_to` it, take a screenshot and click the radio CIRCLE by coordinate (a ref click
   on the label did not select it), then `zoom` to confirm it is filled. Click "Show more" → Tags textbox → type the
   8-12 tags joined by commas, ending with a comma. Category should already say Education (fix it if not).
5. Click **Next** (bottom right) 3 times (wait 2 s between) → Visibility. `find` "Schedule" → click the "Schedule"
   header. Time zone must be "(GMT+0530) Local Time" (IST). Convert the slot to IST (12:00 ET = 22:30 IST and
   19:00 ET = 05:30 IST the next day while US is on EST). Click the date box and click the day in the calendar; click
   the time box, `find` the option "HH:MM" (15-minute steps) and click it. Zoom/screenshot to confirm date + time.
6. Click the **Schedule** button (bottom right). Wait 5 s; `javascript_tool`: the page text must contain
   "Video scheduled" and a `youtube.com/shorts/<id>` link — that id is the video id. Close the dialog.
7. If the built-in browser is unreachable or Studio fails twice: fall back to Zapier (`youtube_upload_video`,
   connection_id 02322a7b-7e7d-8a1a-9aad-6c9bc6a79dc3, privacy private + publish_at) only while the Zapier trial still
   works; otherwise save the video as pending (section 1a) and report.
8. Append one line to `topics.md` on `main`:
   `- <slot, e.g. 2026-11-22 13:00 ET> · <title> · https://youtube.com/shorts/<id> · <one-line topic> · <main source>`,
   then `git pull --rebase` and push `main` (retry once if another run pushed first).

## 4b. Send the same video to the owner's Telegram (right after it is scheduled)

1. Only after step 4 confirmed the schedule. Check `D:\Ai Video Edit\_claude\telegram-ok.txt` exists (owner ran
   telegram-setup once). If it doesn't, skip this and say so in the report.
2. `python3 blender/build_job.py tg --name <job>-tg --render-job <job> --out /mnt/user-data/outputs/jobs/<job>-tg --caption "<text>"`
   with caption (≤ 1000 chars): the title, then "YouTube par publish: <IST time> IST (<ET time> ET)", then
   `https://youtu.be/<id>`. Commit the two printed files, then `ready.txt` last. Wait ~1-2 min for `done.txt`; stage
   `result.txt`: it must say `TELEGRAM OK` (it never contains the token). If it failed, mention it in the report.

## 5. Report

End with a short message in Hindi written in Roman letters: the title, the link, the scheduled publish time in India
time (IST) and US Eastern time, whether Telegram got it, and anything that went wrong.

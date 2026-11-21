# RUNBOOK: one new Short for "Wait, That Really Happened"

Each scheduled run makes ONE brand-new Short from start to finish and uploads it. Follow every step in order.
Do not ask the owner anything during a run: nobody is watching. If a step fails in a way you cannot fix, do NOT
upload; finish with a short note (in Hindi written in Roman letters) saying what failed.

## Fixed facts (never change these)

- Channel: **Wait, That Really Happened**, handle `@WaitThatReallyHappenedUS`, channel ID `UCEbKzlOb63pBdElUTl9wRvg`.
- Zapier YouTube connection for this channel: `connection_id = 02322a7b-7e7d-8a1a-9aad-6c9bc6a79dc3`.
  ALWAYS pass this connection_id. The Zapier default YouTube connection is a DIFFERENT channel (The Fandom Room):
  never upload without the connection_id.
- File host: this repo, branch `upload` (force-pushed, holds only the current video). Public URL:
  `https://raw.githubusercontent.com/mukeshbhaidoller-blip/wtrh-shorts/upload/video.mp4`
- Log of everything already uploaded: `topics.md` on branch `main`.

## 1. Setup

1. Attach the repo with push access (`add_repo` owner `mukeshbhaidoller-blip`, repo `wtrh-shorts`, access `push`), clone it to
   `/home/claude/wtrh-shorts` (`git clone --depth 1 ...`, long timeout), set git user.name `mukeshbhaidoller-blip`,
   user.email `mukeshbhaidoller-blip@users.noreply.github.com`.
2. Load the `anthropic-skills:faceless-shorts` skill and read `styles/tall-tale/STYLE.md` in full.
3. Run the skill's `scripts/setup.sh`. Whisper may fail to download (Hugging Face is blocked here): that is fine, `words.py`
   falls back to spreading words inside the exact voice line times. Node, ffmpeg, Chrome, Kokoro voice must be OK.

## 1b. Pick the publish slot (videos are made ONE DAY AHEAD and scheduled on YouTube)

- TWO videos per day. Publish slots are 12:00 and 19:00 **America/New_York** time, every day.
- Take the earliest slot that is at least **20 hours after now** and is not already used by a line in `topics.md`.
  (Runs start at about 06:15 and 12:15 New York time, so the pipeline always stays about one day ahead.)
- Convert the slot to UTC (`TZ=America/New_York date -d ... -u +%Y-%m-%dT%H:%M:%SZ`, mind daylight saving time).
  That UTC time is `PUBLISH_AT`.

## 2. Pick the topic (NEW FORMAT from 2026-11-21: "how things are built / how they work")

The owner's reference channel style: realistic-looking 3D explainers that solve an everyday engineering puzzle as a
chain of problems and fixes. Two shapes, pick one per video:
- **A. "If you…" chain (45-58 s, the main one).** Line 1: "If you <do a simple thing>, you get <result>." Then repeat:
  "But <problem>." → "So, <the real-world fix>." 4-6 rounds, each fix a TRUE engineering detail. End with
  "You see, <the hidden science in one sentence>." + "That's why <something viewers see every day>."
  Example (already made, do not repeat): `reference/road-lines/script.json` (painted road lines → thermoplastic →
  glass beads → rain → raised reflectors → snowplows → recessed pockets).
- **B. "This <machine> just <did something amazing>" (25-35 s).** Line 1 states the wow moment, then 4-6 lines of how
  it works, then one surprising number to finish.
- Topics: things American viewers see or use: highways, bridges, dams, skyscrapers, airports, planes, trains,
  stadiums, farms, grain silos, ski resorts, theme parks, fire trucks, garbage trucks, ships and ports, national
  parks, gas stations, drive-thrus, etc. Set it in the USA when there is a place in the story.
- Read `topics.md`. Never repeat a topic, and avoid two topics on the same theme back to back.
- Use WebSearch: confirm every engineering fact and number on at least 2 reliable sources (DOT / .gov manuals,
  manufacturers, encyclopedias, major outlets). List them in `script.json` "sources". Write ORIGINAL scripts: never copy
  another creator's lines or their exact sequence of steps.
- Skip: gore, accidents played for drama, tragedies, politics, living private individuals, brands as characters.

## 3. Make the video (Deep Dive 3D engine, reference-style captions)

1. `bash <skill>/scripts/new_video.sh deep-dive <slug>`; read `<skill>/styles/deep-dive/STYLE.md`.
2. Copy the caption look from `reference/road-lines/captions.js` into `src/core/captions.js` (plain white sentence-case
   text, soft shadow, up to 2 lines, y 1300, NO yellow word, NO pop). In `script.json` give every line `caps` chunks of
   3-6 words split with `|`, e.g. `"If you paint a white line | on a road, you get a lane."`.
3. `script.json`: voice `am_michael`, speed 1.0, music `bed`, gap 0.16. ~140-165 words for shape A, ~80 for shape B.
   Then `voice.py`, then `words.py`. Numbers as spoken in `text`, digits in `caps`.
4. Build the world in `src/core/<topic>.js` and the shots in `src/shots.js`, one shot per line (two for a long line),
   cut with `cut(i)`, key moments on `Wd('word', i)`. Start from `reference/road-lines/road.js` + `shots.js`
   (highway with day/dusk/night/snow modes, rain, car, trucks, worker in hi-vis, macro scene). People are `Human`
   from `core/human.js` (posable). Keep looks realistic and calm: daylight, real-world colors, soft shadows, small
   dark info pills only for one key number per shot.
   Lessons learned:
   - **The frame is vertical and very narrow.** Visible horizontal half-width ≈ 0.18 × distance at fov 36, 0.21 at
     fov 40, 0.23 at fov 45, 0.26 at fov 50. Keep every subject near the camera's line of sight. Macro shots: keep the
     camera ~2-3 m from a ~0.5 m subject at fov 45, or the frame fills with one blown-out surface.
   - Macro/close scenes: low `environmentIntensity` (~0.1), modest spotlights (~25), bloom ≤ 0.4 with threshold ≥ 0.8.
   - Night: bloom ~0.55, threshold ~0.7; emissive lines ≤ ~1.0, or the whole frame glows.
   - Valid cues: whoosh slide pop plop gulp boing bubbles sizzle sparkle thud slam tock zip alarm inhale heartbeat.
     Any other name crashes `mix.py` unless you add it to BOTH `FX` and `LEVEL`.
   - Keep key subjects out of the caption band (y 1230-1380).
5. With `SOFTWARE_GL=1 QS='&res=0.5&aa=0&shadow=1024'`: `node tools/capture.mjs check` (CHECK OK), `cues`,
   `<skill>/scripts/py tools/mix.py .`, then `sheet review/all.jpg 1.5 8` and LOOK at it. Fix every washed-out, empty,
   off-frame or mistimed shot; re-check those times with `frames review/g "t1,t2,..."`.
6. Final render (~45-50 min): in the background
   `SOFTWARE_GL=1 QS='&res=0.7&aa=0&shadow=1024' FPS=24 node tools/capture.mjs video renders/final.mp4 > /tmp/render.log 2>&1`
   and poll it with foreground `sleep 540` checks until the log prints the output path. Never end the turn while it runs.
7. Check the MP4: ffprobe shows 1080x1920, duration ≤ 59 s, audio present; grab 9 frames into one strip and look.
8. To save usage: do not re-read big files you already have, keep sheets at 1.5 s steps, and look only at frames you
   changed.

## 4. Upload

1. `git checkout --orphan upload-tmp`, remove everything from the index, add only `video.mp4` (the final MP4), commit,
   `git push -f origin upload-tmp:upload`. Then `curl -sSI` the raw URL: must be HTTP 200 and the right content-length.
2. Verify the channel: Zapier YouTube `youtube_make_api_get_request` GET `https://www.googleapis.com/youtube/v3/channels`
   `part=snippet, mine=true` with the connection_id above. The id MUST be `UCEbKzlOb63pBdElUTl9wRvg`; otherwise STOP.
3. Upload: Zapier `youtube_upload_video` (selected_api `YouTubeV4CLIAPI`, action `upload_video`) with the connection_id,
   params: `video` = raw URL, `title` (≤ 60 chars, curiosity hook, 1 emoji max, no clickbait lies), `description`
   (2-3 sentence teaser of the puzzle and its fix, Sources line, subscribe line with @WaitThatReallyHappenedUS,
   then `#shorts` + 4-6 hashtags), `tags` (8-12), `category_id` "27", `privacy_status` "private",
   `publish_at` = PUBLISH_AT (ISO UTC, e.g. 2026-11-22T13:00:00Z), `made_for_kids` "false",
   `embeddable` "true", `notify_subscribers` "true", `default_language` "en", `default_audio_language` "en",
   `license` "youtube". (YouTube makes a private video with publishAt go public by itself at that time.)
   - If Zapier rejects `publish_at`: upload with `privacy_status` "private" and no publish_at, then call
     `youtube_make_api_mutating_request` PUT `https://www.googleapis.com/youtube/v3/videos?part=status` with body
     `{"id":"<id>","status":{"privacyStatus":"private","publishAt":"<PUBLISH_AT>","selfDeclaredMadeForKids":false}}`.
   - If that also fails, set the video public with the same PUT (`"privacyStatus":"public"`, no publishAt) and say so
     in the report.
4. Check with GET `videos?part=status,processingDetails&id=<id>` that `status.publishAt` equals PUBLISH_AT (or that it
   is public, in the fallback case) and that the upload was not rejected.
5. Append one line to `topics.md` on `main`:
   `- <slot, e.g. 2026-11-22 13:00 ET> · <title> · https://youtu.be/<id> · <one-line topic> · <main source>`,
   then `git pull --rebase` and push `main` (retry once if another run pushed first).

## 5. Report

End with a short message in Hindi written in Roman letters: the title, the link, the scheduled publish time in India
time (IST) and US Eastern time, and anything that went wrong.

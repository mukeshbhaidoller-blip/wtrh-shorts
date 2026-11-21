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

## 2. Pick the story

- Read `topics.md`. Never repeat a story, and avoid two stories on the same theme back to back.
- The story must be **TRUE and set in the UNITED STATES** (American people, towns, companies, laws, history), for a US
  audience. Funny, clever or "wait, what?": loopholes, backfires, odd laws, genius hacks, weird inventions, bizarre
  true events. Examples of the KIND only (always check facts first, never assume): a US town that elected an animal as
  mayor, a US law that backfired, an American company promotion that went wrong, a US inventor's accidental discovery.
- Use WebSearch: confirm every fact on at least 2 reliable sources (museums, encyclopedias, major outlets, .gov). Use
  the numbers most sources agree on. List them in `script.json` "sources".
- Skip: gore, deaths played for laughs, tragedies, currently contested politics, living private individuals, crimes
  against named private people, anything medical-scary, copyrighted characters or brands as characters.

## 3. Make the video (Tall Tale 3D style)

1. `bash <skill>/scripts/new_video.sh tall-tale <slug>`.
2. Write `script.json`: 40-55 s narration (~130-165 words), voice `am_michael` speed 1.05, music `bounce`. Shape: open on
   the most surprising fact, then "See, ..." rewind, step-by-step, punchline that flips the start. One line = one cut.
   Write numbers as spoken; use `caps` to show digits ("20,000"). Check caps chunks: when a chunk's first word is a
   number written differently from the spoken word, the next chunk must start on a word that IS spoken, or the caption
   will lag (see `reference/hanoi-rats/script.json`).
3. `voice.py`, then `words.py`.
4. Write `src/shots.js` (and new kit pieces in `src/core/`) for THIS story. Study `reference/hanoi-rats/` (shots.js,
   rats.js): it is a full working example (overlays: REW badge, paper notice card, stamp, counter, "?" pop).
   Lessons learned:
   - **The frame is vertical and very narrow.** Horizontal half-width visible ≈ 0.18 × distance at fov 36, ≈ 0.23 ×
     distance at fov 44, ≈ 0.26 × distance at fov 50. Put every subject of a shot near the camera's line of sight
     (arrange people in depth, not side by side). Check each shot in the sheet; anything off-frame is a bug.
   - Interiors: keep the camera inside the walls (interior w = width, x within ±w/2, z < 2).
   - New sound effect names must be added to BOTH `FX` and `LEVEL` in `tools/mix.py` (see reference mix.py `rewind`).
   - Valid cues: whoosh slide pop plop gulp boing bubbles sizzle sparkle thud slam tock zip alarm inhale heartbeat ding
     chirp chug stamp (+ rewind if you copy it).
   - Keep key subjects out of the caption band (y 1250-1550 of 1920).
5. In the project, with `SOFTWARE_GL=1 QS='&res=0.6&aa=0&shadow=1024'`: `node tools/capture.mjs check` (CHECK OK),
   `cues`, `<skill>/scripts/py tools/mix.py .`, then `sheet review/all.jpg 1 9` and LOOK at it. Fix every framing,
   timing and caption problem; re-render the sheet until it is clean. Look at 3-4 key frames full size too.
6. Final render (~35 min): run in the background
   `SOFTWARE_GL=1 QS='&res=0.7&aa=0&shadow=1024' FPS=24 node tools/capture.mjs video renders/final.mp4 > /tmp/render.log 2>&1`
   and poll it with foreground `sleep 540` checks until the log prints the output path. Never end the turn while it runs.
7. Check the MP4: ffprobe shows 1080x1920, duration ≤ 59 s, audio present; grab 9 frames into one strip and look.

## 4. Upload

1. `git checkout --orphan upload-tmp`, remove everything from the index, add only `video.mp4` (the final MP4), commit,
   `git push -f origin upload-tmp:upload`. Then `curl -sSI` the raw URL: must be HTTP 200 and the right content-length.
2. Verify the channel: Zapier YouTube `youtube_make_api_get_request` GET `https://www.googleapis.com/youtube/v3/channels`
   `part=snippet, mine=true` with the connection_id above. The id MUST be `UCEbKzlOb63pBdElUTl9wRvg`; otherwise STOP.
3. Upload: Zapier `youtube_upload_video` (selected_api `YouTubeV4CLIAPI`, action `upload_video`) with the connection_id,
   params: `video` = raw URL, `title` (≤ 60 chars, curiosity hook, 1 emoji max, no clickbait lies), `description`
   (2-3 sentence story teaser, "This is a true story.", Sources line, subscribe line with @WaitThatReallyHappenedUS,
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

# A/B style test (owner's wish, 2026-11-23): 4 videos, ONE new option each, then the owner picks

Each new video run takes the FIRST row whose `job` is empty, uses its settings, and writes its job name + publish slot in
that row (same commit as topics.md). When all 4 rows are filled, make videos the normal ("classic") way until the owner
says which option(s) to keep — then make that the default in RUNBOOK and delete this file.
Control video (old style, for comparison): the extra run of 23 Nov morning.

| test | option | what to set | job | slot |
|---|---|---|---|---|
| 1 | Kahani + beech caption | script.json `"style": "mid"`; write the script as a "you" problem → fix chain ("If you… / But… / So you… / But then… / So you…", a new problem every 5-8 s, each fix adds something visible) ending "…and you've built <thing>." Every caption chunk has ONE `*keyword` (it turns yellow). | 2026-11-25-0100-roof-build | 25 Nov 01:00 IST |
| 2 | Bade keyword + sound | `"style": "pops"`; every caption chunk that holds the key noun/number gets `*keyword` (aim 6-10 per video: names, numbers, the thing being built). They pop big and yellow on the word with a pop SFX. | 2026-11-25-1900-rail-track | 25 Nov 19:00 IST |
| 3 | Music hatao, SFX badhao | `"style": "nomusic"` AND `"music": "none"` (BEFORE mix.py); add `*keyword` on 6-10 chunks (they get a pop) and per-line `"sfx"` for real actions (thud, slam, zip, sizzle…). The mix is loudness-normalised to -15 LUFS. |  |  |
| 4 | Progress board | `"style": "hud"` + `"hud": {"title": "<THING> BUILD", "steps": [["<step 1>", <line index>], …]}` (3-6 steps, each ticks at the start of that line, with a sparkle SFX). Pick a topic where something is built step by step. |  |  |

In meta.json set `"telegram_caption": "TEST <n>/4 · Option: <option>\n<title>"` so the owner knows which one he is watching
(the YouTube title/description stay normal). Mention the test number in the Hindi report.

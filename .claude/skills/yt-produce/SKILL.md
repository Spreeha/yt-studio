---
name: yt-produce
description: Take raw footage in videos/<slug>/ to a finished final.mp4, Shorts, thumbnail options and a ready-to-paste YouTube package. Use when the creator has recorded a video and says produce, edit, cut, or package it. Never uploads.
---

# yt-produce <slug>

**Where to work:** this skill lives in the studio folder, `~/Studio/yt-studio` (tools/install_global_skills.sh rewrites this path to wherever you cloned it). Before anything else, `cd` there (if that folder is missing, say so and stop) and read its CLAUDE.md and brand.json. All paths below are relative to that folder.

Raw footage in, deliverables out. Claude is the editor; FFmpeg cuts, Remotion renders.
Read CLAUDE.md first for the layout, the rules and the three timelines (raw / rough cut / final).
Set up the task list with the stages below so the creator can see progress.

## 0. Check inputs
- `videos/<slug>/raw.*` exists (one file; if several clips, ask whether to join them in order with
  ffmpeg concat into `work/raw-joined.mp4` and use that as raw).
- `videos/<slug>/script.md` is optional but makes step 2 much better.
- `ffprobe` the raw: note duration, resolution, fps, whether it is HDR (`color_transfer` smpte2084 or
  arib-std-b67). If HDR, warn once that colours may look washed out and suggest turning off HDR video
  in the phone's camera settings for next time.

- **Orientation decides the mode.** Height > width (after rotation metadata) = **Short mode**: the whole
  video is one Short. No intro, outro, lower third, chapters or Shorts cut-downs; skip steps 6-7's
  long-form parts. Width > height = **Long mode**, all steps.

## 1. Transcribe raw
`python3 tools/transcribe.py videos/<slug>/raw.<ext> videos/<slug>/work/raw --no-words`

## 2. Build the cut list (Claude's edit)
1. `python3 .claude/skills/yt-edit/deadair.py videos/<slug>/work/raw.srt --json > videos/<slug>/work/cuts.json`
2. Read raw.srt end to end. Add `"kind": "MANUAL"` cuts (raw seconds, with a `why`) for:
   - repeated takes: keep the LAST complete take of a line, cut the earlier ones
   - false starts, "wait, let me redo that", off-camera talk, the bit before they start and after they finish
   - if script.md exists: anything far off-script that adds nothing (flag, don't silently cut, when unsure)
3. `python3 tools/roughcut.py <raw> videos/<slug>/work/cuts.json --dry-run`
4. **Show the creator** in chat: runtime before -> after, counts by kind, and every MANUAL cut as
   `m:ss-m:ss  why`. Ask: "Good to cut, or change anything?" Accept plain-English changes
   ("keep the coffee tangent", "also cut 4:10 to 4:30"), edit cuts.json, show the new summary.
   If they are not there to answer, proceed with DEAD/FILLER/REPEAT cuts only and list the MANUAL ones
   you held back.

## 3. Rough cut and re-transcribe
- `python3 tools/roughcut.py <raw> videos/<slug>/work/cuts.json videos/<slug>/work/roughcut.mp4`
- `python3 tools/transcribe.py videos/<slug>/work/roughcut.mp4 videos/<slug>/work/roughcut`

## 4. Package (texts)
Use the pack skills on `work/roughcut.srt`, in the creator's voice (voice.md):
- Chapters: `python3 .claude/skills/yt-chapters/chapters.py videos/<slug>/work/roughcut.srt --json`.
  Add brand.introSec (2) to every chapter except the first, which must stay 0:00. Rename vague ones.
- `/yt-package`: 3 title + thumbnail-text pairings, linted. Thumbnail text 3-5 words; mark the accent
  word with *stars*.
- `/yt-seo`: description (first two lines carry the hook), worthwhile tags, the 3 queries it should win.
- Write `videos/<slug>/package/package.md`: titles (3), description with chapters pasted in, tags,
  pinned-comment draft, and a checklist: upload final.mp4, upload captions.srt (English), pick thumbnail,
  add end screen over the last 5 s, tick "Altered or synthetic content" ONLY if AI-generated realistic
  visuals or voice were used, tick paid promotion if it is a brand deal.

## 4b. Cards and animated graphics
Read roughcut.captions.json and decide where a graphic makes a point land faster than words alone.
Write them to `work/cards.json` in ROUGH CUT seconds, timed to the word that triggers them (start the
graphic on that word, never before it).

| Kind | Use it when | Example |
| --- | --- | --- |
| `logo` | a product, model or company central to the story is first named | `{"at": 4.2, "kind": "logo", "text": "KIMI K3", "img": "kimi.png"}` |
| `stat` | the speaker says one striking number (size, price, %, date). Counts up. | `{"at": 7.1, "kind": "stat", "value": 2.7, "suffix": "T", "label": "parameters"}` |
| `compare` | the speaker compares two to four things with numbers | `{"at": 12.0, "kind": "compare", "text": "$ per million tokens", "items": [{"label": "Kimi K3", "value": 15, "display": "$15"}, {"label": "Rival", "value": 50, "display": "$50"}]}` |
| `list` | the speaker counts things off ("three things", "first... second...") | `{"at": 20.5, "kind": "list", "text": "What changes", "items": ["Cost", "Speed", "Lock-in"]}` |
| `zoom` | a punchline, the key takeaway, or a deadpan aside: a quick punch-in | `{"at": 31.0, "dur": 1.5, "kind": "zoom", "scale": 1.12}` |
| `sticker` | a light, self-aware beat (the creator's humour, see voice.md): a small tilted tag | `{"at": 31.0, "dur": 2, "kind": "sticker", "text": "plot twist"}` |
| `section` | Long mode only: each chapter start after the first, 3 s | `{"at": 95.0, "dur": 3, "kind": "section", "text": "Data Science and Maths round"}` |

Rules:
- **Only real numbers.** `stat` and `compare` values must be exactly what is said (or what script.md
  states with a source). Never round up, estimate or invent; if unsure, use `logo` or nothing.
- **Pacing.** In a Short, at most one graphic every 6-8 seconds and none in the first 2.5 s (the title
  card is there). In long-form, at most one a minute besides section cards. Never two graphics at once,
  except a `zoom` paired with a `sticker`.
- **Durations.** logo and stat 2.5 s, compare and list 3.5 s, zoom 1-1.5 s, sticker about 2 s. A list
  needs about 1 s per item; trim items to 1-4 words each.
- **Stickers stay rare and kind:** 0-1 per Short, 2-6 words, about the creator or the situation ("plot twist",
  "I checked twice", "my wallet: 😅"), never mocking a person, company or viewer.
- **Zooms** go on emphasis, not on every sentence: 1-2 per Short.
- When in doubt, leave it out. A clean shot of the speaker talking beats a busy screen.

If you want a logo you don't have, list it in the hand-off so the creator can drop the PNG in assets/.
In the hand-off, list each graphic with its time (in the final video) so the creator can veto any in one line.

## 5. Final render
**Short mode:** `python3 tools/props.py vertical <slug> --title "<the chosen title>"` and run the printed render.
Captions, title card, cards, graphics and the tag are all burned in. Extract a frame from out/final.mp4
at the middle of each graphic and look at them: nothing may cover the speaker's eyes or mouth or overlap the
captions; fix cards.json and re-render if it does. Then skip to step 6 (one thumbnail is enough
for a Short: the title card frame works) and step 8.

**Long mode:**
- `python3 tools/props.py main <slug>` (writes props and package/captions.srt shifted for the intro)
- Run the render command it prints. Then extract 4 frames from out/final.mp4 (intro, lower third at
  ~6 s, the middle, the outro) with ffmpeg and look at them before saying it is done.

## 6. Thumbnails (3 options)
- Extract a frame every 10 s from roughcut.mp4 into `work/frames/` at 640 px wide; look at them and
  pick 3 where the creator's face is expressive and sharp.
- For each of the 3 /yt-package texts (n = 1, 2, 3):
  `python3 tools/props.py thumb <slug> --at <sec> --text "<text>" --name thumbnail-<n>`, then run the printed render.
- Look at all three. Text must be readable at phone size and not cover a face; re-render if not.

## 7. Shorts
- Run `/yt-shorts` on `work/roughcut.srt`. Turn its picks (max 3) into `work/shorts.json`
  (rough-cut seconds, `slug`, `hook`, `x` crop centre: look at a frame to place it on the speaker's face).
- `python3 tools/shorts.py videos/<slug>/work/roughcut.mp4 videos/<slug>/work/shorts.json videos/<slug>/work/shorts/`
- For each short: `python3 tools/transcribe.py videos/<slug>/work/shorts/<s>.mp4 videos/<slug>/work/shorts/<s>`
  then `python3 tools/props.py short <slug> <s>` and run the printed render.
- Add each short's title and caption (Shorts + Reels) to package.md.

## 8. Hand off (Gate 2)
In chat: runtime, the deliverables list (paths), the 3 title options. Then stop. Do not upload.

## Revisions after review
The creator gives FINAL timestamps. Convert each with
`python3 tools/maptime.py videos/<slug>/work/roughcut.mp4.keeps.json <m:ss>`, add/remove cuts in
cuts.json, and re-run from step 3. Text, colour and layout changes go in `brand.json` (name, colours, font style), `studio/src/brand.ts` or
`parts.tsx`; re-run step 5 only.

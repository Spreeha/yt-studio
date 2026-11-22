---
name: yt-clip
description: Turn an existing long-form video (already edited or published) into finished vertical Shorts and Reels of up to 60 seconds, one for every strong moment, with faces kept centred, follow-the-speaker and stacked two-person layouts, the creator's captions, title card and graphics. Use for "make Shorts from my video", "clip this interview", "cut-downs from <video>". Never uploads.
---

# yt-clip <slug>

**Where to work:** this skill lives in the studio folder, `~/Studio/yt-studio` (tools/install_global_skills.sh rewrites this path to wherever you cloned it). Before anything else, `cd` there (if that folder is missing, say so and stop) and read its CLAUDE.md and brand.json. All paths below are relative to that folder.

Long video in, Shorts out: every part worth a Short becomes one, each up to 60 seconds, with whoever is on
screen kept dead centre. Nothing in the long video is re-edited. Set up the task list with the steps below.

## 0. Get the source
- The source is `videos/<slug>/raw.mp4`. If it isn't there, look for the newest .mp4 in ~/Downloads and offer
  to move it (`mv` it into `videos/<slug>/raw.mp4`). If it's only on YouTube, tell the creator: YouTube Studio →
  Content → hover the video → ⋮ → Download. Never download from YouTube any other way.
- `ffprobe` it. If it is vertical, stop: this skill is for landscape videos (a vertical video already is a Short).
- Extract one frame every 20 s at 640 px wide into `work/frames/` and look at them:
  - **Burned-in captions?** Published videos usually have them. Note the fraction of the frame height they
    occupy at the bottom (usually 0.15-0.20) → `--trim-bottom`.
  - **Burned-in cards or titles** (e.g. handwritten section cards at the top): note where and when they appear.
    If one would sit inside a Short's crop, set `"trim_top"` on that clip (just enough to drop the card,
    never through anyone's head) or start the clip after the card has gone.
  - **How many people** and roughly where they sit.

## 0b. Find the faces
`python3 tools/faces.py videos/<slug>/raw.mp4 videos/<slug>/work/faces.json --trim-bottom <from step 0>`
It prints where each person usually sits (e.g. person 1 at x=0.30, person 2 at x=0.64). Use those numbers as
the x / top / bottom hints in step 3; at cut time every crop snaps to the real face and keeps it centred,
panning smoothly if the person leans or moves. If it says OpenCV is missing, run
`python3 -m pip install --user opencv-python-headless` once and retry.

## 1. Transcribe once, with word timings
`python3 tools/transcribe.py videos/<slug>/raw.mp4 videos/<slug>/work/raw`
(writes raw.srt and raw.captions.json; every Short reuses these, nothing is transcribed twice).

## 2. Find every moment worth a Short
Read all of `work/raw.srt` (use the `/yt-shorts` method) and list **every** part that can stand on its own as a
Short. There is no fixed number: a 14-minute interview might give 4 to 8, a rambling one 2. Leave out
warm-ups, logistics, repeated points and anything that needs earlier context.
- **Length: 45-60 seconds, never over 60.** A clip can be several `ranges` from the source joined in order,
  to drop a tangent, a long pause, a repeated sentence or a slow middle and still land the point inside
  60 s. Never reorder, never join mid-sentence, never change what anyone meant.
- **Starts strong**: a question, a surprising number, a strong opinion, a laugh. Cut the warm-up words.
- **Ends on a payoff**, not mid-thought.
- For interviews: the guest's most specific, useful answers; the host's sharp questions; funny exchanges.
- Each gets a **title-card hook** (under 45 characters, in the creator's voice from voice.md, a question or a surprising
  claim) and a working title.
- Rank them by strength.

**Show the creator** the list in chat as a table: rank, source times (with any skipped parts), length, first line
spoken, hook, why it works. Ask "Make all of these, or drop any?" If they aren't there, make every clip you'd
rank as strong and say which weaker ones you held back.

## 3. Lay out each clip (who's on screen when)
Read the clip's lines in raw.srt and work out who is speaking when (the host asks short questions; the guest
gives longer answers; check frames at the turn points when unsure). Then build `layout` segments
(seconds from the clip's start):
- **single, following the speaker** (`{"from": t, "mode": "single", "x": <speaker x from 0b>}`) when one
  person talks for more than about 5 seconds. Cut to the other person when they start talking. The crop
  keeps their face centred automatically.
- **stacked** (`{"from": t, "mode": "stacked", "top": <host x>, "bottom": <guest x>}`) for quick back-and-forth,
  reactions, laughs, rapid-fire, and usually the first 2-4 seconds (the title card sits on the seam, and
  viewers see both people straight away).
- Don't switch more often than every 2 seconds; snap each switch to the start of a word (from raw.captions.json).
- Single-speaker videos: one `single` segment on the speaker's face for the whole clip; no stacked.

`from` counts seconds into the finished Short (after any skipped parts). Write all clips to `work/shorts.json`:
```
[{"slug": "interview-rounds", "hook": "How many interview rounds?",
  "ranges": [[195.0, 221.4], [229.0, 262.6]],
  "layout": [{"from": 0,    "mode": "stacked", "top": 0.30, "bottom": 0.64},
             {"from": 3.6,  "mode": "single",  "x": 0.64},
             {"from": 28.1, "mode": "single",  "x": 0.30}]}]
```

## 4. Cut
`python3 tools/shorts.py videos/<slug>/raw.mp4 videos/<slug>/work/shorts.json videos/<slug>/work/shorts --faces videos/<slug>/work/faces.json --captions videos/<slug>/work/raw.captions.json --trim-bottom <from step 0>`

This writes each clip at 1080x1920 plus its word timings and stacked ranges, and prints the face position it
locked onto for each part. If a printed x is far from your hint, the wrong face was picked: check a frame.

## 5. Graphics
For each clip, write `work/shorts/<clip>.cards.json` using the rules in the yt-produce skill, section 4b
(stat, compare, list, zoom, sticker, logo), with times in seconds from the clip's start. Keep them to the
**single**-layout parts; in stacked parts the screen is already busy. When in doubt, none.

## 6. Render and check
For each clip: `python3 tools/props.py short <slug> <clip>` and run the render command it prints.
Then extract frames from each `out/shorts/<clip>.mp4` at: 1 s, every layout switch + 0.5 s, and the middle of
each graphic. Look at them: each face centred left-to-right and not cut off, captions readable and not
over a mouth, no old burned-in captions or cards showing, no graphic over a face. Check every Short is 60 s
or less. Fix `shorts.json` or the cards and
re-run steps 4 and 6 for that clip if anything is off.

## 7. Package
Write `videos/<slug>/package/shorts.md`, one section per clip:
- 3 title options (plain English, under 60 characters, then 3-5 hashtags), following voice.md
- the YouTube Shorts description: one line of context + "Full video: <link to the long video>" (ask for the
  link if you don't have it; YouTube also lets you link the Short to the related video when uploading)
- the Instagram Reels caption: 1-2 lines + 5-8 hashtags
- for interviews: a credit line for the guest (name and how they want to be credited; ask if unknown)

## 8. Hand off
In chat: a table of clip, length, hook, file path (`videos/<slug>/out/shorts/<clip>.mp4`), and each graphic with
its time so the creator can veto any. Then stop. Do not upload.

## Revisions
The creator gives times from the Short itself ("switch to me at 0:12", "drop the sticker", "start 2 seconds later",
"cut the bit about X"). Edit that clip's `layout` or `ranges` in shorts.json or its cards.json, and re-run
steps 4 and 6 for that clip only.

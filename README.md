# yt-studio

A YouTube editing studio run by Claude Code on your Mac. You record; Claude cuts the dead air and
retakes, burns in word-by-word captions, adds logo cards and animated stats, renders the final video,
three thumbnails and Shorts, and writes the titles, description and chapters. You approve twice and
upload yourself. Nothing is ever uploaded for you.

```
idea ──/yt-research──▶ topic ──/yt-script──▶ script.md ──[Gate 1: you approve, record]──▶ raw.mov
raw.mov ──/yt-produce──▶ cut list ──▶ rough cut ──▶ final.mp4 + 3 thumbnails + Shorts + package.md
                                                    └──[Gate 2: you approve, you upload]
long video ──/yt-clip──▶ every strong moment as a ≤60 s vertical Short, faces kept centred
```

Built on [youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) (cloned by setup,
pinned), [Remotion](https://www.remotion.dev), FFmpeg, [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
and OpenCV's YuNet face detector.

## What this adds to youtube-agent-skill

The upstream pack gives Claude the writing skills (scripts, titles, SEO, chapters, Shorts picks,
dead-air detection). This repo adds everything around them:

| Area | Added here |
| --- | --- |
| Editing | `/yt-produce`: raw footage to final.mp4 with a cut list you approve first (dead air, filler, retakes), loudness levelling, a rough cut, then a Remotion render. Vertical footage becomes a finished Short; landscape gets intro, lower third, chapters, outro and Shorts cut-downs |
| Captions | Word-by-word burned-in captions from whisper.cpp timings, spoken word highlighted, plus an .srt for YouTube CC |
| Graphics | Logo cards, counting-up stats, comparison bars, lists, punch-in zooms, stickers and section cards, placed by Claude on the word that triggers them, with rules (only real numbers, pacing, never over a face) |
| Shorts from long videos | `/yt-clip`: finds every self-contained moment, joins ranges to stay under 60 s, follows whoever is speaking with face detection (YuNet), stacks two people for back-and-forth, crops out old burned-in captions |
| Thumbnails | 3 options from the sharpest expressive frames, with title text in your font style |
| Look | One `brand.json`: channel name, host, colours, three font styles (`clean`, `punchy`, `classic`), timings |
| Research | `/yt-research` on the official YouTube Data API only: outlier ranking, comment mining for demand, lifestyle peer searches. No downloading other people's videos |
| Voice | A story-led voice template: every video as person, moment, turn, payoff; 8 hook families; 10 rotating Short structures; a story bank; a rule against invented personal stories |
| Phone automations | `cloud/`: a daily idea brief with a trending vlog pick, a Sunday script and a Saturday retention review that run as Claude scheduled tasks and reach your phone, plus the same three as on-demand skills (see [cloud/README.md](cloud/README.md)) |
| Safety | Never uploads or publishes; Claude is denied `yt-dlp`, `.env` and `client_secret.json`; pinned dependencies with 0 known vulnerabilities |

## What you need

- An Apple-silicon Mac (Homebrew, about 3 GB free for tools and the Whisper model)
- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- A YouTube Data API key (free) for studying other channels
- Your own footage. The studio never downloads anyone else's videos.

## Step by step

**1. Clone** this repo somewhere permanent, e.g. `~/Studio/yt-studio`.

**2. Get a YouTube Data API key** (use a personal Google account):
console.cloud.google.com → New project → APIs & Services → Library → "YouTube Data API v3" → Enable →
Credentials → Create credentials → API key → Edit key → API restrictions → restrict to YouTube Data
API v3. Copy the key.

**3. Run setup** in Terminal from this folder: `./setup.sh`. It installs FFmpeg, whisper.cpp, the
Whisper model, the skill pack and Remotion, asks for your channel name, your name, role and handle
(saved to `brand.json`), and asks for the API key (saved to `.env`, readable only by you). About 5 minutes.

**4. Open Claude Code here**: `cd ~/Studio/yt-studio && claude`.

**5. Teach it your voice.** `~/.claude/youtube/voice.md` starts as a template. Download the subtitles
of 3 of your best videos from YouTube Studio (Subtitles → ⋮ → Download .srt), drop them in `research/`,
and tell Claude: "fill in ~/.claude/youtube/voice.md from these three, and ask me for my story bank".

**6. Research.** Put 10-20 channels in `research/channels.txt`, then `/yt-research`.

**7. Script.** `/yt-script` with the idea you picked. Save the approved one as
`videos/<slug>/script.md`. **Gate 1**: you edit it, then record.

**8. Produce.** Put the recording at `videos/<slug>/raw.mov` (or `.mp4`) and run `/yt-produce <slug>`.
Claude shows you the cut list before cutting. Say what to change in plain English.

**9. Review and revise.** Watch `videos/<slug>/out/final.mp4`. Give notes with timestamps from the
final ("cut 3:12 to 3:20", "the lower third is too early"). Claude maps them back and re-renders.

**10. Upload yourself** using `videos/<slug>/package/package.md` as the checklist. **Gate 2.**

## Shorts from a video you already published

Download it from YouTube Studio (Content → ⋮ → Download), save it as `videos/<name>/raw.mp4`, then in
Claude Code: `/yt-clip <name>`. Claude finds every moment that stands on its own, shows you the list,
and cuts each one to 60 seconds or less, following whoever is speaking, with stacked two-person shots
for quick back-and-forth, your captions and graphics, plus titles in `package/shorts.md`.

## Changing the look

`brand.json`: channel name, host, role, colours, font style (`clean`, `punchy` or `classic`), intro and
outro length. `npm run studio` inside `studio/` opens a live preview of every composition.

## Security and privacy

- The API key lives only in `.env` (git-ignored, `chmod 600`); Claude Code is denied reading it, and
  the OAuth client file, through `.claude/settings.json`.
- The studio uses the official YouTube Data API read-only. It never logs in to YouTube, never uploads
  and never downloads other people's videos (`yt-dlp` is denied).
- `npm ci` installs the exact versions in `package-lock.json`; `npm audit` reported 0 vulnerabilities
  at release. Run `npm audit` after any upgrade.

## If something breaks

| Symptom | Fix |
| --- | --- |
| Colours look washed out | HDR footage. Turn off HDR video in your phone's camera settings for next time |
| `Quota exhausted` | The Data API allows 10,000 units a day; it resets at midnight Pacific time |
| Transcript has wrong words | Use a bigger model: download `ggml-medium.en.bin` and set `WHISPER_MODEL` |
| You speak more than one language | Download `ggml-small.bin` (multilingual) and pass `--lang auto` |
| First render is slow to start | Remotion downloads a headless Chrome once |

## Experimental: weekly analytics pull

`tools/google_auth.py`, `tools/weekly_pull.py` and `tools/install_weekly.sh` pull your own channel's
numbers and retention curves into a Google Drive folder every Friday via the YouTube Analytics API.
This needs your own OAuth "Desktop app" client (consent screen in Testing, yourself as a test user,
`client_secret.json` in this folder, then `python3 tools/google_auth.py`). It is experimental: some
Google Cloud setups reject the sign-in, and while the app is in Testing the login expires every 7 days.
The rest of the studio does not depend on it; a manual YouTube Studio export works just as well.

## Licence and credits

MIT, see [LICENSE](LICENSE). Third-party parts and their licences are listed in [CREDITS.md](CREDITS.md).
Remotion is free for individuals and companies of up to 3 people; larger companies need a
[Remotion company licence](https://www.remotion.dev/license).

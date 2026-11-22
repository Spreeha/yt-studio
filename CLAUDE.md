# yt-studio

This folder turns raw footage into a finished, packaged YouTube video. Claude runs everything up to
the final render and the package; the creator approves at two gates and uploads themselves.
The channel's name, host, role, colours and font style are in `brand.json`. Read it first.

## Layout

```
brand.json                         channel name, host, role, handle, colours, font style, intro/outro length
videos/<slug>/raw.<mov|mp4>        footage straight off the camera/phone (never modify it)
videos/<slug>/script.md            the approved /yt-script output, if there is one
videos/<slug>/assets/              optional logo PNGs for cards (kimi.png, nvidia.png ...)
videos/<slug>/work/                transcripts, cuts.json, roughcut.mp4, cards.json, shorts.json, shorts/
videos/<slug>/out/                 final.mp4, shorts/*.mp4, thumbnail*.png   <- deliverables
videos/<slug>/package/             package.md, captions.srt                  <- deliverables
research/                          channels.txt, collected.json, comments-*.json
tools/                             research.py transcribe.py roughcut.py shorts.py faces.py props.py maptime.py
                                   brand.py google_auth.py weekly_pull.py install_weekly.sh install_global_skills.sh
studio/                            Remotion project: brand.ts (reads brand.json), parts.tsx, Root.tsx
.claude/skills/                    yt-* pack (Jakeschincariol, a2feb21) + yt-research + yt-produce + yt-clip
cloud/                             prompts and skills for the phone automations (scheduled tasks), see cloud/README.md
```

Slugs are lowercase-hyphenated: `ai-pricing-explainer`.

## Rules

- NEVER upload, publish, schedule or post anything. Everything ends in `out/` and `package/`.
- NEVER modify `raw.*`. All edits happen through `work/cuts.json` and a re-run of roughcut.py.
- NEVER download other people's videos (no yt-dlp). Study other channels only through
  `tools/research.py`, which uses the official Data API.
- NEVER read or print `.env` or `client_secret.json`, and never paste keys or tokens into chat.
- Don't invent numbers in titles, descriptions or scripts. Ask, or write the line without it.
- Voice comes from `~/.claude/youtube/voice.md`. Never invent personal stories for the creator.
- When offering titles, hooks or thumbnail text, give 3 options, short and punchy, not one.
- Captions are burned in on everything (Shorts: bold, spoken word in the accent colour; long-form:
  bottom, spoken word on the highlight colour). Long-form also gets `package/captions.srt` for YouTube CC.
- Every video carries the small channel-name tag top left. Logo and section cards come from
  `work/cards.json`; logos the creator drops in `videos/<slug>/assets/` are used when present.
- Vertical raw = Short mode (the whole video is one Short). Landscape raw = Long mode.
- Times: cuts.json uses RAW seconds. shorts.json uses ROUGH CUT seconds. The creator's review notes use
  FINAL seconds (intro included) -> convert with tools/maptime.py before editing cuts.json.

## Commands

| Step | Command |
| --- | --- |
| Research | `/yt-research` (or `python3 tools/research.py discover ...`, then `swipe.py`) |
| Produce a video | `/yt-produce <slug>` |
| Shorts from an existing long video | `/yt-clip <slug>` |
| Preview compositions | `cd studio && npm run studio` (opens Remotion Studio in the browser) |
| Change the brand | edit `brand.json` |

Renders: `cd studio && npx remotion render ...` exactly as tools/props.py prints it. The first render
downloads a headless Chrome once. Encoding uses `-preset veryfast` unless the creator asks for best quality.

---
name: yt-research
description: Study what is working for other channels in the creator's niche through the official YouTube Data API, rank outliers, mine comments for demand, and propose video ideas. Use for topic research, competitor study, or "what should I make next".
---

# yt-research

**Where to work:** this skill lives in the studio folder, `~/Studio/yt-studio` (tools/install_global_skills.sh rewrites this path to wherever you cloned it). Before anything else, `cd` there (if that folder is missing, say so and stop) and read its CLAUDE.md and brand.json. All paths below are relative to that folder.

Read-only study of other channels through `tools/research.py` (official Data API, API key in `.env`).
Never download videos and never scrape pages.

## Steps

1. **Pick the pool.** Use `research/channels.txt` (one @handle per line) if the creator has filled it.
   Otherwise ask for 2-4 search phrases for the topic, or derive them from their request.
   **Lifestyle formats:** if the creator also follows lifestyle creators on Instagram (which the YouTube API
   can't see), or asks about vlogs, run `--query` searches for the same formats on YouTube, e.g.
   "day in the life <their job>", "<their job> desk setup", "gadgets I use every day", "<their city> tech
   life vlog", and treat those channels as a lifestyle peer set. Add strong ones to research/channels.txt
   under a `# lifestyle` comment.
2. **Collect.**
   `python3 tools/research.py discover --channels research/channels.txt --per-channel 30 --long-only --since <6 months ago>`
   and/or `--query "<phrase>"` (each query costs 1 of the 100 daily search calls; keep it to 4 or fewer).
   Use `--shorts-only` instead when the question is about Shorts.
3. **Rank.** `python3 .claude/skills/yt-viral/swipe.py research/collected.json --min 2.0`
   Channels with fewer than 4 videos are skipped by design; say so if it happens.
4. **Read the top 5 outliers properly.** From collected.json: title, duration, publish date,
   the first lines of the description. Note the formula swipe.py names, and what the title promises.
5. **Mine demand.** For the top 2-3 outliers:
   `python3 tools/research.py comments <video_id> --max 100`
   Pull out questions people ask, things they say were missing, and disagreements. Quote nothing longer
   than a short phrase; summarise.
6. **Report** in chat, short:
   - a table: multiple, channel, title, formula, why it likely landed (your judgement, labelled as such)
   - 3 gaps from the comments
   - 3 video ideas for the channel in brand.json, each with a working title, a story-led first line in the
     creator's voice (voice.md), and the angle only they can bring; one of them a lifestyle idea.
     Hand-off line: "Pick one and I'll run /yt-script."
7. **Save it.** Write the same report to `research/outliers-YYYY-MM-DD.md` (today's date) and run
   `open research` to show the file. If a Google Drive tool is available in this session and the creator
   has told you which Drive folder they keep research in, also upload it there as a Google Doc titled
   `outliers-YYYY-MM-DD`.

## Limits to state plainly when relevant

- The API does not expose other creators' transcripts. For their structure, the creator watches the video.
- View multiples say what over-performed, not why. Keep the "why" labelled as a guess.
- Instagram-only accounts can't be studied through the YouTube API; skip them and say which.

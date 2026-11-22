# Phone automations (run in Claude's cloud, no Mac needed)

Three scheduled tasks send results to the Claude app on your phone, and three skills run the same
jobs whenever you ask in any chat. They read and write a Google Drive folder, so the Mac and the
phone share one set of notes.

| Job | When (suggested) | Prompt | On-demand skill |
| --- | --- | --- | --- |
| Idea brief: 3 news lines, what creators are posting, 2 story-led ideas and a trending vlog pick | daily, 8:00 | `prompts/daily-brief.md` | `yt-idea-brief` |
| Script: this week's script as clean teleprompter text, plus structure, story check, hooks, titles, edit notes | Sunday morning | `prompts/sunday-script.md` | `yt-story-script` |
| Weekly review: scoreboard, retention read, niche patterns, next week's plan, one experiment | Saturday morning | `prompts/weekly-review.md` | `yt-weekly-review` |

They never post, upload, publish or email anything.

## 1. Make the Drive folder

Create a folder named like `My Channel Studio` (the name goes in `config.json` as `DRIVE_FOLDER`) with:

```
My Channel Studio/
  voice            Google Doc: paste templates/voice.md, then fill it in (README step 5)
  channels         Google Doc: creators to watch, one per line (@handle | platform | note)
  lifestyle-creators  Google Doc: lifestyle creators you study, your versions of their formats, a swipe file of reel links
  briefs/          daily briefs land here
  starred/         ideas you star from a brief or review ("star idea 2")
  scripts/         Sunday scripts land here
  weekly-reviews/  Saturday reviews land here
  studio-exports/  each week: YouTube Studio → Analytics → Advanced mode → Export → Google Sheets, moved here
  mac-research/    optional: /yt-research reports from the Mac
```

To change your voice later, edit the `voice` doc. To keep an old version, rename it to start with
`voice (` (e.g. `voice (old)`); the tasks ignore those.

## 2. Fill in your details

```
cp cloud/config.example.json cloud/config.json     # edit it: city, audience, time zone, folder name
python3 cloud/build.py
```

`cloud/out/prompts/` now holds the three prompts with your details, and `cloud/out/*.zip` the three
skills. Both are git-ignored.

## 3. Create the scheduled tasks

In Claude (with the Google Drive connector connected), ask: "Create a scheduled task named Daily idea
brief, every day at 8:00 in my time zone, with push notifications, using this prompt:" and paste
`cloud/out/prompts/daily-brief.md`. Do the same for the Sunday script and the Saturday review.

## 4. Add the skills

Upload each zip in `cloud/out/` as a skill in Claude. Then "run my brief", "script my starred idea"
or "weekly review" works in any chat.

## How the pieces fit

- The brief tags every idea with its hook family and structure, e.g. `[confession · structure 2]`,
  so the next day's brief and the Sunday script can rotate and never repeat the same shape.
- "star idea N" saves an idea to `starred/`; Sunday's script takes the newest one without a
  `DONE - ` doc and marks it done.
- Saturday's review picks one retention experiment; the Sunday script applies it.
- Instagram pages can't be fetched by the tasks, so lifestyle trends come from search, press and
  creator-stats sites, and the tasks say so rather than pretend to have watched a reel.

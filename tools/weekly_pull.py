#!/usr/bin/env python3
"""weekly_pull.py - gather the week's numbers and put them in Google Drive for a weekly review. EXPERIMENTAL.

    python3 tools/weekly_pull.py            # what the weekly Mac job runs
    python3 tools/weekly_pull.py --no-upload # write the report locally only

Collects, with no Claude involved (so it costs nothing and runs while you sleep):
  1. Your channel: last 7 days vs the 7 before; every upload from the last 60 days with views, average
     % viewed, average view duration, subs gained; and the audience-retention curve of the 6 newest.
  2. Your niche: outliers from research/channels.txt via the Data API key (same as /yt-research).
Writes research/weekly/weekly-data-YYYY-MM-DD.md and uploads it to the Drive folder
"<channel name from brand.json> - weekly data". Needs the OAuth setup in README (experimental).
"""
import datetime as dt, json, os, re, subprocess, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import google_auth as g  # noqa: E402
import brand  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YT = "https://www.googleapis.com/youtube/v3/"
YTA = "https://youtubeanalytics.googleapis.com/v2/reports"
DRIVE_FOLDER_NAME = f"{brand.name()} - weekly data"
DRIVE_CONF = os.path.join(g.CONF, "drive.json")
today = dt.date.today()


def iso_seconds(d):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m: return 0
    days, h, mi, s = (int(x or 0) for x in m.groups())
    return days * 86400 + h * 3600 + mi * 60 + s


def report(start, end, metrics, dimensions=None, filters=None, sort=None, max_results=None):
    r = g.request(YTA, params={"ids": "channel==MINE", "startDate": str(start), "endDate": str(end),
                               "metrics": metrics, "dimensions": dimensions, "filters": filters,
                               "sort": sort, "maxResults": max_results})
    cols = [h["name"] for h in r.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in r.get("rows", [])]


def fmt_dur(s):
    s = int(round(s or 0)); return f"{s // 60}:{s % 60:02d}"


def section_channel(lines):
    me = g.request(YT + "channels", params={"part": "snippet,contentDetails,statistics", "mine": "true"})
    if not me.get("items"):
        lines.append("## Your channel\n\nThe signed-in Google account has no YouTube channel. Re-run google_auth.py and pick the channel's account.\n")
        return
    ch = me["items"][0]
    stats = ch["statistics"]
    lines.append(f"## Your channel: {ch['snippet']['title']}\n")
    lines.append(f"Subscribers: {stats.get('subscriberCount', '?')} · Videos: {stats.get('videoCount', '?')}\n")

    # Week over week. Analytics data lags ~2-3 days, so "this week" ends 3 days ago.
    end = today - dt.timedelta(days=3)
    wk = (end - dt.timedelta(days=6), end)
    prev = (wk[0] - dt.timedelta(days=7), wk[0] - dt.timedelta(days=1))
    m = "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost"
    a = (report(*wk, m) or [{}])[0]
    b = (report(*prev, m) or [{}])[0]
    lines.append(f"### Week over week (Analytics lags ~3 days: {wk[0]} to {wk[1]} vs {prev[0]} to {prev[1]})\n")
    lines.append("| Metric | This week | Week before |\n| --- | --- | --- |")
    for k, label in [("views", "Views"), ("estimatedMinutesWatched", "Watch time (min)"),
                     ("averageViewDuration", "Avg view duration (s)"), ("subscribersGained", "Subs gained"),
                     ("subscribersLost", "Subs lost")]:
        lines.append(f"| {label} | {a.get(k, 0)} | {b.get(k, 0)} |")
    lines.append("")

    # Uploads from the last 60 days
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = g.request(YT + "playlistItems", params={"part": "contentDetails", "playlistId": pl, "maxResults": 50}).get("items", [])
    ids = [i["contentDetails"]["videoId"] for i in items]
    vids = []
    for k in range(0, len(ids), 50):
        vids += g.request(YT + "videos", params={"part": "snippet,contentDetails,statistics", "id": ",".join(ids[k:k + 50])}).get("items", [])
    cutoff = today - dt.timedelta(days=60)
    recent = [v for v in vids if v["snippet"]["publishedAt"][:10] >= str(cutoff)]
    recent.sort(key=lambda v: v["snippet"]["publishedAt"], reverse=True)
    if not recent:
        lines.append("No uploads in the last 60 days.\n")
        return
    per = {}
    rows = report(cutoff, today, "views,averageViewDuration,averageViewPercentage,subscribersGained,likes,comments,shares",
                  dimensions="video", filters="video==" + ",".join(v["id"] for v in recent[:200]), sort="-views", max_results=200)
    for r in rows: per[r["video"]] = r
    lines.append("### Uploads, last 60 days (newest first)\n")
    lines.append("| Published | Type | Title | Length | Views | Avg % viewed | Avg view | Subs | Likes | Comments |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for v in recent:
        secs = iso_seconds(v["contentDetails"]["duration"])
        r = per.get(v["id"], {})
        kind = "Short" if secs <= 180 else "Long"
        title = v["snippet"]["title"].replace("|", "/")[:70]
        lines.append(f"| {v['snippet']['publishedAt'][:10]} | {kind} | [{title}](https://youtu.be/{v['id']}) | {fmt_dur(secs)} | "
                     f"{r.get('views', v['statistics'].get('viewCount', 0))} | {round(r.get('averageViewPercentage', 0), 1)}% | "
                     f"{fmt_dur(r.get('averageViewDuration', 0))} | {r.get('subscribersGained', 0)} | {r.get('likes', 0)} | {r.get('comments', 0)} |")
    lines.append("")

    # Retention curves for the 6 newest
    lines.append("### Audience retention, 6 newest uploads\n")
    lines.append("audienceWatchRatio = share of viewers still watching at that point (can exceed 1.0 when people rewatch). "
                 "relative = vs YouTube videos of similar length (0.5 = average, higher is better).\n")
    for v in recent[:6]:
        secs = iso_seconds(v["contentDetails"]["duration"])
        try:
            curve = report(v["snippet"]["publishedAt"][:10], today, "audienceWatchRatio,relativeRetentionPerformance",
                           dimensions="elapsedVideoTimeRatio", filters="video==" + v["id"], sort="elapsedVideoTimeRatio")
        except RuntimeError as e:
            curve = []; print("  ! retention", v["id"], e, file=sys.stderr)
        lines.append(f"**{v['snippet']['title'][:80]}** ({fmt_dur(secs)}, published {v['snippet']['publishedAt'][:10]})\n")
        if not curve:
            lines.append("No retention curve returned yet (too new, too few views, or not available for this video).\n")
            continue
        pts = [p for p in curve if round(p["elapsedVideoTimeRatio"] * 100) % 10 == 0 or p["elapsedVideoTimeRatio"] in (0.01, 0.02, 0.03, 0.05)]
        lines.append("| At | Time | Still watching | Relative |\n| --- | --- | --- | --- |")
        for p in pts:
            r = p["elapsedVideoTimeRatio"]
            lines.append(f"| {round(r * 100)}% | {fmt_dur(r * secs)} | {round(p['audienceWatchRatio'] * 100)}% | {round(p.get('relativeRetentionPerformance', 0), 2)} |")
        # steepest single drops (cliffs)
        drops = sorted(((curve[i - 1]["audienceWatchRatio"] - curve[i]["audienceWatchRatio"], curve[i]["elapsedVideoTimeRatio"])
                        for i in range(2, len(curve))), reverse=True)[:3]
        if drops:
            lines.append("\nSteepest drops: " + ", ".join(f"{round(d * 100, 1)} pts at {fmt_dur(t * secs)}" for d, t in drops if d > 0) + "\n")
        lines.append("")


def section_niche(lines):
    chans = os.path.join(ROOT, "research", "channels.txt")
    since = str(today - dt.timedelta(days=60))
    out = os.path.join(ROOT, "research", "collected.json")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "research.py"), "discover", "--channels", chans,
                        "--per-channel", "20", "--since", since, "--out", out], capture_output=True, text=True)
    if r.returncode:
        lines.append(f"## Niche outliers\n\nCould not collect: {(r.stderr or r.stdout).strip()[-300:]}\n"); return
    swipe = os.path.join(ROOT, ".claude", "skills", "yt-viral", "swipe.py")
    s = subprocess.run([sys.executable, swipe, out, "--min", "2.0"], capture_output=True, text=True)
    lines.append("## Niche outliers (last 60 days, 2x or more over each channel's own median)\n")
    lines.append("```\n" + (s.stdout.strip() or s.stderr.strip() or "none")[:6000] + "\n```\n")


def drive_folder():
    if os.path.exists(DRIVE_CONF):
        fid = json.load(open(DRIVE_CONF)).get("folder")
        try:
            f = g.request(f"https://www.googleapis.com/drive/v3/files/{fid}", params={"fields": "id,trashed"})
            if not f.get("trashed"): return fid
        except RuntimeError:
            pass
    f = g.request("https://www.googleapis.com/drive/v3/files", method="POST",
                  body={"name": DRIVE_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"})
    os.makedirs(g.CONF, exist_ok=True)
    json.dump({"folder": f["id"]}, open(DRIVE_CONF, "w"))
    print(f"  created Drive folder '{DRIVE_FOLDER_NAME}' (you can move it anywhere in your Drive)")
    return f["id"]


def upload(path):
    folder = drive_folder()
    meta = {"name": os.path.basename(path), "parents": [folder], "mimeType": "text/markdown"}
    boundary = "ytstudioboundary7f3a"
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(meta)}\r\n"
            f"--{boundary}\r\nContent-Type: text/markdown; charset=UTF-8\r\n\r\n").encode() + open(path, "rb").read() + f"\r\n--{boundary}--".encode()
    f = g.request("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart", method="POST", body=body,
                  headers={"Content-Type": f"multipart/related; boundary={boundary}"})
    return f["id"]


def notify(msg):
    if sys.platform == "darwin":
        clean = lambda t: str(t).replace("\\", "").replace('"', "")  # keep the AppleScript string well-formed
        subprocess.run(["osascript", "-e", f'display notification "{clean(msg)}" with title "{clean(brand.name())}"'],
                       capture_output=True)


def main():
    lines = [f"# Weekly data, {today}\n", "Pulled automatically by tools/weekly_pull.py for the weekly review.\n"]
    ok = True
    for fn in (section_channel, section_niche):
        try:
            fn(lines)
        except (RuntimeError, SystemExit) as e:
            ok = False
            lines.append(f"## {fn.__name__.replace('section_', '').title()}\n\nFailed: {e}\n")
            print(f"  ! {fn.__name__}: {e}", file=sys.stderr)
    d = os.path.join(ROOT, "research", "weekly"); os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"weekly-data-{today}.md")
    open(path, "w").write("\n".join(lines))
    print(f"  wrote {path}")
    if "--no-upload" not in sys.argv:
        try:
            upload(path); print("  uploaded to Drive"); notify("Weekly data is in Drive for Saturday's review" + ("" if ok else " (with errors)"))
        except (RuntimeError, SystemExit) as e:
            print(f"  ! upload failed: {e}", file=sys.stderr); notify("Weekly data pull could not upload to Drive"); sys.exit(1)


if __name__ == "__main__":
    main()

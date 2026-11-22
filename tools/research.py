#!/usr/bin/env python3
"""research.py - study other channels through the official YouTube Data API v3 (API key, read-only).

    python3 tools/research.py discover --query "system design interview" --query "sre explained"
    python3 tools/research.py discover --channels research/channels.txt --per-channel 30
    python3 tools/research.py comments VIDEO_ID --max 100

discover writes research/collected.json in the format skills/yt-viral/swipe.py reads, so:

    python3 .claude/skills/yt-viral/swipe.py research/collected.json --min 2.0

What the official API gives you about OTHER people's videos: titles, descriptions, tags, publish
dates, durations, views, likes, comment counts and the comments themselves. What it does NOT give
you: their transcripts (captions.download only works for videos you own). Study the packaging and
the comment demand; watch the video yourself for the rest.

Quota (default project, per day): search.list has its own bucket of 100 calls; channels, playlist
and video lookups cost 1 unit each from the 10,000-unit pool. A full discover run is ~5-30 units
plus one search call per --query.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request

API = "https://www.googleapis.com/youtube/v3/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USAGE = {"search": 0, "units": 0}


def api_key():
    key = os.environ.get("YOUTUBE_API_KEY")
    env = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env):
        for line in open(env):
            if line.strip().startswith("YOUTUBE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("No YOUTUBE_API_KEY. Put it in .env (YOUTUBE_API_KEY=...) or export it.")
    return key


def call(endpoint, **params):
    params = {k: v for k, v in params.items() if v is not None}
    params["key"] = api_key()
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.load(r)
            if endpoint == "search":
                USAGE["search"] += 1
            else:
                USAGE["units"] += 1
            return data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 403 and "quota" in body.lower():
                sys.exit("Quota exhausted for today. It resets at midnight Pacific time.")
            if e.code in (500, 503) and attempt < 2:
                time.sleep(2 ** attempt); continue
            sys.exit(f"API error {e.code} on {endpoint}: {body[:400]}")
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(2 ** attempt); continue
            sys.exit(f"Network error reaching YouTube ({e.reason}). Check the internet connection and try again.")


def iso_seconds(d):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    if not m: return 0
    days, h, mi, s = (int(x or 0) for x in m.groups())
    return days * 86400 + h * 3600 + mi * 60 + s


def chunks(xs, n=50):
    for i in range(0, len(xs), n): yield xs[i:i + n]


def resolve_channels(lines):
    """Accepts @handles, channel IDs (UC...) or full channel URLs, one per line."""
    out = {}
    for raw in lines:
        s = raw.split("#")[0].strip()
        if not s: continue
        m = re.search(r"(UC[\w-]{22})", s)
        h = re.search(r"@([\w.-]+)", s)
        if m:
            d = call("channels", part="snippet,contentDetails,statistics", id=m.group(1))
        elif h:
            d = call("channels", part="snippet,contentDetails,statistics", forHandle="@" + h.group(1))
        else:
            d = call("channels", part="snippet,contentDetails,statistics", forHandle="@" + s.lstrip("@"))
        for c in d.get("items", []):
            out[c["id"]] = c
        if not d.get("items"):
            print(f"  ! could not resolve channel: {s}", file=sys.stderr)
    return out


def channels_by_id(ids):
    out = {}
    for group in chunks(list(ids)):
        d = call("channels", part="snippet,contentDetails,statistics", id=",".join(group))
        for c in d.get("items", []): out[c["id"]] = c
    return out


def recent_upload_ids(channel, n):
    pl = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < n:
        d = call("playlistItems", part="contentDetails", playlistId=pl,
                 maxResults=min(50, n - len(ids)), pageToken=token)
        ids += [i["contentDetails"]["videoId"] for i in d.get("items", [])]
        token = d.get("nextPageToken")
        if not token: break
    return ids


def video_details(ids):
    out = []
    for group in chunks(ids):
        d = call("videos", part="snippet,statistics,contentDetails", id=",".join(group))
        out += d.get("items", [])
    return out


def row(v, ch):
    sn, st = v["snippet"], v.get("statistics", {})
    return {
        "channel": sn.get("channelTitle", ""),
        "channel_id": sn.get("channelId", ""),
        "subscribers": int(ch.get("statistics", {}).get("subscriberCount", 0) or 0) if ch else None,
        "title": sn.get("title", ""),
        "url": f"https://www.youtube.com/watch?v={v['id']}",
        "video_id": v["id"],
        "published": sn.get("publishedAt", "")[:10],
        "duration": iso_seconds(v["contentDetails"].get("duration")),
        "views": int(st.get("viewCount", 0) or 0),
        "likes": int(st.get("likeCount", 0) or 0),
        "comments": int(st.get("commentCount", 0) or 0),
        "tags": sn.get("tags", [])[:15],
        "description": (sn.get("description") or "")[:600],
    }


def discover(a):
    chans = {}
    if a.channels:
        chans.update(resolve_channels(open(a.channels).read().splitlines()))
    for q in a.query or []:
        d = call("search", part="snippet", q=q, type="video", maxResults=25,
                 order=a.order, publishedAfter=(a.since + "T00:00:00Z") if a.since else None,
                 regionCode=a.region, relevanceLanguage="en")
        found = {i["snippet"]["channelId"] for i in d.get("items", [])}
        chans.update(channels_by_id(found - set(chans)))
    if not chans:
        sys.exit("No channels. Pass --query and/or --channels.")
    rows = []
    for cid, ch in chans.items():
        for v in video_details(recent_upload_ids(ch, a.per_channel)):
            r = row(v, ch)
            if a.since and r["published"] < a.since: continue
            if a.long_only and r["duration"] <= 180: continue
            if a.shorts_only and r["duration"] > 180: continue
            rows.append(r)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(rows, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"  {len(rows)} videos from {len(chans)} channels -> {a.out}")
    print(f"  quota used: {USAGE['search']} search calls, {USAGE['units']} units")
    print(f"  next: python3 .claude/skills/yt-viral/swipe.py {a.out} --min 2.0")


def comments(a):
    out, token = [], None
    while len(out) < a.max:
        d = call("commentThreads", part="snippet", videoId=a.video_id, order="relevance",
                 maxResults=min(100, a.max - len(out)), textFormat="plainText", pageToken=token)
        for t in d.get("items", []):
            c = t["snippet"]["topLevelComment"]["snippet"]
            out.append({"likes": c.get("likeCount", 0), "replies": t["snippet"].get("totalReplyCount", 0),
                        "text": c.get("textDisplay", "")[:500]})
        token = d.get("nextPageToken")
        if not token: break
    path = a.out or os.path.join(ROOT, "research", f"comments-{a.video_id}.json")
    json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"  {len(out)} comments -> {path}  (quota: {USAGE['units']} units)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover", help="collect recent uploads from channels found by query or listed in a file")
    d.add_argument("--query", action="append", help="search phrase; repeatable; 1 search call each")
    d.add_argument("--channels", help="file of @handles / channel IDs / URLs, one per line")
    d.add_argument("--per-channel", type=int, default=30, help="recent uploads per channel (min 4 for swipe.py)")
    d.add_argument("--since", help="YYYY-MM-DD; drop older videos")
    d.add_argument("--order", default="relevance", choices=["relevance", "viewCount", "date"])
    d.add_argument("--region", default=None, help="e.g. IN")
    g = d.add_mutually_exclusive_group()
    g.add_argument("--long-only", action="store_true", help="drop videos of 3 min or less")
    g.add_argument("--shorts-only", action="store_true", help="keep only videos of 3 min or less")
    d.add_argument("--out", default=os.path.join(ROOT, "research", "collected.json"))
    c = sub.add_parser("comments", help="top comments on one video, for finding what viewers ask for")
    c.add_argument("video_id")
    c.add_argument("--max", type=int, default=100)
    c.add_argument("--out")
    a = p.parse_args()
    discover(a) if a.cmd == "discover" else comments(a)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""props.py - stage media into the Remotion project and write render props.

    python3 tools/props.py main  <slug> [--burn-captions] [--lower-third-at 4]
    python3 tools/props.py short <slug> <short-slug>
    python3 tools/props.py thumb <slug> --at 63.5 --text "Your pager is lying"

Each prints the exact render command. Media is hard-linked (or copied) into studio/public/<slug>/,
because Remotion can only read files from its public folder; clear old slugs out of it now and then.
"""
import argparse, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO = os.path.join(ROOT, "studio")


def stage(src, slug, name):
    if not os.path.exists(src): sys.exit(f"missing {src}")
    d = os.path.join(STUDIO, "public", slug); os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, name)
    if os.path.exists(dst): os.remove(dst)
    try: os.link(src, dst)
    except OSError: shutil.copy2(src, dst)
    return f"{slug}/{name}"


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip())


def intro_sec():
    try:
        return float(json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8")).get("introSec", 2))
    except (OSError, ValueError):
        return 2.0


def shift_srt(text, by):
    def f(m):
        t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000 + by
        return f"{int(t // 3600):02}:{int(t % 3600 // 60):02}:{int(t % 60):02},{round(t % 1 * 1000) % 1000:03}"
    return re.sub(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)", f, text)


def cards(path, slug):
    """Logo and section cards: [{"at": sec, "dur": sec, "text": "KIMI K3", "img": "kimi.png", "kind": "logo"}].
    img is a file in videos/<slug>/assets/ (a PNG logo works best); leave it out for a text-only card."""
    if not os.path.exists(path): return []
    out = []
    for c in json.load(open(path)):
        c = dict(c)
        if c.get("img"):
            src = os.path.join(ROOT, "videos", slug, "assets", c["img"])
            if os.path.exists(src): c["img"] = stage(src, slug, "asset-" + os.path.basename(src))
            else:
                print(f"  ! card image not found, using text only: {src}"); c.pop("img")
        out.append(c)
    print(f"  {len(out)} cards from {os.path.relpath(path, ROOT)}")
    return out


def layout(path):
    """Stacked (two-person) time ranges written by shorts.py, so captions sit on the seam there."""
    return json.load(open(path)).get("stacked", []) if os.path.exists(path) else []


def caps(path):
    return json.load(open(path)) if os.path.exists(path) else []


def write(slug, kind, props):
    d = os.path.join(STUDIO, "props"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{slug}.{kind}.json")
    json.dump(props, open(p, "w"), indent=1)
    return os.path.relpath(p, STUDIO)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("main"); m.add_argument("slug")
    m.add_argument("--no-captions", action="store_true", help="don't burn captions in (the SRT is still made)")
    m.add_argument("--lower-third-at", type=float, default=4.0, help="seconds into the video; -1 for none")
    m.add_argument("--no-intro", action="store_true")
    s = sub.add_parser("short"); s.add_argument("slug"); s.add_argument("short")
    v = sub.add_parser("vertical", help="the whole rough cut is a vertical Short (filmed 9:16)")
    v.add_argument("slug"); v.add_argument("--title", default="", help="title card text for the first beat")
    t = sub.add_parser("thumb"); t.add_argument("slug"); t.add_argument("--at", type=float, required=True)
    t.add_argument("--text", required=True); t.add_argument("--accent", default="")
    t.add_argument("--name", default="thumbnail", help="output name, e.g. thumbnail-2")
    a = p.parse_args()
    work = os.path.join(ROOT, "videos", a.slug, "work")
    out = os.path.join(ROOT, "videos", a.slug, "out")
    os.makedirs(out, exist_ok=True)

    if a.cmd == "main":
        src = os.path.join(work, "roughcut.mp4")
        props = {"src": stage(src, a.slug, "roughcut.mp4"), "durationSec": duration(src),
                 "captions": caps(os.path.join(work, "roughcut.captions.json")),
                 "burnCaptions": not a.no_captions, "intro": not a.no_intro,
                 "lowerThirdAt": a.lower_third_at,
                 "cards": cards(os.path.join(work, "cards.json"), a.slug)}
        rel = write(a.slug, "main", props)
        srt = os.path.join(work, "roughcut.srt")
        if os.path.exists(srt):  # YouTube CC file, shifted to line up after the intro card
            pkg = os.path.join(ROOT, "videos", a.slug, "package"); os.makedirs(pkg, exist_ok=True)
            by = 0.0 if a.no_intro else intro_sec()
            open(os.path.join(pkg, "captions.srt"), "w").write(shift_srt(open(srt).read(), by))
            print(f"  package/captions.srt shifted +{by:g}s for the intro")
        target = os.path.relpath(os.path.join(out, "final.mp4"), STUDIO)
        print(f"  cd studio && npx remotion render Main {target} --props={rel}")
    elif a.cmd == "short":
        src = os.path.join(work, "shorts", a.short + ".mp4")
        spec = [c for c in json.load(open(os.path.join(work, "shorts.json"))) if c["slug"] == a.short]
        props = {"src": stage(src, a.slug, f"short-{a.short}.mp4"), "durationSec": duration(src),
                 "captions": caps(os.path.join(work, "shorts", a.short + ".captions.json")),
                 "hook": spec[0].get("hook", "") if spec else "",
                 "cards": cards(os.path.join(work, "shorts", a.short + ".cards.json"), a.slug),
                 "stacked": layout(os.path.join(work, "shorts", a.short + ".layout.json"))}
        rel = write(a.slug, f"short-{a.short}", props)
        target = os.path.relpath(os.path.join(out, "shorts", a.short + ".mp4"), STUDIO)
        print(f"  cd studio && npx remotion render Short {target} --props={rel}")
    elif a.cmd == "vertical":
        src = os.path.join(work, "roughcut.mp4")
        props = {"src": stage(src, a.slug, "roughcut.mp4"), "durationSec": duration(src),
                 "captions": caps(os.path.join(work, "roughcut.captions.json")),
                 "hook": a.title, "cards": cards(os.path.join(work, "cards.json"), a.slug)}
        rel = write(a.slug, "vertical", props)
        target = os.path.relpath(os.path.join(out, "final.mp4"), STUDIO)
        print(f"  cd studio && npx remotion render Short {target} --props={rel}")
    else:
        frame = os.path.join(work, f"thumb-frame-{a.at:g}.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a.at), "-i",
                        os.path.join(work, "roughcut.mp4"), "-frames:v", "1", frame], check=True)
        props = {"frame": stage(frame, a.slug, f"{a.name}-frame.png"), "text": a.text, "accent": a.accent}
        rel = write(a.slug, a.name, props)
        target = os.path.relpath(os.path.join(out, f"{a.name}.png"), STUDIO)
        print(f"  cd studio && npx remotion still Thumbnail {target} --props={rel}")


if __name__ == "__main__":
    main()

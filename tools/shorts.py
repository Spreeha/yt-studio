#!/usr/bin/env python3
"""shorts.py - cut vertical 1080x1920 Shorts/Reels out of a landscape video, people kept centred.

    python3 tools/shorts.py <source.mp4> <shorts.json> <outdir> [--faces faces.json]
                            [--captions <source>.captions.json] [--trim-bottom 0.18] [--trim-top 0]

shorts.json is a list of clips:
    [{"slug": "interview-rounds", "hook": "How many interview rounds?",
      "ranges": [[195.0, 221.4], [229.0, 262.6]],          # source seconds; joined in order (skips a tangent)
      "layout": [{"from": 0,    "mode": "stacked", "top": 0.30, "bottom": 0.64},
                 {"from": 6.5,  "mode": "single",  "x": 0.64},
                 {"from": 24.0, "mode": "single",  "x": 0.30}]}]
"start"/"end" still work instead of "ranges" for one continuous piece.

layout ("from" = seconds into the finished Short, first at 0):
    single   9:16 crop on one person. x = roughly where that person sits (0 = left edge, 1 = right edge).
             Switching x between segments = cutting to whoever is speaking.
    stacked  two people, one above the other (1080x960 each). top / bottom = each person's rough x.
With --faces (from tools/faces.py), each rough x snaps to the real face nearest to it and the crop keeps
that face dead centre, panning smoothly if the person moves. Without it, the x values are used as given.

--trim-bottom / --trim-top (or "trim_bottom"/"trim_top" per clip) leave out a band of the frame, e.g. 0.18 to
drop captions burned into a published video. Writes <slug>.mp4, <slug>.layout.json (stacked ranges) and,
with --captions, <slug>.captions.json (word timings mapped onto the Short; nothing is re-transcribed).
"""
import argparse, json, os, statistics, subprocess, sys


def probe(path):
    d = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height:stream_side_data=rotation", "-of", "json", path],
                                  capture_output=True, text=True, check=True).stdout)
    s = d["streams"][0]
    w, h = s["width"], s["height"]
    for sd in s.get("side_data_list", []) or []:
        if abs(int(sd.get("rotation", 0) or 0)) in (90, 270): w, h = h, w
    a = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                   "-of", "json", path], capture_output=True, text=True).stdout or "{}")
    return w, h, bool(a.get("streams"))


class Faces:
    """Face centres over time from faces.py; finds the face nearest a rough x and follows it."""

    def __init__(self, path):
        d = json.load(open(path))
        self.samples = d["samples"]

    def track(self, a, b, hint):
        """[(t, cx)] for the face nearest `hint` between source seconds a and b (t relative to a)."""
        pts, last = [], hint
        for s in self.samples:
            if s["t"] < a - 0.25 or s["t"] > b + 0.25 or not s["faces"]: continue
            f = min(s["faces"], key=lambda f: abs(f[0] - last))
            if abs(f[0] - hint) > 0.18: continue  # nearest face is someone else; ignore this sample
            pts.append((max(0.0, s["t"] - a), f[0])); last = f[0]
        if len(pts) >= 5:  # smooth out detector jitter: running median of 5
            xs = [p[1] for p in pts]
            pts = [(pts[i][0], statistics.median(xs[max(0, i - 2):i + 3])) for i in range(len(pts))]
        return pts


def box(W, H, aspect, top, bottom):
    y = int(round(H * top)); h = int(round(H * (1 - top - bottom)))
    w = min(W, int(round(h * aspect)))
    if w == W: h = min(h, int(round(W / aspect)))
    return w - w % 2, h - h % 2, y


def x_expr(W, w, centre_pts, fallback):
    """ffmpeg crop x for a face that should stay centred: a constant, or a smooth pan through keyframes."""
    def px(cx): return max(0, min(W - w, int(round(cx * W - w / 2))))
    if not centre_pts: return str(px(fallback)), fallback
    xs = [c for _, c in centre_pts]
    med = statistics.median(xs)
    if max(xs) - min(xs) < 0.025 or len(centre_pts) < 3:  # sitting still: lock the crop
        return str(px(med)), med
    keys, nxt = [], 0.0  # a keyframe about every 1.5 s
    for t, c in centre_pts:
        if t >= nxt: keys.append((t, px(c))); nxt = t + 1.5
    if centre_pts[-1][0] > keys[-1][0]: keys.append((centre_pts[-1][0], px(centre_pts[-1][1])))
    keys = keys[:24]
    e = str(keys[-1][1])
    for (t0, x0), (t1, x1) in reversed(list(zip(keys, keys[1:]))):
        e = f"if(lt(t,{t1:.2f}),{x0}+({x1 - x0})*(t-{t0:.2f})/{max(0.01, t1 - t0):.2f},{e})"
    e = f"if(lt(t,{keys[0][0]:.2f}),{keys[0][1]},{e})"
    return f"'{e}'", med


def pieces_for(ranges, segs):
    """Split the Short's timeline into pieces that each have one source range and one layout segment."""
    vt, src = [], []
    for s, e in ranges:
        base = vt[-1][1] if vt else 0.0
        vt.append((base, base + (e - s))); src.append((s, e))
    total = vt[-1][1]
    bounds = sorted({0.0, total} | {float(g["from"]) for g in segs if 0 < float(g["from"]) < total} | {v[0] for v in vt})
    out = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a < 0.05: continue
        seg = [g for g in segs if float(g["from"]) <= a + 1e-6][-1]
        i = [k for k, (va, vb) in enumerate(vt) if va <= a + 1e-6 < vb][0]
        sa = src[i][0] + (a - vt[i][0])
        out.append({"va": a, "vb": b, "sa": sa, "sb": sa + (b - a), "seg": seg})
    return out, total


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src"); p.add_argument("spec"); p.add_argument("outdir")
    p.add_argument("--faces", help="faces.json from tools/faces.py: keep people centred")
    p.add_argument("--captions", help="word timings of the whole source (transcribe.py's .captions.json)")
    p.add_argument("--trim-bottom", type=float, default=0.0, help="leave out this fraction at the bottom (burned-in captions)")
    p.add_argument("--trim-top", type=float, default=0.0, help="leave out this fraction at the top")
    a = p.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    W, H, has_audio = probe(a.src)
    if H > W: sys.exit("This source is already vertical. Cut it with roughcut.py / props.py vertical instead.")
    faces = Faces(a.faces) if a.faces else None
    words = json.load(open(a.captions)) if a.captions else None

    for c in json.load(open(a.spec)):
        ranges = [tuple(map(float, r)) for r in c.get("ranges") or [[c["start"], c["end"]]]]
        top, bottom = float(c.get("trim_top", a.trim_top)), float(c.get("trim_bottom", a.trim_bottom))
        segs = sorted(c.get("layout") or [{"from": 0, "mode": "single", "x": c.get("x", 0.5)}], key=lambda g: float(g.get("from", 0)))
        segs[0]["from"] = 0
        pieces, total = pieces_for(ranges, segs)
        if total > 180: print(f"  ! {c['slug']}: {total:.0f}s is over the 3-minute Shorts limit, skipped"); continue
        if total > 90: print(f"  note {c['slug']}: {total:.0f}s, too long for Reels (90 s)")
        origin = max(0.0, min(r[0] for r in ranges) - 1.0)  # seek close to the first range, then trim precisely
        end = max(r[1] for r in ranges) + 0.5
        parts, labels, stacked, report = [], [], [], []
        for i, pc in enumerate(pieces):
            g, sa, sb = pc["seg"], pc["sa"] - origin, pc["sb"] - origin
            t = f"trim=start={sa:.3f}:end={sb:.3f},setpts=PTS-STARTPTS"
            if g.get("mode") == "stacked":
                bw, bh, by = box(W, H, 1080 / 960, top, bottom)
                xs = []
                for hint in (float(g.get("top", 0.3)), float(g.get("bottom", 0.7))):
                    ex, med = x_expr(W, bw, faces.track(pc["sa"], pc["sb"], hint) if faces else [], hint)
                    xs.append(ex); report.append(f"{med:.2f}")
                parts.append(f"[0:v]{t},split=2[p{i}a][p{i}b];"
                             f"[p{i}a]crop={bw}:{bh}:{xs[0]}:{by},scale=1080:960,setsar=1[p{i}t];"
                             f"[p{i}b]crop={bw}:{bh}:{xs[1]}:{by},scale=1080:960,setsar=1[p{i}u];"
                             f"[p{i}t][p{i}u]vstack=2,format=yuv420p[v{i}]")
                stacked.append([round(pc["va"], 3), round(pc["vb"], 3)])
            else:
                cw, ch, cy = box(W, H, 9 / 16, top, bottom)
                hint = float(g.get("x", 0.5))
                ex, med = x_expr(W, cw, faces.track(pc["sa"], pc["sb"], hint) if faces else [], hint)
                report.append(f"{med:.2f}")
                parts.append(f"[0:v]{t},crop={cw}:{ch}:{ex}:{cy},scale=1080:1920,setsar=1,format=yuv420p[v{i}]")
            labels.append(f"[v{i}]")
            if has_audio:
                fo = max(0.0, (sb - sa) - 0.01)
                parts.append(f"[0:a]atrim=start={sa:.3f}:end={sb:.3f},asetpts=PTS-STARTPTS,"
                             f"afade=t=in:d=0.01,afade=t=out:st={fo:.3f}:d=0.01[a{i}]")
                labels.append(f"[a{i}]")
        n = len(pieces)
        parts.append("".join(labels) + f"concat=n={n}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else ""))
        out = os.path.join(a.outdir, c["slug"] + ".mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{origin:.3f}", "-t", f"{end - origin:.3f}", "-i", a.src,
               "-filter_complex", ";".join(parts), "-map", "[v]"] + \
              (["-map", "[a]", "-c:a", "aac", "-b:a", "192k"] if has_audio else []) + \
              ["-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-movflags", "+faststart", out]
        if subprocess.run(cmd).returncode: sys.exit(f"ffmpeg failed on {c['slug']}")
        json.dump({"stacked": stacked}, open(os.path.join(a.outdir, c["slug"] + ".layout.json"), "w"))
        if words is not None:
            clip, base = [], 0.0
            for s, e in ranges:
                for w in words:
                    if w["startMs"] >= s * 1000 - 50 and w["endMs"] <= e * 1000 + 50:
                        clip.append({"text": w["text"], "startMs": int(w["startMs"] - s * 1000 + base * 1000),
                                     "endMs": int(w["endMs"] - s * 1000 + base * 1000)})
                base += e - s
            json.dump(clip, open(os.path.join(a.outdir, c["slug"] + ".captions.json"), "w"))
        print(f"  {out}  ({total:.1f}s from {len(ranges)} range(s); "
              f"{' + '.join(g.get('mode', 'single') for g in segs)}; face x: {', '.join(report)})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""roughcut.py - apply a cut list to raw footage with ffmpeg, then normalise loudness for YouTube.

    python3 tools/roughcut.py videos/<slug>/raw.mov videos/<slug>/work/cuts.json videos/<slug>/work/roughcut.mp4
    python3 tools/roughcut.py ... --dry-run      # print what stays, change nothing

cuts.json is deadair.py --json output, edited by hand or by Claude. Each cut is
    {"kind": "DEAD|FILLER|REPEAT|MANUAL", "start": 12.4, "end": 15.1, "why": "..."}
Delete a cut to keep that bit. Add a MANUAL cut to drop a tangent. Times are seconds in the RAW file.
Overlapping cuts are merged. Audio gets 8 ms fades at every join so cuts don't click, then
EBU R128 loudness normalisation to -14 LUFS, -1 dBTP (YouTube's playback target).
"""
import argparse, json, subprocess, sys


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    return float(d["format"]["duration"]), any(s["codec_type"] == "audio" for s in d["streams"])


def keeps_from(cuts, duration, min_keep=0.12):
    spans = sorted((max(0.0, float(c["start"])), min(duration, float(c["end"]))) for c in cuts
                   if float(c["end"]) > float(c["start"]))
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1] + 0.05:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    keeps, t = [], 0.0
    for s, e in merged:
        if s - t >= min_keep: keeps.append((round(t, 3), round(s, 3)))
        t = max(t, e)
    if duration - t >= min_keep: keeps.append((round(t, 3), round(duration, 3)))
    return keeps


def fmt(t): return f"{int(t // 60)}:{t % 60:05.2f}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src"); p.add_argument("cuts"); p.add_argument("out", nargs="?")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-loudnorm", action="store_true")
    p.add_argument("--crf", default="14", help="rough cut is an intermediate file, so keep it near-lossless")
    a = p.parse_args()
    data = json.load(open(a.cuts))
    cuts = data["cuts"] if isinstance(data, dict) else data
    dur, has_audio = probe(a.src)
    keeps = keeps_from(cuts, dur)
    kept = sum(e - s for s, e in keeps)
    print(f"  {len(cuts)} cuts -> {len(keeps)} kept segments, {fmt(dur)} -> {fmt(kept)} "
          f"({dur - kept:.1f}s removed)")
    if a.dry_run or not a.out:
        for s, e in keeps: print(f"    keep {fmt(s)} - {fmt(e)}")
        return
    parts, labels = [], []
    for i, (s, e) in enumerate(keeps):
        parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}]")
        labels.append(f"[v{i}]")
        if has_audio:
            fo = max(0.0, (e - s) - 0.008)
            parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d=0.008,afade=t=out:st={fo:.3f}:d=0.008[a{i}]")
            labels.append(f"[a{i}]")
    n = len(keeps)
    parts.append("".join(labels) + f"concat=n={n}:v=1:a={1 if has_audio else 0}[v]" + ("[ac]" if has_audio else ""))
    if has_audio:
        parts.append("[ac]" + ("anull" if a.no_loudnorm else "loudnorm=I=-14:TP=-1:LRA=11") + ",aresample=48000[a]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", a.src, "-filter_complex", ";".join(parts),
           "-map", "[v]"] + (["-map", "[a]", "-c:a", "aac", "-b:a", "192k"] if has_audio else []) + \
          ["-c:v", "libx264", "-preset", "veryfast", "-crf", a.crf, "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", a.out]
    r = subprocess.run(cmd)
    if r.returncode: sys.exit("ffmpeg failed")
    json.dump({"source": a.src, "keeps": keeps}, open(a.out + ".keeps.json", "w"), indent=1)
    print(f"  wrote {a.out}")


if __name__ == "__main__":
    main()

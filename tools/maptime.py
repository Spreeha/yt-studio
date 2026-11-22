#!/usr/bin/env python3
"""maptime.py - turn a timestamp you saw in final.mp4 into the matching time in the raw footage.

    python3 tools/maptime.py videos/<slug>/work/roughcut.mp4.keeps.json 3:12.5 [--intro 2]

Use it when reviewing: "cut 3:12 to 3:20 in the final" -> map both ends -> add a MANUAL cut to
cuts.json with the raw times -> re-run roughcut.py. --intro is brand.introSec (0 if rendered --no-intro).
"""
import json, sys


def secs(s):
    p = [float(x) for x in s.split(":")]
    return sum(v * 60 ** i for i, v in enumerate(reversed(p)))


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(1)
    intro = float(a[a.index("--intro") + 1]) if "--intro" in a else 2.0
    keeps = json.load(open(a[0]))["keeps"]
    t = secs(a[1]) - intro
    if t < 0: sys.exit("that time is inside the intro card")
    acc = 0.0
    for s, e in keeps:
        if t <= acc + (e - s):
            raw = s + (t - acc)
            print(f"{raw:.2f}  (raw {int(raw // 60)}:{raw % 60:05.2f})"); return
        acc += e - s
    sys.exit("that time is past the end of the rough cut (outro card?)")


if __name__ == "__main__":
    main()

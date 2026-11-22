#!/usr/bin/env python3
"""faces.py - find where every face is, over time, so Shorts can keep people centred.

    python3 tools/faces.py videos/<slug>/raw.mp4 videos/<slug>/work/faces.json [--fps 2] [--trim-bottom 0.18]

Samples frames (2 per second by default), runs the bundled YuNet face detector (OpenCV) and writes
    {"width": W, "height": H, "fps": 2, "samples": [{"t": 12.5, "faces": [[cx, cy, w, h, score], ...]}, ...]}
with cx, cy, w, h as fractions of the frame. shorts.py --faces uses it to put each person dead centre and
to follow them smoothly if they move. It also prints where the people usually sit (their x positions),
which is what to use for "x" / "top" / "bottom" hints in shorts.json.

Needs OpenCV once: python3 -m pip install --user opencv-python-headless
"""
import argparse, json, os, subprocess, sys

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_detection_yunet_2023mar.onnx")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src"); p.add_argument("out")
    p.add_argument("--fps", type=float, default=2.0)
    p.add_argument("--trim-bottom", type=float, default=0.0, help="ignore the bottom band (burned-in captions)")
    p.add_argument("--start", type=float, default=0.0); p.add_argument("--end", type=float, default=None)
    a = p.parse_args()
    try:
        import cv2, numpy as np
    except ImportError:
        sys.exit("OpenCV is missing. Run once: python3 -m pip install --user opencv-python-headless")

    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height:format=duration", "-of", "json", a.src],
                                     capture_output=True, text=True, check=True).stdout)
    W, H = info["streams"][0]["width"], info["streams"][0]["height"]
    dur = float(info["format"]["duration"])
    end = min(a.end or dur, dur)
    sw = 640; sh = int(round(H * sw / W / 2) * 2)  # detect on a 640-wide copy: fast and plenty for faces
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(a.start), "-to", str(end), "-i", a.src,
           "-vf", f"fps={a.fps},scale={sw}:{sh}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    det = cv2.FaceDetectorYN.create(MODEL, "", (sw, sh), 0.6, 0.3, 50)
    usable_h = sh * (1 - a.trim_bottom)
    samples, n, frame_bytes = [], 0, sw * sh * 3
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes: break
        img = np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
        _, faces = det.detect(img)
        found = []
        for f in (faces if faces is not None else []):
            x, y, w, h, score = float(f[0]), float(f[1]), float(f[2]), float(f[3]), float(f[-1])
            if y + h / 2 > usable_h or w < sw * 0.03: continue  # skip faces in captions/thumbnails, tiny ones
            found.append([round((x + w / 2) / sw, 4), round((y + h / 2) / sh, 4), round(w / sw, 4), round(h / sh, 4), round(score, 3)])
        samples.append({"t": round(a.start + n / a.fps, 3), "faces": found})
        n += 1
        if n % 200 == 0: print(f"  {n / a.fps:.0f}s scanned", file=sys.stderr)
    proc.wait()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"width": W, "height": H, "fps": a.fps, "samples": samples}, open(a.out, "w"))

    # Summarise where people usually sit: 1-D clustering of face centres.
    xs = sorted(f[0] for s in samples for f in s["faces"])
    clusters = []
    for x in xs:
        if clusters and x - clusters[-1][-1] < 0.08: clusters[-1].append(x)
        else: clusters.append([x])
    big = [c for c in clusters if len(c) >= max(3, 0.1 * len(samples))]
    with_face = sum(1 for s in samples if s["faces"])
    print(f"  {len(samples)} frames scanned, a face in {with_face} ({100 * with_face // max(1, len(samples))}%)")
    for i, c in enumerate(big):
        print(f"  person {i + 1}: usually at x={sorted(c)[len(c) // 2]:.2f} (seen in {len(c)} frames)")
    print(f"  wrote {a.out}")


if __name__ == "__main__":
    main()

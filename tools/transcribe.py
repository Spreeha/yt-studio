#!/usr/bin/env python3
"""transcribe.py - local transcription with whisper.cpp (whisper-cli from Homebrew).

    python3 tools/transcribe.py videos/<slug>/raw.mov videos/<slug>/work/raw

Writes, next to the given base path:
    <base>.srt            sentence-level cues -> deadair.py, chapters.py, YouTube CC upload
    <base>.captions.json  word-level [{text,startMs,endMs}] -> Remotion burned captions

Model: $WHISPER_MODEL, default ~/.cache/whisper/ggml-small.en.bin (setup.sh downloads it).
Speaking more than one language? Use a multilingual model (ggml-small.bin) and --lang auto.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

DEFAULT_MODEL = os.path.expanduser("~/.cache/whisper/ggml-small.en.bin")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(cmd[:3])} ...\n{r.stderr[-1500:]}")


def words_to_captions(path):
    d = json.load(open(path, encoding="utf-8"))
    caps = []
    for seg in d.get("transcription", []):
        t = (seg.get("text") or "").strip()
        if not t or t.startswith("[") or t.startswith("("):  # [BLANK_AUDIO], (music)
            continue
        s, e = seg["offsets"]["from"], seg["offsets"]["to"]
        if caps and t in ",.!?;:" :  # stray punctuation token -> glue onto previous word
            caps[-1]["text"] += t; continue
        caps.append({"text": t, "startMs": int(s), "endMs": int(e)})
    return caps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("media"); p.add_argument("base")
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", DEFAULT_MODEL))
    p.add_argument("--lang", default="en")
    p.add_argument("--no-words", action="store_true", help="skip the word-level pass")
    a = p.parse_args()
    cli = shutil.which("whisper-cli") or shutil.which("whisper-cpp")
    if not cli: sys.exit("whisper-cli not found. Run: brew install whisper-cpp")
    if not os.path.exists(a.model): sys.exit(f"model not found at {a.model}. Run ./setup.sh")
    os.makedirs(os.path.dirname(a.base) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "audio.wav")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.media, "-ar", "16000", "-ac", "1",
             "-c:a", "pcm_s16le", wav])
        run([cli, "-m", a.model, "-f", wav, "-l", a.lang, "-osrt", "-of", a.base])
        print(f"  {a.base}.srt")
        if not a.no_words:
            wb = os.path.join(tmp, "words")
            run([cli, "-m", a.model, "-f", wav, "-l", a.lang, "-ml", "1", "-sow", "-oj", "-of", wb])
            caps = words_to_captions(wb + ".json")
            json.dump(caps, open(a.base + ".captions.json", "w"), indent=0)
            print(f"  {a.base}.captions.json  ({len(caps)} words)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""build.py - fill the cloud prompts and skills with your details.

    cp cloud/config.example.json cloud/config.json   # then edit it
    python3 cloud/build.py

Writes cloud/out/prompts/*.md (paste each into a scheduled task) and cloud/out/<skill>.zip
(upload each to Claude as a skill). HOST, CHANNEL_NAME, HANDLE and PROMISE come from brand.json
when config.json leaves them at the example values.
"""
import json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
PAIRS = {"yt-idea-brief": "daily-brief.md", "yt-story-script": "sunday-script.md", "yt-weekly-review": "weekly-review.md"}


def load_config():
    path = os.path.join(HERE, "config.json")
    if not os.path.exists(path):
        sys.exit("Copy cloud/config.example.json to cloud/config.json and fill it in first.")
    cfg = json.load(open(path, encoding="utf-8"))
    example = json.load(open(os.path.join(HERE, "config.example.json"), encoding="utf-8"))
    try:
        brand = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    except (OSError, ValueError):
        brand = {}
    for key, bkey in (("HOST", "host"), ("CHANNEL_NAME", "name"), ("HANDLE", "handle"), ("PROMISE", "promise")):
        if cfg.get(key, example[key]) == example[key] and brand.get(bkey):
            cfg[key] = brand[bkey]
    return cfg


def fill(text, cfg):
    def rep(m):
        if m.group(1) not in cfg:
            sys.exit(f"config.json is missing {m.group(1)}")
        return str(cfg[m.group(1)])
    return re.sub(r"\{\{([A-Z_]+)\}\}", rep, text)


def main():
    cfg = load_config()
    os.makedirs(os.path.join(OUT, "prompts"), exist_ok=True)
    prompts = {}
    for name in sorted(os.listdir(os.path.join(HERE, "prompts"))):
        prompts[name] = fill(open(os.path.join(HERE, "prompts", name), encoding="utf-8").read(), cfg)
        open(os.path.join(OUT, "prompts", name), "w", encoding="utf-8").write(prompts[name])
        print("prompt ", os.path.join("cloud", "out", "prompts", name))
    for skill, prompt in PAIRS.items():
        skill_md = fill(open(os.path.join(HERE, "skills", skill, "SKILL.md"), encoding="utf-8").read(), cfg)
        z = os.path.join(OUT, f"{skill}.zip")
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
            f.writestr(f"{skill}/SKILL.md", skill_md)
            f.writestr(f"{skill}/prompt.md", prompts[prompt])
        print("skill  ", os.path.join("cloud", "out", f"{skill}.zip"))


if __name__ == "__main__":
    main()

"""brand.py - read brand.json (channel name, host, colours, timings) for the Python tools."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "brand.json")


def load():
    try:
        return json.load(open(PATH, encoding="utf-8"))
    except (OSError, ValueError):
        return {"name": "My Channel", "introSec": 2, "outroSec": 6}


def name():
    return load().get("name") or "My Channel"

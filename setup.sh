#!/usr/bin/env bash
# One-time setup for yt-studio on an Apple-silicon Mac.
# Safe to re-run: every step skips what is already there.
set -euo pipefail
cd "$(dirname "$0")"
say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

say "Homebrew"
command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh  then re-run ./setup.sh"; exit 1; }

say "FFmpeg, whisper.cpp, Node"
for pkg in ffmpeg whisper-cpp; do brew list "$pkg" >/dev/null 2>&1 || brew install "$pkg"; done
if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 18 ]; then
  brew install node
fi
echo "ffmpeg $(ffmpeg -version | head -1 | cut -d' ' -f3) · whisper-cli $(command -v whisper-cli) · node $(node -v)"

say "Whisper model (small.en, ~470 MB, once)"
MODEL="$HOME/.cache/whisper/ggml-small.en.bin"
mkdir -p "$(dirname "$MODEL")"
[ -s "$MODEL" ] || curl -L --fail -o "$MODEL" \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin
echo "$MODEL"

say "youtube-agent-skill (pinned to a2feb21)"
if [ ! -d .claude/vendor/youtube-agent-skill ]; then
  git clone https://github.com/Jakeschincariol/youtube-agent-skill.git .claude/vendor/youtube-agent-skill
  git -C .claude/vendor/youtube-agent-skill checkout -q a2feb21
fi
cp -R .claude/vendor/youtube-agent-skill/skills/yt-* .claude/skills/
./tools/install_global_skills.sh
ls -d .claude/skills/yt-* | xargs -n1 basename | tr '\n' ' '; echo

say "Your channel (brand.json)"
if grep -q '"name": "My Channel"' brand.json; then
  read -r -p "Channel name (shown on every video): " CH_NAME
  read -r -p "Your name (lower third): " CH_HOST
  read -r -p "Your role, e.g. Software Engineer: " CH_ROLE
  read -r -p "YouTube handle, e.g. @yourchannel: " CH_HANDLE
  CH_NAME="$CH_NAME" CH_HOST="$CH_HOST" CH_ROLE="$CH_ROLE" CH_HANDLE="$CH_HANDLE" python3 - <<'PY'
import json, os
d = json.load(open("brand.json", encoding="utf-8"))
for key, env in (("name", "CH_NAME"), ("host", "CH_HOST"), ("role", "CH_ROLE"), ("handle", "CH_HANDLE")):
    v = os.environ.get(env, "").strip()
    if v:
        d[key] = v
json.dump(d, open("brand.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
open("brand.json", "a").write("\n")
PY
  H=$(python3 -c 'import json;print(json.load(open("brand.json"))["handle"])')
  if [ "$H" != "@yourhandle" ] && ! grep -qx "$H" research/channels.txt; then echo "$H" >> research/channels.txt; fi
  echo "saved brand.json (colours and font style are in there too)"
else
  echo "kept your brand.json"
fi

say "voice.md"
mkdir -p "$HOME/.claude/youtube"
if [ ! -f "$HOME/.claude/youtube/voice.md" ]; then
  cp templates/voice.md "$HOME/.claude/youtube/voice.md"; echo "created ~/.claude/youtube/voice.md (a template: README step 5 fills it in)"
else
  echo "kept your existing ~/.claude/youtube/voice.md"
fi

say "Face detection for Shorts (OpenCV)"
python3 -c "import cv2" 2>/dev/null || python3 -m pip install --user --quiet opencv-python-headless
python3 -c "import cv2; print('OpenCV', cv2.__version__)"

say "Remotion"
(cd studio && npm ci --no-audit --no-fund)

say "YouTube Data API key"
if ! grep -q '^YOUTUBE_API_KEY=.\+' .env 2>/dev/null; then
  read -r -p "Paste your API key (or press Enter to add it to .env later): " KEY
  [ -n "$KEY" ] && printf 'YOUTUBE_API_KEY=%s\n' "$KEY" > .env && chmod 600 .env && echo "saved to .env"
else
  echo "already in .env"
fi

say "Done"
echo "Next: open this folder in Claude Code (claude) and follow README.md, step 3."

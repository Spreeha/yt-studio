#!/usr/bin/env bash
# Install every yt-* skill for Claude Code globally (~/.claude/skills), so /yt-script, /yt-research,
# /yt-produce etc. work from any folder. The global copies point at this studio folder, wherever it lives.
# Safe to re-run after updates.
set -euo pipefail
cd "$(dirname "$0")/.."
STUDIO="$PWD"
mkdir -p ~/.claude/skills
cp -R .claude/skills/yt-* ~/.claude/skills/
# Point the studio skills at this folder instead of the default ~/Studio/yt-studio.
for s in yt-produce yt-clip yt-research; do
  f="$HOME/.claude/skills/$s/SKILL.md"
  [ -f "$f" ] && STUDIO="$STUDIO" python3 - "$f" <<'PY'
import os, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read().replace("~/Studio/yt-studio", os.environ["STUDIO"])
open(p, "w", encoding="utf-8").write(s)
PY
done
ls -d ~/.claude/skills/yt-* | xargs -n1 basename | tr '\n' ' '; echo
echo "Installed globally (studio folder: $STUDIO). Restart any open Claude Code session to pick them up."

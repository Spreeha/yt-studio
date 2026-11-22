#!/usr/bin/env bash
# install_weekly.sh - run tools/weekly_pull.py every Friday at 9 PM on this Mac.
# If the Mac is asleep then, macOS runs it as soon as the Mac wakes (not if it was shut down).
#   ./tools/install_weekly.sh            install or update
#   ./tools/install_weekly.sh --remove   uninstall
#   ./tools/install_weekly.sh --run-now  run it once right away (to test)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LABEL="com.ytstudio.weekly"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY="$(command -v python3)"

if [ "${1:-}" = "--remove" ]; then
  launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"; echo "Removed the weekly job."; exit 0
fi
if [ "${1:-}" = "--run-now" ]; then
  launchctl kickstart -k "gui/$(id -u)/$LABEL" && echo "Started. Watch: tail -f research/weekly/weekly.log"; exit 0
fi

mkdir -p "$HOME/Library/LaunchAgents" research/weekly
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$ROOT/tools/weekly_pull.py</string></array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$ROOT/research/weekly/weekly.log</string>
  <key>StandardErrorPath</key><string>$ROOT/research/weekly/weekly.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed: every Friday 9 PM (or on next wake). Test it now with: ./tools/install_weekly.sh --run-now"

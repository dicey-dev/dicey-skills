#!/usr/bin/env bash
# Link every skill in this repo into each installed agent harness.
# Safe to re-run: existing entries are never replaced.
set -eu

repo=$(cd -P "$(dirname "$0")" && pwd)
config=${XDG_CONFIG_HOME:-$HOME/.config}
codex=${CODEX_HOME:-$HOME/.codex}
kiro=${KIRO_HOME:-$HOME/.kiro}

# name | path that exists when the harness is installed | skills folder
harnesses="
Claude Code|$HOME/.claude|$HOME/.claude/skills
OpenCode|$config/opencode|$config/opencode/skills
Codex|$codex|$codex/skills
Pi|$HOME/.pi/agent|$HOME/.pi/agent/skills
Antigravity|$HOME/.gemini/antigravity-cli|$HOME/.gemini/config/skills
Gemini CLI|$HOME/.gemini/settings.json|$HOME/.gemini/skills
Grok|$HOME/.grok|$HOME/.grok/skills
Cursor|$HOME/.cursor|$HOME/.cursor/skills
Kiro|$kiro|$kiro/skills
Copilot CLI|$HOME/.copilot|$HOME/.copilot/skills
"

while IFS='|' read -r name marker dest; do
  [ -n "$name" ] || continue
  if [ ! -e "$marker" ]; then
    echo "$name: not found, skipped"
    continue
  fi
  mkdir -p "$dest"
  linked=0 present=0 kept=""
  for d in "$repo"/skills/*/; do
    [ -f "$d/SKILL.md" ] || continue
    s=$(basename "$d")
    if [ "$(readlink "$dest/$s" 2>/dev/null)" = "$repo/skills/$s" ]; then
      present=$((present + 1))
    elif [ -e "$dest/$s" ] || [ -L "$dest/$s" ]; then
      kept="$kept $s"
    else
      ln -s "$repo/skills/$s" "$dest/$s"
      linked=$((linked + 1))
    fi
  done
  echo "$name: $linked linked, $present already linked${kept:+, kept existing:$kept} ($dest)"
done <<EOF
$harnesses
EOF

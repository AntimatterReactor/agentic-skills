#!/usr/bin/env bash
# Scaffold new skill from template/.
# Usage: scripts/new_skill.sh <skill-name>
set -euo pipefail

name="${1:-}"
if [[ -z "$name" ]]; then
  echo "usage: $0 <skill-name>" >&2
  exit 1
fi
if [[ ! "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ || ${#name} -gt 64 ]]; then
  echo "error: name must be lowercase letters, digits, hyphens; max 64 chars" >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/skills/$name"
if [[ -e "$dest" ]]; then
  echo "error: $dest already exists" >&2
  exit 1
fi

cp -r "$root/template" "$dest"
sed -i.bak "s/^name: skill-name$/name: $name/" "$dest/SKILL.md" && rm "$dest/SKILL.md.bak"
title=""
IFS='-' read -ra parts <<< "$name"
for w in "${parts[@]}"; do title+="$(printf '%s' "${w:0:1}" | tr '[:lower:]' '[:upper:]')${w:1} "; done
title="${title% }"
sed -i.bak "s/^# Skill Name$/# $title/" "$dest/SKILL.md" && rm "$dest/SKILL.md.bak"

echo "created $dest"
echo "next: edit $dest/SKILL.md, then run: python3 scripts/validate_skills.py"

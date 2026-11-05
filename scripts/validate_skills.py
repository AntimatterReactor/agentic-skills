#!/usr/bin/env python3
"""Validate every skills/<name>/SKILL.md against Agent Skills rules.

Checks:
  - SKILL.md exists and starts with YAML frontmatter
  - `name`: required, lowercase/digits/hyphens, <=64 chars, matches dir name,
    no reserved words ("anthropic", "claude")
  - `description`: required, non-empty, <=1024 chars, no XML tags
  - body present
No third-party deps.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED = ("anthropic", "claude")
TAG_RE = re.compile(r"<[^>]+>")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    raw, body = text[4:end], text[end + 4 :]
    data: dict[str, str] = {}
    key = None
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            data[key] = (data[key] + " " + line.strip()).strip()
    for k, v in data.items():
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            data[k] = v[1:-1]
        if v in (">", "|", ">-", "|-"):
            data[k] = ""
    return data, body


def validate(skill_dir: Path) -> list[str]:
    errs: list[str] = []
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        return ["missing SKILL.md"]
    parsed = parse_frontmatter(md.read_text(encoding="utf-8"))
    if parsed is None:
        return ["SKILL.md must start with '---' frontmatter block"]
    fm, body = parsed

    name = fm.get("name", "")
    if not name:
        errs.append("frontmatter missing 'name'")
    else:
        if not NAME_RE.match(name):
            errs.append(f"name {name!r}: use lowercase letters, digits, single hyphens")
        if len(name) > 64:
            errs.append(f"name {name!r}: exceeds 64 chars")
        if name != skill_dir.name:
            errs.append(f"name {name!r} does not match directory {skill_dir.name!r}")
        if any(r in name for r in RESERVED):
            errs.append(f"name {name!r}: contains reserved word")

    desc = fm.get("description", "")
    if not desc:
        errs.append("frontmatter missing 'description'")
    else:
        if len(desc) > 1024:
            errs.append(f"description exceeds 1024 chars ({len(desc)})")
        if TAG_RE.search(desc):
            errs.append("description must not contain XML tags")

    if not body.strip():
        errs.append("SKILL.md body is empty")
    return errs


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print("no skills/ directory")
        return 1
    dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not dirs:
        print("no skills yet — nothing to validate")
        return 0
    failed = 0
    for d in dirs:
        errs = validate(d)
        if errs:
            failed += 1
            print(f"FAIL {d.name}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"ok   {d.name}")
    print(f"\n{len(dirs) - failed}/{len(dirs)} skills valid")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

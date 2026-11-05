#!/usr/bin/env python3
"""Lint a learnings file written in the agent-learn entry format.

Entry format (see references/entry-format.md):

    ### DO: <imperative title>
    - **When:** ...
    - **Why:** ...
    - **Instead:** ...        (required for DONT and ANTIPATTERN)
    - **Evidence:** ...
    - **Source:** user | observed | inferred
    - **Scope:** project | user | skill:<name> | tool:<name>
    - **Added:** YYYY-MM-DD
    - **Recheck:** ...        (required when Source is inferred)

Kinds: DO, DONT, PATTERN, ANTIPATTERN. PATTERN and ANTIPATTERN should carry a
fenced code block (the "shape").

Errors (exit 1): missing/invalid fields, duplicate titles, secret-looking text.
Warnings (exit 0, or 1 with --strict): vague titles, missing shape, long entries.

Usage: lint_learnings.py FILE [FILE...] [--strict]
Stdlib only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KINDS = ("DO", "DONT", "PATTERN", "ANTIPATTERN")
HEADING = re.compile(r"^###\s+([A-Z]+):\s*(.*\S)\s*$")
FIELD = re.compile(r"^-\s+\*\*([A-Za-z]+):\*\*\s*(.*)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}\b")
SOURCES = {"user", "observed", "inferred"}
SCOPE = re.compile(r"^(project|user|skill:[a-z0-9-]+|tool:[\w.-]+)$")
REQUIRED = ["When", "Why", "Evidence", "Source", "Scope", "Added"]
NEEDS_INSTEAD = {"DONT", "ANTIPATTERN"}
VAGUE = re.compile(r"^(be careful|keep in mind|remember|note|consider|try to|make sure)\b", re.I)
SECRETS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\b(?:ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}"), "GitHub token"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "API secret key"),
    (re.compile(r"(?i)\b(password|passwd|secret|token|storePassword|keyPassword)\s*[=:]\s*['\"]?[^\s'\"<>*]{6,}"), "credential assignment"),
]


def parse(text: str) -> list[dict]:
    entries: list[dict] = []
    cur: dict | None = None
    in_fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if cur is not None:
                cur["fence"] = True
                cur["lines"].append(line)
            continue
        m = HEADING.match(line) if not in_fence else None
        if m:
            cur = dict(kind=m.group(1), title=m.group(2), line=n, fields={}, fence=False, lines=[line])
            entries.append(cur)
            continue
        if cur is None:
            continue
        cur["lines"].append(line)
        if not in_fence:
            f = FIELD.match(line)
            if f:
                cur["fields"][f.group(1)] = f.group(2).strip()
    return entries


def lint(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    entries = parse(text)
    if not entries:
        errors.append(f"{path}: no entries found (expected '### DO: ...' headings)")
        return errors, warnings

    seen: dict[str, int] = {}
    for e in entries:
        where = f"{path}:{e['line']}"
        kind, title, fields = e["kind"], e["title"], e["fields"]
        if kind not in KINDS:
            errors.append(f"{where}: unknown kind {kind!r} (use {', '.join(KINDS)})")
            continue
        key = f"{kind}:{title.lower()}"
        if key in seen:
            errors.append(f"{where}: duplicate of entry at line {seen[key]}")
        seen[key] = e["line"]

        for req in REQUIRED:
            if not fields.get(req):
                errors.append(f"{where}: {kind} '{title}' missing **{req}:**")
        if kind in NEEDS_INSTEAD and not fields.get("Instead"):
            errors.append(f"{where}: {kind} '{title}' missing **Instead:** (say what to do)")

        src = fields.get("Source", "").split()[0].lower() if fields.get("Source") else ""
        if src and src not in SOURCES:
            errors.append(f"{where}: Source must be one of {sorted(SOURCES)}, got {fields['Source']!r}")
        if src == "inferred" and not fields.get("Recheck"):
            errors.append(f"{where}: inferred entry needs **Recheck:** (how/when to verify)")
        scope = fields.get("Scope", "")
        if scope and not SCOPE.match(scope):
            errors.append(f"{where}: Scope {scope!r} must be project | user | skill:<name> | tool:<name>")
        added = fields.get("Added", "")
        if added and not DATE.match(added):
            errors.append(f"{where}: Added must start with YYYY-MM-DD, got {added!r}")

        body = "\n".join(e["lines"])
        for rx, label in SECRETS:
            if rx.search(body):
                errors.append(f"{where}: possible {label} in '{title}'; remove it")
        if VAGUE.match(title):
            warnings.append(f"{where}: vague title '{title}'; lead with the action")
        if len(title) > 110:
            warnings.append(f"{where}: title over 110 chars")
        if kind in ("PATTERN", "ANTIPATTERN") and not e["fence"]:
            warnings.append(f"{where}: {kind} '{title}' has no code/config shape block")
        if len(e["lines"]) > 25:
            warnings.append(f"{where}: '{title}' is {len(e['lines'])} lines; split or trim")
    return errors, warnings


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 2
    all_err: list[str] = []
    all_warn: list[str] = []
    count = 0
    for f in files:
        p = Path(f)
        if not p.is_file():
            all_err.append(f"{f}: not a file")
            continue
        e, w = lint(p)
        all_err += e
        all_warn += w
        count += len(parse(p.read_text(encoding="utf-8")))
    for w in all_warn:
        print(f"warn  {w}")
    for e in all_err:
        print(f"error {e}")
    print(f"{count} entries, {len(all_err)} error(s), {len(all_warn)} warning(s)")
    return 1 if all_err or (strict and all_warn) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

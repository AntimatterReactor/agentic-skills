#!/usr/bin/env python3
"""Surface candidate learnings from a git repo's history (read-only).

Prints signals that usually hide a lesson:
  1. reverts and fixes          what broke, and what the fix was
  2. removals                   features or code that were built, then dropped
  3. renames                    names that did not survive
  4. churn hotspots             files touched in many commits (fragile or central)
  5. deleted and never restored files that existed once and are gone now
  6. directive lines            "never / always / don't / must" lines added to
                                agent docs (AGENTS.md, CLAUDE.md, ...)

These are *leads*, not learnings. Open the commit, confirm the cause, then
write the entry (see references/entry-format.md).

Usage:
  harvest_git.py [--repo DIR] [--since DATE] [--max-commits N] [--top N] [--json]
Stdlib only; runs git with read-only commands.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SEP = "\x1f"
REC = "\x1e"

FIX_RE = re.compile(r"\b(fix(es|ed)?|bug|broken|regress\w*|crash\w*|hotfix|workaround|oops|revert\w*)\b", re.I)
REMOVE_RE = re.compile(r"\b(remov\w+|drop(ped)?|delet\w+|obsolete|legacy|deprecat\w+)\b", re.I)
RENAME_RE = re.compile(r"\b(renam\w+|moved?)\b", re.I)
DIRECTIVE_RE = re.compile(
    r"\b(never|always|must|do not|don't|dont|avoid|only|instead|gotcha|trap|careful|beware|unless)\b", re.I
)
AGENT_DOCS = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules", "CONTRIBUTING.md", "docs/learnings.md"]
NOISE = re.compile(r"(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|\.lock$|\.png$|\.webp$|\.jpg$|\.json$|\.svg$|\.idea/)")


def git(repo: Path, *args: str) -> str:
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def commits(repo: Path, since: str | None, limit: int) -> list[dict]:
    args = ["log", f"--max-count={limit}", "--numstat", f"--format={REC}%h{SEP}%ad{SEP}%s{SEP}%b{SEP}", "--date=short"]
    if since:
        args.insert(1, f"--since={since}")
    out = git(repo, *args)
    rows = []
    for chunk in out.split(REC)[1:]:
        head, _, stats = chunk.partition(f"{SEP}\n") if f"{SEP}\n" in chunk else (chunk, "", "")
        parts = head.split(SEP)
        if len(parts) < 4:
            continue
        sha, date, subject, body = parts[0], parts[1], parts[2], parts[3]
        added = deleted = 0
        files: list[str] = []
        for line in stats.strip().splitlines():
            cols = line.split("\t")
            if len(cols) != 3:
                continue
            a, d, path = cols
            if a.isdigit() and d.isdigit():
                added += int(a)
                deleted += int(d)
            files.append(path)
        rows.append(dict(sha=sha, date=date, subject=subject.strip(), body=body.strip(), added=added, deleted=deleted, files=files))
    return rows


def directive_lines(repo: Path, since: str | None, limit: int) -> list[dict]:
    present = [p for p in AGENT_DOCS if (repo / p).exists()]
    if not present:
        return []
    args = ["log", f"--max-count={limit}", "-p", "--unified=0", f"--format={REC}%h{SEP}%ad", "--date=short"]
    if since:
        args.insert(1, f"--since={since}")
    out = git(repo, *args, "--", *present)
    found = []
    for chunk in out.split(REC)[1:]:
        head, _, diff = chunk.partition("\n")
        sha, _, date = head.partition(SEP)
        path = ""
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                path = line[6:]
            elif line.startswith("+") and not line.startswith("+++") and DIRECTIVE_RE.search(line):
                text = line[1:].strip()
                if 20 <= len(text) <= 400:
                    found.append(dict(sha=sha, date=date.strip(), file=path, line=text))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository directory (default: .)")
    ap.add_argument("--since", help="only commits after this date, e.g. 2026-10-01 or '3 weeks ago'")
    ap.add_argument("--max-commits", type=int, default=500)
    ap.add_argument("--top", type=int, default=12, help="max rows per section")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    git(repo, "rev-parse", "--git-dir")
    rows = commits(repo, args.since, args.max_commits)
    if not rows:
        print("no commits in range")
        return 0

    def brief(c: dict) -> dict:
        return dict(sha=c["sha"], date=c["date"], subject=c["subject"], added=c["added"], deleted=c["deleted"])

    body_fix = re.compile(r"(?im)^[-*\s]*(fix|fixed|fixes)\b")
    fixes = [brief(c) for c in rows if FIX_RE.search(c["subject"]) or body_fix.search(c["body"])]
    removals = [
        brief(c)
        for c in rows
        if REMOVE_RE.search(c["subject"]) or (c["deleted"] >= 100 and c["deleted"] >= 3 * max(c["added"], 1))
    ]
    renames = [brief(c) for c in rows if RENAME_RE.search(c["subject"])]

    churn: Counter[str] = Counter()
    for c in rows:
        for f in set(c["files"]):
            if not NOISE.search(f):
                churn[f] += 1
    hotspots = [dict(file=f, commits=n) for f, n in churn.most_common(args.top)]

    gone_raw = git(repo, "log", f"--max-count={args.max_commits}", "--diff-filter=D", "--name-only", "--format=").split()
    tracked = set(git(repo, "ls-files").splitlines())
    gone = sorted({f for f in gone_raw if f not in tracked and not NOISE.search(f)})
    directives = []
    seen_lines: set[str] = set()
    for d in directive_lines(repo, args.since, args.max_commits):  # newest first; keep the latest wording
        if d["line"] not in seen_lines:
            seen_lines.add(d["line"])
            directives.append(d)

    report = {
        "commits_scanned": len(rows),
        "range": f"{rows[-1]['date']}..{rows[0]['date']}",
        "reverts_and_fixes": fixes[: args.top],
        "removals": removals[: args.top],
        "renames": renames[: args.top],
        "churn_hotspots": hotspots,
        "deleted_never_restored": gone[: args.top * 2],
        "directive_lines_in_agent_docs": directives[: args.top * 2],
    }
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        print()
        return 0

    print(f"# git harvest: {len(rows)} commits, {report['range']}\n")

    def section(title: str, items: list[dict], fmt) -> None:
        print(f"## {title} ({len(items)})")
        for it in items or []:
            print("  " + fmt(it))
        if not items:
            print("  (none)")
        print()

    cm = lambda c: f"{c['sha']} {c['date']} +{c['added']}/-{c['deleted']}  {c['subject']}"
    section("Reverts and fixes", report["reverts_and_fixes"], cm)
    section("Removals (built, then dropped)", report["removals"], cm)
    section("Renames", report["renames"], cm)
    section("Churn hotspots", hotspots, lambda h: f"{h['commits']:>3} commits  {h['file']}")
    section("Deleted and never restored", [dict(f=f) for f in report["deleted_never_restored"]], lambda h: h["f"])
    section(
        "Directive lines added to agent docs",
        report["directive_lines_in_agent_docs"],
        lambda d: f"{d['sha']} {d['file']}: {d['line'][:200]}",
    )
    print("Next: open each lead (git show <sha>), confirm the cause, then write an entry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

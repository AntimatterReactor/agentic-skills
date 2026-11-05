#!/usr/bin/env python3
"""Claude Code Stop hook: keep agent working until tests pass (bounded).

Configure in .claude/settings.json:
  {"hooks": {"Stop": [{"hooks": [{"type": "command",
     "command": "python3 /abs/path/stop_hook.py --cmd 'npm test' --max 5"}]}]}}

Behavior:
  - Runs --cmd. Pass → exit 0 (agent may stop), counter reset.
  - Fail → print tail of output to stderr, exit 2 (Claude Code blocks the stop
    and feeds stderr back to the agent so it keeps fixing).
  - After --max consecutive blocked stops → exit 0 and tell agent to report.
Counter stored in .claude/.test-loop-count (per project). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True, help="test command to run")
    ap.add_argument("--max", type=int, default=5, help="max consecutive blocked stops")
    ap.add_argument("--timeout", type=int, default=600, help="seconds")
    ap.add_argument("--tail", type=int, default=60, help="output lines to feed back")
    args = ap.parse_args()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd = Path(payload.get("cwd") or ".")
    counter = cwd / ".claude" / ".test-loop-count"
    count = int(counter.read_text()) if counter.is_file() and counter.read_text().strip().isdigit() else 0

    try:
        proc = subprocess.run(args.cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=args.timeout)
        ok, output = proc.returncode == 0, (proc.stdout + proc.stderr)
    except subprocess.TimeoutExpired:
        ok, output = False, f"test command timed out after {args.timeout}s"

    if ok:
        counter.unlink(missing_ok=True)
        return 0

    count += 1
    if count > args.max:
        counter.unlink(missing_ok=True)
        print(f"test-loop: still failing after {args.max} attempts; stopping loop. Report remaining failures to user.", file=sys.stderr)
        return 0

    counter.parent.mkdir(parents=True, exist_ok=True)
    counter.write_text(str(count))
    tail = "\n".join(output.strip().splitlines()[-args.tail:])
    print(
        f"test-loop attempt {count}/{args.max}: `{args.cmd}` failed. Fix root cause "
        f"(do not skip/disable tests or weaken assertions), then finish again.\n\n{tail}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

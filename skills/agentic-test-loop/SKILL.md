---
name: agentic-test-loop
description: Sets up and runs a continuous agentic testing loop — detect test/lint/typecheck commands, run them, triage failures, fix root causes, rerun, repeat until green or budget runs out; optionally keep it running via /loop, a Stop hook, or scheduled runs. Use when the user asks for a "test loop", "testing loop", "keep running tests until they pass", "fix all failing tests", "continuous testing", "TDD loop", "watch and fix", or "make CI green".
---

# Agentic Test Loop

Loop: **run → triage → fix → rerun**, until green or budget exhausted. Then optionally keep it running continuously.

## 1. Setup (AFWF-style, once)

Detect commands:
```bash
python3 <skill-dir>/scripts/detect_test_cmd.py <project-dir>
```
Prints JSON of candidate `test`, `lint`, `typecheck`, `build` commands. Verify each runs (`--help`, dry run, or quick execution) before relying on it.

Then ask **one batch** of questions, each with a default:
1. Commands to loop on — default: detected test + lint + typecheck.
2. Scope — default: whole suite; or a path/package.
3. Budget — default: max 10 iterations, stop if same failure survives 3 fixes.
4. May fix source only, or tests too? — default: **source only**; change a test only when it is provably wrong, and say so.
5. Commit fixes? — default: one commit per green iteration, no push.
6. Continuous mode — default: none (one-shot). Options in §3.

## 2. Loop

Each iteration:

1. **Run** full selected commands. Capture output to `.agentic/test-runs/<n>.log` (gitignored) if long.
2. **Triage**:
   - Group failures by root cause, not by test name (one broken import can fail 40 tests).
   - Order: build/compile errors → typecheck → test failures → lint.
   - Suspect flaky? Rerun that test 3×. Passes sometimes → mark flaky, report, don't "fix" by retry wrappers.
3. **Fix** the highest-leverage root cause first. Minimal change. Several independent causes → fix in parallel (or spawn agents if `ultracode` is on).
4. **Rerun failing subset** fast (e.g. `pytest -x path::test`, `npm test -- -t name`, `cargo test name`), then full suite to catch regressions.
5. **Record** in `.agentic/test-loop.md`: iteration, failures before/after, what changed.

Exit when:
- All green → final full run to confirm.
- Budget hit, or same failure survives 3 attempts → stop, report.
- Fix needs a decision outside agreed scope (API change, dependency upgrade, test expectation change) → finish other fixes, then ask one batched question.

## 3. Continuous modes

| Mode | How | Good for |
|------|-----|----------|
| In-session interval | `/loop 10m run one agentic-test-loop iteration on <scope>` | Long sessions while code changes |
| Self-paced | `/loop run agentic-test-loop until green` | Unattended fix-up |
| Stop hook | `scripts/stop_hook.py` blocks agent from finishing while tests fail | Every task ends green |
| Scheduled | Scheduled task / cron / CI nightly running this skill | Catch drift, flaky tests |

### Stop hook
Add to project `.claude/settings.json` (merge with existing `hooks`; use absolute path):
```json
{
  "hooks": {
    "Stop": [
      {"hooks": [{"type": "command",
        "command": "python3 /abs/path/agentic-test-loop/scripts/stop_hook.py --cmd 'npm test' --max 5"}]}
    ]
  }
}
```
On failure the hook exits 2 and feeds the tail of the output back, so the agent keeps fixing. After `--max` consecutive blocks it lets the agent stop and report — no infinite loop. Use a **fast** command here (unit tests, not e2e). Add `.claude/.test-loop-count` to `.gitignore`.

## Rules (never break)
- Never skip, delete, disable, quarantine, or `xfail` tests to get green.
- Never weaken assertions or widen tolerances unless the test is provably wrong — and say so in report.
- Never add blanket retries or sleeps to hide flakiness.
- Never commit generated logs; keep `.agentic/test-runs/` gitignored.
- Don't push or open PRs unless pre-approved.

## Report
- Start vs. end: failing counts per command.
- Root causes fixed (one line each, file:line).
- Flaky tests found.
- Remaining failures + why stopped (budget / needs decision).

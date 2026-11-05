---
name: agentic-perf-loop
description: Continuous agentic performance-improvement loop — set a measurable target, benchmark a baseline, profile to find the hotspot, apply one optimization at a time, re-benchmark with repeated runs, keep only statistically real wins that pass tests, revert the rest, and repeat until target or budget. Use when the user asks to "make it faster", "optimize performance", "perf loop", "speed up", "reduce latency / memory / bundle size / build time", "profile and fix", or "keep optimizing".
---

# Agentic Perf Loop

Loop: **measure → profile → change one thing → measure → keep or revert**. Every kept change is backed by numbers and green tests.

Composes with: `afwf` (setup questions), `agentic-test-loop` (correctness gate), `ultracode` (parallel experiments in separate worktrees).

## 1. Setup (AFWF, once)

Recon: find entry points, existing benchmarks (`bench/`, `criterion`, `pytest-benchmark`, `hyperfine`, `vitest bench`, `go test -bench`), profilers available, test commands (`agentic-test-loop/scripts/detect_test_cmd.py`).

Ask one batch, each with default:
1. **Metric** — default: wall time of the main workload. Alternatives: p95 latency, throughput, peak memory, bundle size, build time, startup time.
2. **Workload** — exact command/benchmark that represents real use. Default: existing benchmark, else a script you write and show.
3. **Target** — default: stop at 20% improvement or when 3 iterations in a row yield nothing.
4. **Allowed changes** — default: algorithms, data structures, caching, I/O batching, concurrency within existing deps. Ask before: new dependencies, API/behavior changes, build flags, infra.
5. **Trade-offs** — default: no readability-destroying micro-opts for <5% gain; memory may grow ≤10% for speed.
6. **Commit** — default: one commit per kept win, no push.

## 2. Baseline

```bash
python3 <skill-dir>/scripts/bench.py --cmd '<workload>' --runs 10 --warmup 2 --save .agentic/perf/baseline.json
```
- Run tests first; never optimize a red build.
- Quiet machine: close heavy processes; same power/CPU settings across runs.
- Noise check: if stdev > 10% of median, raise `--runs` or stabilize workload before continuing.
- Non-time metrics (memory, size): measure with the right tool (`/usr/bin/time -v`, `du`, bundle analyzer) and record in log.

## 3. Loop (each iteration)

1. **Profile** current code — don't guess. Python `py-spy`/`cProfile`, Node `--cpu-prof`/`clinic`, Rust/C `perf`/`flamegraph`, Go `pprof`, browser Performance panel. Find the top hotspot by self/total time.
2. **Hypothesize** one change targeting that hotspot; write expected gain in log.
3. **Change one thing.** Smallest diff that tests the hypothesis.
4. **Verify correctness**: test suite green (use `agentic-test-loop` budget if it breaks).
5. **Measure**:
   ```bash
   python3 <skill-dir>/scripts/bench.py --cmd '<workload>' --runs 10 --compare .agentic/perf/baseline.json
   ```
   Verdict `IMPROVED` (exit 0) / `REGRESSED` (3) / `NOISE` (4).
6. **Decide**:
   - IMPROVED + green → commit `perf: <change> (-X% <metric>)`, re-save new baseline.
   - NOISE or REGRESSED → revert (`git checkout -- <files>` / `git stash`), log as tried-and-rejected.
7. **Log** to `.agentic/perf-loop.md`: iteration, hotspot, hypothesis, result numbers, kept/reverted.

Parallel experiments (ultracode): give each agent its own worktree and one hypothesis; benchmark sequentially on same machine so numbers compare fairly.

## 4. Stop when
- Target hit.
- 3 consecutive iterations with no kept win.
- Next hotspot needs a change outside allowed scope → finish, then ask one batched question.

## Rules
- One change per measurement. Never stack untested optimizations.
- Never keep a change without numbers; never trust a single run.
- Never break behavior for speed: outputs, APIs, error handling stay identical unless approved.
- Never "optimize" by deleting work the program must do (skipping validation, caching stale data, lowering precision) without approval.
- Never tune benchmarks to flatter the result (smaller inputs, warm caches that real use won't have).
- Keep `.agentic/perf/` raw results gitignored; commit only the log if wanted.

## Report
- Baseline → final numbers (median, p95), total % change.
- Kept wins: one line each with % and commit.
- Rejected attempts: one line each (what, why).
- Next hotspot + suggested next step.

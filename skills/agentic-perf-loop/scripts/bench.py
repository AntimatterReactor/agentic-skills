#!/usr/bin/env python3
"""Benchmark a shell command with repeated runs; save or compare results.

Usage:
  bench.py --cmd 'CMD' [--runs 10] [--warmup 2] [--save base.json]
  bench.py --cmd 'CMD' --compare base.json [--threshold 3]

Measures wall time per run. Reports min / median / p95 / mean / stdev / MAD.
--compare verdict:
  IMPROVED   median faster by > max(threshold%, noise)   (exit 0)
  REGRESSED  median slower by > max(threshold%, noise)   (exit 3)
  NOISE      difference inside noise band               (exit 4)
noise = 2 * max(MAD_base, MAD_new) / median_base * 100 (%).
Command failure → exit 1. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import subprocess
import sys
import time


def run_once(cmd: str, timeout: int) -> float:
    t0 = time.perf_counter()
    p = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=timeout)
    dt = time.perf_counter() - t0
    if p.returncode != 0:
        sys.stderr.write(f"command failed (exit {p.returncode}):\n{p.stderr[-2000:]}\n")
        sys.exit(1)
    return dt


def summarize(times: list[float]) -> dict:
    s = sorted(times)
    med = st.median(s)
    return {
        "runs": len(s),
        "min": s[0],
        "median": med,
        "p95": s[min(len(s) - 1, round(0.95 * (len(s) - 1)))],
        "mean": st.fmean(s),
        "stdev": st.stdev(s) if len(s) > 1 else 0.0,
        "mad": st.median([abs(x - med) for x in s]),
        "times": s,
    }


def fmt(r: dict) -> str:
    ms = lambda x: f"{x * 1000:.1f}ms"
    return (f"runs={r['runs']} min={ms(r['min'])} median={ms(r['median'])} p95={ms(r['p95'])} "
            f"mean={ms(r['mean'])} stdev={ms(r['stdev'])} mad={ms(r['mad'])}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cmd", required=True)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--save")
    ap.add_argument("--compare")
    ap.add_argument("--threshold", type=float, default=3.0, help="min %% change to count")
    a = ap.parse_args()

    for _ in range(a.warmup):
        run_once(a.cmd, a.timeout)
    res = summarize([run_once(a.cmd, a.timeout) for _ in range(a.runs)])
    res["cmd"] = a.cmd
    print(fmt(res))

    if a.save:
        with open(a.save, "w") as f:
            json.dump(res, f, indent=2)
        print(f"saved {a.save}")

    if a.compare:
        with open(a.compare) as f:
            base = json.load(f)
        bm, nm = base["median"], res["median"]
        change = (bm - nm) / bm * 100  # positive = faster
        noise = 2 * max(base["mad"], res["mad"]) / bm * 100
        band = max(a.threshold, noise)
        print(f"base median={bm * 1000:.1f}ms new median={nm * 1000:.1f}ms change={change:+.1f}% (band ±{band:.1f}%)")
        if change > band:
            print("IMPROVED")
            return 0
        if change < -band:
            print("REGRESSED")
            return 3
        print("NOISE")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())

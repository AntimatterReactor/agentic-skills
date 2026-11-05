#!/usr/bin/env python3
"""Detect test / lint / typecheck / build commands for a project.

Usage: python3 detect_test_cmd.py [project_dir]
Prints JSON: {"test": [...], "lint": [...], "typecheck": [...], "build": [...], "sources": [...]}
Stdlib only. Heuristic: verify each command before relying on it.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path


def detect(root: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"test": [], "lint": [], "typecheck": [], "build": [], "sources": []}

    def add(kind: str, cmd: str, src: str) -> None:
        if cmd not in out[kind]:
            out[kind].append(cmd)
        if src not in out["sources"]:
            out["sources"].append(src)

    pkg = root / "package.json"
    if pkg.is_file():
        try:
            scripts = json.loads(pkg.read_text()).get("scripts", {}) or {}
        except json.JSONDecodeError:
            scripts = {}
        runner = "npm run"
        if (root / "pnpm-lock.yaml").exists():
            runner = "pnpm run"
        elif (root / "yarn.lock").exists():
            runner = "yarn"
        elif (root / "bun.lockb").exists() or (root / "bun.lock").exists():
            runner = "bun run"
        for name in scripts:
            n = name.lower()
            kind = None
            if n == "test" or n.startswith("test:"):
                kind = "test"
            elif n.startswith("lint"):
                kind = "lint"
            elif n in ("typecheck", "type-check", "tsc", "check-types"):
                kind = "typecheck"
            elif n == "build":
                kind = "build"
            if kind:
                add(kind, f"{runner} {name}", "package.json")

    pyproject = root / "pyproject.toml"
    py_cfg = {}
    if pyproject.is_file():
        try:
            py_cfg = tomllib.loads(pyproject.read_text())
        except tomllib.TOMLDecodeError:
            py_cfg = {}
    tool = py_cfg.get("tool", {})
    if "pytest" in tool or (root / "pytest.ini").exists() or (root / "conftest.py").exists() or (root / "tests").is_dir() and any((root / "tests").glob("test_*.py")):
        add("test", "python3 -m pytest", "pyproject.toml/pytest")
    if "ruff" in tool or (root / "ruff.toml").exists():
        add("lint", "ruff check .", "ruff")
    if "mypy" in tool or (root / "mypy.ini").exists():
        add("typecheck", "mypy .", "mypy")

    if (root / "Cargo.toml").is_file():
        add("test", "cargo test", "Cargo.toml")
        add("lint", "cargo clippy -- -D warnings", "Cargo.toml")
        add("build", "cargo build", "Cargo.toml")
    if (root / "go.mod").is_file():
        add("test", "go test ./...", "go.mod")
        add("lint", "go vet ./...", "go.mod")
        add("build", "go build ./...", "go.mod")

    for mk in ("Makefile", "makefile", "GNUmakefile"):
        f = root / mk
        if f.is_file():
            targets = set(re.findall(r"^([A-Za-z0-9_.-]+):", f.read_text(), re.M))
            for t, kind in (("test", "test"), ("check", "test"), ("lint", "lint"), ("typecheck", "typecheck"), ("build", "build")):
                if t in targets:
                    add(kind, f"make {t}", mk)
            break

    if (root / "justfile").is_file() or (root / "Justfile").is_file():
        jf = root / "justfile" if (root / "justfile").is_file() else root / "Justfile"
        recipes = set(re.findall(r"^([A-Za-z0-9_-]+)\s*:", jf.read_text(), re.M))
        for t in ("test", "lint", "build"):
            if t in recipes:
                add(t, f"just {t}", jf.name)

    if not out["test"] and (root / "scripts").is_dir():
        for p in sorted((root / "scripts").glob("*")):
            if re.search(r"(test|validate|check)", p.name):
                add("test", f"python3 {p.relative_to(root)}" if p.suffix == ".py" else str(p.relative_to(root)), "scripts/")
    return out


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    print(json.dumps(detect(root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

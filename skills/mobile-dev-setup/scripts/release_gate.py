#!/usr/bin/env python3
"""Pre-release gate for an Android Gradle project (read-only).

Checks the things that were expensive to get wrong in a first Play release:
  - versionCode never goes backwards vs. git history
  - signing material exists locally, is gitignored, and is not tracked
  - no signing passwords or key files committed
  - a Room schema JSON exists for the current @Database version
  - destructive-migration fallbacks are only for versions that never shipped
  - billing library => licence key set (a blank key makes purchases never unlock)
  - release build has R8/minify on and keep rules exist
  - privacy policy and store listing docs exist; manifest permissions listed
  - tracked data files (csv/db/sqlite) that look like real user data
  - working tree is clean

Usage: release_gate.py [project_dir]
Exit 1 when any FAIL. Stdlib only.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

results: list[tuple[str, str]] = []


def add(level: str, msg: str) -> None:
    results.append((level, msg))


def git(root: Path, *args: str) -> str | None:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"FAIL no such directory: {root}")
        return 1
    is_git = git(root, "rev-parse", "--git-dir") is not None
    build = next((p for p in (root / "app/build.gradle.kts", root / "app/build.gradle") if p.is_file()), None)
    if build is None:
        print("FAIL no app/build.gradle[.kts]; run from the project root")
        return 1
    btxt = read(build)
    rel_build = build.relative_to(root).as_posix()

    # --- identity and versions ------------------------------------------
    app_id = re.search(r'applicationId\s*=\s*"([^"]+)"', btxt)
    vcode = re.search(r"versionCode\s*=\s*(\d+)", btxt)
    vname = re.search(r'versionName\s*=\s*"([^"]+)"', btxt)
    if app_id:
        add("INFO", f"applicationId {app_id.group(1)}")
        if app_id.group(1).startswith("com.example."):
            add("FAIL", "applicationId is a com.example.* placeholder; Play rejects it and it cannot change after the first upload")
    else:
        add("FAIL", "no applicationId found")
    if vcode:
        n = int(vcode.group(1))
        add("INFO", f"versionCode {n}, versionName {vname.group(1) if vname else '?'}")
        if is_git:
            hist = git(root, "log", "-p", "--format=", "-G", r"versionCode\s*=", "--", rel_build) or ""
            seen = [int(x) for x in re.findall(r"^[+-].*?versionCode\s*=\s*(\d+)", hist, re.M)]
            if seen and n < max(seen):
                add("FAIL", f"versionCode {n} is lower than {max(seen)} in history; Play only accepts increasing codes")
            elif seen:
                add("PASS", f"versionCode {n} >= highest in history ({max(seen)}); bump it for every Play upload")
    else:
        add("FAIL", "no versionCode found")

    # --- signing --------------------------------------------------------
    ks = root / "keystore.properties"
    if ks.is_file():
        add("PASS", "keystore.properties present")
        if is_git:
            ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "keystore.properties"]).returncode == 0
            add("PASS" if ignored else "FAIL", "keystore.properties is gitignored" if ignored else "keystore.properties is NOT gitignored")
    else:
        add("WARN", "no keystore.properties: a release build would be unsigned (fine for CI that injects it)")
    if is_git:
        tracked = (git(root, "ls-files") or "").splitlines()
        keys = [f for f in tracked if re.search(r"\.(jks|keystore|p12|pfx)$", f)]
        if keys:
            add("FAIL", f"signing key file(s) tracked in git: {', '.join(keys)}")
        else:
            add("PASS", "no key files tracked")
        leaks = []
        for f in tracked:
            txt = read(root / f)
            if f.endswith(".properties"):
                pat = r"(?im)^\s*(storePassword|keyPassword)\s*=\s*([^\s$<]+)\s*$"
            elif f.endswith((".kts", ".gradle", ".sh", ".md")):
                pat = r"""(?im)\b(storePassword|keyPassword)\s*[=:]\s*["']([^"'$<\s]{4,})["']"""  # quoted literals only; lookups like getProperty(...) are fine
            else:
                continue
            if re.search(pat, txt):
                leaks.append(f)
        if leaks:
            add("FAIL", f"signing password assignment in tracked file(s): {', '.join(sorted(set(leaks)))}")
        data = [f for f in tracked if re.search(r"\.(csv|sqlite3?|db)$", f) and "/test" not in f and "/androidTest" not in f and "schemas" not in f]
        if data:
            add("WARN", f"tracked data files (real user data?): {', '.join(data[:5])}")
        untracked_data = [l[3:] for l in (git(root, "status", "--porcelain") or "").splitlines() if l.startswith("??") and re.search(r"\.(csv|sqlite3?|db)$", l)]
        if untracked_data:
            add("INFO", f"untracked data files, keep them out of commits (git add explicit paths): {', '.join(untracked_data[:5])}")

    # --- release build type --------------------------------------------
    rel = re.search(r"release\s*\{(.*?)\n\s{4}\}", btxt, re.S)
    block = rel.group(1) if rel else btxt
    minify = re.search(r"isMinifyEnabled\s*=\s*true|optimization\s*\{\s*enable\s*=\s*true", block, re.S)
    add("PASS" if minify else "WARN", "release build has R8/minify enabled" if minify else "release build is not minified (R8 off); fine for a first smoke test, not for production")
    keep_dir = root / "app/src/main/keepRules"
    rules = list(keep_dir.glob("*")) if keep_dir.is_dir() else []
    rules += [p for p in (root / "app").glob("proguard*.pro")]
    if minify and not rules:
        add("WARN", "R8 on but no keep rules found; enums stored in DB/backup/JSON need `-keep enum <pkg>.** { *; }`")
    elif rules:
        txt = "".join(read(p) for p in rules)
        add("PASS" if "enum" in txt else "WARN", "keep rules mention enums" if "enum" in txt else "keep rules exist but none keep enums; names persisted to DB/JSON break when R8 renames them")

    # --- Room schema ----------------------------------------------------
    ver = None
    for p in (root / "app/src/main").rglob("*.kt"):
        m = re.search(r"@Database\([^)]*?version\s*=\s*(\d+)", read(p), re.S)
        if m:
            ver = int(m.group(1))
            break
    if ver is not None:
        schemas = list((root / "app/schemas").rglob(f"{ver}.json"))
        add("PASS" if schemas else "FAIL", f"schema {ver}.json exported" if schemas else f"@Database version {ver} has no app/schemas/**/{ver}.json (commit exported schemas; migration tests need them)")
        destructive = []
        for p in (root / "app/src/main").rglob("*.kt"):
            t = read(p)
            if re.search(r"fallbackToDestructiveMigration\s*\(", t):
                destructive.append(p.name)
            if re.search(r"fallbackToDestructiveMigrationFrom", t):
                add("INFO", f"destructive fallback FROM specific versions in {p.name}: confirm those versions never shipped")
        if destructive:
            add("FAIL", f"unconditional fallbackToDestructiveMigration() in {', '.join(destructive)}: wipes user data on any missing migration")
    else:
        add("INFO", "no Room @Database found; skipped schema checks")

    # --- billing --------------------------------------------------------
    catalog = read(root / "gradle/libs.versions.toml") + btxt
    if re.search(r"billing", catalog, re.I):
        props = read(root / "gradle.properties") + read(Path.home() / ".gradle/gradle.properties")
        key = re.search(r"(?m)^playLicenseKey\s*=\s*(\S+)", props)
        if key:
            add("PASS", "Play licence key is set")
        else:
            add("FAIL", "billing library present but no playLicenseKey: signature checks fail closed and purchases never unlock")
        add("INFO", "Billing adds INTERNET and ACCESS_NETWORK_STATE: privacy policy and Data safety answers must say so")

    # --- manifest and docs ---------------------------------------------
    man = read(root / "app/src/main/AndroidManifest.xml")
    perms = re.findall(r'<uses-permission[^>]*android:name="([^"]+)"', man)
    add("INFO", f"manifest permissions: {', '.join(p.rsplit('.', 1)[-1] for p in perms) or 'none declared (libraries may merge more)'}")
    docs = [p.relative_to(root).as_posix() for p in root.rglob("*.md") if not any(x in p.parts for x in ("node_modules", "build", ".git"))]
    for label, rx in (("privacy policy", r"privacy"), ("store listing", r"store-?listing|play-?listing")):
        hit = [d for d in docs if re.search(rx, d, re.I)]
        add("PASS" if hit else "WARN", f"{label}: {hit[0]}" if hit else f"no {label} document found" + (" (Play needs a hosted privacy-policy URL for most apps)" if label == "privacy policy" else " (draft the listing text, data-safety and content-rating answers in docs/)"))

    # --- tree state ------------------------------------------------------
    if is_git:
        dirty = [l for l in (git(root, "status", "--porcelain") or "").splitlines() if not l.startswith("??")]
        add("PASS" if not dirty else "WARN", "working tree has no modified tracked files" if not dirty else f"{len(dirty)} modified tracked file(s); release from a clean commit so the build is reproducible")

    order = {"FAIL": 0, "WARN": 1, "PASS": 2, "INFO": 3}
    for level, msg in sorted(results, key=lambda r: order[r[0]]):
        print(f"{level} {msg}")
    fails = sum(1 for l, _ in results if l == "FAIL")
    print(f"\n{fails} FAIL, {sum(1 for l, _ in results if l == 'WARN')} WARN")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

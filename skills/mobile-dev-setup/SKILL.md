---
name: mobile-dev-setup
description: Generalized playbook for creating a mobile app end to end, distilled from the RecItDown Android app (Kotlin, Room, Robolectric/Roborazzi, Play Billing, Play Store release; Linux/WSL host). Covers choosing the stack and app id, toolchain and wrapper scripts, a device-free dev loop, data and migrations, theming, home-screen widgets and shortcuts, Free/Pro monetization, signing, R8, store listing, privacy policy, store screenshots, and release gating. Use when the user wants to start, set up, scaffold, or ship a mobile or Android app, set up an Android dev environment (WSL), add Play Billing or a widget, plan a Play release, or says "mobile dev setup". Android is verified; iOS, Flutter, and React Native get principles only.
---

# Mobile Dev Setup

What building a real mobile app took, from the RecItDown repo (70 commits, 2026-09-08 to 2026-11-05; offline Android ledger from raw SQLite to a signed AAB with in-app purchase). Android specifics are verified against that repo. Other platforms: use the *principles* (decide ids early, test migrations, device-free loop, gate releases) and confirm tooling against current docs; nothing here was verified for iOS, Flutter, or React Native.

Composes with: `afwf` (the setup question batch), `agentic-test-loop` (run the loop until green), `ultracode` (parallel work), `agent-learn` (record what this project teaches), `craft-connect` (design apps), `agentic-build-loop` (grow scope per iteration).

## 1. Recon (read-only)

- Existing project? `scripts/android_env_check.sh <dir>` checks JDK, wrapper, SDK, compileSdk platform, adb, Gradle flags, `.gitignore`, LFS (add `--devices` to list adb devices).
- Read the project's agent docs (`AGENTS.md`, `CLAUDE.md`), `SCHEME`/`TODO`-style plan docs, and `git log`. Follow what they say over this skill.
- Check for human-only sections, real-user data in the repo, and where signing material lives.

## 2. Setup questions (one batch, defaults first)

Ask these together; recon answers some. Each default is what RecItDown did or learned.

| # | Question | Default | Why |
|---|----------|---------|-----|
| 1 | One-paragraph pitch, principles, and **non-goals**? | none; must ask | a built-then-cut module cost thousands of lines |
| 2 | Platform and UI toolkit? | native Android, Kotlin; match the existing toolkit (RecItDown = Views); Compose is the usual choice for new UI, but RecItDown does not validate it | iOS needs macOS; cross-platform only if both ship day one |
| 3 | Final **app name and `applicationId`**? | decide now, never `com.example.*` | renames moved real data to a new install |
| 4 | minSdk / target? | minSdk 29, compile/target latest stable | per project |
| 5 | Data: local only or backend? Sensitive? | local Room + Flow, versioned JSON backup | drives privacy policy and Data safety |
| 6 | Money model? | free core; one-time lifetime Pro via Play Billing; no ads; data-safety features never paywalled | ads and subscriptions were rejected with reasons |
| 7 | Home-screen surfaces (shortcuts, widget)? | shortcuts yes, widget if the core action is one tap | see `references/ui-and-surfaces.md` |
| 8 | Does a real device hold the owner's real data? | assume yes: back up before migrations, never drive their phone | |
| 9 | Distribution? | Google Play: internal → closed → staged production | new personal accounts need a 12-tester, 14-day closed test (verify) |
| 10 | Git: commit, push? LFS? | no commits unless asked; LFS for binaries | match the owner's rule |

Also ask: host OS (WSL/Linux/macOS/Windows), physical phone available, owner's account status (Play Console, payments profile, EU trader details).

## 3. Phases and gates

| Phase | Do | Done when |
|-------|----|-----------|
| 0 Plan | `SCHEME.md`-style doc: pitch, principles, scope, non-goals, data draft, milestones, open questions | owner confirms; milestones have dates or issues |
| 1 Environment | install SDK + JDK; root wrappers `build.sh`, `test.sh`, `run_app.sh`, `scripts/loop.sh`; `gradle.properties` caching; `.gitignore` + LFS; [toolchain.md](references/toolchain.md) | `android_env_check.sh` has no FAIL; `./build.sh` builds |
| 2 Skeleton | single `:app`, version catalog, final id, theme tokens, nav shell, ViewBinding/Compose setup | app launches in tests |
| 3 Data | Room + Flow + KSP, converters, exported schemas, `testDb()`, first `MigrationTest`; [data-layer.md](references/data-layer.md) | DAO tests green; schema JSON committed |
| 4 Dev loop | Robolectric + Roborazzi `ScreenTest`, text view dump, `scripts/dev_loop.sh`; [dev-loop-testing.md](references/dev-loop-testing.md) | loop is the default check after every change |
| 5 Features | one milestone at a time: plan commit → code commits → docs-done commit; pure cores tested on JVM | loop green; `AGENTS.md` updated in the same commit |
| 6 Surfaces | shortcuts, invisible entry activity, widget; [ui-and-surfaces.md](references/ui-and-surfaces.md) | tap-to-result tested via the pure core |
| 7 Money | decision record, `Pro.decide`, billing wrapper, caps, freeze, privacy update; [monetization.md](references/monetization.md) | unit tests green; test-track purchase works |
| 8 Release | signing, R8 + keep rules, `release.sh`, `release_gate.py`, listing, policy, Data safety; [release-store.md](references/release-store.md) | gate has no FAIL; internal-testing install works |
| 9 Store media | screenshots from `StoreShotsTest` on demo data; feature graphic; optional video | assets in `docs/`, LFS tracked, no real data |
| 10 Post-launch | staged rollout, vitals, next milestones | issues filed per milestone |

Do not skip a gate to move faster; the history shows rework from deciding the app id and the scope late.

## 4. Scripts

```bash
python3 -I <skill-dir>/scripts/release_gate.py <project>          # pre-release checks, exit 1 on FAIL
<skill-dir>/scripts/android_env_check.sh <project> [--devices]    # toolchain check, read-only
<skill-dir>/scripts/dev_loop.sh [--record] [--module app] [gradle args]   # terse test + golden loop
```

`dev_loop.sh` is a generalised, hardened copy of RecItDown's `scripts/loop.sh`: copy it into the project as `scripts/loop.sh`. Set `LOOP_VERIFY_TASK=:app:testDebugUnitTest` when the project has no Roborazzi. Stub-tested for failing tests, golden diffs, compile errors, and stale results.

## 5. Hard rules

- **Never destructive-migrate a shipped version.** Real `Migration` + `MigrationTest` from an exported schema.
- **Never commit, print, or paste** keystores, `keystore.properties`, passwords, or the owner's real data (CSV exports, DB files). Use `git add <paths>`, not `git add -A`, when untracked data files sit in the tree.
- **Never drive the owner's phone** or clear its data; run the loop and give them a short numbered list to try.
- **Initialise process-wide state in every entry point** (shortcut, widget, receiver), not just the main activity.
- **Record goldens in one environment only**; look at the new PNGs before committing them.
- **Billing and migrations reach users only through Play internal testing first.**
- **No real user data in screenshots, videos, or fixtures.**
- Bump `versionCode` per upload; keep enum names safe from R8; update the privacy policy when a permission or SDK is added.
- Follow the owner's conventions (RecItDown's owner: no commits and no code comments unless asked). Ask if unknown.

Full set with evidence: [references/lessons.md](references/lessons.md) (34 entries in `agent-learn` format).

## 6. Report

End each phase with: what changed, gate result (loop / env check / release gate output), what the human must check on a device or test track (a numbered list), and open questions.

## Resources

- `scripts/android_env_check.sh`, `scripts/dev_loop.sh`, `scripts/release_gate.py`: described above.
- `references/toolchain.md`: stack versions, WSL layout, JDK/daemon, adb and usbipd, repo hygiene.
- `references/data-layer.md`: Room + Flow, migration rules and test pattern, converters, prefs, backup.
- `references/dev-loop-testing.md`: loop internals, ScreenTest anatomy, testable cores, store shots, blind spots.
- `references/ui-and-surfaces.md`: toolkit, theming, accent overlays, edge-to-edge, perf traps, shortcuts and widget.
- `references/monetization.md`: decision record, billing shape, caps and freeze, testing limits, prerequisites.
- `references/release-store.md`: signing, R8, tracks, store listing, privacy policy, assets, Play rules.
- `references/lessons.md`: 34 evidence-backed Do/Don't/Pattern/Antipattern entries.
- `references/history.md`: the git log digest: timeline, cadence, reversals.

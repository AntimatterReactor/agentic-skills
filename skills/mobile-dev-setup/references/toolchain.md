# Toolchain (Android; Linux/WSL host)

Verified in RecItDown unless marked *(general)*. Versions are a 2026-11 snapshot; check for newer before copying.

## Stack snapshot

| Piece | Used | Notes |
|-------|------|-------|
| AGP / Gradle | 9.4.0 / 9.6.0 | wrapper pins `distributionSha256Sum`, `validateDistributionUrl=true` |
| SDK | compile/target 37, minSdk 29 | Java 11 bytecode |
| Language | Kotlin + KSP 2.3.12 | `app/build.gradle.kts` applies only `android.application`, `ksp`, `androidx.room`, `roborazzi`; no separate Kotlin plugin |
| UI | Views + ViewBinding, Material Components 1.14.0 | no Compose, no Navigation library |
| Data | Room 2.8.5 + Flow, coroutines 1.10.2, lifecycle 2.11.0 | schemas exported |
| Billing | `billing-ktx` 9.1.0 | see [monetization.md](monetization.md) |
| Tests | JUnit 4.13.2, Robolectric 4.16, Roborazzi 1.76.0, Espresso 3.5.1 | JVM only; instrumented tests need a device |

Single module (`:app`), version catalog `gradle/libs.versions.toml`, `RepositoriesMode.FAIL_ON_PROJECT_REPOS`, `google()` content-filtered in `pluginManagement`.

## WSL layout

- **SDK** at `~/Android/Sdk`; `local.properties` has `sdk.dir=/home/<user>/Android/Sdk` (gitignored). Packages: `platforms;android-37.0`, `build-tools;36.0.0`, `platform-tools`, `cmdline-tools;latest`. Accept licences once with `sdkmanager --licenses`.
- **JDK**: a system JDK 17 only launches the wrapper. The daemon runs on JDK 25, pinned in `gradle/gradle-daemon-jvm.properties` (generate with `./gradlew updateDaemonJvm`) and auto-provisioned into `~/.gradle/jdks` by the `org.gradle.toolchains.foojay-resolver-convention` plugin (1.0.0) in `settings.gradle.kts`. Without the resolver plugin a pinned daemon JVM does not download itself.
- **`gradle.properties`**: `org.gradle.parallel=true`, `org.gradle.caching=true`, `org.gradle.configuration-cache=true`, `org.gradle.jvmargs=-Xmx3g`. It started at `-Xmx2048m` with parallel commented out and was raised in the WSL switch (c852e02); the commit does not say why, so treat 3g as a working value, not a requirement.
- **Wrapper scripts at the repo root**, each `set -uo pipefail` (most with `-e`) and `--console=plain` so output is readable by an agent:
  - `build.sh` → `:app:assembleDebug`
  - `test.sh` → `assembleDebug` + `testDebugUnitTest`
  - `scripts/loop.sh` → the device-free loop ([dev-loop-testing.md](dev-loop-testing.md))
  - `run_app.sh [IP:PORT]` → build, `adb install -r`, `am start -n <pkg>/.MainActivity` (optional `adb connect` first)
  - `release.sh` → signed APK + AAB, with guard rails ([release-store.md](release-store.md))
- **Windows to WSL** (2026-10-21, c852e02): the first wrappers called `cmd.exe /c gradlew.bat` with Android Studio's JBR. Everything moved to the Linux wrapper in WSL; Android Studio remains optional for editing. Do not mix toolchains in one checkout: two daemons, two caches, goldens that render differently.
- Run `scripts/android_env_check.sh <project>` to verify all of this read-only.

## Devices

- **USB phone in WSL** needs `usbipd` on Windows, from an admin PowerShell: `usbipd list` (find the BUSID), `usbipd bind --busid <id>` once, `usbipd attach --wsl --busid <id>` after every replug. Then `adb devices` in WSL. While attached to WSL the phone is invisible to Windows tools; give it back with `usbipd detach`.
- `no permissions` → `adb kill-server && sudo adb start-server` (the server must run as root in WSL).
- **Wireless adb**: `adb pair <IP>:<pair_port>` once, then `adb connect <IP>:<connect_port>` each session. The connect port differs from the pairing port.
- **Inspect** (UI-only changes): `adb exec-out screencap -p > shot.png` then view it; `adb logcat -d`; `adb shell uiautomator dump`; `adb shell input tap/swipe/text`. The screen must be on. Images shown to a model are downscaled, so multiply displayed coordinates by the scale factor before `input tap`.
- **Real data**: `adb install -r` keeps app data. Never clear data or delete records on a phone that holds the owner's real ledger without asking. Remind them to back up before a build that adds a migration.
- RecItDown does not use an emulator or adb in its loop (device-free by design); the phone is for what the loop cannot see.

## Repo housekeeping

- `.gitignore`: `*.iml`, `.gradle`, `/local.properties`, `/build`, `.idea/` caches and per-machine files (`deploymentTargetSelector.xml`, `deviceManager.xml`, …), `keystore.properties`, `*.jks`, `*.keystore`, `*.log`, `*.swp`. `.idea/` per-machine files were untracked after the first commit (f7d99b1); do it from the start.
- `hs_err_pid*.log` / `replay_pid*.log` in the root are JVM crash noise: gitignored, do not read or commit.
- Git LFS for binaries (`.gitattributes`: store screenshots, feature graphic, `*.figcraft`, `*.mp4`, `*.mov`). Install `git-lfs` and run `git lfs install` before the first binary commit, or pointers land in history. Plain-JSON design files and test goldens stay in normal git.
- Local keystore at `~/.android-keys/<app>-upload.jks`, outside the repo.

# Device-free dev loop and testing

The loop that RecItDown's agents live in: no emulator, no phone, no adb. Added 2026-10-21 (1adec30), refined since.

## The loop

`scripts/loop.sh` (generalised as `scripts/dev_loop.sh` in this skill):

1. Runs `:app:verifyRoborazziDebug`: **all JVM tests** plus screenshot verification against committed goldens.
2. Prints only: failing tests (class.name plus the first four message lines), `DIFF <golden> <pct>% -> <compare png>` for changed goldens, compile errors, and `PASS|FAIL in Ns`.
3. Writes the full log to `app/build/loop.log`; per-screen text dumps go to `app/build/screen-dumps/<screen>.txt`.
4. Exits nonzero on failure. Extra args go to Gradle (`--tests '*ScreenTest'`). `--record` re-records goldens.

Read order on a failure: the failure text, then the view-tree dump, and only then (if still unexplained) `app/build/outputs/roborazzi/<screen>_compare.png`. Text is cheaper than images and usually enough.

An intended UI change: `--record`, **look at the new PNGs**, then commit them. Record goldens in one environment only (WSL), so rendering stays consistent; goldens recorded on another OS churn.

## ScreenTest anatomy

```kotlin
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], qualifiers = "w393dp-h852dp")
@GraphicsMode(GraphicsMode.Mode.NATIVE)   // real pixels for Roborazzi
class ScreenTest { … }
```

- Launch `MainActivity` with `ActivityScenario`, **pin shared state** (the date range anchored to a fixed day, `Pro.forceForTest(true)`), `scenario.recreate()`, then `idle()` = `shadowOf(Looper.getMainLooper()).idle()`.
- Drive with Espresso (`onView(withId(...)).perform(click())`), assert titles/body text, dump the view tree (visible views only, class + id + text) to a text file, and `captureRoboImage("src/test/screenshots/<name>.png")`.
- **Screens that show the current time get no golden** (the Add record sheet): they would diff every run. They still get the text dump and assertions.
- Dialog roots need `.inRoot(isDialog())`.
- Seed per test, clean up in `finally` (the grid test adds four presets and deletes them).

## What to unit-test as pure logic

The pattern that made the loop worth it: put decisions in Android-free (or lightly Android) cores and test them on the JVM.

| Core | What it decides |
|------|-----------------|
| `CalcEngine` | keypad arithmetic |
| `QuickLaunch.handleTap` | tap → `Recorded | OpenSheet | Missing` |
| `Pro.decide`, `Pro.verify` | entitlement from purchases, signature check (real RSA keypair in the test) |
| `PresetWidget.gridShape/layoutFor` | widget tile layout from size |
| `TileColors.look` | colour + style → background/content with ≥ 3:1 contrast |
| `MoneyFormat`, `TransactionGrouping`, `Backup`, `CsvImport/Export` | formatting and data transforms |
| DAO tests on in-memory Room | queries, rename cascades, reorder |
| `MigrationTest` | every shipped schema step |
| `CapsTest` | free caps, locked colours, freeze on losing Pro |

Test seams used: `testDb()` (in-memory Room through the production `configure`), `Pro.forceForTest(Boolean?)`, `@VisibleForTesting`.

## Store screenshots from tests

`StoreShotsTest` seeds **demo data** (never real data), then captures six screens for phone, phone-dark, 7" and 10" tablets via `captureScreenRoboImage("build/store-shots/<device>/<n>.png")`. It `assumeTrue(System.getenv("STORE_SHOTS") != null)`, so it skips in the normal loop:

```bash
STORE_SHOTS=1 ./gradlew :app:testDebugUnitTest --tests '*StoreShotsTest' -Proborazzi.test.record=true
```

Copy results to `docs/store-shots/` (LFS). Qualifiers per device: `w360dp-h640dp-xxhdpi`, `…-night-…`, `w540dp-h960dp-xhdpi`, `w720dp-h1280dp-xhdpi`.

## What the loop cannot see (ask the human)

Shaders/`RenderEffect`, WebView, camera, maps, media, IME/keyboard and permissions, system UI (status/nav bars, edge-to-edge insets), real touch feel (ripples, animations), performance and jank, process death, and **billing** (needs a Play test track).

## Phone checks: tell the user, do not drive

Driving a phone over adb (screenshot, read, tap, repeat) is slow, burns tokens, and writes test rows into the owner's real data. For a UI-only change (layout, colour, icons, animation) one screenshot is fine. For anything else: run the loop, build the APK, and hand the user a **short numbered list** of what to try and what they should see. Do not create records or presets on their phone; ask first if a check truly needs it.

## Other notes

- The default test classes `ExampleUnitTest`/`ExampleInstrumentedTest` are templates; delete or ignore them.
- No lint beyond AGP defaults is configured; add `lint` as a gate only if the owner wants it.
- Every screen test pins one Robolectric SDK (33) and one device size (`w393dp-h852dp`) so goldens are comparable run to run.

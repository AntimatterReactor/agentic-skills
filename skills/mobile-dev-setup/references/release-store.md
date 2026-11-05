# Release, signing, and Play Store

RecItDown's path from debug builds to a signed AAB on a Play test track (M5 data safety and release, 2026-10-29; M6/M7 store work, 2026-11). Play policies change; confirm current requirements in Play Console before submitting.

## Signing

- Play App Signing **on**: Google holds the app signing key; you hold an **upload key**.
- Upload key outside the repo: `~/.android-keys/<app>-upload.jks`, alias `upload`. Credentials in the **gitignored** `keystore.properties` (`storeFile`, `storePassword`, `keyAlias`, `keyPassword`). `app/build.gradle.kts` reads it and creates the `release` signing config only if the file exists, so a fresh clone still builds debug.
- **Never commit, print, or paste** the keystore or its passwords. Back both up somewhere safe; losing the upload key means a reset request in Play Console.
- `*.jks`, `*.keystore`, `keystore.properties` in `.gitignore` from day one.

## Release build

```kotlin
buildTypes { release {
    optimization { enable = true }   // R8, as written for AGP 9.4; older AGP used isMinifyEnabled = true
    if (keystoreFile.exists()) signingConfig = signingConfigs.getByName("release")
} }
```

- Keep rules live in `app/src/main/keepRules/` (AGP combines every file there). RecItDown's one rule: `-keep enum <package>.** { *; }`, because enum constant **names** are stored in the DB and in JSON backups. The default `proguard-rules.pro` was deleted.
- `release.sh`: refuses without `keystore.properties`, refuses without `playLicenseKey`, then `:app:assembleRelease :app:bundleRelease` and prints the APK and AAB paths. **Upload the AAB**; use the APK for sideload tests.
- **`versionCode` must increase on every Play upload**; RecItDown bumped it per release-facing commit (2 licence key, 3 new icon, 4 record actions). `versionName` is for humans.
- `applicationId` is permanent after the first upload; never leave `com.example.*`. Put the final id and name in the first commit ([lessons.md](lessons.md)).
- Run `python3 scripts/release_gate.py <project>` before building.

## Test tracks and rollout

Internal testing first for anything touching **migrations or billing**, always. Then closed testing (new personal accounts: at least 12 testers for 14 days), then production with a **staged rollout** (start about 20%, watch Android vitals). Billing needs licence testers on a test track. Moving real data between app ids needs Backup → Restore by the user.

## Store listing package (`docs/store-listing.md`)

Keep the drafts in the repo so they version with the code:
- App name, category (Finance), tags, contact email, privacy-policy URL, price line ("Free, no ads, contains in-app purchases").
- **Short description ≤ 80 chars**, full description in sections (one-tap, widget, overview, accounts, data, theming, privacy, Free vs Pro), release notes.
- **Content rating** notes (utility, no violence/gambling/UGC; expected Everyone/PEGI 3), **target audience 18+** for a finance app.
- **Data safety** answers: say what *your* code collects (nothing), then answer for every SDK (Billing: INTERNET, telemetry), encryption in transit, deletion route (Erase all data / uninstall). The draft says outright that the SDK Index check was not yet done; do it.
- Other declarations: ads (none), government (no), financial features (none regulated: personal record-keeping), health (no), news (no).

## Privacy policy

Plain-language, in the repo (`docs/privacy-policy.md`), **hosted at a public URL** (RecItDown uses GitHub Pages from a separate public repo and says "copy changes there too"). Cover: what is stored and where, network use (Billing library permissions and diagnostics), purchases handled by Google, files the user exports (plain text, their responsibility), Android system backup, sharing (none), feedback email, children, deleting data, changes, contact. Update it **in the same milestone** as any permission or SDK change.

## Graphics and assets

| Asset | Source | Notes |
|-------|--------|-------|
| App icon 512×512 PNG | `docs/play-icon-512.png` | from the logo sources in `design/` |
| Feature graphic 1024×500 | `docs/feature-graphic.png` | source `design/feature-graphic.vectorcraft` embeds a screenshot |
| Screenshots | `docs/store-shots/{phone,phone-dark,tablet-7in,tablet-10in}/` | made by `StoreShotsTest`; 6 screens each, demo data only |
| Widget on a real home screen | real phone or emulator | cannot come from Robolectric |
| Framed mockups, promo video, marketing video | planned in `docs/media-plan.md` | Hyperframes/`brag` toolchain; see that file |

Play screenshot rules recorded in the media plan (re-check): 2–8 per device type, PNG or JPEG up to 8 MB, 9:16 or 16:9, each side 320–3840 px, long side at most 2× the short side. Tablet shots show a stretched phone layout until real tablet layouts exist; do not market features that have not shipped.

**Binaries go through Git LFS** (`.gitattributes` for store shots, feature graphic, `*.figcraft`, video). **No real user data in any image or video**: record on demo data, never on the owner's phone.

## Post-launch backlog the project kept

Closed test recruitment, per-country prices, Data safety review, EU trader details, staged rollout, then CSV import from other apps, recurring records (Pro), visual polish, tablet layouts (navigation rail ≥ 600dp, two-pane ≥ 840dp). The milestone table and GitHub milestones live in SCHEME.md; mirror that habit ([history.md](history.md)).

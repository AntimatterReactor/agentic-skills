# Monetization: one app, lifetime Pro, no ads

RecItDown's M6 (2026-11-01). The reasoning matters more than the code; Play Billing APIs change, so check current docs before copying signatures.

## Decide before building

The decision record (SCHEME.md M6), with the options it rejected:

| Option | Verdict | Why |
|--------|---------|-----|
| **One-time non-consumable `pro_lifetime`** | chosen | no server, no running costs to justify recurring fees, works offline |
| Ads | rejected | cents per user per month; needs INTERNET and tracking, which breaks a privacy promise; a banner beside tappable tiles violates AdMob's accidental-click policy |
| Subscription | rejected | no running costs to justify it; lifetime would have to be 24–30× the monthly price |
| Separate free and paid apps | rejected | upgrade means backup/restore, ratings split, no try-before-buy, does not avoid EU trader rules |

A fair split: **Free is a complete product; Pro lifts caps and adds extras.** In RecItDown: Free = 8 presets, 1 widget, 16 swatches in Filled style. Pro = unlimited presets and widgets, custom hue picker, Inverted and Tonal styles, plus future power features. **Data-safety features (backup, restore, CSV import/export, erase) are never paywalled.**

## Implementation shape

- **Pure decision core**: `Pro.decide(queryOk, purchases, cached)` returns the cached value when the Play query failed, else true only for a `pro_lifetime` purchase that is `PURCHASED`, not `PENDING`, and signature-verified. `ProPurchase` is a plain data class so the core is JVM-testable.
- **Wrapper** `PlayBilling` (object): lazy `BillingClient`, `enablePendingPurchases(oneTimeProducts)`, a state flow (`LOADING, AVAILABLE, UNAVAILABLE, PENDING, OWNED`), price flow from `oneTimePurchaseOfferDetails.formattedPrice`, refresh on `MainActivity.onResume`. **Every failure leaves the cached entitlement in place** (offline use, Play outages).
- **Local signature check** `Pro.verify`: SHA1withRSA over `purchase.originalJson` with the Play Console base64 public key from `gradle.properties` → `BuildConfig.PLAY_LICENSE_KEY`. **Fails closed**: empty or garbage key means not Pro. The key is public; the app accepts that piracy is possible at this price.
- **Acknowledge** every verified `PURCHASED` and unacknowledged purchase; Google auto-refunds purchases left unacknowledged for 3 days (per the project docs; re-check the current rule).
- **Cache** in SharedPreferences `pro`, **excluded from Android backup and device transfer** (`backup_rules.xml`, `data_extraction_rules.xml`) and from the app's own JSON backup, so restoring a backup never grants Pro. Call `Pro.load(context)` in every entry point that reads it.
- **Gating**: `Pro.canAddPreset(count, pro)`, `Pro.canAddWidget(others, pro)`, `PageUi.colorPicker` locks Pro options on Free. `ProPrompt` appears **only at the moment a cap is hit** (new preset dialog, new widget config); no other nags.
- **Losing Pro (refund) = freeze, not delete**: nothing is deleted or hidden, items past the cap keep working, no new ones can be added, saved Pro colours stay until edited.
- **Debug override**: debug builds get a Free/Pro switch in Settings (default Pro). Tests use `Pro.forceForTest(Boolean?)`. Release builds ignore the override.
- `release.sh` **refuses to build with an empty `playLicenseKey`**: a blank key would mean purchases never unlock and Google would refund them.

## Testing and its limits

Unit tests cover `verify` (real RSA keypair; tamper, empty key, garbage key/signature), `decide` (failed query keeps cache, pending, unverified), caps, colour locks and freeze. **Billing itself cannot run in the dev loop.** It needs a Play test track and licence testers: buy, refund → freeze, reinstall → restore, pending purchase, acknowledgement. A test purchase succeeded on internal testing on 2026-11-02; the remaining checks moved to the release milestone.

## Side effects to handle in the same milestone

- Billing 9.x adds `INTERNET`, `ACCESS_NETWORK_STATE` and a Google telemetry component (`transport-backend-cct`). The privacy policy's "no internet permission" claim had to go, and the Data safety answers must account for the library (check Google's Play SDK Index). Whether to strip the permissions with `tools:node="remove"` is an open question until proven on a test track.
- Store listing must say "Contains in-app purchases".
- EU trader rules: anyone selling counts as a trader; EU users see name, address, phone and email. Decide the contact details before the first paid release (business address or PO box, or sell outside the EU, or use the owner's own).
- Prices: set per country in Play Console (RecItDown targets about one average meal per country from the owner's meal-price CSV; every country has a minimum price, listed prices usually include local VAT, Google keeps 15% of the rest per the project's notes; verify current fees).

## Account prerequisites (project notes, 2026-11; verify current policy)

Play Console developer account ($25 once, owner 18+, ID verification), a Google payments profile with a bank account, EU trader declaration, and for **new personal accounts a closed test with at least 12 testers for 14 days before production**. Plan to recruit testers early.

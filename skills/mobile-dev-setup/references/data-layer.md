# Data layer: Room, migrations, settings, backup

From RecItDown (offline, local-only ledger). Schema went v3 (pre-Room SQLite) → v8 in two months with real data on the phone, so the migration discipline below is load-bearing.

## Room + Flow

- One `@Database` singleton (`AppDatabase.get(context)`), built with KSP. `configure(context, builder)` holds migrations, fallbacks and seed callbacks so **tests build the database through the same path as production** (`Room.inMemoryDatabaseBuilder(...).allowMainThreadQueries()` passed to `configure`).
- DAOs: writes and one-shot reads are `suspend`; screen reads are `Flow`. Room forbids main-thread queries, so never add a blocking DAO method. Abstract-class DAOs hold multi-statement `@Transaction` logic (rename cascades, reorder).
- Screens observe with `Flow.observe(viewLifecycleOwner) { … }` = `repeatOnLifecycle(STARTED)` (`Observe.kt`), write with `launchIo`. Room re-emits on any change to a queried table, so there is **no manual refresh signal** (no `onResume` re-render, no change broadcasts).
- Known cost: each emission rebuilds hand-built lists with `removeAllViews`. Fine at personal-ledger size; move to RecyclerView + DiffUtil when it is not.
- Shared UI state that must survive tab switches lives in an activity-scoped `ViewModel` (`RangeViewModel` with a `StateFlow`), not in `object`s.

## Migrations (the rules)

1. **Shipped versions need a real `Migration` plus a test.** `fallbackToDestructiveMigrationFrom(true, 1, 2)` is allowed only for versions that never reached a user. Never fall back to DROP and recreate: the phone holds real data.
2. **Export and commit schemas**: `room { schemaDirectory("$projectDir/schemas") }`, files `app/schemas/<package>.AppDatabase/<n>.json`. They are the input to migration tests.
3. **Keep old migrations** even when a later one deletes what they create. `Migration3to4`/`4to5` still create the credit tables that `5to6` drops, so a v3 database can walk the whole chain.
4. **Dropping a column = table rebuild**: create `_new`, `INSERT … SELECT`, drop old, rename, recreate indexes. `Migration5to6` does this for `transactions` and keeps row ids. Finish with `PRAGMA foreign_key_check` where foreign keys exist (`Migration3to4` asserts it).
5. **Additive changes** are one `ALTER TABLE … ADD COLUMN` with a nullable column (`Migration7to8`: `color`, `style`); existing rows keep the default look.
6. **MigrationTest pattern**: `writeSchema(version) { … }` creates a real file database from the exported `<version>.json` (entity `createSql`, indices, `setupQueries`), lets the test insert rows, then opens it through `AppDatabase.configure` and asserts rows, ids and defaults survived. `room-testing` is not a dependency.
7. **Pre-Room → Room** (`Migration3to4`): carries the legacy ledger file in place and copies a second legacy catalog file in via a seed callback, then deletes the legacy file on the next open. Versions that predate Room fall back to destructive (they never shipped data worth keeping).
8. Before a user runs a build that adds a migration on a device with real data, tell them to take a backup (Configure › Manage data › Backup in RecItDown). Migrations cannot be downgraded.

## Storage formats

- `Converters` keep the stored format identical to what earlier versions wrote: datetimes are epoch millis in `ZoneId.systemDefault()`, dates are local-midnight millis, enums are stored by name, unknown currency codes read back as a default. Changing a converter silently changes every migrated row.
- **Enums stored by name** must survive R8: `-keep enum <package>.** { *; }` in `src/main/keepRules/app.keep`.
- **Known traps** (documented, still open in RecItDown): datetimes shift if the device timezone changes; amounts are `Double` with currency ignored by totals; related rows reference accounts/categories by **label strings**, so a rename must rewrite every referencing table in one transaction (`CatalogDao.updateAccount/updateCategory` rewrite transactions, presets and budgets; deleting an entry leaves history intact). For a new project prefer integer minor units (or `BigDecimal`) and ids over labels unless there is a reason not to; that is a recommendation, not RecItDown's choice.
- Catalog uniqueness is `(kind, label, income)`, so a name can exist on both the income and expense side; any rename must say which side.

## Light state: SharedPreferences, not the schema

| Store | Holds | Notes |
|-------|-------|-------|
| `settings` | theme, accent, currency | `Settings.load(context)` before inflating anything |
| `preset_widgets` | `widget_<id>` = comma-separated preset ids | no schema change; cleared in `onDeleted`; missing ids skipped |
| `pro` | cached entitlement | excluded from backups and Android backup ([monetization.md](monetization.md)) |

**Process-wide state must be initialised in every entry point**, not just `MainActivity`. A launcher shortcut (`ShortcutActivity`) or a widget broadcast (`PresetWidget.async`) can be the first code to run in a cold process; each calls `Settings.load` itself, and `Pro.load` is required anywhere `Pro.isPro` is read.

Avoid mutable `object` state for UI (`CalcEngine`'s `var s`): a rotation wipes it and two sheets would share it.

## Backup, export, erase (data-safety features, never paywalled)

- **JSON backup** (`Backup.kt`): one versioned, streaming file with every table (ids kept) plus theme/accent/currency; reads files from the oldest supported schema (6) up, missing fields become null; restore is **Replace or Merge** inside one DB transaction (`withTransaction`); merge skips duplicates and reports `added/skipped`.
- **CSV import/export** round-trip with each other; import is `CsvImport`, export `CsvExport`; both tested.
- **Erase all** is gated by typing `ERASE`; Erase and Import first offer a backup.
- A package/applicationId rename is a new app with a new data directory: move data with Backup (old app) → Restore (new app). This is why the id must be final before real data exists ([lessons.md](lessons.md)).

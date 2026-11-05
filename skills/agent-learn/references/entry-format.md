# Entry format

One entry per learning. A learnings file is a title, an optional intro line, then entries grouped under `## ` headings (by area, not by date). `scripts/lint_learnings.py` checks this format.

```markdown
### DONT: <imperative title, under ~100 chars>
- **When:** the trigger or context in which this applies
- **Why:** the observed consequence (what went wrong, or what it costs)
- **Instead:** what to do (required for DONT and ANTIPATTERN)
- **Evidence:** commit SHA | file:line | "user quote" | command and result
- **Source:** user | observed | inferred
- **Scope:** project | user | skill:<name> | tool:<name>
- **Added:** YYYY-MM-DD
- **Recheck:** condition or date (required when Source is inferred)
```

PATTERN and ANTIPATTERN add a fenced block showing the **shape** (config, code, or tree). Keep it to a few lines; it identifies the shape, it is not a tutorial.

## Field rules

- **Title**: starts with a verb. The kind already carries the polarity, so write `DONT: use unqualified ?attr/colorBackground`, not `DONT: don't use…`. No "be careful", "remember", "note that".
- **When**: concrete enough that you could grep for it or recognize it mid-task.
- **Why**: a consequence, not a restatement. "Phone holds real data" is a reason; "it is important" is not.
- **Evidence**: if you cannot cite one, the entry is `inferred` and needs a **Recheck**.
- **Source**: `user` beats `observed` beats `inferred` when entries conflict.
- **Scope**: where it applies. A rule about one repo's build is `project`; "this user wants X in every repo" is `user`.
- **Added**: absolute date, never "today" or "last week". When you supersede an entry, edit it in place and update the date; add `Supersedes: <old title>` to the Why if the reversal itself is informative.

## Grouping and size

- Group by area (Build, Data, UI, Release, Workflow), not chronology.
- If a file passes ~40 entries, split by area into `docs/learnings/<area>.md`, or prune. The linter warns on entries over 25 lines.
- Do not copy facts the repo's docs already hold; link instead (`Evidence: AGENTS.md > Dev loop`).

## Worked examples

The evidence below comes from a real Android repo (RecItDown); they show the format, they are not claims about the current project.

### DONT: use unqualified `?attr/colorBackground` in Android XML
- **When:** writing layouts or styles that read the theme background
- **Why:** the unqualified attribute does not resolve at build time; other tokens such as `colorSurface` do
- **Instead:** `?android:attr/colorBackground`
- **Evidence:** AGENTS.md > Repo-specific gotchas
- **Source:** observed
- **Scope:** project
- **Added:** 2026-11-05

### ANTIPATTERN: destructive-migration fallback for a version that has shipped
- **When:** a Room schema changes and the app is already on a real device
- **Why:** DROP and recreate wipes the user's ledger; the phone holds real data
- **Instead:** a real `Migration` plus a test that builds the old DB from its exported schema JSON and opens it through the production `configure`
- **Evidence:** AGENTS.md > Persistence; 426e3d4 (v5→v6 drops credit tables but keeps ledger ids); MigrationTest
- **Source:** observed
- **Scope:** project
- **Added:** 2026-11-05

```kotlin
.fallbackToDestructiveMigrationFrom(true, 1, 2)   // only versions that never shipped
.addMigrations(Migration3to4(context), Migration4to5, /* … */)
```

### PATTERN: put the decision in a pure core and keep the Android shell thin
- **When:** a feature has Android entry points (shortcut, widget tap, receiver) around real logic
- **Why:** the core is testable on the JVM without a device; the shell only wires Intents and Toasts
- **Evidence:** QuickLaunch.handleTap(db, id) returns `Recorded | OpenSheet | Missing`; QuickLaunchTest
- **Source:** observed
- **Scope:** project
- **Added:** 2026-11-05

```kotlin
suspend fun handleTap(db: AppDatabase, presetId: Long): Tap   // pure outcome
suspend fun tap(context: Context, …)                         // shows the Toast, starts the activity
```

### DONT: drive the user's phone over adb to check logic
- **When:** verifying anything beyond a layout or colour change
- **Why:** slow, token-heavy, and it writes test rows into the user's real data
- **Instead:** run the device-free loop, then give the user a short numbered list of what to try and what they should see
- **Evidence:** CLAUDE.md > Testing on the phone: tell the user, don't drive it
- **Source:** observed
- **Scope:** project
- **Added:** 2026-11-05

### DO: supersede a stale design directive instead of appending to it
- **When:** a plan or direction doc changes (a stack, a theme, a scope decision)
- **Why:** the repo said "leaving Material Design, no M3E" on 2026-10-21 and "M3E stays, only Material You is dropped" on 2026-10-29; an agent that trusted the first would avoid M3E components the app still uses
- **Instead:** edit the old line, note the date and reason in the commit, and re-read the doc's other mentions
- **Evidence:** 7f1b7d9 vs b066567
- **Source:** observed
- **Scope:** user
- **Added:** 2026-11-05

# UI, theming, and home-screen surfaces

RecItDown's choices. The first section says what is evidence and what is general advice.

## Toolkit choice

RecItDown is **Views + ViewBinding + Material Components (M3 Expressive theme parent), no Compose, no Navigation library**: screens are fragments and activities, tabs are a `ViewPager2` (swipe disabled) driven by a `BottomNavigationView`. The history does not record a Compose-versus-Views decision; the first scaffold was Views. For a *new* project, ask the owner; Compose is the usual default for new Android UI, but nothing in RecItDown validates it. The installed `mobile-android-design` skill assumes Compose and Material You; with a Views project take its spacing, type and layout rules, not its code or its dynamic-colour advice.

## Theme system (works in Views; the ideas carry to Compose)

- Parent `Theme.Material3Expressive.DayNight.NoActionBar`, all colour roles mapped to `@color/...` tokens in `values/colors.xml` and `values-night/colors.xml` (neutral palette, light and dark).
- **User-picked accent** (8 choices) as `ThemeOverlay.<App>.Accent.<Name>` styles that set primary, secondary and tertiary families. `Settings.applyAccent(activity)` runs `activity.theme.applyStyle(accent.styleRes, true)` **before `super.onCreate` in every activity**; `Settings.accentVersion` is bumped on change and `MainActivity` recreates when it moved.
- **No Material You / `DynamicColors`** (dropped in M4c, b066567). The docs record the decision, not the reason. The path matters: on 2026-10-21 the plan was to replace the Material theme entirely with an own visual language (SCHEME M4 as first written); what shipped on 2026-10-29 kept M3 Expressive and added a neutral palette plus accent overlays. See the reversal in [lessons.md](lessons.md).
- **Type**: M3 text appearances (`android:textAppearance="?attr/textAppearanceBodyLarge"` in XML, `PageUi.type(view, attr)` in code, which keeps the view's colour). No raw `textSize`; `RemoteViews` widget layouts are the exception and keep `sp` sizes on the M3 scale.
- **Targets**: icon buttons ≥ 48dp. **No hardcoded colours in layouts**; icon drawables ship raw white/black fills and are tinted at use sites with `android:tint="?attr/…"`.
- **Gotcha**: unqualified `?attr/colorBackground` does not compile; use `?android:attr/colorBackground`. Other tokens (`colorSurface`, `colorOnBackground`, …) are fine unqualified.
- **Edge-to-edge**: transparent status/navigation bars, `android:windowLightStatusBar` bound to `?attr/isLightTheme`, insets applied **per view in code** (`ViewCompat.setOnApplyWindowInsetsListener`: top bar = top inset, bottom nav = bottom inset), not `fitsSystemWindows`. `windowSoftInputMode="adjustResize"` on the main activity.

## User colours that stay readable

`TileColors`: `ColorStyle` FILLED / INVERTED / TONAL, a 16-swatch palette, plus a custom hue/saturation/brightness picker with hex. `TileColors.look(color, style, …)` returns background, content and stroke and **nudges the colour toward black or white until contrast ≥ 3:1**. A preset with no colour inherits colour and style from its category (or from-account for transfers). A theme-less overload exists for the widget. Pure function, unit-tested.

## Performance traps found on the owner's real phone

- A full-height bottom sheet with window and sheet shadows made its open animation GPU-bound on the owner's phone (a Galaxy A71 per SCHEME.md). Fix: a theme overlay that sets elevation 0 on window and sheet (`ThemeOverlay.<App>.AddRecordSheet`), `skipCollapsed = true` and `STATE_EXPANDED` set in `onCreateDialog`, keypad colours resolved once, dropdowns filled once after the catalog loads (0f57c06).
- Touch feel: `RippleDrawable` timing is not configurable, only its colour (`colorControlHighlight`). To change the feel, swap the ripple for a `<selector>` with `enterFadeDuration`/`exitFadeDuration` (`dropdown_selector.xml`, wired via `dropDownListViewStyle`). This needs a human to tune on a device.

## Home-screen surfaces

**Launcher shortcuts** (`QuickLaunch.kt`): dynamic shortcuts for the first three presets in grid order plus "Add record"; icons are adaptive bitmaps painted with the preset's colour. `MainActivity` observes the presets Flow and republishes shortcuts and refreshes widgets on every change.

**Invisible entry activity** (`ShortcutActivity`): translucent theme, `exported=false`, `excludeFromRecents`, `noHistory`, `taskAffinity=""`. Shortcut and widget taps go here, run `QuickLaunch.tap` (testable core `handleTap`: record with a toast, or hand off to `MainActivity` with `EXTRA_PRESET` / `EXTRA_ADD_RECORD`), then `finish()`. `MainActivity` is `singleTop` and handles those extras **once in `onResume`**, not on state restore or from Recents.

**Widget** (`PresetWidget`, `AppWidgetProvider`):
- Plain `RemoteViews` rows of weighted tiles, no collection view, no service. Every picked preset gets a tile and tiles fill the widget.
- `layoutFor(count, width, height)` picks header, padding, columns and tile class (large/medium/small → icon+name+amount / icon+name / icon) from the widget size; `gridShape` picks the column count whose tiles are closest to square. `onAppWidgetOptionsChanged` rebuilds on resize.
- Manifest provider XML: `resizeMode="horizontal|vertical"`, `targetCellWidth/Height`, `minResize*`, `widgetFeatures="reconfigurable"`, `previewLayout`, `configure` activity, `updatePeriodMillis=1800000`.
- Per-widget config activity (`exported=true`, `APPWIDGET_CONFIGURE`) stores picks in SharedPreferences `widget_<id>`; `onDeleted` clears them.
- DB work in `onUpdate` uses `goAsync()` with a coroutine and `pending.finish()` in `finally`.
- Widget colours come from `Settings.accentColors(context, followApp = false)` so they follow the **launcher's** light/dark, not the app theme. No undo in the widget; a toast confirms.
- Free tier caps widgets (`Pro.FREE_WIDGETS`); the picker shows the Pro prompt only when the cap is hit.

## Design tooling (optional)

RecItDown keeps design sources in `design/`: `.vectorcraft` (JSON) for logo and feature graphic, `.figcraft` (LFS) for screen mockups, and `build_figcraft.py` that regenerates the mockup file from `colors.xml` and the drawables through FigCraft's MCP. See the `craft-connect` skill for wiring those apps up. Launcher icon is three drawables (`ic_launcher_foreground`, `_background`, `_monochrome` for themed icons) plus a 512 px Play icon.

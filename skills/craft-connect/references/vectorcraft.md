# VectorCraft

Vector illustration app (Rust, alpha). Repo: https://github.com/storytold/vectorcraft. Docs: `docs/mcp.md`, `docs/control-protocol.md`.

## Install
- Release packages (getartcraft.com/apps/vectorcraft or GitHub releases); CLI ships with the app:
  - Windows MSI: `%LOCALAPPDATA%\Programs\ArtCraft\VectorCraft\vectorcraft-cli.exe` (all-users: `C:\Program Files\ArtCraft\VectorCraft\`). **Not on PATH.**
  - Linux deb/rpm: `/usr/bin/vectorcraft-cli`.
  - macOS: separate asset `vectorcraft-cli-<version>-macos-<arch>.zip` (the `.app` has no CLI).
- Source (Rust 1.95+), from repo root:
  ```bash
  cargo install --path apps/vectorcraft-cli --locked
  export PATH="${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
  vectorcraft-cli --help
  ```

## Modes
| Mode | Command | Notes |
|------|---------|-------|
| Auto | `vectorcraft-cli mcp` | Tries 127.0.0.1:7979 once at startup, else headless |
| Headless | `vectorcraft-cli mcp --headless` | No `inspect_ui`, `type_text`, `answer_dialog`, `open_panel`, window screenshots |
| Remote (live) | `vectorcraft-cli mcp --connect 127.0.0.1:7979` | Full feature set; needs app running with `--control 7979` |

Start app with control port:
- Linux: `vectorcraft --control 7979`
- macOS (quit app first): `open -a VectorCraft --args --control 7979`
- Windows: `& "$env:LOCALAPPDATA\Programs\ArtCraft\VectorCraft\vectorcraft.exe" --control 7979`
- Source: `cargo run --release -p vectorcraft -- --control 7979`
- Dock/Start-menu launchers open no port unless `VECTORCRAFT_CONTROL_PORT` is set.

## Register
```bash
claude mcp add vectorcraft -- vectorcraft-cli mcp
claude mcp add vectorcraft-headless -- vectorcraft-cli mcp --headless
claude mcp add vectorcraft-app -- vectorcraft-cli mcp --connect 127.0.0.1:7979
```
Windows:
```powershell
claude mcp add vectorcraft -- "$env:LOCALAPPDATA\Programs\ArtCraft\VectorCraft\vectorcraft-cli.exe" mcp
```

## File access roots
`--automation-read-root <dir>` / `--automation-write-root <dir>` (repeatable; dirs must exist). They imply `--headless`; combining with `--connect` is an error. To confine the live app: `vectorcraft --control 7979 --automation-read-root <dir> --automation-write-root <dir>`.

## Tools (partial)
`command_list`, `command_run`, `command_batch` (≤256 steps, optional `atomic`), `doc_inspect`/`inspect_document`, `render_preview`, `ui_inspect`, `ui_screenshot`, `select_tool`, `pointer_gesture`, `draw_path`, `draw_shape`, `set_paint`, `press_key`, `type_text`, `invoke_menu`, `open_panel`, `screenshot`, `open_file`, `save_file`, `export`.
Prompts: `poster`, `icon-set`, `recolor`, `trace-and-style`, `export-set`. Resources: `vectorcraft://document`, `vectorcraft://commands`.
Coordinates: points, origin top-left of first artboard, y down; new doc 612×792.

## Troubleshooting
- `ENOENT` / not in PATH → `command -v vectorcraft-cli` in the client's environment; restart client after PATH change.
- `vectorcraft-cli: cannot connect to 127.0.0.1:7979: ...` → app not running with `--control 7979`; `open -a` / PowerShell `&` return before port opens, wait for window.
- `automation path rejected: outside the write root ...` → path outside roots.
- Error `-32003` (`data.busy`) → engine busy >2 s; retry after current call.

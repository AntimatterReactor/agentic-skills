# PhotoCraft

Photo editor (Rust, alpha). Repo: https://github.com/storytold/photocraft. Docs: `docs/mcp.md`, `docs/development.md` (bridge/control port).

## Install
Source:
```bash
cargo install --path apps/photocraft-cli --locked
export PATH="${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
photocraft-cli mcp --help
```
- Linux deb/rpm: `/usr/bin/photocraft-cli`. AppImage: `./photocraft-<ver>-linux-x86_64.AppImage --cli mcp`. Flatpak: `flatpak run ai.storyteller.photocraft`.
- macOS: `photocraft-cli-<version>-macos-universal.zip`.

## Modes
| Mode | Command |
|------|---------|
| Headless | `photocraft-cli mcp --automation-read-root <dir> --automation-write-root <dir>` |
| Bridge (live app) | `photocraft-cli mcp --bridge --control-token-file <file>` |

Bridge: desktop app started with `photocraft --control` (authenticated, loopback). Token via `--control-token` / `--control-token-file` or env `PHOTOCRAFT_CONTROL_TOKEN` / `PHOTOCRAFT_CONTROL_TOKEN_FILE`; port via `PHOTOCRAFT_CONTROL_PORT`. Root flags are **rejected** with `--bridge` — set roots on the desktop app.

## Register
```bash
claude mcp add photocraft -- photocraft-cli mcp --automation-read-root /work/project --automation-write-root /work/project/out
```
JSON:
```json
{"mcpServers":{"photocraft":{"command":"photocraft-cli","args":["mcp","--automation-read-root","/work/project","--automation-write-root","/work/project/out"]}}}
```

## Tools
`command_list`, `command_run` (`id`, `params`, `wait`), `command_batch` (not atomic), `doc_inspect`, `render_preview` (`max_side` default 1024, max 2048), `ui_inspect`, `ui_screenshot`, `doc_save`, `doc_export`. Resources: `photocraft://document`, `photocraft://commands`.

## Notes
- Write root should be a dedicated output folder: document text can try to steer the agent.
- Writes only replace image/document formats. In-app undo doesn't roll back disk writes.
- Non-MCP batch: `photocraft-cli batch --actions grade.json --in ./raw --out ./graded`.

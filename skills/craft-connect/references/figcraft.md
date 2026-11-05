# FigCraft (ArtCraft)

Interface design and prototyping app (Rust, early alpha). Repo: https://github.com/storytold/figcraft. Docs: `docs/mcp.md`, `docs/server.md`.

**Not** the unrelated Figma plugin `divikwu/figcraft` (Node, WebSocket relay on port 3055). If the user means that one, see its README instead: clone, `npm install && npm run build`, import `manifest.json` in Figma Desktop, MCP entry `node dist/mcp-server/index.js` with `cwd` = clone path.

## Install
Source:
```bash
cargo build --release -p figcraft-cli
```
Binary: `target/release/figcraft-cli` (use absolute path). AppImage: `FigCraft.AppImage cli mcp` runs the CLI. Fonts: `git clone https://github.com/storytold/craft-fonts ../craft-fonts` next to repo.

## Modes
| Mode | Command |
|------|---------|
| Headless (no window, one untitled doc) | `figcraft-cli mcp` |
| Live (attach to running app) | `figcraft-cli mcp --attach <port>` (or `host:port`) |

App with control channel (loopback only): `figcraft --control <port>`. Docs use 7979 in mcp.md and 47800 in README — no stated default; pick one and use it on both sides.

## Register
```bash
claude mcp add figcraft -- /path/to/figcraft-cli mcp
claude mcp add figcraft-app -- /path/to/figcraft-cli mcp --attach 7979
```
`.mcp.json`:
```json
{"mcpServers": {"figcraft": {"command": "/path/to/figcraft-cli", "args": ["mcp"]}}}
```

## Flags
- `--automation-read-root DIR` / `--automation-write-root DIR` — headless only; with `--attach` it's a usage error (start the app with the same flags instead).
- `--timeout SECONDS` (1–600, default 60), `--no-system-fonts`.

## Tools (partial)
`list_commands`, `run_command`, `batch`, `create_node`, `set_properties`, `inspect_document`, `get_node`, `select`, `export`, `screenshot`, `open_file`, `save_file`, `undo`, `redo`, `pointer`, `key`, `type_text`, `inspect_ui`, `wait_for_changes`. Commands include `file.newFromTemplate`, `template.list`, `node.find`, `text.preview`.

## Notes
- Attached calls are not replayed after a transport failure — re-inspect state before retrying.
- Attached agent appears as "Claude (agent)" in live collaboration sessions.
- Other CLI uses: `figcraft-cli render x.figcraft -o x.png --scale 2`, `figcraft-cli export x.figcraft -o out/ --format svg`.

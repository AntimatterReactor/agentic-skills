# Other *Craft apps

## Craft Anything
Reverse-engineer and rebuild software. Repo: https://github.com/storytold/craft-anything (Rust 1.97+).
```bash
git clone https://github.com/storytold/craft-anything && cd craft-anything
cargo install --path apps/craft-anything-cli
craft-anything-cli doctor
claude mcp add craft-anything -- craft-anything-cli mcp
```
- `craft-anything-cli setup` connects it to coding-agent apps automatically; check `docs/claude-code.md` in repo.
- Needs a locally signed-in coding agent; it runs the user's own `claude` binary.
- Each of its tools is both a CLI subcommand and an MCP tool (`craft-anything-cli commands` lists them).
- No root/headless/control flags documented — confirm with `--help`.

## Siblings (not individually documented here)
FilmCraft (video), LightCraft (photo dev), DeckCraft (slides), PDFCraft, DesignCraft (layout), EffectCraft (motion), GridCraft (spreadsheet), MaterialCraft, WordCraft, SoundCraft, CADCraft, TextureCraft — all under https://github.com/storytold. SolidCraft is community: https://github.com/tangency-labs/solidcraft.

## Discovery procedure for an undocumented craft
1. Read repo `README.md` and `docs/mcp.md` (raw: `https://raw.githubusercontent.com/storytold/<name>/HEAD/docs/mcp.md`).
2. Find CLI: `command -v <name>-cli`, `~/.cargo/bin`, `/usr/bin`, AppImage `--cli`. Else `cargo install --path apps/<name>-cli --locked`.
3. `<name>-cli --help` and `<name>-cli mcp --help` → note live-mode flag (`--connect` / `--attach` / `--bridge`), control flag on app, root flags.
4. Register headless first with read/write roots, verify with list/inspect tool, then add live variant if wanted.
5. Add a reference file here for that app once confirmed.

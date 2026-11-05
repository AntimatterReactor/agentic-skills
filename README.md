# agentic-skills

Personal collection of [Claude Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview). Each skill is a folder with a `SKILL.md` (YAML frontmatter + instructions) plus optional scripts and reference docs. Claude loads a skill's `name` + `description` up front and reads the rest only when the skill is relevant.

Repo is also a Claude Code plugin marketplace, so all skills install in one step.

## Layout

```
.
├── .claude-plugin/
│   ├── plugin.json         # plugin manifest (skills/ auto-discovered)
│   └── marketplace.json    # lets Claude Code install this repo as a marketplace
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md        # required
│       ├── scripts/        # optional executable helpers
│       └── references/     # optional docs loaded on demand
├── template/               # copied by scripts/new_skill.sh
├── scripts/
│   ├── new_skill.sh        # scaffold a new skill
│   └── validate_skills.py  # lint all SKILL.md files (also runs in CI)
├── .github/workflows/validate.yml
├── CLAUDE.md               # authoring rules for Claude working in this repo
└── LICENSE                 # Unlicense
```

## Skills

| Skill | Description |
|-------|-------------|
| [afwf](skills/afwf/SKILL.md) | Ask First, Work Fast: batch every clarifying question up front, then execute end-to-end without interruptions. |
| [ultracode](skills/ultracode/SKILL.md) | "ultracode" / "ultracode style" = orchestrate: decompose task and spawn parallel subagents, then integrate and verify. |
| [craft-connect](skills/craft-connect/SKILL.md) | Connect Claude to ArtCraft *Craft apps (VectorCraft, FigCraft, PhotoCraft, Craft Anything, …) via their `*-cli mcp` servers. |
| [agentic-test-loop](skills/agentic-test-loop/SKILL.md) | Run → triage → fix → rerun until green; continuous via `/loop`, a bounded Stop hook, or scheduled runs. |
| [agentic-build-loop](skills/agentic-build-loop/SKILL.md) | Continuous creation: each iteration plans next features, asks one AFWF round, builds, verifies, commits, proposes more scope. |
| [agentic-perf-loop](skills/agentic-perf-loop/SKILL.md) | Measure → profile → one change → re-benchmark → keep real wins (tests green) or revert; repeat until target. |

### Using a skill

Claude picks skills automatically when the task matches the `description`. To force one, name it in the prompt ("use afwf", "AFWF this") or run it as slash command:

```
/afwf migrate the auth module to the new session API
```

Skills compose: `afwf` asks first, `ultracode` fans out, `agentic-test-loop` verifies, `agentic-perf-loop` optimizes with test loop as correctness gate, `agentic-build-loop` drives them per iteration.

Installed via the plugin, the name is namespaced: `/agentic-skills:afwf`.

## Add a skill

```bash
scripts/new_skill.sh my-skill
```

Edit `skills/my-skill/SKILL.md`, delete unused `scripts/` / `references/` folders, then:

```bash
python3 scripts/validate_skills.py
```

Add row to Skills table above. CI runs the same validator on every push and PR.

### SKILL.md rules

- `name`: lowercase letters, digits, hyphens; max 64 chars; must equal folder name; no `anthropic` / `claude`.
- `description`: max 1024 chars; say **what** it does and **when** to use it (triggers drive auto-invocation).
- Keep `SKILL.md` body under ~500 lines; push detail into `references/` and link to it.

## Install

### Claude Code (plugin marketplace)

```bash
/plugin marketplace add AntimatterReactor/agentic-skills
```

```bash
/plugin install agentic-skills@agentic-skills
```

Update later with `/plugin marketplace update agentic-skills`.

### Claude Code (manual, global)

Copy into user skills folder; available in every project:

```bash
git clone https://github.com/AntimatterReactor/agentic-skills.git
```

```bash
mkdir -p ~/.claude/skills && cp -r agentic-skills/skills/* ~/.claude/skills/
```

Symlink instead of copy to pick up `git pull` updates:

```bash
ln -s "$PWD/agentic-skills/skills/afwf" ~/.claude/skills/afwf
```

Project-scoped: copy into `.claude/skills/` of target repo instead.

### Claude.ai / Claude app

Zip skill folder (folder at zip root) and upload it in claude.ai settings (Skills section):

```bash
cd skills && zip -r ../my-skill.zip my-skill
```

## License

[Unlicense](LICENSE) — public domain. Do whatever you want.

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
└── .github/workflows/validate.yml
```

## Skills

| Skill | Description |
|-------|-------------|
| [afwf](skills/afwf/SKILL.md) | Ask First, Work Fast: batch every clarifying question up front, then execute end-to-end without interruptions. |

## Add a skill

```bash
scripts/new_skill.sh my-skill
```

Edit `skills/my-skill/SKILL.md`, delete unused `scripts/` / `references/` folders, then:

```bash
python3 scripts/validate_skills.py
```

Add row to Skills table above.

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

### Claude Code (manual, single skill)

```bash
cp -r skills/my-skill ~/.claude/skills/
```

Project-scoped: copy into `.claude/skills/` of target repo instead.

### Claude.ai / Claude app

Zip skill folder (folder at zip root) and upload under Settings → Capabilities → Skills:

```bash
cd skills && zip -r ../my-skill.zip my-skill
```

## License

[Unlicense](LICENSE) — public domain. Do whatever you want.

# CLAUDE.md

Repo holds Claude Agent Skills. One skill per folder under `skills/`.

## Conventions

- Create skills with `scripts/new_skill.sh <name>`; never hand-copy `template/`.
- Frontmatter `name` must equal folder name (kebab-case, ≤64 chars).
- `description` (≤1024 chars) must state what skill does AND when to trigger it.
- Keep `SKILL.md` concise (<500 lines). Long material → `references/*.md`, linked from `SKILL.md`.
- Scripts in `scripts/` must be runnable standalone, documented in `SKILL.md`, and avoid non-stdlib deps where possible.
- Remove empty `scripts/` / `references/` folders (and their `.gitkeep`) before committing a skill.
- After adding/renaming a skill, update Skills table in `README.md`.

## Checks

Run before commit:

```bash
python3 scripts/validate_skills.py
```

---
name: agent-learn
description: Distills what an agent learned — from user choices and corrections, codebase quirks, failed attempts, git history, tool gotchas, and other skills — into short, evidence-backed Do/Don't rules and Pattern/Antipattern entries, then saves them where the next session will find them. Use when the user says "what did you learn", "distill learnings", "lessons learned", "retro", "do's and don'ts", "write down what we figured out", "remember this for next time", "agent-learn", or after a milestone, a hard debugging session, a repeated user correction, or before ending, handing off, or compacting a long session.
---

# Agent Learn

Turn experience into rules the next session can obey. A learning is a **claim that changes future behavior**, with evidence and a scope. A session summary, a diary, or a restatement of the code is not a learning.

Output kinds:

| Kind | Use for | Shape |
|------|---------|-------|
| **DO** / **DONT** | agent behavior and workflow: "when X, do/never Y" | imperative + trigger + why (+ instead) |
| **PATTERN** / **ANTIPATTERN** | code, config, or design shapes worth copying or avoiding | name + tiny shape block + why (+ replacement) |

Rule of thumb: if it reads "when X, do Y", it is DO/DONT. If you can point at a recognizable chunk of code or structure, it is PATTERN/ANTIPATTERN. Pair an ANTIPATTERN with the PATTERN that replaces it.

## Workflow

### 1. Scope

Default scope: this conversation plus the current repo. If the user names a range ("since October", "this milestone"), use it. Note which destination applies (step 5) before drafting.

### 2. Harvest (read-only)

Collect raw candidates from every source, highest signal first:

1. **User signals** (weight: highest). Corrections ("no, don't…", "stop doing…"), explicit preferences, answers to batched questions, and *quiet confirmations* (a non-obvious choice the user accepted without pushback). Quote the words.
2. **Friction.** Commands that failed then worked, retries, reverted edits, a test that failed for a non-obvious reason, an environment quirk you had to discover.
3. **Codebase.** Things that compile but are wrong, hidden coupling, invariants, naming and structure conventions, "known oddities" sections, docs that disagree with the code.
4. **History.** Run `python3 -I <skill-dir>/scripts/harvest_git.py --repo <dir>` for reverts, fixes, built-then-dropped features, renames, churn hotspots, deleted files, and directive lines added to agent docs. These are leads; open the commit before trusting them.
5. **Other skills and docs.** Rules a skill or doc gave you that proved right or wrong *here*.

Skip: progress narration, what you did, one-off facts, anything the code or git log already states plainly.

### 3. Gate each candidate

Keep it only if **all** hold:

- **Non-obvious**: a competent agent reading the code for five minutes would not already know it, and it is not already in the project's docs.
- **Durable**: it will matter again (next session, next milestone), not only today.
- **Actionable**: it has a trigger and a concrete action or replacement.
- **Evidenced**: points at a commit SHA, `file:line`, user quote, or command output.
- **Verified now**: re-read the file or re-run the command. Never record a guess as fact.
- **Safe**: no secrets, credentials, personal data, or private user content. Refer to real data by path/rule, never by value.

Tag **Source**: `user` (user said it), `observed` (you saw it happen), `inferred` (reasoned, unverified). `inferred` entries need a **Recheck** line or get dropped.

Conflicts: a user statement beats an observation; a newer entry supersedes an older one (edit or delete the old one, do not stack contradictions); two user statements that disagree → ask.

### 4. Write each entry

Use the exact format in [references/entry-format.md](references/entry-format.md): heading `### KIND: imperative title`, then When / Why / Instead / Evidence / Source / Scope / Added (/ Recheck), plus a shape block for patterns. Keep each entry under ~15 lines. Prefer one sharp entry over three vague ones.

### 5. Save where it will be read

Pick the destination by scope; follow the repo's existing convention first.

| Scope | Destination | Approval |
|-------|-------------|----------|
| `project` | the project's agent file (`AGENTS.md` / `CLAUDE.md` "Learned" section) or `docs/learnings.md`; whichever the repo already uses | write, then show the diff |
| `user` | user memory or `~/.claude/CLAUDE.md` | show the draft, write after OK |
| `skill:<name>` | a proposed patch to that skill's `SKILL.md` | show the patch; edit only skills in this repo |
| `tool:<name>` | the project file, under the tool's heading | as `project` |

Hard limits: never edit a section marked human-only or "do not touch"; never commit or push unless asked; never put a secret in a learnings file.

### 6. Maintain

Learnings rot. When touching the file: merge duplicates, supersede stale entries (note the replacement), delete entries proven wrong, and re-verify anything past its **Recheck**. Lint before finishing:

```bash
python3 -I <skill-dir>/scripts/lint_learnings.py docs/learnings.md
```

Exit 1 means a missing field, a duplicate, an `inferred` entry with no recheck, or secret-looking text.

### 7. Report

End with a short table: entries **saved** (kind, title, destination), candidates **dropped** and why (one phrase each), and anything **needing the user's call** (conflicts, `inferred` items, global-scope writes). Do not paste the whole file back.

## Quality bar

Good: "DONT: record Roborazzi goldens outside WSL. Why: rendering differs per host, so goldens churn. Instead: `scripts/loop.sh --record` in WSL only. Evidence: AGENTS.md > Dev loop."
Bad: "Be careful with screenshots." (no trigger, no action, no evidence)

Good: "ANTIPATTERN: destructive migration fallback on a shipped version. Instead: a real `Migration` plus a test that builds the old DB from its exported schema."
Bad: "We migrated the database." (a fact about the past, not a rule)

More worked examples, drawn from a real repo, are in [references/entry-format.md](references/entry-format.md).

## Resources

- `scripts/harvest_git.py`: read-only git-history lead finder (reverts/fixes, removals, renames, hotspots, deleted files, directive lines in agent docs). `--json`, `--since`, `--top`.
- `scripts/lint_learnings.py`: validates the entry format; `--strict` also fails on warnings.
- `references/entry-format.md`: exact entry format, field rules, and worked examples.

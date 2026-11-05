---
name: afwf
description: Ask First, Work Fast (AFWF). ALWAYS use when the user writes "afwf" or "AFWF" anywhere in a message (any case, e.g. "afwf: add login", "do this afwf"). Front-loads every clarifying question into one batched round before any side-effecting action, then executes the whole task end-to-end without further interruptions. Also use for multi-step or ambiguous tasks (features, refactors, migrations, setups, research, documents) where mid-task questions would stall progress, or when the user says "ask first", "ask everything up front", "ask then go", or wants to hand off work and walk away.
---

# AFWF — Ask First, Work Fast

Two phases, hard boundary between them:

1. **Ask phase** — investigate read-only, then ask *every* question in one batch.
2. **Work phase** — execute everything, fast, with zero further questions.

User pays attention once, up front. After that, agent owns the task.

## Phase 1: Ask

### 1. Recon (read-only)

Before asking, learn what can be learned without bothering the user:

- Read relevant files, configs, docs, git history, existing conventions.
- Check tools, environment, access, dependencies available.
- Allowed: reads, searches, listing, dry-runs, `--help`. **Not allowed**: writes, installs, commits, pushes, network mutations, anything with side effects.

Never ask a question recon can answer.

### 2. Find every decision

Walk the whole task mentally, start to finish. At each step note anything that is:

- **Ambiguous** — two reasonable readings lead to different results.
- **A preference** — style, naming, format, location, tooling choice the user may care about.
- **Risky** — destructive, irreversible, outward-facing, costly (deletes, force-push, deploys, emails, paid APIs, migrations).
- **Blocked** — needs credentials, access, files, or info only the user has.

See [references/question-checklist.md](references/question-checklist.md) for categories to sweep.

Drop anything with an obvious conventional default — decide it, list it as an assumption instead.

### 3. Ask in one batch

- Ask **all** questions in a single round. No drip-feeding.
- Order by impact: questions that change the plan most go first.
- Each question gets a **recommended default** and short reason, so user can answer "defaults" in one word.
- Prefer multiple choice over open-ended.
- Request **permission up front** for every risky action found in step 2, so work phase never pauses for approval.
- Include a short **plan preview** (3–7 bullets) and an **assumptions list** so user can correct them in same reply.
- If a structured question tool exists (e.g. `AskUserQuestion`), use it; chain calls back-to-back if limit per call is hit. Otherwise use a numbered list.

Format (plain text fallback):

```
Plan:
- ...

Assuming (say if wrong):
- ...

Questions:
1. <question>? — Recommend: <default> (<why>)
   a) ...  b) ...
2. ...

Permissions needed:
- <risky action> — OK?

Reply with answers, or "defaults" to accept all recommendations.
```

If recon shows zero real questions, skip asking: state plan + assumptions and go straight to work.

## Phase 2: Work Fast

Once answers arrive, lock spec and execute. Do not wait for another confirmation.

- **No new questions.** Fresh ambiguity → pick most reasonable option consistent with user's answers, log it as a decision, continue.
- **Parallelize.** Batch independent tool calls; don't serialize what can run together.
- **No narration of options.** Decide, act, move on.
- **Verify as you go.** Run tests, linters, builds, checks the project has; fix failures without asking.
- **Stay in scope.** Do what was agreed. Note out-of-scope findings for final report instead of chasing them.

### Only stop when

- An action is destructive/irreversible/outward-facing **and** was not pre-approved.
- Answers turn out contradictory or the premise is wrong (e.g. file user named doesn't exist and no clear substitute).
- A hard blocker: missing credentials, access denied, required resource unavailable.

When stopping: finish all unblocked work first, then ask *one* batched follow-up covering every blocker at once.

## Phase 3: Report

End with a short report:

- **Done** — what was completed, where (files, branches, links).
- **Decisions made** — judgment calls taken during work phase.
- **Verified** — what checks ran and results (quote failures exactly).
- **Not done / follow-ups** — skipped items, blockers, out-of-scope findings.

## Anti-patterns

- Asking things answerable by reading code or docs.
- Asking "Should I proceed?" after answers are given.
- Asking one question, waiting, asking another.
- Starting side-effecting work before the ask round.
- Questions without a recommended default.
- Pausing mid-work for a decision the user's answers already imply.

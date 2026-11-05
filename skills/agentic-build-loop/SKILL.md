---
name: agentic-build-loop
description: Continuous agentic creation loop — repeatedly grows a project by implementing the next set of features and scope, running one AFWF (Ask First, Work Fast) question round per iteration, then building, verifying, committing, and proposing the next iteration. Use when the user asks to "keep building", "keep adding features", "continuously expand", "iterate on this project", "build loop", "creation loop", "grow the scope each round", or wants an agent to develop a product over many iterations with check-ins.
---

# Agentic Build Loop

Continuous creation: each iteration **plans → asks (AFWF) → builds fast → verifies → commits → proposes next**. User touches the loop once per iteration, at the ask step. Everything else runs uninterrupted.

Depends on: `afwf` (ask round), `agentic-test-loop` (verify step). Optional: `ultracode` (parallel build).

## State file

Keep loop state in `.agentic/build-loop.md` (committed) so any session can resume. Format: [references/state-template.md](references/state-template.md). Create it on first run; read it at start of every iteration.

## Iteration 0: Kickoff

1. Recon project (read-only): purpose, stack, structure, tests, existing roadmap/issues.
2. AFWF ask round covering whole loop:
   - Vision / end goal; what the product must eventually do.
   - Stack, constraints, style.
   - Iteration size — default: **one vertical slice (1–3 features) per iteration**.
   - Cadence — default: **wait for user answers each iteration**; alternative: auto-accept defaults after each iteration (unattended).
   - Standing permissions: commit each iteration (default yes), push (default no), add dependencies (default ask), run migrations (default no).
   - Stop condition — default: user says stop, backlog empty, or N iterations.
3. Write state file: vision, constraints, permissions, initial backlog (prioritized).

## Each iteration N

### 1. Plan
- Read state file + `git log` since last iteration.
- Pick next increment from backlog: highest value, unblocked, fits iteration size.
- Expand scope deliberately: each iteration may add up to 2 **proposed** new backlog items (ideas discovered while building). Proposed, never built without approval.

### 2. Ask (AFWF, one round)
Single batched message:
```
Iteration N — last iteration: <1-line result>

Plan this round:
- <feature 1>: <what, where>
- <feature 2>

Assuming (say if wrong):
- ...

Questions:
1. ... — Recommend: <default> (<why>)

New scope proposals (approve / reject / later):
- <idea> — <why it helps>

Reply with answers, "defaults", or "stop".
```
Rules: every question has a default; no question recon can answer; also ask about anything from last iteration's review that needs a decision.
Unattended cadence → skip waiting, apply defaults, log them as decisions.

### 3. Build fast
- No further questions this iteration (AFWF work phase).
- Independent features → parallel (spawn agents when `ultracode` is on).
- Write tests alongside features.

### 4. Verify
Run `agentic-test-loop` on the project (bounded budget). Iteration is **done only when green**. If budget runs out: keep the failing work on a branch or revert it, and note it.

### 5. Commit + log
- One commit (or small series) per iteration: `iter N: <summary>`.
- Update state file: iteration log entry, backlog changes, decisions, open questions.

### 6. Report + next
Short report (done / decisions / verified / not done), then go straight into step 1 of iteration N+1, ending with its ask round. The report and the next ask go in **one message**.

## Continuous running
- Interactive: loop is natural — each user reply starts the next build phase.
- Unattended: `/loop` self-paced with prompt `continue agentic-build-loop`, cadence = auto-defaults. Cap iterations (default 5) and stop on any red verify.
- Resume later: "continue build loop" → read state file, start at step 1.

## Rules
- Never build unapproved scope; proposals wait for a yes.
- Never leave main branch red at end of iteration.
- Never skip the ask round in interactive cadence. No questions → still send plan + scope proposals; user's reply (or "defaults") starts the build.
- Keep iterations small; a feature too big for one iteration → split it in backlog.
- Pushes, deploys, publishing, paid APIs: only with standing permission from kickoff.

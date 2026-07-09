---
name: workflow
description: Phased plan-then-build discipline for tasks in projects that have no workflow process of their own. Use when starting any non-trivial change (a feature, a refactor, a bug fix beyond a one-liner) and a structured approach is wanted, understand the task, write a plan, cross-check it against whatever conventions the project already documents, implement with checkpoints, and verify. Also invoked explicitly as /lodestar:workflow. Skip for trivial edits, or when the project already ships its own documented workflow, defer to that instead.
---

# Lodestar

A portable process for turning a task into a plan and a plan into shipped,
verified work — for any project, including ones with no process of their own.

Lodestar carries only the transferable techniques: phased execution, a strict
question protocol, a written-down plan as the source of truth, adaptive TDD,
progress checkpoints, and verification. It carries **no** project-specific
machinery (no task registry, no numbering, no archive folders, no mandated ADR
flow). The plan lives in an ephemeral, git-ignored file and is deleted or kept
at the end by the user's choice.

## When to use

- Any feature, refactor, or non-trivial bug fix where a disciplined path helps.
- Invoked explicitly via `/lodestar:workflow`.

## When NOT to use

- **Trivial edits** — typo, one-line config tweak, obvious rename. Just do it.
- **The project already documents its own workflow** (e.g. a `WORKFLOW.md`, a
  contributing process, a task-workflow skill). Defer to the project's process;
  do not impose Lodestar over it. If unsure whether one exists, the Understand
  phase will surface it — then stop and ask which to follow.

## Invocation modes

Everything after `/lodestar:workflow` is the argument. The first word may select a mode;
otherwise the whole argument is the task description and the full flow runs.

| Invocation | Phases run | Behavior |
|------------|-----------|----------|
| `/lodestar:workflow <task>` | 0–6 | Full flow. Plans, then implements after the approval gate. |
| `/lodestar:workflow plan <task>` | 0–3 | **Plan only.** Writes and gets the plan approved, then STOPS. Does not implement. |
| `/lodestar:workflow execute <plan-file>` | 4–6 | **Execute a saved plan.** Reads an existing `.workflow/plan-*.md` and implements it. Works in a fresh session. |
| `/lodestar:workflow plan-all <files/dir>` | 0–3 ×N | Fans out one subagent per task file to produce a plan file each. See Batch mode. |
| `/lodestar:workflow execute-all` | 4–6 ×N | Fans out one subagent per approved plan in `.workflow/`. See Batch mode. |
| `/lodestar:workflow help` | none | Print the modes table and a one-line reminder of each, then stop. Take no other action. |

When invoked with `help` (or with an argument that is clearly a request to list
usage, e.g. an empty `?`), reproduce this table for the user and do nothing
else — do not start a task, do not ask clarifying questions.

`plan` and `execute` are the two halves of the gate made explicit, bridged by
the durable plan file. `execute` mode still runs the Phase 1 *convention
discovery* (read `CLAUDE.md`, `.claude/rules/`, specs) so implementation stays
rule-compliant — it just skips the clarifying questions, which the plan already
resolved.

## God Rules (never skip, no exceptions)

1. **Think deeply before proposing.** Analyze the affected code and logic for
   gaps, trade-offs, UX impact, and possible regressions. Surface anything
   non-obvious that could be affected.
2. **Fix the cause, not the symptom.** If the best available fix is a
   workaround, say so explicitly, name the root cause it leaves unresolved,
   propose a proper fix, and ask which to take — never silently ship a workaround.
3. **Follow existing patterns, never invent.** Find an existing example of the
   same kind and follow its structure and conventions exactly. Read sibling
   code first. If no precedent exists, ask. Place logic where the architecture
   dictates, not where it's convenient.
4. **Ask, don't guess.** Ambiguous requirement → ask before implementing.
   Never assume intent.
5. **Explain before acting.** Briefly state what will change and why, then get
   confirmation before writing code.
6. **Push back when something seems wrong.** Don't follow instructions blindly.
   If something risks a regression or doesn't make sense, stop and ask.
7. **Never push without asking.** `git push`, force-push, tags/releases, or any
   outward-facing git action — ask first.
8. **Maintain the project's rules proactively** *(only when the project
   documents conventions — `.claude/rules/`, `CONTRIBUTING.md`, specs)*. If work
   reveals a documented rule is missing, outdated, or incomplete, flag it, name
   the file, show the exact proposed text, and get confirmation before editing.
9. **Design for extension.** When behavior branches on a finite set (type,
   provider, status, role), put the branch in one place — an enum method,
   strategy, or registry — so new cases opt in without hunting call sites.
   Heavier abstractions need an explicit trade-off discussion first.
10. **Evidence before hypothesis.** Measure before diagnosing a bug. If a fix
    doesn't move the measurement, revert it before the next hypothesis — never
    stack guesses.
11. **Never run destructive or irreversible commands without explicit
    per-command approval** — dropping/resetting a database, mass deletes,
    `rm -rf`, force-push, any mutation of a production or shared environment.
    "Just verifying" is not a reason; use a test or throwaway target.

Two process invariants that sit alongside the God Rules:

- **The plan is the single source of truth.** In-session thinking does not
  survive; the plan file does (until deleted).
- **No scope creep, no speculative abstractions.**

## Phases

Small tasks skip phases 2 and 3. See the Task Size Guide.

### Phase 0 · Scope

Assess size against the Task Size Guide before anything else. Decide whether a
plan file is needed (Medium/Large) or the work goes straight to implementation
(Small). If the task spans several independent subsystems, say so and help
decompose it before refining details — do not plan a task that should be split.

### Phase 1 · Understand

1. Read `CLAUDE.md` / `AGENTS.md` at the repo root if present.
2. **Discover the project's own conventions.** Look for `.claude/rules/`, a
   `docs/` spec directory, ADRs, `CONTRIBUTING.md`, or a documented workflow.
   - If found: load the parts that apply to the affected layers and treat them
     as binding constraints for the plan and the code.
   - If a full workflow process is found: stop and ask whether to follow that
     instead of Lodestar (see "When NOT to use").
   - If nothing is found: proceed lean — this is the projects-without-process case.
3. Ask clarifying questions via the Question Protocol until purpose,
   constraints, and success criteria are clear.
4. Confirm shared understanding before planning.

### Phase 2 · Plan (Medium / Large)

1. Ensure `.workflow/` is git-ignored: if the repo has a `.gitignore` and it
   lacks `.workflow/`, append it. If there is no `.gitignore`, create one
   containing `.workflow/`.
2. Write the plan to `.workflow/plan-<slug>.md`. Start the file with a header
   line `status: draft`, then: goal and non-goals, affected files/modules,
   ordered implementation steps as checkboxes (`- [ ]`), and acceptance
   criteria. The `status` line is what `execute-all` reads to tell approved
   plans from drafts.
3. **Cross-check the plan against every convention discovered in Phase 1.**
   Where a rule/spec applies, the plan must comply — file placement, naming,
   contracts, testing conventions. If a rule conflicts with the intended
   approach, flag it in the plan and resolve it before writing code. A plan
   that silently violates a discovered rule is invalid.
4. *(Optional, offer it)* Run the plan through `lodestar:audit-solution` to catch
   workarounds, fragile choices, or a better pattern before committing to it.
5. **Gate — no implementation without explicit approval.** Present the plan and
   wait for a clear "go". On approval, flip the file's header to
   `status: approved`. In `plan` / `plan-all` mode, **stop here** and tell the
   user how to run it later (`/lodestar:workflow execute .workflow/plan-<slug>.md`). In
   full mode, continue to Phase 4.

### Phase 3 · Design Review (Large only)

Propose 2–3 approaches with trade-offs via the Question Protocol, one
recommended. User picks. Record the chosen approach in the plan file.

### Phase 4 · Implement

1. **Adaptive TDD.** If the project has a test setup (or one clearly fits),
   work test-first: write a failing test → minimal code to pass → refactor
   green. If there is no test setup and none fits, say so explicitly and plan
   verification by other means (run it, lint it, exercise the flow).
2. **Follow the discovered conventions** while coding, not just while planning.
   If implementation reveals a rule the plan missed, stop and revise the plan.
3. Work the plan step by step; check off boxes as steps land.
4. **Checkpoint after each major step** — a one-line summary of what was done.
5. **Roll back, don't fix forward.** If a step produces unexpected results,
   stop and show the problem before continuing. Never stack guesses.
6. **No mid-work commits.** Accumulate changes; commit once after verification,
   and only when the user asks.

### Phase 5 · Verify

1. Run the relevant tests and linters if they exist; otherwise run the app /
   exercise the changed flow and observe it end-to-end.
2. On failure: fix and re-run. If the fix is non-trivial or changes the
   approach, stop and discuss.
3. If the project has `.claude/rules/`, offer to run `lodestar:check-rules` over the
   changes.
4. *(Optional, offer it)* Run `lodestar:audit-solution` over the final diff.
5. Confirm the result matches the plan; note any deviations in the plan file.

### Phase 6 · Wrap-up

1. **Propose — never perform unprompted — documentation updates**, and only when
   an update is genuinely warranted (a README, a doc the change makes stale, a
   discovered spec). State exactly what would change and ask first.
2. Offer `/lodestar:pm-report` for a plain-language summary of the session.
3. Ask whether to **delete or keep** `.workflow/plan-<slug>.md`.

## Batch mode with subagents

For several tasks described in files, plan and execute them as a fan-out. Each
subagent runs Lodestar's own phases on one item and writes/consumes a plan file
in `.workflow/`. The plan files are the hand-off contract between the two batch
phases.

### `plan-all <files or dir>`

1. Resolve the list of task files (a glob, a directory, or an explicit list).
2. Dispatch **one subagent per task file**, in parallel (independent work — send
   the Agent calls together). Each subagent's brief: read its task file, run
   Phase 0–2 for that task, and write `.workflow/plan-<slug>.md` with
   `status: draft`. The subagent does **not** implement and does **not** ask the
   user questions — it records open questions in an `## Open questions` section
   of its plan instead.
3. Collect the results and present the list of draft plans for review. The user
   reviews and approves each (flipping to `status: approved`) or sends notes
   back. Nothing is implemented in this phase.

### `execute-all`

1. Read `.workflow/` and select every plan with `status: approved`. Report which
   were skipped as `draft` — never silently execute an unapproved plan.
2. Dispatch **one subagent per approved plan**. Each subagent's brief: run
   `execute` mode on its plan file (Phase 1 convention-discovery + Phases 4–6),
   then mark the plan done.
3. **Isolation.** If the tasks touch overlapping files, run them with
   `isolation: "worktree"` (each subagent in its own git worktree) or run them
   sequentially — parallel edits to shared files corrupt each other. If the
   tasks are disjoint, plain parallel is fine.
4. Each subagent verifies its own task (Phase 5). Aggregate the outcomes and
   report per-task pass/fail; do not claim the batch succeeded if any task's
   verification failed.

Subagents inherit no conversation context — every brief must name the task
file or plan file path explicitly and restate the project-root path so the
subagent can re-discover `CLAUDE.md` and `.claude/rules/` on its own.

## Question Protocol

Applies whenever asking the user anything during any phase.

1. **Scope check first.** Flag an over-large task before refining its details.
2. **One question per message.** Never batch.
3. **Focus** each question on purpose, constraints, or success criteria — fill a
   real gap, don't ask filler.
4. **Numbered options** (A, B, C…), each a genuine alternative. Mark one
   **recommended** with a one-line why.
5. **Action line:** invite a letter, or discussion. Anything that isn't a
   letter is treated as discussion — answer it, then re-present the options.
6. **Low-stakes shortcut:** when the answer is near-obvious (convention-following
   placement, etc.), label it low-stakes and offer a default to confirm.
7. Wait for the response before the next question.

## Task Size Guide

| Size | Examples | Phases | Plan file? |
|------|----------|--------|------------|
| Small | Bug fix, typo, config change | 0, 1, 4, 5, 6 | No |
| Medium | New endpoint, new component, focused refactor | 0, 1, 2, 4, 5, 6 | Yes |
| Large | New subsystem, cross-cutting change | 0, 1, 2, 3, 4, 5, 6 | Yes |

## Companion skills

Lodestar orchestrates other skills but always **offers** them — it never runs
them silently:

- **`lodestar:audit-solution`** — vet the plan (Phase 2) and/or the final diff (Phase 5)
  for robustness and better patterns.
- **`lodestar:check-rules`** — verify the diff against `.claude/rules/` when the project
  has them (Phase 5).
- **`lodestar:pm-report`** — plain-language session summary at wrap-up (Phase 6).

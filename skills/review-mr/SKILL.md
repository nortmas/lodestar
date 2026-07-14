---
name: review-mr
description: Independent review of a merge/pull request (GitLab MR or GitHub PR) or a local branch diff. Catches what tests and the author miss — behavior drift, violated invariants, and unmet requirements / gaps. Anchors to the spec, behavior-diffs the change, checks coverage, and judges the whole (code and parallel paths outside the diff, not just changed lines). Triggers on '/lodestar:review-mr' — manual only; shows findings before posting, never merges or approves.
disable-model-invocation: true
---

# Review MR / PR

You are an **independent** reviewer of a merge/pull request. Your job is not "read the diff and find
bugs" — it is to catch the failures that automated tests and the author both miss: a change that
**silently alters existing behavior, violates a documented invariant, or fails to satisfy a
requirement** — while looking clean and green. The defect is as often what the change **omits** as
what it does.

The target is whatever the user passed after the command:
- A number / `!123` / `#123` / MR-or-PR URL → review that MR/PR on the remote.
- A branch name → review that branch vs the default branch.
- Empty → review the current branch vs the repository's default branch.

Write the review in the user's language.

## Why this skill exists (the failure modes it defends against)

The most expensive review miss is **requirement drift**: the author built a feature and, in doing so,
made the code do something *different than before* for the same input — and the tests pass because
the same author wrote tests for the new behavior, not the required one. The author cannot catch this
(they are inside their own frame) and green tests do not catch it (they assert the implemented
behavior). Only **independence + a source-of-truth anchor** catches it. That is the entire point of
this skill; everything below serves it.

The second is **omission**: a requirement the change was supposed to satisfy is simply not met — a
behavior the parallel path has that the new one lacks, a config/data source the incumbent reads that
the new code doesn't, a spec clause with no corresponding code. No line in the diff is *wrong*, so a
behavior-diff and green tests both slide past it. Only deriving the full requirement set and checking
coverage against it catches a gap. Both modes share a root: the decisive context lives **outside the
diff** — in the spec and in the sibling implementation the change parallels.

## Four rules

1. **Behavior-diff, not code-diff.** For every change ask: *"what does this do differently than
   before, for the same input?"* A refactor should be behavior-neutral; anything that adds a removal,
   exclusion, filter, flag, or side effect the old path didn't have is a **divergence** that must be
   justified against the spec — flag it even if the code is correct.
2. **Anchor to the source of truth, not the diff.** Find the governing spec / requirements / rules
   and check the change *against them*. When the diff and the spec disagree, the spec wins. A change
   that contradicts a documented invariant is a top-severity finding regardless of test status.
3. **Distrust green tests.** A passing test can assert the wrong thing. For each test touched/added
   ask: *what does it actually assert, and could it pass while the behavior is wrong?* A test whose
   name claims a property ("parity", "idempotent", "isolation") but exercises only one side of it is
   a red flag — call it out.
4. **Judge the whole, not the diff.** Correctness routinely depends on things the diff never
   touches: a requirement with no corresponding code, a removal the change forgot to make, an
   incumbent/parallel path that reads a different source. Pull in the governing spec and the sibling
   implementation and review the change as a *system in its context*, not a line-by-line delta. A
   required behavior with **no** change to point at is still a finding.

## Step 0 — Detect the environment (do not assume)

- Remote host: `git remote get-url origin` → GitHub, GitLab, or other.
- Default branch: `git symbolic-ref refs/remotes/origin/HEAD` or `git remote show origin` (fall back
  to `main`/`master`/`develop`).
- Platform tooling:
  - **GitHub** → `gh` CLI (`gh pr view`, `gh pr diff`, `gh pr review`) if present.
  - **GitLab** → GitLab MCP tools (load via ToolSearch: `get_merge_request`,
    `get_merge_request_diffs` / `list_merge_request_diffs`, `get_merge_request_changed_files`,
    `create_merge_request_discussion_note`, `create_draft_note`). Resolve the project from the remote
    URL (namespace/path or numeric id).
  - Neither / offline → local diff (`git diff <default>...HEAD`).

If the target is an MR/PR you cannot resolve, ask for the id/URL or fall back to the local current
branch (state which you did).

## Step 1 — Gather the change

- Full diff + list of changed files.
- MR/PR **title + description** if remote — it states the *intent* you check behavior against.
- Read enough surrounding code (not just the hunks) to know what each changed unit did **before**.
  You cannot judge a behavior-diff from added/removed lines alone.

## Step 2 — Find the governing invariants (source of truth)

Discover whatever exists — do not assume a fixed path:
- Spec / requirements (search `spec`, `requirements`, `specs/`, `docs/`, `*.md` about the affected
  feature; the MR/PR description may link one).
- Project rules / conventions: `.claude/rules/`, `CLAUDE.md` / `AGENTS.md`, `CONTRIBUTING.md`.
- The **existing sibling behavior** the change parallels (e.g. an old code path the new one must
  match). Its current behavior is an invariant to preserve unless the MR explicitly changes it.

If you find no source of truth for a risky change, that absence is itself worth reporting.

## Step 3 — Review with fresh context (independence)

Dispatch the analysis to **independent subagents** (Task tool). Withhold **the author's design
rationale** — do not pre-load "here's why the author did X"; that withholding is what reproduces the
outsider's view that catches drift. But give each subagent the diff, the spec/invariants, the stated
intent, **and full read access to the repository** — they must be able to pull in callers, the
parallel/incumbent path, and derived data that live *outside* the diff, or the lenses below cannot do
their job. Lenses:

- **Parity / invariant** — does it violate a documented invariant or silently diverge from the
  behavior it parallels? (Highest priority.)
- **Completeness / requirement coverage** — derive the checklist of everything the change *must*
  satisfy (spec clauses, the behaviors/inputs/config-sources of the parallel path it mirrors, the
  stated intent) and verify each item is actually met. An unmet item is a finding even when no diff
  line is wrong — this is how omissions and gaps surface, which a behavior-diff cannot. Look beyond
  the changed files to find what's missing.
- **Correctness & blast radius** — logic errors, edge cases, N+1 / performance cliffs, security,
  error handling. For every changed symbol ask: *what calls it, and do their expectations still
  hold?* Flag caches, indexes, and denormalized/derived data (e.g. generated columns, materialized
  counts) the change must update but doesn't — a frequent out-of-diff regression.
- **Test quality** — do tests assert the *required* behavior or just the *implemented* one? Could
  any pass while the behavior is wrong? Anything named for a property it doesn't verify?
- **Design fit & convention** — does it follow the project's own rules/patterns (Step 2)? Does the
  change belong here (right layer/module) or was it put where convenient? Is it over-engineered or
  solving a speculative future problem instead of the one at hand?

For large diffs, fan out by area/file and merge. Scale effort to diff size.

## Step 4 — Verify and rank

- Confirm each candidate finding against the actual code (open the file, trace it) before reporting.
  Drop what you cannot substantiate — no speculative noise.
- **Impact threshold.** Report a finding only if it scores on all three: *likely to occur* ×
  *harmful if it does* × *non-obvious to the author*. Drop what a linter, formatter, or CI already
  catches — spend judgment on logic, design, and behavior, not style.
- **Assume defects exist.** Approach the change expecting to find problems, not to confirm it is
  fine. **Zero findings is a stop signal** — re-analyze against the spec and the parallel path, or
  state explicitly why the change is genuinely clean. Do not default to LGTM.
- Rank by severity × confidence; a behavior/invariant divergence outranks a style nit.
- Per finding: `file:line`, what's wrong, the concrete failure scenario (input → wrong outcome), and
  the fix direction.

## Step 5 — Deliver

- **Verdict first**: safe to merge / merge with changes / do not merge, plus the 1–3 findings that
  drive it. Then the ranked findings.
- **Posting to the MR/PR**: offer to post findings as inline comments, but **show them first and post
  only after the user confirms.** Prefer draft/pending comments (GitLab `create_draft_note`, GitHub
  `gh pr review`). Never approve or merge on the user's behalf.
- Review only. Do not fix code in this skill unless the user explicitly asks afterward.

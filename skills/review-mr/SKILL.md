---
name: review-mr
description: Independent review of a merge/pull request (GitLab MR or GitHub PR) or a local branch diff. Catches what tests and the author both miss — silent behavior drift and violated invariants. Anchors to the spec, does a behavior-diff (what changed for the same input), distrusts green tests, and reviews with fresh context. Triggers on '/lodestar:review-mr' — manual only. Posts inline comments only after the user confirms; never merges or approves.
disable-model-invocation: true
---

# Review MR / PR

You are an **independent** reviewer of a merge/pull request. Your job is not "read the diff and find
bugs" — it is to catch the failure that automated tests and the author both miss: a change that
**silently alters existing behavior or violates a documented invariant**, while looking clean and
green.

The target is whatever the user passed after the command:
- A number / `!123` / `#123` / MR-or-PR URL → review that MR/PR on the remote.
- A branch name → review that branch vs the default branch.
- Empty → review the current branch vs the repository's default branch.

Write the review in the user's language.

## Why this skill exists (the failure mode it defends against)

The most expensive review miss is **requirement drift**: the author built a feature and, in doing so,
made the code do something *different than before* for the same input — and the tests pass because
the same author wrote tests for the new behavior, not the required one. The author cannot catch this
(they are inside their own frame) and green tests do not catch it (they assert the implemented
behavior). Only **independence + a source-of-truth anchor** catches it. That is the entire point of
this skill; everything below serves it.

## Three rules

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

Dispatch the analysis to **independent subagents** (Task tool), each given **only the diff +
spec/invariants + intent — and none of the author's design rationale**. This reproduces the
outsider's view that catches drift; do not pre-load "here's why the author did X." Lenses:

- **Parity / invariant** — does it violate a documented invariant or silently diverge from the
  behavior it parallels? (Highest priority.)
- **Correctness** — logic errors, edge cases, N+1 / performance cliffs, security, error handling.
- **Test quality** — do tests assert the *required* behavior or just the *implemented* one? Could
  any pass while the behavior is wrong? Anything named for a property it doesn't verify?
- **Convention** — does it follow the project's own rules/patterns (Step 2)?

For large diffs, fan out by area/file and merge. Scale effort to diff size.

## Step 4 — Verify and rank

- Confirm each candidate finding against the actual code (open the file, trace it) before reporting.
  Drop what you cannot substantiate — no speculative noise.
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

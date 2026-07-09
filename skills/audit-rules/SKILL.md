---
name: audit-rules
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
description: Audits project rules in .claude/rules/ for clarity, conciseness, structural compliance, and cross-rule integrity. Produces a markdown report with prioritized findings and per-rule rewrite proposals. Use when asked to audit rules, check rule quality, find rule gaps, lint a rule, review .claude/rules, or improve rule wording. Triggers on '/lodestar:audit-rules' or when user asks to check, audit, lint, or improve project rules.
---

# Audit Rules

## When to use

Trigger this skill when the user asks to:
- Audit project rules in `.claude/rules/`
- Check rule quality, structure, or compliance
- Find gaps, inconsistencies, or drift across rules
- Lint a specific rule for clarity or conciseness
- Improve rule wording or trim bloat`
- Run `/lodestar:audit-rules` (with or without an argument)

**Do NOT trigger for:**
- Writing a new rule from scratch (use `skill-creator` or `superpowers:writing-skills`)
- Checking application code against rules (use `lodestar:check-rules`)
- Editing CLAUDE.md (use `claude-md-management:claude-md-improver`)
- Auditing rules outside `.claude/rules/` (e.g., plugin rule files in `.claude/plugins/`)

## Inputs

The skill accepts an optional target argument:
- **No argument** → audit ALL files matching `.claude/rules/*.md`
- **Filename** (basename or relative path) → audit a single rule. Match by basename first; if multiple match, fail with a list.
- **Glob pattern** (e.g. `laravel-*.md`) → audit the matched subset.

If the target resolves to zero files, fail loudly with a directory listing of `.claude/rules/`. Never silently audit nothing.

If `.claude/rules/` itself doesn't exist, fail with a clear message — this skill operates on a project-local rules folder.

Additional input edge cases:
- **No extension on filename argument.** If the user passes a basename without `.md` (e.g. `cost-tracking`), append `.md` automatically and re-attempt the basename match. If still no match, fail with the standard "no files match" error.
- **Absolute path argument.** Reject absolute paths with: *"Provide a basename or glob pattern, not an absolute path. The audit operates only on `.claude/rules/`."* Do not attempt to normalize.
- **Glob escaping the rules folder.** All glob patterns are evaluated relative to `.claude/rules/`. Patterns resolving outside that directory (e.g. `../*.md`, `..`, `/`) are rejected with: *"Glob patterns must stay within `.claude/rules/`."*

## Workflow

1. **Resolve scope.** Parse the optional argument; build the list of target files. Fail fast on resolution errors. Record the audit start timestamp immediately after the file list is resolved. This timestamp is the mtime baseline for all subsequent apply-gate checks.

2. **Load rubric and exemplar.** Read into memory:
   - `references/best-practices.md` — the canonical rubric
   - `references/audit-checklist.md` — the actionable checks with severity tiers
   - `references/report-template.md` — the report skeleton
   - `examples/exemplary-rule.md` — the canonical good rule for comparison

3. **Per-rule deterministic pass.** For each target file:
   - Parse the markdown structure (headings, code blocks, links).
   - Run the regex/heuristic scans listed in `references/audit-checklist.md` §4.
   - Validate `Related rules` links resolve to real files in `.claude/rules/`.
   - Collect findings with severity tags from `references/audit-checklist.md` §1.

4. **Per-rule LLM judgment pass.** For each target file (one at a time, in isolation):
   - Apply the LLM judgment questions in `references/audit-checklist.md` §3 yourself, using the rule + rubric + exemplar + collected deterministic findings as context.
   - Produce additional findings + a **proposed rewrite** (only when MAJOR or BLOCKER findings exist; MINOR/NIT-only files get findings without a rewrite).

5. **Cross-rule pass** — only when scope > 1 file. Run the cross-rule checks in `references/audit-checklist.md` §5: bidirectional gaps, overlapping prescriptions, contradictions, naming drift.

6. **Render report inline.** Fill in `references/report-template.md` with:
   - Header summary (totals)
   - Overview table (sorted by total severity weight; blocker = 8, major = 4, minor = 2, nit = 1)
   - Cross-rule findings (if scope > 1)
   - Per-rule findings (per affected rule)
   - Passed-clean table (rules with zero findings)

   Print the rendered report directly to the chat as the assistant's response. **Do NOT write the report to a file.** The user reads it inline; if they want a copy, they can ask explicitly.

7. **Apply gate.** Print the prompt for the apply choice (see Apply Step below).

## Output

**Report destination:** the chat response. The skill MUST NOT write the report to a file by default. If the user explicitly asks "save this audit" they can copy the chat content; persistence is a manual step, not an automatic one.

**Required leading summary line** — emit BEFORE the full report tables, so a long report is scannable:

> Audit complete: N rules audited · M with findings (B blockers, J majors, K minors, L nits) · R rules with proposed rewrites. Top 3 affected: rule1 (counts), rule2 (counts), rule3 (counts).

After the summary line, render the full report (overview table, cross-rule findings if scope > 1, per-rule findings, passed-clean list) directly in the chat.

## Apply step

After the report is rendered in chat, prompt the user:

> N rules have proposed rewrites · R recommended (real findings) · S skipped (advisory or known false positives). How would you like to proceed?
> 1. **Apply recommended** — apply all R recommended fixes in one pass; advisory MAJORs and known FPs are skipped automatically.
> 2. **Review each** — I show each proposed rewrite (counts + diff summary + full text); you accept/skip/edit per rule.
> 3. **Apply specific** — name a comma-separated list of rule basenames from the report above.
> 4. **Skip apply** — exit; the report stays in chat history.

**What counts as "recommended" vs "skipped":**

- **Recommended:** any rule with at least one finding that is BLOCKER, MAJOR (non-advisory, non-FP), or actionable MINOR (e.g., bare opening fence, dead cross-reference, leaked task number).
- **Skipped automatically:** advisory MAJORs (non-canonical first H2 — by-design acceptable per the calibrated rubric), known self-referential false positives (e.g., the rule that documents an anti-pattern using illustrations of it), and inline-only `Related rules` MINORs (project convention per "Known Deviations").

The skill MUST classify each rule's findings explicitly into recommended vs skipped before emitting the apply prompt. The R and S counts in the prompt come from this classification.

Per project rule (CLAUDE.md God Rule 8 — rule edits require explicit confirmation), there is **NO "apply all without classification" option**. "Apply recommended" is permitted because the classification (recommended vs skipped) is itself an explicit confirmation step the skill commits to in this rubric — the user opts into a defined, enumerated set, not a blanket "everything".

**Mtime guard:** before applying a rule's rewrite, re-stat the rule file. If its mtime is newer than the audit start timestamp recorded in step 1, abort that rule's apply with: *"Rule changed since audit — re-run /lodestar:audit-rules to refresh."* The skill MUST NEVER overwrite changes it didn't see.

**Edit mechanic:**
- For a rewrite where more than 50% of the file's lines are changed: use `Write` (full-file replacement).
- For smaller scoped changes: use `Edit` with old/new strings derived from the per-finding "Proposed fix" cells in the rendered report (they're in chat scrollback).

## Failure modes

| Failure | Behavior |
|---|---|
| `.claude/rules/` missing | Fail with clear message; this skill needs a project-local rules folder. |
| Target glob matches nothing | Fail with directory listing of `.claude/rules/`. |
| Rule file unreadable | Log path + error; skip the file; continue with the rest. |
| Markdown parse error | Fall back to regex-only scans for that file; emit a NIT finding noting the parse error. |
| LLM judgment output malformed | Retry once with stricter format prompt; on second failure, drop LLM judgment findings for that file but keep deterministic findings. |
| User invokes during another long-running operation | Run anyway; the audit is read-only until the apply gate. |

---
name: init-rules
description: Generate project-specific coding-standard rules at .claude/rules/ by analyzing the existing codebase and balancing it against best practices. Use this whenever the user wants to bootstrap, (re)generate, or refresh Claude Code rules for a project, mentions "project rules", "coding standards", "CLAUDE rules", ".claude/rules", "onboard this repo", or asks Claude to learn/codify how this codebase does things. Prefer this skill even if the user does not say the word "rules" but describes wanting Claude to follow their project's conventions.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, WebSearch, WebFetch
---

# lodestar:init-rules

Generate modular, path-scoped rule files at the target project's `.claude/rules/*.md` that
encode how *this* codebase actually works — not generic textbook standards.

**Defining behavior — the balance policy.** When the codebase already follows a consistent
pattern, that pattern becomes the rule, even if it diverges from best practice. Best practice
is used only where the codebase has no consistent pattern, or where the existing pattern is a
**security, correctness, or performance defect**. This inverts the usual "refactor toward the
textbook" posture: here, working consistency outranks theory — everywhere except the safety
carve-out. The full algorithm lives in `references/balance-policy.md`; internalize it before
generating anything.

## Golden rules

- Write ONLY to `.claude/rules/`. Never touch `CLAUDE.md`, `.ai/guidelines/`, source, or config.
- Never overwrite an existing rule file silently — diff and ask (see step 5).
- Reference files load on demand. Read only the layers the detected stack activates.
- Be honest in the report: label every rule `existing-pattern` | `best-practice` | `researched`.

## Reference map — read a file only when its cue fires

| File | Read this when… |
|------|-----------------|
| `references/detection.md` | Step 1 — mapping repo signals to layers; adding a new layer |
| `references/balance-policy.md` | Step 3 — deciding each rule's source (the core algorithm) |
| `references/rule-authoring.md` | Step 4 — writing any `.claude/rules/*.md` file (required shape + example) |
| `references/base/*.md` | A base concern (core, naming, architecture, git) is activated |
| `references/languages/<lang>.md` | That language is detected |
| `references/frameworks/<fw>.md` | That framework is detected |
| `references/packages/**/<pkg>.md` | That dependency is detected (Boost-style, per-package) |
| `references/concerns/<c>.md` | That cross-cutting concern is in scope |
| `references/devops/*.md` | Docker / GitLab CI / general pipeline files are present |

Each reference file declares a tier (see `references/detection.md`): Tier 1 is authoritative,
Tier 2 is usable-now, Tier 3 is a skeleton with a research hook — deepen Tier 3 layers via
`WebSearch` on activation (provenance `researched`).

## Workflow

### 1. Detect the stack

Read `references/detection.md` and follow it. Inspect (whichever exist): `composer.json` +
`composer.lock`, `package.json` + lockfile, `pyproject.toml` / `requirements.txt`, an existing
`CLAUDE.md`, framework markers (`artisan`, `config/app.php`, `vite.config.*`, `manage.py`,
`Dockerfile`, `docker-compose.yml`, `.gitlab-ci.yml`), and the directory layout. Map each
signal to the reference layers to activate.

**Detect at the package level too (Boost-style):** walk the dependency lists and activate the
matching `packages/*` reference — `livewire/livewire` → `packages/laravel/livewire.md`,
`filament/filament` → `filament.md`, `pestphp/pest` → `pest.md`, `tailwindcss` →
`packages/frontend/tailwind.md`, etc. Prefer the *installed* version (from the lockfile) when a
rule is version-specific.

### 2. Confirm with the user

Present the detected stack and the list of concern areas that will get rules. Ask the user to
confirm or correct **before** generating. Accept overrides (add/remove any layer or concern).
This matters because a wrong detection wastes a whole generation pass and can mislabel provenance.

### 3. Analyze + decide per concern

For each activated concern, read the relevant reference file(s) AND sample the real codebase
(a meaningful set of files, never one). Then apply `references/balance-policy.md` to classify
the existing pattern (`CONSISTENT` / `MIXED` / `ABSENT`) and choose the rule source. This is
where working consistency wins over theory — except for the security/correctness/performance
carve-out, where best practice wins and you emit a migration note instead.

### 4. Generate rules

Write one file per concern to `.claude/rules/`, following `references/rule-authoring.md`
*exactly*: YAML frontmatter with `name`, `description`, and `globs`; concrete quantified
directives; at least one `❌ Bad` / `✅ Good` pair per key rule; a provenance footer. Draw the
`✅ Good` example from the real codebase when codifying an existing pattern. Only emit concerns
relevant to the detected stack.

Before writing each file, run its **quality gate** (`references/rule-authoring.md` → "Quality
gate"): no voice softeners, every fence language-tagged, every `❌` paired with a `✅`, no leaked
task/ADR numbers or unresolvable code symbols, `globs` tight, provenance footer present. Fix in
place so every rule is born audit-clean — a hedged or self-inconsistent rule stops catching
violations.

### 5. Safe write / update mode

Before writing, check whether the target file already exists.
- **New file** → write it.
- **Existing file** → show a diff and ask before changing. In update mode, **merge** (preserve
  the user's edits and additions) rather than clobber. Never blow away hand-tuned rules.

### 6. Do not modify CLAUDE.md

`CLAUDE.md` is assumed to exist; only read it (for context and to avoid duplicating what it or
`.ai/guidelines/` already inject). After writing, print a suggested `@`-import snippet the user
can paste manually, for any rule that should always be in context, e.g.:

```
@.claude/rules/architecture.md
@.claude/rules/security.md
```

### 7. Report

Emit a summary table: each generated rule, its provenance
(`existing-pattern` | `best-practice` | `researched`), a confidence level (high/medium/low),
and any `⚠ migration note` where a legacy anti-pattern was intentionally NOT codified. Keep
`existing-pattern`, `best-practice`, and `researched` visually separated so the user sees at a
glance what came from their code vs. the library vs. the web.

Only if an `lodestar:audit-rules` skill is actually present (verify first — see below), close the report by
recommending it for ongoing review of the generated rules (clarity, cross-rule integrity, drift
over time). If it is not present, say nothing about it — do not suggest installing it. This skill
generates audit-clean rules; it does not replace a periodic dedicated audit, but never
reimplement one here.

**Check for `lodestar:audit-rules` before mentioning it:** confirm it exists in the available-skills list
for this session, or that `.claude/skills/lodestar/skills/audit-rules/` (project) or `~/.claude/skills/lodestar/skills/audit-rules/`
(user) is present. No hit → no mention.

## Internet fallback (only when the balance policy calls for it)

When reference coverage is thin for a niche library or a specific version, `WebSearch` /
`WebFetch` for current, version-specific best practice. Prefer official docs; cross-check two
sources for contested advice; record the source URL + retrieval date inside the rule; never
block generation on a failed search — degrade to the best available library content and lower
the confidence. Provenance = `researched`.

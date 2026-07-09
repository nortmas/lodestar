# Audit Checklist for `.claude/rules/` Files

This document translates the quality rubric in `references/best-practices.md` into actionable, classified checks the `lodestar:audit-rules` skill executes. Checks are divided into deterministic (regex/file-system) and LLM-judgment passes.

## 1. Severity Tier Definitions

| Tier | Weight | Definition |
|---|---|---|
| BLOCKER | 8 | Rule is broken in a way that makes it unenforceable or self-contradictory. The skill MUST surface every BLOCKER before proposing any rewrite. Examples: rule contradicts another rule's absolute statement; no `# Title` heading. |
| MAJOR | 4 | Rule has a structural defect that weakens enforceability without fully breaking it. Examples: normative pattern prescribed without paired CORRECT/WRONG examples; voice softener present in a normative sentence; `## Related rules` absent when peer rules exist; rationale missing entirely (neither in `## Why` nor in opening section). Note: a non-canonical first H2 (e.g. `## Code Quality` instead of `## Rule`) is reported as ADVISORY MAJOR per §2 — the rule may still be well-structured. |
| MINOR | 2 | Stylistic or formatting issue; enforceability is intact. Examples: code fence without language tag; single WRONG-only example; prose list with embedded pipe separators instead of a table; inline-only cross-references instead of a formal `## Related rules` section; linked file in a `Related rules` entry doesn't exist on disk. |
| NIT | 1 | Surface-level issue; auto-fixable. Examples: trailing whitespace, heading-depth skip (h2 → h4), inconsistent blank-line spacing. |

---

## 2. Per-Rule Deterministic Checks

The skill MUST run all deterministic checks on every file in scope before the LLM-judgment pass.

| Severity | Check | Detection mechanism |
|---|---|---|
| BLOCKER | Missing title — no `# ` heading at line 1 | Regex: `^# .+` MUST match line 1 |
| MAJOR (advisory) | Non-canonical first H2 — first H2 heading in lines 1–30 is not one of `## Rule`, `## Purpose`, or `## Scope`. Treat as advisory: many well-structured rules use a domain-specific opening (e.g., `## Recalculability Rule`, `## Critical Rules`). The check exists to nudge toward canonical naming, not to block. | Parse first H2 heading from lines 1–30; if not in allowed set, emit ADVISORY MAJOR with proposed fix "consider renaming opening section to `## Rule`/`## Purpose`/`## Scope` if its content is the absolute statement". The LLM judgment pass §3 covers the deeper question (is the primary statement findable in first 5 lines). |
| MAJOR | Missing `## Related rules` when peer rules exist in `.claude/rules/` | File-system: count `.md` files in `.claude/rules/`; if > 1, assert `^## Related rules` exists |
| MAJOR | Single-sided example — a fenced block labeled `// CORRECT` has no following fenced block labeled `// WRONG` within 20 lines | Regex pair-search: for each `// CORRECT` marker find `// WRONG` within next 20 lines; flag unpaired occurrences |
| MAJOR | Voice softener in normative prose | regex scan — see §4 for pattern |
| MAJOR | Internal task number leaked into prose | regex scan — see §4 for pattern |
| MAJOR | ADR reference in prose | regex scan — see §4 for pattern |
| MINOR | Dead cross-reference — a backtick path (`` `.claude/rules/x.md` ``) in the file doesn't resolve to a real file | File-system: extract all `` `path` `` tokens matching `.claude/rules/*.md`; check each exists on disk |
| MINOR | Code fence without language tag | Regex: line matching `^\`\`\`$` exactly (no language specifier after the backticks) |
| MINOR | Single-sided WRONG-only example | Regex: `// WRONG` block without a preceding `// CORRECT` within 20 lines |
| MINOR | Implementation history phrase | regex scan — see §4 for pattern |
| MINOR | Reviewer-aimed comment | regex scan — see §4 for pattern |
| MINOR | Relative path in prose | regex scan — see §4 for pattern |
| NIT | Trailing whitespace | Regex: `[ \t]+$` per line |
| NIT | Heading depth skip | Parser: flag any `####` heading not preceded by a `###` heading in the same section |

---

## 3. Per-Rule LLM Judgment Checks

After deterministic checks, the skill MUST ask the LLM each of the following questions about the rule file. Each question produces a finding or a "no issue" verdict.

- "Could this rule be ~20% shorter without losing a failure-mode anchor, decision table, or paired example? If yes, identify the specific sentences or paragraphs to cut. Do NOT propose removing items from the conservative-trimming protected list in `references/best-practices.md` §7."
- "Is the rule's primary statement — the absolute MUST or MUST NOT — findable within the first 5 lines of the file? If not, propose a concrete reordering."
- "Are any sentences redundant with their section heading or with an adjacent sentence? If yes, quote each redundant sentence and state which heading or sentence it duplicates."
- "Does any prose list use embedded `|` pipe separators (formatted as rows but not rendered as a table)? If yes, propose converting it to a markdown table, citing `best-practices.md` §5."
- "Does the rule restate content that is already canonical in another rule file in `.claude/rules/` rather than linking to it? If yes, name the peer rule and the restated passage, and propose replacing the restatement with a reference link."
- "Does the rule explain WHY the rule exists — either via a `## Why` heading OR within the first 2 sentences of the opening section OR within a clear rationale paragraph? If rationale is entirely absent, flag MAJOR. If present but buried after substantial prescription content (roughly 200+ lines), flag MAJOR with proposed reordering. If present near the primary statement (typical case for project rules), no finding."
- "Do the WRONG examples represent realistic violations that actually occur in this codebase, or are they obviously absurd strawmen? If the latter, flag as MAJOR."
- "Does the rule contain code-symbol references the LLM cannot resolve (e.g., specific class names, file paths, function names from the project codebase) presented as if the LLM has access to them? If so, propose either inlining the relevant detail or replacing with a generic description." (MINOR)
- "For any single-word softener candidates flagged at NIT severity by §4 (`consider`, `might`, `generally`), determine whether each occurrence is normative (weakens an absolute statement the rule is making → upgrade to MAJOR) or descriptive (plausibility, hedging about external facts, describing what users might do → no finding). Only the normative cases produce a real finding."

---

## 4. Anti-Pattern Regex/Heuristic Scans

> **Note:** Literal regex reference for §2's deterministic checks. The patterns below are what the §2 "regex scan" detection mechanisms use. This section exists for quick copy-paste; §2 is the canonical list of WHAT to check and at which severity.

The deterministic pass applies all patterns below to every rule file.

```text
/\btask[\s-]?\d+\b/i  (outside code blocks)                      → leaking task numbers (MAJOR)
/\bADR-?\d+\b/  (outside code blocks)                            → ADR reference in prose (MAJOR)
/\/\/\s*TODO|this could be cleaner|FIXME/  (outside code blocks) → reviewer-aimed comments (MINOR)
/\b(may want to|should probably|try to|it could be a good idea)\b/i  (outside code blocks)  → voice softeners — multi-word phrases (MAJOR; reliable)
/\b(consider|might|generally)\b/i  (outside code blocks)  → voice softeners — single words (NIT; HIGH false-positive rate, e.g. "evidence the user might ask about" is plausibility prose, not a softener — confirm via LLM judgment §3 before treating as MAJOR)
/(^|\s)~\/|(^|\s)\.\//  (outside code blocks)                    → relative file paths in prose (MINOR)
/since the migration|after the rollout|in the new format|the old way/i  (outside code blocks)  → implementation history phrases (MINOR)
```

"Outside code blocks" means the regex applies only to text NOT enclosed in fenced blocks — lines between a ` ``` ` opener and its matching closer are excluded from all pattern scans.

---

## 5. Cross-Rule Checks

Cross-rule checks apply only when the audit scope covers more than one file. The skill MUST skip these checks when auditing a single file in isolation.

| Severity | Check | When applicable |
|---|---|---|
| BLOCKER | Two rules contain mutually exclusive absolute statements — rule A says "MUST X" and rule B says "MUST NOT X" for the same construct | LLM judgment; scope > 1 file only |
| MAJOR | Two rules cover the same topic with overlapping prescriptions without cross-referencing each other | LLM judgment; scope > 1 file only |
| MAJOR | Bidirectional cross-reference gap — rule A's `## Related rules` links to rule B, but B's `## Related rules` does not link back AND the topics are reciprocally relevant | LLM judgment determines "reciprocally relevant"; deterministic check detects the one-way link |
| MINOR | Naming drift — multiple rules use different absolute language for the same concept (e.g., "MUST" in one rule, "always" in another for the same pattern) | LLM judgment; low confidence — flag only when the same exact construct is named both ways |

---

## 6. Severity-to-Action Mapping

| Severity | Report inclusion | Rewrite proposal |
|---|---|---|
| BLOCKER | MUST appear in the per-rule findings section | The apply step MUST refuse to commit a rewrite for that rule until every BLOCKER is addressed |
| MAJOR | Appears in per-rule findings | A rewrite proposal is included in the report |
| MINOR | Appears in per-rule findings | A rewrite proposal is included in the report only when the rule also has at least one MAJOR or BLOCKER finding; otherwise findings are reported without a proposal |
| NIT | Appears in per-rule findings | NEVER alone triggers a rewrite proposal; included as a trailing list after higher-severity findings |

---

## Related rules

- `.claude/rules/prompts.md` — sandwich pattern this checklist's regex checks enforce
- `.claude/rules/adapter-friendly-prompts.md` — schema and behavioral authoring rules; checklist §2 and §4 directly enforce its §3 and §4
- `.claude/rules/enum-constants.md` — naming consistency that cross-rule checks in §5 detect

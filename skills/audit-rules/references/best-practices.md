# Best Practices Rubric for `.claude/rules/` Files

This document defines the canonical quality standard the `lodestar:audit-rules` skill measures every rule file against. When auditing, report deviations as BLOCKER, MAJOR, MINOR, or NIT findings using the criteria below.

## Why this rubric exists

Rules drift. Without a shared quality bar, rules accumulate softeners, broken cross-references, single-sided examples, and task numbers that leak internal context to the LLM. Drift is compounding: a weakened rule stops catching violations, violations become patterns, and the project re-pays the cost of bugs it already solved. This rubric exists to catch drift before it ships — keeping rules precise, enforceable, and self-consistent across the lifetime of the codebase.

---

## 1. Anatomy Template

Every rule file MUST follow this heading order. Sections marked **required** are blocking if absent; **conditional** sections are required only when the condition applies; **optional** sections are encouraged but not blocking.

| Section | Required? | Condition |
|---|---|---|
| `# Title` | Required | Always — names the rule domain |
| `## Rule` / `## Purpose` / `## Scope` | Required | Always — states the absolute constraint up front |
| `## Why` | Required | Always — anchors the rule in concrete failure modes |
| `## Pattern` (CORRECT/WRONG blocks) | Conditional | Required when the rule prescribes a coding pattern; optional for purely declarative rules |
| Tables | Conditional | Required when content maps "what goes where", "X→Y", or status→behavior |
| `## Checklist` | Conditional | Required when the rule has a workflow trigger (e.g. "when adding a new agent", "before merging a prompt change") |
| `## Decision tests` | Optional | Encouraged when the rule has gray-zone judgment calls |
| `## Anti-patterns` | Optional | Encouraged — makes violations concrete for code reviewers |
| `## Related rules` | Required | Required when at least one peer rule exists in the same folder (always true in a mature `.claude/rules/` folder) |

**Ordering rule:** `## Why` MUST appear before or immediately after the opening rule statement. A `## Why` section appearing after 200+ lines of prescription is a MAJOR finding — rationale must be reachable without scrolling through all the enforcement detail first.

**Frontmatter:** Rules scoped to specific file globs MAY include a YAML frontmatter block (e.g. `globs: apps/agentic_ai/src/**/prompts.py`). This is optional and structural — not part of the prose anatomy.

---

## 2. Voice Spec

Rules MUST be written in imperative, second-person voice using `MUST`, `MUST NOT`, and `NEVER` for absolute constraints.

- State the absolute first. Exceptions follow the absolute — never precede it.
- Use `MUST NOT` and `NEVER` interchangeably for hard prohibitions; prefer `NEVER` for zero-tolerance patterns.
- `SHOULD` is acceptable for strong recommendations that have documented exceptions.

**Forbidden softeners** — flag any of these as a MINOR finding:

| Softener | Why it fails |
|---|---|
| `consider` | Non-binding; does not enforce |
| `might` | Suggests optionality where none exists |
| `generally` | Invites undocumented exceptions |
| `may want to` | Non-binding suggestion |
| `it could be a good idea` | Vague advice without enforcement |
| `should probably` | Hedged obligation |
| `try to` | Non-binding when used as a nudge |
| `prefer to` | Only acceptable as `prefer X over Y` when X is the absolute pattern — not as a general nudge |

Exception: `prefer X over Y` used as a named pattern ranking (not a general nudge) is acceptable.

---

## 3. Examples Spec

When a rule prescribes a pattern (code, configuration, command, or data shape), it MUST supply paired CORRECT and WRONG examples.

**Format requirements (paired illustration):**

```php
// CORRECT — recalculate from source before save
$context->recalculateTotalCost();
$context->save();

// WRONG — incremental accumulation
$context->total_cost_usd += $newCost;
$context->save();
```

The above block is itself a compliant example: language-tagged fence, both sides labeled. A non-compliant illustration looks like this:

````markdown
```
$context->recalculateTotalCost();
$context->save();
```
````

No language tag on the fence, no `// CORRECT` label, no WRONG counterpart — three MINOR findings in one block.

- Use `// CORRECT` and `// WRONG` comment labels on the line immediately above the block.
- Code fences MUST declare the language (` ```php `, ` ```python `, ` ```typescript `) — bare ` ``` ` is a MINOR finding.
- A CORRECT block without a WRONG counterpart is a MAJOR finding. A single-sided example forces the reader to imagine the violation; the WRONG block must show a realistic failure, not a strawman.
- A WRONG block without a CORRECT counterpart is a MINOR finding (better than nothing, but incomplete).
- The WRONG example MUST represent a realistic violation that actually occurs in the codebase — not an obviously absurd misuse.

---

## 4. Cross-Reference Spec

`## Related rules` entries MUST use this exact format:

```text
`.claude/rules/x.md` — one-line description of what that rule covers
```

- The backtick-path form MUST resolve to a real file in `.claude/rules/`. Broken links are a MINOR finding.
- Forward references in prose (mentioning another rule mid-section) MUST also use the backtick-path form: `` per `.claude/rules/cost-tracking.md` ``.
- Rules that prescribe complementary patterns MUST bidirectionally link. When two rules each prescribe part of the same pattern (e.g., one defines when to use an abstraction and the other defines how to implement it), and one already references the other, the reverse link MUST also exist in a formal `## Related rules` section.
- A `Related rules` section listing rules that don't exist is a MINOR finding. A rule with obvious peers but no `Related rules` section is a MAJOR finding.

---

## 5. Tables-vs-Prose Spec

Use a markdown table when content maps:

- "what goes where" (data element → sub-tree, field → owner)
- "X → Y" (input type → output location, status → branch behavior)
- Role → permission, agent type → surface, severity → check
- Inventory lists with two or more properties per item

A bullet list with embedded ` | ` pipe separators rendered as prose is a MINOR finding — convert to a table.

Use prose when:

- The content is a narrative explanation or rationale (→ `## Why`)
- The list items are uniform and order matters (→ ordered list)
- There are fewer than three items and no repeated structure

---

## 6. Anti-Patterns to Detect

The following anti-patterns are MAJOR findings unless noted:

| Anti-pattern | Severity | Example |
|---|---|---|
| Internal task numbers in prose | MAJOR | `(task 086)`, `per task 053`, `# task 070 context` |
| ADR references in prose | MAJOR | `per ADR-0019`, `(ADR 0002)` |
| Code symbol references the LLM can't resolve | MAJOR | file paths, class names, module paths used as if the reader has codebase access (e.g. `see CITATION_CONTRACT_CLAUSE`, `per BaseAgent.run()`) |
| Implementation history | MINOR | `since the migration`, `after the rollout`, `in the new format` |
| Reviewer-aimed comments | MINOR | `// TODO: simplify`, `"this could be cleaner"`, `FIXME later` |
| Vague advice without enforcement | MAJOR | `"try to keep things clean"`, `"be careful"` with no actionable rule |
| Single-sided example (CORRECT only or WRONG only) | MAJOR | Missing counterpart — see §3 |
| `## Why` buried after 200+ lines of prescription | MAJOR | Rationale appears at line 250; rule statement is at line 10 |
| Content restated from another rule rather than linked | MINOR | Copy-pasting text that already exists in a peer rule |
| Concatenated `{NAME}_SYSTEM_PROMPT` alias style | MAJOR | A single constant that joins header + behavioral + footer at module load |
| Long bullet list with pipe-separated values | MINOR | Should be a table — see §5 |
| Broken `Related rules` link | MINOR | Path does not resolve to a real file |

**On the `{NAME}_SYSTEM_PROMPT` alias:** This pattern bakes the default behavioral into a single constant at module load time. Because the runtime adapter substitutes the behavioral at call time, a pre-concatenated alias bypasses the override entirely — the adapter's rewrite never reaches the LLM. The three sandwich constants (`IMMUTABLE_HEADER`, `BEHAVIORAL_DEFAULT`, `IMMUTABLE_FOOTER`) plus `SCHEMA` are the only valid public surface of a prompt module. See `.claude/rules/adapter-friendly-prompts.md` for the full rationale.

---

## 7. Conservative Trimming Guidance

When the `lodestar:audit-rules` skill proposes edits to an existing rule, it MUST NOT propose removing the following categories of content even if they appear long or redundant:

| Protected content | Why |
|---|---|
| Failure-mode anchors with concrete measurements | e.g. "the fact_sheet duplication cost ~130 KB per research (~40%)" — these prevent re-litigation of settled decisions |
| Canonical example pointers | e.g. "`NcfImages.tsx` is the reference implementation" — removing breaks the cross-reference chain |
| Decision tables | Structured "goes in / stays out" tables are the most compact form of the rule |
| Paired CORRECT/WRONG blocks | Both sides are load-bearing — removing either half degrades the rule |
| `## Why` sections, even when long | Rationale is what enables contributors to apply the rule in novel situations |
| "Known minor violations" / "Deferred reductions" sections | Explicitly prevent re-opening settled trade-offs in future sessions |
| "When in doubt, ask" meta rules | Cheap insurance against autonomous decisions in high-blast-radius situations |

**Allowed-to-trim list** — the skill MAY propose removing or shortening:

- Leaking task numbers, ADR refs, or code symbol references in prose (§6)
- Broken cross-reference links
- Near-duplicate adjacent paragraphs that say the same thing twice in different words
- Wordy phrasings of identical content (condense, don't delete)
- Sections the rest of the rule never touches or references

---

## Known Deviations in Existing Rules

The rubric was validated against two real rule files before being published.

**`.claude/rules/cost-tracking.md`**

- No explicit `## Why` heading. The rationale ("performance cache, not source of truth") appears inline in the opening `## Recalculability Rule` section, immediately at the top. This satisfies the spirit of the requirement (rationale is near the top). Verdict: no defect — the rubric's "required" for `## Why` is satisfied when rationale is the opening sentence of the first section, not only when it gets its own heading.
- Has no `## Anti-patterns` section. This is optional — not a finding.
- No `## Related rules` section. The rule references peers inline (`.claude/rules/llm-evidence.md`) but lacks a formal section. In a mature folder this is a MINOR finding. Documented here as a known deviation in the exemplar.
- CORRECT/WRONG pair is present. ✓

**`.claude/rules/prompts.md`**

- Has frontmatter `globs:` — acceptable per §1 note on frontmatter. ✓
- `## Decision Test` and `## Audit before merging` serve the checklist + decision-tests roles implicitly. ✓
- Has a "What goes WHERE" table. ✓
- "Forbidden content inside prompt strings" section covers the anti-patterns domain. ✓
- No formal `## Related rules` section — peers referenced inline only. Same MINOR finding as `cost-tracking.md`. Documented.

**Conclusion:** Both exemplars satisfy the anatomy requirements structurally, with the one recurring deviation being the absence of a formal `## Related rules` section (peers linked inline instead). The rubric's requirement is correct — inline-only cross-references are a MINOR finding, not a blocking defect.

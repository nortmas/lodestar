<!--
Exemplar rule for the lodestar:audit-rules skill.

Source: .claude/rules/cost-tracking.md (copied 2026-05-07)

Rationale: Selected as the canonical exemplar over .claude/rules/prompts.md because it
has fewer rubric findings. prompts.md carries a MAJOR finding (pattern-prescribing rule
with no paired CORRECT/WRONG code examples); cost-tracking.md has only a MINOR finding
(no formal ## Related rules section — peers linked inline instead, a known convention
documented in best-practices.md §"Known Deviations in Existing Rules").
Specifically demonstrates:
- Paired CORRECT/WRONG code blocks with language-tagged fences and labeled comments ("// CORRECT — recalculate from source before save" / "// WRONG — incremental accumulation")
- Rationale appears as the opening sentence of the first section, satisfying the ## Why requirement without a separate heading ("performance cache, not a source of truth")
- Actionable enforcement language throughout: every section states exactly what MUST exist, what is forbidden, and what an acceptable alternative looks like

Known deviations from the rubric (acknowledged): no formal ## Related rules section
(this rule links to peers inline). Per references/best-practices.md §"Known Deviations
in Existing Rules", this is the convention in older rules and is not disqualifying.

This file is a FROZEN COPY. Drift in the source rule does NOT auto-propagate.
Re-copy intentionally when the rubric is updated and a fresher exemplar is needed.
-->

# Cost Tracking Conventions

## Recalculability Rule

`total_cost_usd` on any model (`ConversationContext`, `ConversationResearch`, etc.) is a **performance cache**, not a source of truth. It MUST always be recalculatable from the underlying stored meta records.

Every LLM call that contributes to `total_cost_usd` MUST store its full `LlmMetaData` (model, provider, input/output tokens, cost) in a retrievable record — either as a dialog entry, a dedicated meta field, or another auditable structure.

**Never** add cost to `total_cost_usd` without also persisting the source meta. If the meta records were summed from scratch, the result must equal `total_cost_usd`.

## Enforcement

- Every model with `total_cost_usd` MUST have a `recalculateTotalCost(): float` method that sums from source meta records.
- Before saving, call `recalculateTotalCost()` and **assign** the result — never use `+=` to increment `total_cost_usd` directly.
- If a model's cost comes from a linked record (e.g., `ReportSectionVersion` costs tracked on `ConversationMessageMeta` via `conversation_message_id`), document this invariant in the model's `casts()` method with a comment.

```php
// CORRECT — recalculate from source before save
$context->recalculateTotalCost();
$context->save();

// WRONG — incremental accumulation
$context->total_cost_usd += $newCost;
$context->save();
```

## Single Canonical Aggregate — the cache is the contract

The cached `total_cost_usd` on the parent model (`ConversationResearch`, `ConversationContext`, etc.) is the **single canonical aggregate** every downstream consumer reads — admin tables, dashboard widgets, conversation overview, drill-down totals. All of them MUST agree.

A drill-down presenter (e.g., `ResearchCostPresenter`) MUST NOT fold in a cost source that `recalculateTotalCost()` doesn't also read. Doing so makes the drill-down visually correct while silently leaving every other surface (dashboard, conversation table, admin column) understated. That is a rule violation, not a clever fix.

Valid responses when a new LLM/image/API call's cost doesn't currently reach `meta->costs->steps` (or the equivalent source `recalculateTotalCost()` reads):

1. **Inject at the source** (preferred). Persist the cost into the canonical source the parent's `recalculateTotalCost()` already reads (for `ConversationResearch` that is `meta->costs->steps`). Then call `recalculateTotalCost()` + save. Every consumer updates automatically.
2. **Extend `recalculateTotalCost()`** to read the new source AND call it + save at every persistence point where the new source changes. Document the dependency in the model's `casts()` method.

Never both: one source, one aggregate, one cache. "Fold-in-at-render-time" is forbidden.

## Multi-Source Aggregates

When a parent's `recalculateTotalCost()` must aggregate from more than one table (e.g., `ConversationResearch.meta->costs->steps` plus `ReportSectionVersion.meta.calls`), treat each source equally:

- List every source in a docblock on `recalculateTotalCost()`.
- Every persistence path that writes to any of those sources MUST call `recalculateTotalCost()` + save on the parent before returning.
- A test MUST exercise the union — build up cost across all sources in a single scenario and assert the cached aggregate equals the independently computed sum.

## Evidence vs cost — separate trees

`meta.llm_evidence` (per `.claude/rules/llm-evidence.md`) lives as a **sibling**
of `meta.costs.steps`, never inside it. `recalculateTotalCost()` must continue
to read only `meta.costs.steps`. Adding, modifying, or removing evidence MUST
NOT change `total_cost_usd`. Folding evidence into the cost sub-tree is a
contract violation of both rules — one cost source, one audit source, zero
overlap.

## Testing
At least one test per model with `total_cost_usd` MUST verify that `recalculateTotalCost()` returns the same value as `total_cost_usd` after a **complete flow**, meaning:

- Every source that contributes to the aggregate is populated in the scenario (including section-version image costs, message USD_PRICE rows, dialog meta — whatever applies to the model).
- The test asserts the cache equals the independently computed sum.
- A single-source test is NOT sufficient when the aggregate has multiple sources. Drift between sources is the exact failure this rule protects against.

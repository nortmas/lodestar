<!--
  report-template.md — Markdown skeleton for rules-audit output.

  Purpose: the lodestar:audit-rules skill loads this file, substitutes every
  {{PLACEHOLDER}} with real findings data, and renders the result inline
  in the chat as the assistant's response. The skill MUST NOT write the
  rendered report to a file by default — persistence is a manual step
  the user requests explicitly.

  Placeholder convention: {{UPPER_SNAKE_CASE}} — names are self-explanatory.
  The skill replaces each placeholder exactly once; unused placeholders
  (e.g. {{FULL_PROPOSED_REWRITE}} for a rule with no rewrite) are replaced
  with an empty string, or the enclosing section is omitted entirely.

  Section 3 (Cross-rule findings) is emitted only when audit scope > 1 file.
  Section 4 (Per-rule findings) repeats once per rule that has ≥ 1 finding.
  Section 5 (Passed clean) lists every rule with zero findings.
-->

# Rules Audit — {{TIMESTAMP_ISO}}

## Summary

- {{N_AUDITED}} rules audited · {{N_WITH_FINDINGS}} with findings · {{N_PASSED_CLEAN}} passed clean
- Severity totals: {{N_BLOCKER}} blockers · {{N_MAJOR}} major · {{N_MINOR}} minor · {{N_NIT}} nits
- Cross-rule findings: {{N_CROSS_RULE}}
- Proposed rewrites: {{N_REWRITES}}

---

## Overview

<!-- One row per audited rule, sorted by severity weight (blockers > major > minor > nit).
     Rewrite: ✓ when a full proposed rewrite is included in §4; blank otherwise.
     Top issue: 2–6 word summary of the most severe finding. -->

| # | Rule | Blocker | Major | Minor | Nit | Rewrite | Top issue |
|---|------|--------:|------:|------:|----:|:-------:|-----------|
{{OVERVIEW_TABLE_ROWS}}

---

## Cross-Rule Findings

<!-- Present only when audit scope > 1 file. Omit this section entirely for
     single-file audits.
     ID format: XR-1, XR-2, ...
     Rules involved: use ↔ for symmetric findings (overlap, contradiction);
                          → for directional findings (one-way link gap). -->

| ID | Severity | Rules involved | Issue | Proposed action |
|----|----------|----------------|-------|-----------------|
{{CROSS_RULE_TABLE_ROWS}}

---

## Per-Rule Findings

<!-- This section repeats the block below once for every rule that has at least
     one finding. Rules with zero findings appear only in §5 (Passed clean). -->

<!-- BEGIN PER-RULE BLOCK — repeat for each rule with findings -->

### `{{RULE_FILENAME}}`

**Counts:** {{N_RULE_BLOCKER}} blocker · {{N_RULE_MAJOR}} major · {{N_RULE_MINOR}} minor · {{N_RULE_NIT}} nit · {{REWRITE_FLAG}}

| # | Severity | Location | Finding | Proposed fix |
|---|----------|----------|---------|--------------|
{{RULE_FINDINGS_TABLE_ROWS}}

**Diff summary:** {{DIFF_SUMMARY}}

**Proposed rewrite:**

````markdown
{{FULL_PROPOSED_REWRITE}}
````

<!-- END PER-RULE BLOCK -->

---

## Passed Clean

<!-- Rules with zero findings across all deterministic, LLM-judgment,
     and cross-rule checks.
     Last modified: from `git log -1 --format=%ci -- <file>` (ISO date). -->

| Rule | Last modified |
|------|---------------|
{{PASSED_CLEAN_TABLE_ROWS}}

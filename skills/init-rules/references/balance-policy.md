# Balance policy — legacy vs. best practice

This is the decision algorithm the skill runs for **every** concern. It answers one question:
*does this rule come from the codebase, from the best-practice library, or from the web?*

Core stance: **a consistent existing pattern outranks generic best practice** — except where
the pattern is a security, correctness, or performance defect. Working consistency beats theory;
safety beats consistency.

## Algorithm (per concern `C`)

### 1. Gather evidence
Use `Glob`/`Grep` to find the files relevant to `C` and sample a *meaningful* set — never a
single file. Read enough to state, in one sentence, how the codebase currently handles `C`.

### 2. Classify the existing pattern

| Class | Meaning | Threshold (tunable) |
|-------|---------|---------------------|
| `CONSISTENT` | One dominant approach across samples | **≥ 5** relevant occurrences **AND ≥ 70%** follow the same approach |
| `MIXED` (разнобой) | Multiple competing approaches, none dominant | occurrences present, dominance < 70% |
| `ABSENT` | Concern doesn't appear, or too few samples to judge | < 5 occurrences |

Both conditions are required for `CONSISTENT`: enough evidence (sample size) **and** agreement
(dominance). State the observed count and dominance in the rule's confidence note. These
thresholds are defaults — the project may tune them.

### 3. Choose the rule source

```
CONSISTENT and NOT critical
    → codify the EXISTING PATTERN as the rule (even if it diverges from best practice).
      If it diverges, add one line:
        "Project convention (diverges from common best practice: <what best practice would be>)."
      Provenance = existing-pattern

CONSISTENT but CRITICAL  (security / correctness / performance defect — see carve-out)
    → do NOT codify it. Use best practice, and emit a ⚠ migration note describing the legacy
      anti-pattern and the safe replacement.
      Provenance = best-practice

MIXED or ABSENT
    → use BEST PRACTICE from the relevant references/ file.
      Provenance = best-practice

Reference coverage thin/absent for a niche lib or specific version (any class above)
    → WebSearch for current, version-specific best practice; prefer official docs; cite the
      source URL inside the rule; then codify.
      Provenance = researched
```

### 4. Enrich
When codifying an existing pattern, draw the `✅ Good` example from the **real codebase** (a
representative snippet, cleaned up) and construct a plausible `❌ Bad` counter-example. This makes
the rule recognizably "ours" and keeps it honest.

### 5. Precedence — two independent axes
- **Layer specificity** (from lifedever): `framework > language > base`. A Laravel rule beats a
  generic PHP rule beats a base rule on the same point.
- **Source authority** (our inversion): within a concern, a `CONSISTENT` existing pattern
  outranks best practice — *except* the security/correctness/performance carve-out below.

### 6. Traceability
Every generated rule records provenance + confidence so the final report honestly separates what
came from the code, the library, and the web.

## The critical carve-out — be precise

The existing pattern wins **only** for non-critical concerns: imperfect-but-working
architecture, layering choices, stylistic conventions, naming, formatting.

It **never** wins for defects in these three categories:

| Category | Examples that FORCE best practice + migration note |
|----------|----------------------------------------------------|
| **Security** | Raw string concatenation into SQL; disabled CSRF; secrets committed in code; missing output escaping (XSS); broken/absent authz; unsafe deserialization; `md5`/`sha1` for passwords |
| **Correctness** | Logic that is simply wrong; swallowed exceptions hiding failures; race conditions; non-deterministic tests relied on as truth; float money math |
| **Performance** | Guaranteed N+1 queries; unbounded memory growth; missing pagination on large sets; blocking I/O on hot paths; missing indexes on hot queries |

Litmus test:
- *"I don't love this design"* → **not** critical. Defer to the codebase.
- *"This leaks secrets / is wrong / falls over under load"* → **critical**. Defer to best practice
  and emit a `⚠ migration note`.

A concern can be split: defer to the codebase on its style while overriding one critical sub-point
in the same file (e.g. keep their controller layout, but flag the one N+1 loop).

## Worked mini-examples

### A. Services return arrays, not DTOs → codify with divergence note (non-critical)
Evidence: 14 of 16 service methods return associative arrays; no DTO/Resource layer in domain
code. Class = `CONSISTENT`, not critical (a design taste, not a defect).
→ **Codify arrays** as the project convention.
```
Rule: Service methods return associative arrays shaped `['data' => ..., 'meta' => ...]`.
Project convention (diverges from common best practice: dedicated DTOs / readonly value objects).
Source: existing-pattern · Confidence: high (14/16 methods)
```

### B. SQL built by string concatenation → refuse to codify (security)
Evidence: 9 of 11 repositories interpolate variables directly into query strings. Class =
`CONSISTENT`, but **critical (SQL injection)**.
→ **Do NOT codify.** Mandate the query builder / bound parameters; emit migration note.
```
Rule: Build every query via the query builder or parameter bindings. Never interpolate input
into SQL strings.
⚠ migration note: 9/11 repositories currently concatenate input into SQL (SQL-injection risk).
Migrate to bindings — do not follow the existing pattern here.
Source: best-practice · Confidence: high
```

### C. Controllers lazy-load relations inside loops → refuse to codify (performance)
Evidence: 6 controllers iterate a collection and access a relation per element → guaranteed N+1.
Class = `CONSISTENT`, but **critical (performance)**.
→ **Do NOT codify.** Mandate eager loading (`with()` / `load()`); emit migration note.
```
Rule: Eager-load relations accessed inside loops (`Model::with('rel')`); never trigger lazy
loads per iteration.
⚠ migration note: 6 controllers currently lazy-load in loops (N+1). Convert to eager loading.
Source: best-practice · Confidence: high
```

### D. Niche package, no library coverage → research (any class)
Evidence: project uses `some/rare-sdk ^3.2`; no reference file covers it. Class doesn't matter.
→ **WebSearch** official docs for v3.2 conventions; cite URL + date; codify.
```
Source: researched · https://docs.example.com/v3 (retrieved 2026-07-08) · Confidence: medium
```

# Rule authoring standard

The required shape of **every file the skill writes** to the target project's `.claude/rules/`.
Read this at workflow step 4. Follow it exactly — consistency here is what makes the generated
rules auto-loadable and trustworthy.

## Required shape

1. **YAML frontmatter** with `name`, `description`, and `globs` (path-scoping so the rule only
   loads for relevant files):
   ```yaml
   ---
   name: laravel-error-handling
   description: How this project handles errors, exceptions, and failures in Laravel code.
   globs: ["app/**/*.php", "routes/**/*.php"]
   ---
   ```
   - `name`: kebab-case, `<layer>-<concern>` (e.g. `php-naming`, `vue-components`).
   - `description`: one line, what the rule governs — phrased so Claude knows when it applies.
   - `globs`: array of path patterns. Scope tightly (front-end rules → `resources/js/**`,
     API rules → `app/Http/**` + `routes/**`). A rule with no natural scope may use `["**/*"]`
     but prefer specificity.

2. **Concrete, actionable directives.** Never vague wording like "handle errors properly" or
   "use appropriate X". State exactly what to do, in the imperative.

3. **Quantify where sensible**, as tunable defaults (not dogma): functions ≤ ~30 lines,
   files ≤ ~300 lines, nesting ≤ 3, parameters ≤ 4, cyclomatic complexity ≤ ~10. Mark them as
   defaults the project can adjust.

4. **`❌ Bad` / `✅ Good` code comparisons** for the key rules. When codifying an existing
   pattern, the `✅ Good` snippet is drawn from the real codebase (cleaned up). All code
   comments in the examples are in **English**.

5. **Provenance footer** on every file:
   `Source: existing-pattern | best-practice | researched · Confidence: high|medium|low`
   plus any `⚠ migration note` (when a legacy anti-pattern was intentionally not codified —
   name the anti-pattern and the safe replacement). For `researched`, add the source URL +
   retrieval date.

6. **Token-frugal.** Assume the model already knows the language/framework basics. Encode only
   project-specific or non-obvious decisions. Do **not** restate standard PHP/Laravel/JS
   knowledge (the criticism leveled at Boost's generated files). If a rule would be true of
   *any* project in this language, cut it.

## Anti-patterns to avoid in generated files
- Restating language tutorials ("PHP is dynamically typed…").
- Vague imperatives with no test ("write clean code").
- Rules with no `globs`, so they load everywhere and dilute context.
- Copying a `❌ Bad` example that never appears in this codebase (make it plausible for *this* repo).
- Omitting the provenance footer — every file must be traceable.

## Quality gate — write rules that are born audit-clean

Rules drift and rot. A generated rule that is vague, hedged, or self-inconsistent stops catching
violations, and violations become patterns. Apply this gate to every file **before** writing it,
so the output already passes a later `/lodestar:audit-rules` review (see "Ongoing auditing" below).

**Voice — state absolutes, never hedge.** Use imperative `MUST`/`NEVER`/`do X`. Ban softeners
that dissolve enforceability: `consider`, `might`, `generally`, `try to`, `may want to`,
`should probably`, `it could be a good idea`. `prefer X over Y` is allowed only as a named
pattern ranking, not as a nudge. `SHOULD` is acceptable only for a recommendation with a
documented exception.

**Examples — realistic and paired.** Every prescribed pattern needs both a `❌ Bad` and a
`✅ Good` block (a single-sided example is a defect). Both must be *realistic for this repo* — the
`❌ Bad` shows a violation that actually occurs here, not an absurd strawman; the `✅ Good` is
drawn from real code when codifying an existing pattern. Every code fence declares its language
(```` ```php ````, ```` ```python ````) — never a bare ```` ``` ````.

**No unresolvable or leaky references.** The rule is read by a model with no access to this
project's issue tracker or private history. Forbidden in prose:
- Internal task/ticket numbers (`task 086`), ADR references (`per ADR-0019`).
- Bare code-symbol references presented as if the reader can resolve them (`see BaseAgent.run()`,
  a raw class/file path with no context) — inline the relevant detail or describe it generically.
- Implementation-history phrasing (`since the migration`, `the old way`) and reviewer TODOs.
- Relative/`~` paths in prose — the file-reference convention is absolute or repo-rooted.

**Rationale near the top.** State *why* the rule exists in one line within the first couple of
sentences (or a short `## Why`). A rule nobody understands is a rule nobody applies. Keep it to a
line — this is not the place for an essay.

**Optional but encouraged for mature rule sets:** a one-line cross-reference to a sibling rule
when two rules prescribe two halves of one pattern (e.g. `See also .claude/rules/security.md`).
If you add one, make sure the path resolves to a file you actually generated.

**Self-check before writing each file** (cheap, deterministic — run it in your head or via grep):
no softeners · every fence language-tagged · every ❌ has a ✅ · no task/ADR/relative-path leaks ·
`globs` present and tightly scoped · provenance footer present. Fix in place; do not ship a rule
that fails its own gate.

## Ongoing auditing (don't reinvent it)

This gate makes rules *born* clean; it does not replace periodic auditing as rules evolve.
**Only if an `lodestar:audit-rules` skill is actually present** — verify it first (in the session's
available-skills list, or a `.claude/skills/lodestar/skills/audit-rules/` / `~/.claude/skills/lodestar/skills/audit-rules/`
directory) — recommend it in the final report for ongoing review (clarity, cross-rule integrity,
drift); it runs deterministic + judgment passes and a safe apply gate. If it is not present, do
not mention it and do not suggest installing it. Never duplicate that machinery inside this skill;
generate well, then defer to the dedicated auditor when one exists.

## Fully-written example (the quality bar to imitate)

````markdown
---
name: laravel-error-handling
description: Error, exception, and failure handling conventions for this Laravel project.
globs: ["app/**/*.php", "routes/**/*.php"]
---

# Error Handling (Laravel)

- Throw typed domain exceptions; never `throw new \Exception('...')` in domain code.
- Never swallow exceptions with an empty `catch`. Catch only what you can handle.
- Return a consistent JSON error envelope from the API layer; map exceptions in one place.

❌ Bad
```php
// Swallows the failure and hides the cause from callers and logs.
try {
    $this->charge($order);
} catch (\Throwable $e) {
    // ignored
}
```

✅ Good
```php
// Fail fast with a typed, catchable domain exception; let the handler map it.
try {
    $this->charge($order);
} catch (PaymentGatewayException $e) {
    throw new OrderPaymentFailed($order, previous: $e);
}
```

Source: best-practice · Confidence: high
````

## Update / merge mode

On re-run against an existing rule file: never clobber. Show a diff, ask, and **merge** — keep
the user's hand-edits and any rules they added; only introduce/adjust the specific directives
this run changed. If a rule already exists and still holds, leave it. Preserve user comments.

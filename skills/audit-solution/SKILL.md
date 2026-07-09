---
name: audit-solution
description: Audit plans, solutions, and code for robustness and quality. Catches workarounds, quickfixes, fragile approaches, and suboptimal decisions that should use better patterns. Use when reviewing a plan before implementation, reviewing code after implementation, or when uncertain whether a chosen approach is the right one. Triggers on '/lodestar:audit-solution' or when the user asks to check if a solution is robust, reliable, or correct.
---

# Audit Solution

Evaluate whether a plan, solution, or implementation is **robust, reliable, and architecturally sound** — or whether it is a workaround, quickfix, or suboptimal choice that leaves root causes unresolved.

This skill does NOT check convention compliance (that is `/lodestar:check-rules`). This skill checks whether the **right approach was chosen**.

## Scope Detection

Determine what to audit based on context:

1. **Arguments provided** — If invoked as `/lodestar:audit-solution <file-or-path>`, audit that specific file or path.
2. **Plan audit** — If the conversation contains a written plan or the user points to a planning document, audit the plan before code is written.
3. **Code audit** — If code changes exist in the session (check `git diff` for staged/unstaged changes), audit the implementation.
4. **Both** — If both a plan and code changes exist, audit both and cross-reference (does the code actually implement the plan's approach?).
5. **No context** — If none of the above, ask the user what to audit.

## Audit Process

### Phase 1: Gather Context

1. Understand the problem being solved — read the plan, task description, or relevant documentation the user points to.
2. For plan audits: read the full plan text.
3. For code audits: run `git diff` (staged + unstaged) to see all changes. For larger changes, also read the full files to understand surrounding context.
4. If the project has coding rules or conventions (e.g., CLAUDE.md, `.claude/rules/`, ADRs, style guides), read the ones relevant to the domain being audited.
5. Identify which language(s), framework(s), and layer(s) are involved.

### Phase 2: Apply the Audit Lens

For each decision or approach in the plan/code, ask these questions **in order**. Stop at the first "yes" — that is the finding.

#### Q1: Is this fixing a symptom instead of the cause?

- Does the fix patch over observable behavior without addressing why it happens?
- Would the same class of problem recur with slightly different inputs?
- Is it adding tolerance/permissiveness to compensate for upstream incorrectness?

**Real example**: Relaxing a regex to handle more LLM output formatting quirks instead of switching to structured tool calling. The regex will always be fragile because the root problem is parsing structured data from unstructured text.

**Signal phrases that indicate symptom-fixing:**
- "Make the regex more permissive"
- "Add a fallback for when X doesn't work"
- "Strip/trim/clean the output before parsing"
- "Add another special case for..."
- "Retry with different parameters if it fails"
- "Catch the exception and try the other way"

#### Q2: Is there a well-established solution being ignored?

- Does the language, framework, or ecosystem provide a built-in mechanism for this exact problem?
- Is the code reimplementing something that already exists in the project's dependencies?
- Is there an industry-standard pattern for this class of problem?

**Examples:**
- Custom string-matching for LLM output → use native tool calling / function calling
- Manual retry loops with sleep → use framework retry helpers (`retry()` in Laravel, `tenacity` in Python)
- Hand-rolled auth token validation → use framework middleware
- Custom event bus → use framework events/listeners
- Manual JSON key mapping → use serialization DTOs (Spatie Data, Pydantic)

#### Q3: Is the approach fragile — will it break under predictable conditions?

- Does it depend on specific formatting, ordering, or timing that isn't guaranteed?
- Does it use string matching, regex, or position-based parsing where structured data is available?
- Would concurrent requests, retries, or edge-case inputs break it?
- Does it assume a specific LLM output format without enforcing it?

**Fragility indicators:**
- Regex parsing of LLM/AI output
- Position-based array access (`$result[0]`) instead of keyed access
- Timing-dependent logic without synchronization
- String comparison for values that should be enums
- Implicit ordering dependencies between independent operations

#### Q4: Is this a quickfix that accumulates tech debt?

- Does it add complexity (new flags, special cases, conditional branches) to avoid a proper refactor?
- Does it duplicate logic that already exists elsewhere rather than extracting a shared abstraction?
- Does it work around a limitation by adding another layer instead of fixing the layer that has the limitation?
- Would a new team member look at this and ask "why is it done this way?"

#### Q5: Are there unhandled edge cases that matter?

- What happens on page reload / browser refresh?
- What happens on concurrent requests?
- What happens when the external service (LLM, API) returns unexpected data?
- What happens when the user does the same action twice quickly?
- What if the operation partially completes then fails?

#### Q6: Is the solution over-engineered for the actual problem?

Not all solutions need to be the "most robust." Sometimes a simpler approach is genuinely appropriate. Flag this too — audit in both directions.

- Is this adding abstraction layers for a one-time operation?
- Is this building for hypothetical future requirements?
- Is this adding configuration/flexibility that no one asked for?

### Phase 3: Report Findings

For each finding, report:

```
### [Finding title]

**Verdict**: WORKAROUND | FRAGILE | SUBOPTIMAL | OVER-ENGINEERED | ROBUST

**What**: [One sentence describing what was done]
**Why it's [verdict]**: [Concrete explanation of the problem]
**What breaks**: [Specific scenario where this fails or causes pain]
**Better approach**: [Concrete alternative — not vague advice, but a specific technical approach]
**Effort delta**: [Is the better approach significantly more work, or roughly the same?]
```

### Phase 4: Overall Verdict

Summarize with one of:

- **ROBUST** — The approach is sound. No significant concerns. Proceed with confidence.
- **HAS CONCERNS** — Mostly good, but N specific issues should be addressed. List them ranked by severity.
- **NEEDS RETHINK** — The fundamental approach is wrong. A different strategy is needed before proceeding. Explain what and why.

## Anti-Patterns Catalog

These are patterns that almost always indicate a suboptimal solution. Flag them on sight:

| Anti-Pattern | Why It's Bad | Better Approach |
|---|---|---|
| Regex parsing of LLM output | LLMs don't guarantee text format | Structured output / tool calling |
| "Make it more permissive" | Trades false negatives for false positives forever | Fix the source of bad data |
| Silent fallback to expensive operation | Hides bugs, causes financial waste | Fail explicitly, let the user decide |
| Injecting data into a wrong layer to "make it available" | Couples layers, breaks separation | Pass through the proper channel |
| Multiple `if/else` branches for something that should be a lookup | Grows linearly with cases, easy to miss one | Map/dict/enum dispatch |
| Catching broad exceptions to "handle" them | Hides real errors, makes debugging impossible | Catch specific exceptions |
| Copy-pasting with slight modifications | Maintenance burden grows with each copy | Extract shared logic |
| Adding a flag to skip/modify behavior in one place | Flag pollution, hard to trace control flow | Separate code paths or strategy pattern |
| String concatenation for building structured data | Injection risk, encoding bugs | Use builders, templates, or serializers |
| Re-reading data you just wrote to verify it saved | Indicates distrust of the abstraction | Trust the ORM/framework, test properly |

## Important Rules

- **Never just say "looks good."** Even if the solution is robust, explain WHY it's robust — what makes it the right approach. The user invoked this skill because they want analysis, not rubber-stamping.
- **Be concrete, not philosophical.** "This could be more robust" is useless. "This regex will break when the LLM adds a markdown code fence because X" is useful.
- **Propose, don't prescribe.** Present the better approach and explain the trade-offs. The user decides whether to adopt it.
- **Respect existing architecture.** The "better approach" must fit the project's existing patterns and conventions. Check for project rules or conventions before suggesting alternatives.
- **Distinguish "suboptimal but fine" from "this will break."** Not everything needs to be perfect. Clearly separate critical issues from nice-to-haves.

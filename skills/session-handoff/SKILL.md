---
name: session-handoff
description: Structured end-of-session handoff in chat, so a fresh agent can continue after /clear.
disable-model-invocation: true
---

# Session Handoff

Produce a repeatable end-of-session summary so the user can `/clear` and start a fresh agent without losing continuity. The next agent should be able to pick up by reading this summary alone.

This is a **context-handoff artifact**, not a status report. The audience is a future instance of you, not a stakeholder.

## When to invoke

Explicit user invocation only — `/session-handoff`. `disable-model-invocation: true` is set deliberately: never trigger this on your own, and never replicate its workflow by hand when the user merely mentions wrapping up. If the user describes wanting a handoff without typing the command, point them at `/session-handoff` instead of improvising a summary.

## How to produce the summary

1. **Review the full conversation**, not just the last few turns. Handoffs miss things when they only summarize recent context.
2. **Pull state from these sources (in order):**
   - **Standing instructions the user gave in chat** — how to communicate (language, tone, verbosity), what to always or never do, tools to prefer or avoid, things to ask before doing. These arrive as ordinary chat messages, produce no file and no diff, and are therefore the single most-dropped category in a handoff. Sweep every user turn for them, not just the first one — an instruction given mid-session counts as much as one given up front.
   - **Decisions and conclusions reached in conversation that left no artifact** — an option you proposed and the user accepted or rejected, a plan that changed direction, a number or name that got settled, a "yes, do it that way", a correction the user made to your approach. A decision is no less locked because it produced no file. Scan for the moments the user agreed, disagreed, corrected you, or reversed an earlier call.
   - **Facts learned about the system this session** — constraints discovered, settings that turned out not to exist, behaviour that contradicted an assumption, versions and defaults verified. Cheap to re-derive is not the test; if you spent effort establishing it, record it.
   - Plan / task files referenced this session — report the exact path used. If the project documents a plan/task location (in `CLAUDE.md`, `AGENTS.md`, project README, or similar), respect that convention. Fall back to the user-global store (`~/.claude/plans/` on macOS/Linux, equivalent on Windows) only if that's where the plan actually lives. Never guess a path and never hunt the filesystem.
   - TodoWrite state — any in-progress or pending tasks.
   - Background processes you started with `run_in_background` — shell IDs are load-bearing for the next agent.
   - Files created or modified this session — you know what you touched; don't grep to re-discover.
   - Memory files written or updated — same rule: report the exact path used, respect any project-documented memory location, fall back to user-global memory only if that's where writes went.
   - Unresolved questions — things you asked the user that never got a clear answer, or things the user asked that got deflected.
   - Approaches that FAILED this session — what you tried that didn't work, and what the next agent will be tempted to retry. This is the least recoverable information in the whole handoff; the code shows what works, only you remember what didn't.
3. **Do NOT audit the filesystem.** This is synthesis of what happened in THIS session. No `git log`, no broad `Glob` sweeps. If you didn't touch it this session, it doesn't belong here.
4. **If a handoff was already produced this session, update it** rather than writing a second one from scratch.
5. **Run a completeness sweep before writing anything.** Walk the user's turns from first to last and ask of each one: did it contain an instruction, a preference, an agreement, a correction, or a reversal? Every hit must land in "Standing instructions" or "Decisions locked". Only then start filling the template — the sweep does not work as a review pass afterwards, because by then you are re-reading your own summary instead of the conversation.
6. **Produce the output in chat.** Do not write a file. Do not update memory. Chat-only.

## Output template — use exactly this structure, every time

```
# Session Handoff — <one-line title of what this session was about>

## Where it started
<2-3 sentences: what the user asked for, key framing or constraints that emerged>

## Standing instructions from the user
<Anything the user told you about HOW to work that a fresh agent would otherwise violate
on its first reply. Quote the user's own wording. State the scope.>
- <instruction, in the user's words> — <scope: this session / this project / always>
- (or "none")

## Decisions locked + what shipped
<Include decisions that produced no file. Mark them so, don't drop them.>
- <decision or change> — <why, and where it lives (absolute path, or "chat only — no artifact")>
- ...

## Learned this session
- <fact established, constraint discovered, assumption disproved> — <how it was verified>
- (or "none")

## Traps + dead ends
- Tried: <approach> — <how it failed, why it was abandoned>
- Do NOT: <the tempting wrong move> — <what breaks if you do>
- (or "none")

## Key files for next session
- `<absolute path>:L<start>-L<end>` — <what specifically is at those lines, not what the file is>
- Plan file: `<path>` (if a plan drove the session)
- Memory files touched: `<paths>` (if any)
- External artifacts: `<PR / issue / ADR / spec>` — pointer only, never re-embedded here

## Running state
- Background processes: <shell IDs + what they are + how to kill> — or "none"
- Dev servers / ports: <url + port> — or "none"
- Open worktrees / branches: <paths> — or "none"

## Verification — how to confirm things still work
- `<command>` — <expected outcome>
- ...

## Deferred + open questions
- Deferred: <item> — <why pushed to later>
- Open: <question needing the user's input> — <context>

## Pick up here
<1-2 sentences: the single most likely next action for a fresh agent>

---
Read the files listed under "Key files for next session" before acting. Treat every
claim above as context to verify against the actual code, not fact to trust.
```

## Hard rules

1. **Chat output only.** Never write the handoff to a file. Never update memory from this skill.
2. **Never invent state.** If a section has nothing to report, write "none" — do not omit the section. Structure stability is the whole point.
3. **Absolute paths always.** The next agent may have a different working directory.
4. **If a plan file drove the session, name it first** in "Key files" so the next agent reads it before anything else.
5. **No emojis, no hype, no "great job" summaries.** Terse and concrete — paths, commands, shell IDs, decisions. Match the tone of a seasoned engineer handing off at end-of-shift.
6. **Background process IDs are critical.** If you started any `run_in_background` shells, their IDs must appear in "Running state" with the kill command — the next agent cannot find them otherwise.
7. **State, not instructions.** Every section except "Pick up here" describes what *is true*, never what the next agent *should do*. Write "logout endpoint is not implemented; session persistence depends on it" — not "implement the logout endpoint". The next agent decides actions from ground truth.
8. **Reference, don't duplicate.** Never re-embed content that already lives in a plan, spec, ADR, PR, issue, or commit. Point to it by absolute path or URL. A handoff that re-embeds goes stale the moment the source changes.
9. **Redact secrets.** No API keys, tokens, passwords, or PII. Name where the credential lives (`.env.local`, 1Password item, CI variable) — never its value.
10. **Read the project config first.** If `CLAUDE.md` / `AGENTS.md` covers something, don't restate it. The handoff is session-specific only. One exception: a standing instruction the user gave in chat goes in the handoff even if it overlaps the config — the next agent needs to know it was restated and enforced this session.
11. **"Standing instructions" comes first and is never empty by default.** A session where the user gave no instruction about how to work is rare. If you are about to write "none" there, sweep the user's turns once more before you do.

## Anti-patterns — do not do these

- Summarizing the last 3 turns and calling it a handoff.
- Listing files by relative path.
- Skipping the "Running state" section because "nothing is running" — write "none" instead.
- Writing the summary to `~/.claude/handoffs/` or any file. This is chat-only by design.
- Adding a "what went well / what went poorly" retrospective. This isn't a retro.
- Recommending next steps beyond the single "Pick up here" line. The next agent decides; you just hand off.
- Phrasing "Current state" or "Deferred" as a task list. Those sections report status; only "Pick up here" is allowed an imperative.
- Pasting plan, spec, or ADR content into the handoff instead of linking to it.
- Dropping "Traps + dead ends" because nothing dramatic failed. A near-miss or a rejected approach still belongs there; otherwise write "none".
- Naming a file without saying what is in it. `/path/to/auth.ts — auth stuff` is useless; give the line range and the specific thing.
- Dropping an instruction because it "isn't about the work" — "let's speak Russian", "stop writing walls of text", "ask me before touching that repo" are exactly the things a fresh agent breaks first.
- Recording only the decisions that produced a diff. A rejected option, a settled name, a changed direction, an accepted trade-off are all locked decisions with no artifact.
- Treating the first user turn as the source of instructions. Preferences stated in turn 12 outrank the original framing and are the ones most often lost.

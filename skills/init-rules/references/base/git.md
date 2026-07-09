# Git (Tier 1)

## Commit style — match the repo first

If `git log` shows a consistent existing convention, codify THAT — do not impose Conventional Commits over a repo that already follows another clear style. Only default to the below when history is inconsistent or empty.

**Conventional Commits**: `type(scope): imperative subject`

- Types: `feat`, `fix`, `chore`, `refactor`, `test`, `docs` (add `perf`, `ci`, `build` if the repo uses them)
- Subject: imperative mood ("add", not "added"/"adds"), ≤ ~72 chars, no trailing period
- Scope is optional but keep it consistent when used

```
❌ Bad
Fixed the bug where users couldnt login and also updated some styles

✅ Good
fix(auth): reject login when session token is expired
```

## Atomic commits

One logical change per commit. Do not bundle a refactor, a feature, and a formatting sweep together — it makes review and revert painful. Split unrelated changes.

## Branch naming

Follow the team convention if one exists. Common default: `type/short-description`, e.g. `feature/invoice-export`, `fix/null-user-crash`. Keep it lowercase and hyphenated.

## Never commit

- Secrets, credentials, API keys, `.env` files
- Build artifacts, dependencies (`node_modules/`, `dist/`, `vendor/`), local IDE config

Enforce via `.gitignore`; if a secret was committed, rotate it — removing it from HEAD is not enough.

## PR / MR hygiene

- Keep PRs small and single-purpose — easier to review, safer to merge.
- Every PR is reviewed before merge; write a description that states what and why.

Source: best-practice · Confidence: high

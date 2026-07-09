# Python (Tier 1 — authoritative)

Best-practice source when Python is detected. Encode project decisions and modern idioms, not
Python basics.

## Contents
- Typing
- Tooling (ruff, mypy, formatting)
- Packaging & layout
- Idioms & correctness
- Errors

## Typing
- Type hints on all public function signatures and dataclass fields. Prefer precise types over
  `Any`; use `from __future__ import annotations` or 3.10+ syntax (`X | None`, `list[str]`).
- Use `typing.Protocol` for structural interfaces; `TypedDict`/`dataclass`/`pydantic` for
  structured data instead of bare dicts crossing module boundaries.
- Run `mypy` (or `pyright`) — if the repo configures strictness, codify *its* level.

❌ Bad
```python
def load(path):
    return json.loads(open(path).read())   # untyped, leaks a file handle
```
✅ Good
```python
from pathlib import Path

def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))
```

## Tooling
- **ruff** for lint + import sorting + (increasingly) formatting; or `black` + `isort` if that's
  what's installed. Codify the repo's configured tool and its `pyproject.toml` settings, not a
  generic preference.
- Pin the interpreter version in `pyproject.toml`'s `requires-python`.

## Packaging & layout
- Prefer `pyproject.toml` (PEP 621) over `setup.py`. Use the **`src/` layout** for libraries.
- Manage deps with the tool in use (uv / poetry / pip-tools); don't mix. Lock and commit the lock.

## Idioms & correctness
- Use context managers (`with`) for all resources; never leak file/socket handles.
- Prefer comprehensions and generators over manual accumulation; prefer `pathlib` over
  `os.path`; prefer f-strings.
- Guard against mutable default arguments (`def f(x=[])` is a bug) — use `None` sentinels.
- Make functions pure where feasible; isolate I/O at the edges.

## Errors
- Raise specific exception types; never bare `except:` — catch the narrowest class. Never
  `except Exception: pass`.
- Chain with `raise ... from e` to preserve the cause.

## Research hook
For a specific Python version's new features (pattern matching, `ExceptionGroup`, etc.),
`WebSearch` the official `docs.python.org` "What's New" page and codify the idioms actually used.

Source: best-practice · Confidence: high

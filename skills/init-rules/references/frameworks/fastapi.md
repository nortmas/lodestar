# FastAPI (Tier 3)

Balance policy: an existing consistent codebase pattern wins over textbook advice
unless it is a security, correctness, or performance defect.

## Rules

- **Inject dependencies via `Depends`.** Auth, DB sessions, and settings enter
  routes through dependencies — not module globals or manual instantiation. This
  keeps handlers testable via `dependency_overrides`.
- **Separate input and output schemas.** Distinct Pydantic models for request
  bodies vs responses; never expose the ORM entity directly. Keep write-only
  fields (passwords) off the response model.
- **`async def` routes must stay non-blocking.** Use async DB drivers (asyncpg,
  `AsyncSession`) and async HTTP clients (httpx). A blocking call in an async
  route stalls the whole event loop. If a dependency is only sync, define the
  route as plain `def` so FastAPI runs it in a threadpool.
- **Modularize with `APIRouter`.** One router per resource/domain, mounted with a
  prefix and tags. No single monolithic app file.
- **Declare `response_model` and explicit `status_code`.** 201 for creation, 204
  for empty responses; let `response_model` enforce the output contract.
- **Config via `pydantic-settings`.** Load secrets from env into a typed
  `BaseSettings`, provided as a cached dependency — never read `os.environ`
  scattered through handlers.

## ❌ Bad — blocking I/O inside an async route

```python
@router.get("/reports")
async def reports():
    # Sync DB call blocks the event loop for every concurrent request.
    rows = session.execute(text("SELECT * FROM reports")).fetchall()
    return rows
```

## ✅ Good — async driver, typed response

```python
@router.get("/reports", response_model=list[ReportOut], status_code=200)
async def reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report))
    return result.scalars().all()
```

## Research hook

On activation, `WebSearch` `"fastapi <installed-version> best practices"`. Prefer
official docs (fastapi.tiangolo.com), then cross-check a second reputable source.
Codify findings with provenance `researched` + source URL + retrieval date. Never
block on a failed search — fall back to the rules above.

Source: best-practice · Confidence: medium

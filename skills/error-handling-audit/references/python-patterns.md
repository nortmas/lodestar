# Python Error Handling Patterns

Load this file when auditing a Python app. These patterns extend the universal patterns in SKILL.md.

## Patterns

| # | Pattern | Detection | Fix | Mode |
|---|---------|-----------|-----|------|
| PY1 | `logger.error()` in except blocks | grep `logger.error` inside `except` blocks | Change to `logger.exception()` which auto-appends the traceback | auto-fix |
| PY2 | `logging.getLogger()` bypassing project logger | grep `logging.getLogger` in source files, excluding the project's own logger utility | Replace with the project's centralized logger (discovered in Phase 0). Add the import and module-level `logger = get_logger(__name__)` if missing. | auto-fix |
| PY3 | `print()` in source files | grep `print(` in all `.py` files, excluding tests and `prompts.py` | Replace with `logger.info()` or `logger.debug()` using the project logger. Add import and module-level logger variable if missing. | auto-fix |
| PY4 | I/O operations without error handling | Route handlers (FastAPI, Flask, Django) performing database, HTTP, or file I/O without try/except around the specific I/O call | Wrap the **specific I/O call** (not the entire handler body) in try/except. Log with `logger.exception()`. Return appropriate error response (`HTTPException(500)` for FastAPI, `JsonResponse` for Django). **Before fixing:** check if a framework-level exception handler exists — if so, per-route wrapping is only needed for route-specific recovery logic. | ask |
| PY5 | Missing startup validation | Config directories or required files not validated at app boot (e.g., output dirs, model paths, API key presence) | Add existence/writable checks in app startup (`app.py`, `main.py`, or config module). Fail fast with a clear error message — not silently at runtime. | ask |
| PY6 | Async subscribers without timeout | `queue.get()`, `asyncio.wait_for()`, or bare `await` with no timeout on potentially hanging operations | Add a reasonable timeout. Log and clean up on expiry. Choose timeout based on the operation (e.g., 30s for HTTP, 1h for long-running AI pipelines). | ask |
| PY7 | Bare `except:` or `except Exception` without re-raise | Catches everything and continues — the caller never knows something failed | Log with `logger.exception()` and either re-raise, raise a specific exception, or handle the specific expected errors only. | ask |

## Detection Notes

- For PY2, the "project's own logger utility" is whatever was discovered in Phase 0 Step 3. Common patterns: `from myapp.utils.logger import get_logger`, `from myapp.logging import logger`, `import structlog; logger = structlog.get_logger()`.
- For PY3, some `print()` calls are legitimate (CLI tools, management commands with intentional stdout output). If the file is clearly a CLI entry point, skip it.
- For PY4, common I/O that needs wrapping: `httpx.get()`, `requests.post()`, `aiohttp` calls, SQLAlchemy queries, `open()` for file access, `subprocess.run()`.

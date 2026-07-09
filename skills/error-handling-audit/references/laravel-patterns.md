# Laravel Error Handling Patterns

Load this file when auditing a Laravel/PHP app. These patterns extend the universal patterns in SKILL.md.

## Patterns

| # | Pattern | Detection | Fix | Mode |
|---|---------|-----------|-----|------|
| LA1 | `try/catch` without `Log::error()` | grep for `catch` blocks in `.php` files that do not contain `Log::` or `report(` within the catch body | Add `Log::error($e->getMessage(), ['exception' => $e, 'context' => ...])` with relevant context variables | auto-fix |
| LA2 | `dd()`, `dump()`, `ray()` in non-test code | grep `dd(`, `dump(`, `ray(` in `app/`, `routes/`, `config/`, `database/` directories | Remove entirely, or replace with `Log::debug()` if the value is diagnostically useful | auto-fix |
| LA3 | `error_log()` instead of `Log` facade | grep `error_log(` in all PHP source files | Replace with `Log::error()` with a context array: `Log::error($message, ['key' => $value])` | auto-fix |
| LA4 | Exception handler returning generic response without logging | Exception handler (`Handler.php`, `bootstrap/app.php` exception renderers) that returns a response without logging first | Add `Log::error()` with exception context before the response return | auto-fix |
| LA5 | Queue jobs without `failed()` method | Job classes (classes using `Dispatchable`, `InteractsWithQueue`, `Queueable` traits, or implementing `ShouldQueue`) that do not define a `failed(Throwable $exception)` method | Add `failed()` method with `Log::error('Job failed: ' . $exception->getMessage(), ['exception' => $exception, 'job' => static::class])` | ask |
| LA6 | Controller returning 500 without logging | catch block in a controller that returns `response()->json(..., 500)` or `abort(500)` without a `Log::` call before it | Add `Log::error()` before the error response | auto-fix |
| LA7 | Missing validation error responses for API | `$request->validate()` in API controllers without ensuring JSON error format | Ensure the route uses API middleware or the controller returns JSON validation errors. Check `Accept: application/json` header handling. | ask |
| LA8 | Middleware swallowing exceptions | Middleware `handle()` method with catch blocks that redirect or return a response without logging | Add `Log::error()` or `report($e)` before the redirect/response | auto-fix |
| LA9 | Event listeners without error handling | Listener `handle()` methods that perform I/O (DB, HTTP, queue dispatch) without try/catch | Wrap I/O in try/catch. Log with `Log::error()`. Decide: re-throw (fails the event chain) or swallow (other listeners still fire). **Present both options to user.** | ask |
| LA10 | HTTP client calls without error handling | `Http::get()`, `Http::post()`, or other `Http::` calls without `->throw()`, `->throwIf()`, or checking `->failed()`/`->successful()` | Add `->throw()` for calls that must succeed, or check `->failed()` and log `$response->body()` (truncated to 500 chars) for calls that can gracefully degrade | ask |

## Detection Notes

- For LA1, some catch blocks legitimately use `report($e)` instead of `Log::error()` — this is Laravel's built-in exception reporting and counts as proper logging. Do not flag these.
- For LA2, `dd()` is acceptable in `tests/` and in artisan commands explicitly designed for debugging output.
- For LA5, not all jobs need `failed()` — jobs that use `$this->release()` for retry logic or `DeleteWhenMissingModels` may handle failure differently. Present the job to the user.
- For LA8, common legitimate middleware patterns: `TrustProxies`, `HandleCors`, `EncryptCookies` — these don't need error logging. Focus on custom middleware.
- For LA10, `Http::fake()` in tests is not a violation.

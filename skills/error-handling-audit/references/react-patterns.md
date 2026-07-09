# React / JS / TS Error Handling Patterns

Load this file when auditing a React, Next.js, Vue, or other JS/TS frontend. These patterns extend the universal patterns in SKILL.md.

## Core Principle

**Every error path must end with visible user feedback.** No silent catches, no stuck spinners, no blank screens. The user must always know something went wrong and ideally what to do about it.

## Patterns

| # | Pattern | Detection | Fix | Mode |
|---|---------|-----------|-----|------|
| RE1 | Empty `.catch(() => {})` | grep `.catch(` followed by empty body, no-op (`() => {}`), or only `console.log` | Add error state update + user-visible feedback. Requires understanding the component's state and toast/notification patterns. | ask |
| RE2 | `async/await` without try/catch | async functions that perform I/O (fetch, axios, API calls) with no try/catch | Wrap in try/catch. In the catch: set error state, show user feedback (toast, inline error, fallback UI), reset loading state if applicable. | ask |
| RE3 | API calls without error/loading states | Component makes `fetch`/`axios`/API calls but has no error state variable (`useState` for error) | Add `const [error, setError] = useState<string \| null>(null)`. Set it in catch blocks. Render error state in JSX. | ask |
| RE4 | Missing error boundaries | Page-level or route-level components without an `ErrorBoundary` wrapper | Add an error boundary component with a user-friendly fallback UI. If the project already has an ErrorBoundary component, wrap the page with it. If not, propose creating one. | ask |
| RE5 | SSE/WebSocket without disconnect handling | `EventSource`, `WebSocket`, or custom stream hooks with no `onerror` handler, no reconnect logic, no timeout | Add `onerror` handler that: updates connection state, shows user notification, attempts reconnect with backoff (if appropriate). Add cleanup on component unmount. | ask |
| RE6 | Loading state not reset on error | `setLoading(true)` before an async call, but catch block or error path does not call `setLoading(false)` | Add `finally { setLoading(false) }` or ensure catch block resets loading. Prefer `finally` to avoid duplication. | auto-fix |
| RE7 | Fire-and-forget promises | Promise returned from a function call but neither awaited nor `.catch()`-ed | Add `.catch()` with error handling, or `await` inside try/catch. At minimum, add `.catch(console.error)` to prevent unhandled rejection. | auto-fix |
| RE8 | Conditional rendering gaps on error | Component has an error state but renders `null`, empty `<></>`, or nothing when error is set | Add explicit error rendering: `{error && <div className="error">{error}</div>}` or equivalent using the project's error display pattern. | ask |
| RE9 | Generic error toast without detail | Catch block shows only "Something went wrong" or similar generic text | Include actionable detail from the error when safe (HTTP status, error message, field name). Do not expose stack traces or internal details to users. | auto-fix |
| RE10 | useEffect cleanup missing | `useEffect` that adds event listeners (`addEventListener`), intervals (`setInterval`), subscriptions, or timers without a cleanup return | Add cleanup return function: `return () => { removeEventListener(...); clearInterval(...); }`. Missing cleanup causes errors when the component unmounts and the callback fires on stale state. | ask |
| RE11 | API response shape not validated | Response from fetch/axios used directly (`data.results.map(...)`) without checking the expected structure | Add a shape check before using: `if (!data?.results) { setError('Unexpected response'); return; }`. For TypeScript projects, consider a runtime validator (zod, io-ts) if the project uses one. | ask |
| RE12 | Form submission error handling | Form `onSubmit` handler performs async operations without try/catch, or catches errors without showing them to the user | Add try/catch around submission. In catch: show validation errors (if 422) or server errors (if 5xx) to the user. Reset `isSubmitting` state in finally. | ask |

## Detection Notes

- For RE1, `.catch(console.error)` is marginally better than empty but still doesn't show the user anything. Flag these for RE1 but suggest adding user-visible feedback on top of the console.error.
- For RE4, check if the project already has an `ErrorBoundary` component (grep for `componentDidCatch` or `ErrorBoundary`). Reuse it rather than creating a new one.
- For RE5, distinguish between critical streams (must show error immediately) and background streams (can retry silently a few times before alerting). Ask the user which applies.
- For RE7, `void somePromise()` is an intentional fire-and-forget pattern in some codebases. If the project uses `void` prefix deliberately, skip those.
- For RE10, React Strict Mode double-invokes effects in development — missing cleanup will cause doubled event listeners in dev mode, which can be a debugging hint.
- For RE11, GraphQL responses have a different shape (`data.data.results` or `data.errors`). Adjust the check based on the API client used.

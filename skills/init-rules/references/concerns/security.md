# Security (Tier 2 — CRITICAL carve-out)

Everything here is part of the critical carve-out. A consistent existing insecure pattern does NOT win the balance policy: never codify it as the project rule. Override with best practice and emit a migration note pointing at the offending code.

## Validate input at boundaries
Validate and normalize every value crossing a trust boundary (HTTP request, queue message, file, third-party response) before use. Treat client-supplied data as hostile; validate type, range, and shape server-side even if the client already did.

## Escape output for its sink (XSS)
Escape at render time for the specific context — HTML body, attribute, JS, URL, SQL are different escapers. Rely on the templating engine's auto-escaping; never mark raw user input as safe.

```php
// ❌ Bad: reflected XSS
echo "<div>Hello {$_GET['name']}</div>";

// ✅ Good: context-correct escaping
echo '<div>Hello ' . htmlspecialchars($request->query('name'), ENT_QUOTES) . '</div>';
```

## Parameterize every query
Use bound parameters / prepared statements or the ORM's query builder. Never concatenate or interpolate user input into SQL, shell commands, or LDAP filters.

```php
// ❌ Bad: SQL injection — migrate immediately, do not replicate
$db->query("SELECT * FROM users WHERE email = '{$email}'");

// ✅ Good: bound parameter
$db->prepare('SELECT * FROM users WHERE email = ?')->execute([$email]);
```

## Keep secrets out of code and VCS
Credentials, API keys, and tokens live in environment/secret managers, never in source, config committed to git, logs, or error responses. A secret that reached the repo history is compromised — rotate it, don't just delete the line.

## Authorize at the boundary, not just authenticate
Authentication proves who; authorization proves may. Check permissions on every protected action against the specific resource. A logged-in user is not an authorized one — guard against IDOR by verifying ownership/role for the exact record.

```php
// ❌ Bad: authenticated but not authorized — any user reads any invoice
return Invoice::findOrFail($id);

// ✅ Good: ownership enforced
$invoice = Invoice::findOrFail($id);
$this->authorize('view', $invoice);
return $invoice;
```

## Dependency hygiene
Run a vulnerability audit in CI, pin versions with a lockfile, and update on a schedule. An unpatched known CVE in a dependency is a live defect, not tech debt.

## Carve-out reminder
If the codebase already string-concats SQL, skips authz, or hardcodes secrets: do NOT write a rule matching it. Emit the correct rule plus a migration note flagging the insecure code for remediation.

Source: best-practice · Confidence: high

# Architecture (Tier 1)

## Quality metrics (tunable defaults)

These are starting thresholds, not laws. If the project's linter or existing code sets different limits consistently, codify those instead. Flag violations only when they hurt readability or hide a defect.

- Function length: ≤ ~30 lines
- File length: ≤ ~300 lines
- Nesting depth: ≤ 3
- Parameters: ≤ 4 (beyond that, pass an object/struct)
- Cyclomatic complexity: ≤ ~10

## Layering

Organize into layers and keep dependencies pointing inward:

```
presentation → application/service → domain → infrastructure
```

- **Depend on abstractions**, not concretions. Inner layers must not import outer ones.
- The domain layer knows nothing about HTTP, the ORM, or the framework.
- Infrastructure (DB, queues, external APIs) is reached through interfaces the domain defines.

## Coupling & cohesion

- High cohesion: a module does one thing; its parts change together.
- Low coupling: modules interact through narrow, stable interfaces.
- **No circular dependencies** — they signal a missing abstraction or a misplaced responsibility.

## Where business logic lives

Business logic belongs in the domain/service layer, never in controllers, views, or migrations. Controllers translate transport (HTTP) to and from application calls; they do not decide.

```php
// ❌ Bad — fat controller: validation, business rules, and persistence inline
public function store(Request $request)
{
    if ($request->amount <= 0) abort(422);
    $user = User::find($request->user_id);
    if ($user->balance < $request->amount) abort(400);
    $user->balance -= $request->amount;
    $user->save();
    Transaction::create([...]);
    Mail::to($user)->send(new ReceiptMail());
    return response()->json(['ok' => true]);
}

// ✅ Good — controller delegates; the service owns the rules
public function store(TransferRequest $request, TransferService $transfers)
{
    $transfers->debit($request->user(), $request->amount());
    return response()->json(['ok' => true]);
}
```

Source: best-practice · Confidence: high

# PHP 8.x (Tier 1 — authoritative)

Best-practice source for the balance policy when PHP is detected. Only the non-obvious,
version-specific, or project-decision-worthy points — the model already knows PHP syntax.

## Contents
- Types & strictness
- Modern class features (8.0–8.3)
- Error handling & exceptions
- Facades / service location
- Style & PSR alignment

## Types & strictness
- `declare(strict_types=1);` at the top of **every** PHP file. This is the single highest-value
  PHP rule; codify it unless the repo has consciously chosen weak typing everywhere.
- Explicit parameter and return types on all functions/methods, including `: void` and `: never`.
- Type properties; avoid untyped `$this->x`. Prefer nullable (`?T`) over untyped-and-maybe-null.
- Use union/intersection types where they clarify (`int|string`, `Countable&Traversable`), not
  to paper over a design that should be one type.

❌ Bad
```php
function total($items) {           // no strict_types, no types
    return array_sum($items);
}
```
✅ Good
```php
declare(strict_types=1);

function total(array $items): int
{
    return array_sum($items);
}
```

## Modern class features
- **Constructor property promotion** for value/DTO/service constructors.
- **`readonly` properties** (8.1) for immutable value objects; consider `readonly` classes (8.2).
- **First-class enums** (8.1) instead of class constants for closed sets; back them (`: string`)
  when persisted.
- **Nullsafe** `?->` instead of nested `isset` chains.
- **Named arguments** where they materially aid clarity at call sites (many optional params) —
  not everywhere.
- **First-class callable syntax** `$fn(...)` over string callables.

✅ Good
```php
final readonly class Money
{
    public function __construct(
        public int $cents,
        public Currency $currency,   // backed enum
    ) {}
}
```

## Error handling & exceptions
- Throw **typed** exceptions (domain or SPL), never bare `new \Exception('...')` in domain code.
- Never suppress errors with `@`. Never silence with an empty `catch`.
- Catch the narrowest type you can act on; let others propagate.

## Facades / service location
- In **domain** code (services, actions, value objects), prefer constructor injection over
  static facades / `app()` / global helpers — facades-as-service-locator hide dependencies and
  break testability. Facades are acceptable in the HTTP/console edge layer.

## Style & PSR
- Align with **PSR-12** (and PER Coding Style). If the repo already runs `php-cs-fixer` or
  `pint`, codify *its* config as the rule rather than restating PSR-12.
- Prefer `match` over `switch` for value mapping (strict comparison, exhaustive, returns).

## Research hook
If the project targets a PHP version with features newer than covered here, `WebSearch`
`"php <version> new features"` (official `php.net` migration guide) and codify the idioms in use.

Source: best-practice · Confidence: high

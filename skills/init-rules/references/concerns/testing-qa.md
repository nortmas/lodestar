# Testing & QA (Tier 2)

Guidance on what to test, at what level, and how to keep tests trustworthy.

## Respect the pyramid
Many fast unit tests, fewer integration tests, a few end-to-end tests. An inverted pyramid (mostly slow e2e) is a smell: the suite becomes slow, flaky, and expensive to diagnose. Push logic down to units that can be tested in isolation.

## Arrange / Act / Assert
Structure each test in three visible phases with one logical action under test. Multiple unrelated assertions across multiple actions in one test hide which behavior actually broke.

## Factories over fixtures
Prefer data builders/factories that produce objects on demand with sensible defaults and per-test overrides. Shared static fixtures drift, couple unrelated tests, and force readers to scroll elsewhere to understand the setup.

```php
// ❌ Bad: opaque shared fixture, mutated across tests
$user = $this->fixtures['premium_user_with_expired_card'];

// ✅ Good: intent is local and explicit
$user = UserFactory::new()->premium()->withExpiredCard()->create();
```

## Test behavior and contracts, not internals
Assert on observable outcomes (return values, emitted events, persisted state, HTTP responses). Do not assert that a private method was called or pin the framework's own behavior — those tests break on every refactor without catching real regressions.

```php
// ❌ Bad: asserts an implementation detail
$service->expects($this)->method('recalculateInternalCache');

// ✅ Good: asserts the contract the caller depends on
$this->assertSame(90.0, $cart->total());
```

## Coverage is a signal, not a target
Use coverage to find untested branches, not as a gate to game. 100% coverage of trivial getters proves nothing; an uncovered error path is a real gap. Never write assertion-free tests to lift a number.

## Determinism is non-negotiable
No `sleep()`, no real wall-clock, no real network or filesystem in unit tests. Inject a fixed clock, fake the network, seed randomness. A test that passes only sometimes is worse than no test — it trains the team to ignore red.

## Balance note
Follow the project's existing framework, naming, and assertion style even if another is more fashionable. But non-deterministic tests and coverage-gaming are quality defects — flag them regardless of local convention.

Source: best-practice · Confidence: high

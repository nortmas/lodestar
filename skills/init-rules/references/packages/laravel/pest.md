# Pest (Tier 2)

Pest 3 idioms only. For what to test, factories, and `RefreshDatabase` in a
Laravel app see `../../frameworks/laravel.md` and `../../concerns/testing-qa.md`.
Balance policy: a consistent existing pattern wins unless it is a
security/correctness/performance defect.

## Style
- Write `it()` / `test()` closures, not PHPUnit test-method classes. Describe
  behaviour in the string (`it('rejects an expired token')`).
- Share setup via `beforeEach()` and `pest()` config in `tests/Pest.php`; use
  the `uses(RefreshDatabase::class)` binding there rather than per-file traits.

## Datasets over copy-paste
Parameterize repeated cases with `->with([...])` instead of near-duplicate tests.

## Higher-order & chained expectations
Prefer fluent `expect()` chains; use higher-order expectations (`->each`, `->and`)
to keep assertions dense and readable.

## Architecture tests
Encode structural rules with `arch()` (e.g. controllers stay thin, no `dd()`
shipped, models don't depend on HTTP). Cheap, fast guardrails — add them.

## Don't over-mock
Mock external boundaries (HTTP, mail, payment SDKs) only. Let real code and the
database run for domain logic; over-mocking tests the mocks, not the app. Keep
tests deterministic — freeze time (`travelTo`), fake randomness, seed factories.

❌ Bad — verbose PHPUnit style, duplicated cases, over-mocked
```php
class DiscountTest extends TestCase
{
    public function test_ten_percent() { $this->assertEquals(90, (new Discount)->apply(100, 10)); }
    public function test_twenty_percent() { $this->assertEquals(80, (new Discount)->apply(100, 20)); }
    public function test_service()
    {
        $repo = Mockery::mock(OrderRepo::class);   // mocking code under test
        $repo->shouldReceive('total')->andReturn(100);
        // ...
    }
}
```
✅ Good — Pest with a dataset and real collaborators
```php
it('applies a percentage discount', function (int $pct, int $expected) {
    expect((new Discount)->apply(100, $pct))->toBe($expected);
})->with([
    'ten percent'    => [10, 90],
    'twenty percent' => [20, 80],
]);

it('totals an order', function () {
    $order = Order::factory()->hasItems(3)->create();   // real DB via RefreshDatabase
    expect(app(OrderTotals::class)->for($order))->toBe(300);
});

arch('controllers are invokable or thin')
    ->expect('App\Http\Controllers')
    ->not->toUse(['dd', 'dump']);
```

Source: best-practice · Confidence: high

# Livewire (Tier 2)

Livewire 3 idioms only. For Services/Actions, authorization, Eloquent, and N+1
see `../../frameworks/laravel.md`. Balance policy: a consistent existing pattern
wins unless it is a security/correctness/performance defect.

## Components stay small
One component owns one concern. When a component grows many properties and
methods, split it and compose via nested components and events, not one god class.

## Public properties are state
- Every `public` property is serialized to the client and re-hydrated on each
  request. Keep them minimal, scalar, or simple arrays.
- Do **not** store full Eloquent models or large collections as public state —
  Livewire 3 wire:models to typed data; keep heavy data in computed properties.

## Binding: live vs deferred
- Default `wire:model` is **deferred** in Livewire 3 (syncs on the next action).
  Add `.live` only when the UI must react on every keystroke; use `.live.debounce`
  for search inputs. Needless `.live` means a round-trip per keystroke.

## Computed properties & N+1
- Derive data with `#[Computed]` methods instead of persisting it as state; they
  are cached per request.
- Eager-load in the query that feeds `render()`. A relation accessed in the Blade
  loop without `with()` is an N+1 on every re-render.

## Authorize every action
Public methods are HTTP endpoints — anyone can invoke them. Authorize inside the
method (`$this->authorize(...)`) exactly as you would a controller action.

❌ Bad — bloated component doing everything
```php
class Checkout extends Component
{
    public Order $order;              // whole model as state
    public array $allProducts;        // large collection serialized every request

    public function pay()
    {
        // No authorization; payment + inventory + mail inline.
        $this->order->update(['status' => 'paid']);
        Stripe::charge($this->order);
        foreach ($this->order->items as $i) { $i->product->decrement('stock'); }
        Mail::to($this->order->user)->send(new Receipt($this->order));
    }
}
```
✅ Good — thin component delegating to an Action
```php
class Checkout extends Component
{
    public int $orderId;   // minimal serializable state

    #[Computed]
    public function order(): Order
    {
        return Order::with('items.product')->findOrFail($this->orderId); // eager-loaded
    }

    public function pay(PayForOrder $payForOrder)
    {
        $this->authorize('pay', $this->order);
        $payForOrder->handle($this->order);   // Service/Action owns the workflow
    }
}
```

Source: best-practice · Confidence: high

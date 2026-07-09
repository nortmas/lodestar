# Filament (Tier 2)

Filament-specific guidance only. For layering, Services/Actions, Eloquent, N+1,
and policies see `../../frameworks/laravel.md`. Balance policy: a consistent
existing pattern wins unless it is a security/correctness/performance defect.

## Structure
- Keep the generated layout: `app/Filament/Resources/<Model>Resource.php` plus
  its `Pages/` (List/Create/Edit) and `RelationManagers/`. One Resource per model.
- Register custom pages/widgets sparingly — reach for them only when a Resource
  page genuinely cannot express the screen. Every extra page is more surface to
  authorize and maintain.

## Schemas (form & table)
- Build forms and tables through the schema builders (`Forms\Components\*`,
  `Tables\Columns\*`) — do not hand-roll Blade for what a component covers.
- Group and reuse field sets via `->schema([...])` / shared static methods rather
  than copy-pasting field arrays across Create and Edit.

## Business logic stays out of Resources
Resource classes and their Pages are wiring. Put workflow logic in Services or
Actions (see the framework file) and call them from lifecycle hooks
(`mutateFormDataBeforeSave`, `afterCreate`) or table/page actions.

❌ Bad — business logic and a per-row query in the Resource
```php
Tables\Columns\TextColumn::make('invoice_total')
    ->getStateUsing(fn ($record) => $record->invoices()->sum('total')); // N+1 per row

protected function afterCreate(): void
{
    // Payment + mail orchestration hard-wired into the page.
    Stripe::charge($this->record); Mail::to($this->record->user)->send(new Welcome());
}
```
✅ Good — eager-loaded state, logic delegated
```php
public static function table(Table $table): Table
{
    return $table
        ->modifyQueryUsing(fn ($query) => $query->withSum('invoices', 'total'))
        ->columns([
            Tables\Columns\TextColumn::make('invoices_sum_total')->money('eur'),
        ]);
}

protected function afterCreate(): void
{
    app(OnboardCustomer::class)->handle($this->record); // Service/Action owns it
}
```

## Authorization
- Authorize through Laravel **policies** — Filament resolves the model policy
  automatically for view/create/update/delete. Do not scatter `auth()->user()`
  checks in pages; put the rule in the policy so it is enforced everywhere.

## Performance
- Eager-load relations used by table columns via `modifyQueryUsing()` /
  `getEloquentQuery()`; never query inside `getStateUsing`. Prefer
  `withCount`/`withSum` aggregates over closures that hit the DB per row.

Source: best-practice · Confidence: high

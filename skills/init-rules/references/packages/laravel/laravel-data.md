# Spatie Laravel-Data (Tier 2)

spatie/laravel-data v4 idioms only. For FormRequest validation, API Resources,
and Actions see `../../frameworks/laravel.md`, `../../concerns/api-design.md`,
and `../../concerns/validation` guidance in `laravel.md`. Balance policy: a
consistent existing pattern wins unless it is a security/correctness/performance
defect.

## Data objects are typed DTOs across the whole boundary
- Model request input **and** API output as a single `Data` class instead of
  juggling arrays, `$request->all()`, and a separate Resource. One typed object
  carries validation, casting, and transformation.
- Where the project has adopted Data, do **not** reintroduce the
  FormRequest + JsonResource duplication for the same payload — it splits one
  contract across two files that drift.

## Construction
- Build from input with `Data::from($request)` / `Data::from($model)` and
  collections with `Data::collect($models)`. Validation runs automatically on
  `from()` for request-shaped input; add rules via attributes (`#[Required]`,
  `#[Max(255)]`) or a `rules()` method.

## Computed & mapped properties
- Use `#[Computed]` for derived values and `#[MapInputName]` / `#[MapOutputName]`
  (or a class-level mapper) to bridge snake_case JSON and camelCase properties —
  do not hand-map keys in a controller.

## Casts & transformers
- Register casts/transformers for value objects, enums, dates, and money so the
  boundary stays typed. Prefer them over inline `Carbon::parse()` / `(int)` casts
  sprinkled in controllers.

❌ Bad — array juggling, untyped, duplicated shape
```php
public function store(Request $request)
{
    $data = $request->validate(['title' => 'required', 'published_at' => 'nullable|date']);
    $post = Post::create([
        'title'        => $data['title'],
        'published_at' => $data['published_at'] ? Carbon::parse($data['published_at']) : null,
    ]);
    return response()->json(['id' => $post->id, 'title' => $post->title]); // shape defined twice
}
```
✅ Good — one typed Data object in and out
```php
class PostData extends Data
{
    public function __construct(
        #[Required, Max(255)] public string $title,
        public ?CarbonImmutable $publishedAt,   // cast handles parsing
    ) {}
}

public function store(PostData $data): PostData      // validated on resolve
{
    return PostData::from(Post::create($data->toArray()));  // same contract out
}
```

Source: best-practice · Confidence: high

# Spatie Laravel-Medialibrary (Tier 2)

spatie/laravel-medialibrary v11 idioms only. For file validation, storage disks,
and queues see `../../frameworks/laravel.md`, `../../concerns/security.md`, and
`../../concerns/performance.md`. Balance policy: a consistent existing pattern
wins unless it is a security/correctness/performance defect.

## The package owns file storage — never a manual path column
- Attach files with `$model->addMedia($file)->toMediaCollection('avatars')`.
  The `media` table is the source of truth. Do **not** add an `avatar_path`
  string column and move files by hand — you lose conversions, disk abstraction,
  and referential cleanup.
- Retrieve URLs via `getFirstMediaUrl('avatars')` /
  `getFirstMediaUrl('avatars', 'thumb')`, never by concatenating paths.

## Collections & single-file collections
- Define collections in `registerMediaCollections()`; use
  `->singleFile()` for one-slot fields (avatar, hero) so a new upload replaces
  the old one automatically.

## Conversions — register, and queue the heavy ones
- Register conversions in `registerMediaConversions()`. Leave them queued
  (the default) so image processing runs off the request; only force
  `->nonQueued()` for a conversion a synchronous response truly needs.

## Disk config & validation
- Set the disk per collection (`->useDisk('s3')`) rather than relying on the
  default. Validate uploads (mime type, max size, dimensions) at the request
  boundary before `addMedia()` — the package does not validate for you.

❌ Bad — manual path column, hand-built URL, no conversions
```php
$path = $request->file('avatar')->store('avatars', 'public');
$user->update(['avatar_path' => $path]);          // custom column, orphans on replace
// view:
<img src="{{ asset('storage/'.$user->avatar_path) }}">   // string-glued URL, full-size only
```
✅ Good — media collection with a queued conversion
```php
public function registerMediaCollections(): void
{
    $this->addMediaCollection('avatar')->singleFile()->useDisk('s3');
}
public function registerMediaConversions(?Media $media = null): void
{
    $this->addMediaConversion('thumb')->width(150)->height(150);  // queued by default
}

$user->addMediaFromRequest('avatar')->toMediaCollection('avatar');
// view:
<img src="{{ $user->getFirstMediaUrl('avatar', 'thumb') }}">
```

Source: best-practice · Confidence: high

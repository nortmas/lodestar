# Pydantic (Tier 2)

Target **Pydantic v2** when v2 is installed (the default today); use v1 idioms
only if the codebase is uniformly on v1 — then note a migration path (balance
policy). For Python typing see `../../languages/python.md`; for FastAPI request/
response models see `../../frameworks/fastapi.md`.

## Validate at boundaries only
Use `BaseModel` where untrusted data enters (HTTP, queue messages, config, files)
and parse into it once. Internally pass validated objects — do not re-validate
everywhere or thread raw dicts through the app.

## v2 API — not v1 method names
- Parse: `Model.model_validate(data)` / `model_validate_json(raw)` — **not**
  `parse_obj` / `parse_raw`.
- Dump: `instance.model_dump()` / `model_dump_json()` — **not** `.dict()` /
  `.json()`. Use `model_dump(mode="json")` for JSON-safe primitives.
- Config: a `model_config = ConfigDict(...)` attribute — **not** an inner
  `class Config`.

❌ Bad — Pydantic v1 API on a v2 install
```python
class UserIn(BaseModel):
    email: str
    class Config:                      # v1 config style
        orm_mode = True

user = UserIn.parse_obj(payload)        # v1 method
data = user.dict()                      # v1 method
```
✅ Good — v2 API
```python
class UserIn(BaseModel):
    email: EmailStr
    age: int = Field(ge=0, le=120)
    model_config = ConfigDict(from_attributes=True)   # was orm_mode

user = UserIn.model_validate(payload)
data = user.model_dump(mode="json")
```

## `Field` constraints over hand-rolled checks
Express bounds/lengths/patterns declaratively (`Field(ge=..., max_length=...,
pattern=...)`) instead of manual `if` guards. Prefer semantic types (`EmailStr`,
`AnyUrl`, `PositiveInt`).

## Validators
Use `@field_validator` for single-field normalization/checks and
`@model_validator(mode="after")` for cross-field invariants. Keep them pure;
raise `ValueError` to signal invalid input (Pydantic wraps it).

## Separate input and output models
Distinct models for what you accept vs what you return. Keep write-only fields
(passwords, internal flags) off the output model — do not reuse one model for
both directions.

## Config via `pydantic-settings`
Load environment/secrets into a typed `BaseSettings` (`pydantic-settings` package
in v2, not `BaseSettings` from core). Provide it as a single cached object; never
scatter `os.environ` reads.

Source: best-practice · Confidence: high

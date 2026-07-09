# SQLAlchemy (Tier 2)

Target the **2.0 API** when 2.x is installed; only fall back to 1.4 legacy
`Query` if the codebase is uniformly on it (balance policy — then note a
migration path). For Python typing see `../../languages/python.md`; for N+1 and
query performance see `../../concerns/performance.md`; for injection see
`../../concerns/security.md`.

## 2.0 `select()` + `Session.execute`, not legacy `Query`
Use `session.execute(select(...))` and `.scalars()`. Avoid `session.query(...)`
— it is the deprecated 1.x pattern and mixing styles hides bugs.

## Typed `Mapped[...]` declarative models
Declare columns with `Mapped[...]` + `mapped_column(...)` so mypy/pyright and
the ORM agree on nullability and types. Avoid the untyped `Column(...)` class
attributes.

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
```

## Kill N+1 with eager loading
Default lazy relationships fire one query per parent row inside a loop. Load
collections with `selectinload` (separate IN query) and many-to-one with
`joinedload`. Choose per access pattern, not blindly.

❌ Bad — lazy load inside a loop (N+1)
```python
users = session.execute(select(User)).scalars().all()
for u in users:
    print(u.posts)          # one extra SELECT per user
```
✅ Good — one extra query for all posts
```python
users = session.execute(
    select(User).options(selectinload(User.posts))
).scalars().all()
for u in users:
    print(u.posts)          # already loaded
```

## Scope the Session per request / unit of work
Open a `Session` for one logical operation and close it — use a context manager
(`with Session(engine) as s:`) or a framework-scoped dependency (see
`../../frameworks/fastapi.md`). Never share one long-lived Session across
threads/requests; commit once per unit of work.

## Never string-concat SQL — bind parameters
Interpolating values into SQL text is an injection hole. Use ORM expressions or
`text()` with bound `:params`. Security carve-out: override any string-built SQL
and note the migration, even if it is the existing pattern.

❌ `session.execute(text(f"SELECT * FROM u WHERE email = '{email}'"))`
✅ `session.execute(text("SELECT * FROM u WHERE email = :email"), {"email": email})`

Source: best-practice · Confidence: high

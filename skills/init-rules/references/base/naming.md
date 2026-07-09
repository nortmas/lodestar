# Naming (Tier 1)

Names carry intent. A reader should infer purpose without chasing the definition.

## Casing — detect, then codify

The project's existing casing convention wins. Inspect a representative sample first and encode the observed pattern; only fall back to these ecosystem defaults when the codebase is empty or inconsistent:

- Classes / types: `PascalCase`
- Functions / methods / variables: `camelCase` (JS/TS, Java, Go exported aside), `snake_case` (Python, Ruby, Rust)
- Constants: `UPPER_SNAKE_CASE`

Do not mix conventions within one language. If the repo already uses `snake_case` for JS variables everywhere, that is the rule for this repo — consistency beats the textbook default.

## Rules worth stating

- **Intent over mechanics**: name for what a value means, not its type or how it is computed.
- **Booleans**: prefix with `is` / `has` / `can` / `should` so they read as predicates.
- **Collections**: plural nouns (`users`, not `userList`).
- **Abbreviations**: spell words out; allow only universally-known ones (`id`, `url`, `db`, `http`).
- **No Hungarian notation**: the type system already tracks types; `strName` / `arrItems` add noise.
- **File ↔ symbol agreement**: a file exporting one primary class/component matches its name (`InvoiceParser.ts` → `InvoiceParser`).

```python
# ❌ Bad
def calc(d, flg):        # meaningless name, cryptic params
    lst = []             # type-in-name, no intent
    return lst

# ✅ Good
def calculate_overdue_invoices(invoices, include_drafts):
    overdue_invoices = []
    return overdue_invoices
```

```typescript
// ❌ Bad — boolean reads like a noun; abbreviation obscures meaning
let active = true;
const usrCfg = loadConfig();

// ✅ Good — predicate prefix; full words
let isActive = true;
const userConfig = loadConfig();
```

Source: best-practice · Confidence: high

# Go conventions (Tier 3)

Match the repo's module layout and `golangci-lint` config first; the rules below are Go defaults.

## Errors
- Handle every error explicitly with `if err != nil`. Never discard with `_` unless the call genuinely cannot fail and a comment says why.
- Wrap with `fmt.Errorf("doing X: %w", err)` to preserve the chain for `errors.Is`/`errors.As`. Use `%w` (wrap) not `%v` (flatten) when callers may inspect the cause.
- Do not `panic` in library code. Return an error and let the caller decide. `panic` is only for truly unrecoverable programmer bugs; recover at process boundaries (e.g. an HTTP middleware) if at all.

```go
// ❌ Bad: swallows context, breaks errors.Is
if err != nil {
    return errors.New("could not load config")
}

// ✅ Good: wraps so the cause survives
if err != nil {
    return fmt.Errorf("load config %q: %w", path, err)
}
```

## Interfaces and types
- Accept interfaces, return concrete structs. Callers stay decoupled; you keep flexibility to add methods to the return type.
- Keep interfaces small — 1-3 methods. Define them in the consuming package, not the implementing one.

```go
// ❌ Bad: returns an interface, forcing every caller to a narrow view
func NewStore() Storer { return &pgStore{} }

// ✅ Good: return the concrete type; accept an interface where consumed
func NewStore() *PgStore { return &PgStore{} }
func Sync(r io.Reader) error { /* ... */ }
```

## Context
- Pass `context.Context` as the first parameter (`ctx context.Context`) on any function doing I/O, blocking, or cancellable work. Never store a context in a struct; thread it through calls.

## Tooling and tests
- `gofmt`/`goimports` is non-negotiable and settles all formatting — never debate style. Run `golangci-lint` in CI.
- Prefer table-driven tests with subtests (`t.Run`) so cases are named and isolated.

```go
tests := []struct{ name, in, want string }{
    {"empty", "", ""},
    {"trims", "  hi ", "hi"},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        if got := Clean(tt.in); got != tt.want {
            t.Errorf("Clean(%q) = %q, want %q", tt.in, got, tt.want)
        }
    })
}
```

## Research hook
On activation, detect the Go version (`go version`, `go.mod` `go` directive) and `WebSearch` `"go <version> best practices"` and `"go <version> release notes"`. Prefer go.dev (Effective Go, the spec, release notes) as primary; cross-check one reputable second source. Verify version-specific items before codifying: generics usage norms, `log/slog` (1.21+) as the standard structured logger, `min`/`max`/`clear` builtins (1.21+), loop-variable-per-iteration semantics (1.22+ — the classic closure capture footgun is gone), and range-over-func iterators (1.23+). Codify confirmed rules with provenance `researched` + source URL + retrieval date; drop anything you cannot verify.

Source: best-practice · Confidence: high

# Rust conventions (Tier 3)

Match the repo's `Cargo.toml`, `clippy.toml`, and `rustfmt.toml` first; the rules below are Rust defaults.

## Error handling
- In library crates, return `Result<T, E>` and propagate with `?`. Never `unwrap`/`expect`/`panic!` on recoverable errors — you rob the caller of the choice.
- `unwrap`/`expect` are acceptable in tests, examples, and `main`, and where an invariant is provably impossible (add `expect("reason")` documenting why).
- Split by crate kind: libraries define concrete error types (typically `thiserror` deriving `std::error::Error`); binaries use `anyhow::Result` with `.context(...)` for ergonomic top-level handling.

```rust
// ❌ Bad: a library that panics on bad input takes the whole process down
pub fn parse_port(s: &str) -> u16 {
    s.parse().unwrap()
}

// ✅ Good: return a typed error, let the caller decide
pub fn parse_port(s: &str) -> Result<u16, ParseError> {
    s.parse().map_err(|_| ParseError::InvalidPort(s.to_owned()))
}
```

## Ownership over cloning
- Prefer borrowing (`&T`, `&str`, `&[T]`) in function signatures over taking owned values or `.clone()`-ing to dodge the borrow checker. Reserve `clone` for when you genuinely need a second owner.
- Accept `&str`/`&[T]` rather than `&String`/`&Vec<T>` so callers pass any slice.

```rust
// ❌ Bad: forces an allocation the callee does not need
fn greet(name: String) { println!("hi {name}"); }

// ✅ Good: borrow; caller keeps ownership, no clone
fn greet(name: &str) { println!("hi {name}"); }
```

## Unsafe
- Avoid `unsafe`. Every `unsafe` block needs a `// SAFETY:` comment stating the invariants that make it sound. Prefer safe abstractions or a vetted crate first.

## Tooling
- `cargo fmt` (rustfmt) settles all formatting — never hand-format or debate style. Run `cargo clippy -- -D warnings` in CI and fix lints rather than `#[allow(...)]`-ing them without cause.

## Research hook
On activation, read the edition and toolchain (`Cargo.toml` `edition`, `rust-toolchain.toml`, `rustc --version`) and `WebSearch` `"rust <edition/version> best practices"` and `"rust <version> release notes"`. Prefer doc.rust-lang.org (the Book, API guidelines, edition guide, release notes) as primary; cross-check one strong second source. Verify before codifying: edition differences (2021 vs 2024 — closure capture, `IntoIterator` for arrays), `let-else` (1.65+), `async fn` in traits (1.75+), and current async-runtime norms (tokio vs async-std) from the repo's deps. Codify confirmed rules with provenance `researched` + source URL + retrieval date; drop anything unverified.

Source: best-practice · Confidence: high

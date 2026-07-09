# Detection — signals → layers

Map what's in the repo to the reference layers to activate. Read this at workflow step 1.

## Tiers (depth, not priority)

Every reference file has a depth tier. Tier is a *starting* depth — deepen any layer via
`WebSearch` on activation.

- **Tier 1 (deep, authoritative):** `languages/php.md`, `languages/python.md`,
  `frameworks/laravel.md`. Concrete rules, quantified thresholds, multiple `❌/✅` pairs.
- **Tier 2 (solid, usable now):** `languages/typescript.md`, `languages/javascript.md`,
  `frameworks/vue.md`, `packages/frontend/{tailwind,bootstrap,alpine,pinia,sass,vite}.md`,
  `packages/laravel/{filament,livewire,inertia,pest,spatie-permission,laravel-data,media-library,query-builder,sanctum,horizon}.md`,
  `packages/python/{pytest,celery,sqlalchemy,pydantic}.md`, `packages/db/{postgres,redis,mysql}.md`,
  all `concerns/*` (incl. `ui-ux`, `accessibility`, `observability`, `i18n`), all `devops/*`.
- **Tier 3 (skeleton + research hook):** `languages/{go,rust}.md`,
  `frameworks/{react,fastapi,flask,django,symfony,nuxt,nextjs,svelte}.md`,
  `packages/laravel/{nova,flux-ui,folio,passport,telescope}.md`. Ship the highest-value rules
  AND a `WebSearch` hook; when activated, fetch current version-specific best practice to fill
  gaps (provenance = `researched`).

## Signal table

### Manifests & lockfiles (read these first)

| File | Tells you |
|------|-----------|
| `composer.json` / `composer.lock` | PHP project; framework + packages from `require`; **installed versions from the lock** |
| `package.json` + `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` | JS/TS project; framework + packages; installed versions from lock |
| `pyproject.toml` / `requirements.txt` / `Pipfile` | Python project; deps + tool config (ruff, mypy, pytest) |
| existing `CLAUDE.md` | Prior conventions; read for context, never overwrite |
| existing `.ai/guidelines/` | Laravel Boost present — do not duplicate what it injects; cross-reference |

### Language signals → `languages/*`
| Signal | Layer |
|--------|-------|
| `*.php`, `composer.json` | `php.md` (T1) |
| `*.py`, `pyproject.toml`, `requirements.txt` | `python.md` (T1) |
| `tsconfig.json`, `*.ts`, `*.tsx` | `typescript.md` (T2) |
| `*.js`, `*.mjs`, `*.jsx` (no TS) | `javascript.md` (T2) |
| `go.mod`, `*.go` | `go.md` (T3) |
| `Cargo.toml`, `*.rs` | `rust.md` (T3) |

### Framework signals → `frameworks/*`
| Signal | Layer |
|--------|-------|
| `artisan`, `laravel/framework` in composer, `config/app.php` | `laravel.md` (T1) |
| `symfony/framework-bundle`, `bin/console` | `symfony.md` (T3) |
| `*.vue`, `vue` in package.json | `vue.md` (T2) |
| `nuxt` in package.json, `nuxt.config.*` | `nuxt.md` (T3) |
| `react`/`react-dom` in package.json | `react.md` (T3) |
| `next` in package.json, `next.config.*` | `nextjs.md` (T3) |
| `svelte`/`@sveltejs/kit` in package.json | `svelte.md` (T3) |
| `fastapi` in deps | `fastapi.md` (T3) |
| `flask` in deps | `flask.md` (T3) |
| `django` in deps, `manage.py` | `django.md` (T3) |

### Package signals (Boost-style) → `packages/*`
Walk the dependency lists and activate per matched dependency. Prefer the **installed version**.
| Dependency | Layer |
|------------|-------|
| `livewire/livewire` | `packages/laravel/livewire.md` (T2) |
| `filament/filament` | `packages/laravel/filament.md` (T2) |
| `inertiajs/inertia-laravel` (or `@inertiajs/*`) | `packages/laravel/inertia.md` (T2) |
| `pestphp/pest` | `packages/laravel/pest.md` (T2) |
| `spatie/laravel-permission` | `packages/laravel/spatie-permission.md` (T2) |
| `spatie/laravel-data` | `packages/laravel/laravel-data.md` (T2) |
| `spatie/laravel-medialibrary` | `packages/laravel/media-library.md` (T2) |
| `spatie/laravel-query-builder` | `packages/laravel/query-builder.md` (T2) |
| `laravel/sanctum` | `packages/laravel/sanctum.md` (T2) |
| `laravel/horizon` | `packages/laravel/horizon.md` (T2) |
| `laravel/passport` | `packages/laravel/passport.md` (T3) |
| `laravel/telescope` | `packages/laravel/telescope.md` (T3) |
| `laravel/nova` | `packages/laravel/nova.md` (T3) |
| `livewire/flux` / `livewire/flux-pro` | `packages/laravel/flux-ui.md` (T3) |
| `laravel/folio` | `packages/laravel/folio.md` (T3) |
| `pytest` in Python deps | `packages/python/pytest.md` (T2) |
| `celery` in Python deps | `packages/python/celery.md` (T2) |
| `sqlalchemy` in Python deps | `packages/python/sqlalchemy.md` (T2) |
| `pydantic` in Python deps | `packages/python/pydantic.md` (T2) |
| `tailwindcss` | `packages/frontend/tailwind.md` (T2) |
| `bootstrap` in package.json | `packages/frontend/bootstrap.md` (T2) |
| `alpinejs` (or `alpinejs/alpine`) | `packages/frontend/alpine.md` (T2) |
| `pinia` in package.json | `packages/frontend/pinia.md` (T2) |
| `sass`/`node-sass`, `*.scss` | `packages/frontend/sass.md` (T2) |
| `vite` in package.json, `vite.config.*` | `packages/frontend/vite.md` (T2) |

### Datastore signals → `packages/db/*`
Detect from deps (`ext-pgsql`, `psycopg`, `pg`, `predis`/`phpredis`, `redis`, `ext-mysqli`,
`mysqlclient`), `docker-compose.yml` services (`postgres`, `redis`, `mysql`/`mariadb`), or the
app's DB config (`config/database.php` default connection, `DB_CONNECTION` in `.env`).
| Signal | Layer |
|--------|-------|
| PostgreSQL (`pgsql`/`psycopg`/`postgres` service) | `packages/db/postgres.md` (T2) |
| Redis (`predis`/`phpredis`/`redis` dep or service) | `packages/db/redis.md` (T2) |
| MySQL / MariaDB (`mysql`/`mariadb` dep or service) | `packages/db/mysql.md` (T2) |

### Concern signals → `concerns/*` and base
Activate concerns by what the stack implies (a web app almost always wants error-handling,
security, testing-qa, api-design; any UI activates `ui-ux` + `accessibility`). Always consider
`base/core.md` (embeds the balance meta-rule), `base/naming.md`, `base/architecture.md`,
`base/git.md`.
| Signal | Layer |
|--------|-------|
| Any rendered UI (Blade/Vue/React/Svelte/Livewire templates) | `concerns/ui-ux.md` (T2), `concerns/accessibility.md` (T2) |
| Any service that logs / emits metrics (nearly always) | `concerns/observability.md` (T2) |
| `lang/` or `resources/lang/`, `i18n`/`vue-i18n`/`gettext`, multi-locale config | `concerns/i18n.md` (T2) |

### DevOps signals → `devops/*`
| Signal | Layer |
|--------|-------|
| `Dockerfile`, `docker-compose.yml` | `docker.md` |
| `.gitlab-ci.yml` | `gitlab-ci.md` |
| `.github/workflows/*`, `Jenkinsfile`, any CI | `ci-cd.md` |

## Directory-structure cues
- `app/Http/Controllers`, `app/Models`, `database/migrations` → Laravel, standard layout.
- `src/` with `tests/` → typical PHP/Python package layout.
- `resources/js`, `vite.config.*` → frontend build present; check for Vue/React/Inertia.
- Monorepo (`packages/*`, `apps/*`) → detect per package; rules may need per-package `globs`.

## How to add a new layer (no SKILL.md edit needed)

The skill discovers layers by convention, so extend it by adding files, not by editing `SKILL.md`.

1. **Pick the category** — `languages/`, `frameworks/`, `packages/<ecosystem>/`, `concerns/`,
   or `devops/`.
2. **Create the reference file** at that path (e.g. `frameworks/nuxt.md`, `packages/frontend/alpine.md`,
   `languages/../drupal.md`, or a `packages/db/postgres.md` for PostgreSQL conventions).
   Follow the shape of a same-tier sibling: a one-line tier marker, a short TOC if > ~300 lines,
   concrete rules with `❌/✅` pairs, and — for Tier 3 — a **research hook** section
   (`## Research hook` telling the skill what to `WebSearch` on activation).
3. **Register the detection signal** by adding a row to the relevant signal table above:
   the manifest/dependency/file marker → the new layer path.
4. **Nothing in `SKILL.md` changes** — its reference map already points at whole directories,
   and step 1's detection reads this file. New examples worth wiring in later: Drupal, Nuxt,
   Svelte, Alpine, Redis, PostgreSQL conventions.

## Research hook (Tier 3 activation)

When a Tier 3 layer is activated and its skeleton doesn't cover a needed point:
`WebSearch` for `"<tech> <installed-version> best practices <year>"`, prefer the official docs,
cross-check a second source for contested advice, then codify with provenance `researched` and
the source URL + retrieval date. Never block generation on a failed search — degrade to the
skeleton and lower confidence.

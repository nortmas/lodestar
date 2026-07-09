# GitLab CI (Tier 2)

Guidance for authoring `.gitlab-ci.yml`. Apply the balance policy: match the repo's existing stage names, cache keys, and runner tags unless a change fixes a security, correctness, or performance defect.

## Pipeline structure

- Order stages so cheap, fast-failing checks run first: `build → lint → test → deploy`. Never run an expensive deploy after a lint that could have failed in seconds.
- Use `needs:` to build a DAG so independent jobs start as soon as their dependencies finish, rather than waiting for the whole previous stage.

## Caching and artifacts

- Cache dependencies with a key derived from the lockfile, so the cache invalidates only when dependencies actually change (e.g. `key: { files: [package-lock.json] }`).
- Pass build output between stages as `artifacts` with an explicit `expire_in` — unbounded artifacts fill runner storage.

## Rules and secrets

- Use `rules:` for job conditions. `only`/`except` are deprecated and cannot express modern conditions.
- Store secrets as masked and protected CI/CD variables. Never commit secrets to the repo or echo them in job logs.

## Template

```yaml
stages: [build, lint, test, deploy]

variables:
  FF_USE_FASTZIP: "true"

# Cache invalidates when the lockfile changes
.node_cache: &node_cache
  key:
    files: [package-lock.json]
  paths: [node_modules/]

build:
  stage: build
  cache: [*node_cache]
  script:
    - npm ci
    - npm run build
  artifacts:
    paths: [dist/]
    expire_in: 1 week

test:
  stage: test
  needs: [build]          # start as soon as build finishes
  cache:
    - <<: *node_cache
      policy: pull         # test job only reads the cache
  script: npm test

deploy:
  stage: deploy
  needs: [test]
  script: ./deploy.sh      # uses masked/protected CI variables
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

## only/except vs rules

```yaml
# ❌ Bad: deprecated, limited expressiveness
deploy:
  only:
    - main
```

```yaml
# ✅ Good: rules: with explicit conditions
deploy:
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
      when: on_success
    - when: never
```

Source: best-practice · Confidence: high

# CI/CD (Tier 2)

Provider-independent pipeline principles (GitHub Actions, GitLab CI, Jenkins, CircleCI, etc.). Apply the balance policy: adopt the repo's existing tooling and conventions unless a change fixes a security, correctness, or performance defect.

## Fail fast, stay fast

- Order stages cheapest-first so a broken build never reaches the test or deploy phase. Fast feedback beats thorough-but-slow.
- Keep pipelines fast: parallelize independent jobs and cache dependencies keyed by lockfile. A slow pipeline gets bypassed or ignored.

## Reproducibility and parity

- Builds must be reproducible: pin tool and dependency versions, don't rely on ambient runner state. The same commit must produce the same artifact.
- Run the same lint, test, and format checks locally and in CI (shared scripts or a task runner). CI should confirm what a developer already saw, not surprise them.

## Release discipline

- Every merge to `main` must be releasable: gate merges on green pipelines so main is always deployable.
- Automate the quality gate on every change: lint, test, and a security/dependency scan (SAST, `npm audit`, `trivy`, etc.).
- Build an artifact once, then deploy that exact artifact through each environment. Never rebuild per environment or deploy raw source — you'd ship something that was never tested.
- Have a rollback strategy: keep the previous versioned artifact deployable, or automate revert on a failed health check. Every deploy must have an undo.

## Deploy artifact, not source

```yaml
# ❌ Bad: pulls latest source on the server and builds in place —
# unreproducible, untested, no rollback target
deploy:
  script:
    - ssh prod "cd /app && git pull && npm install && npm run build && pm2 restart app"
```

```yaml
# ✅ Good: deploy a pre-built, versioned artifact produced earlier in the pipeline
deploy:
  script:
    - VERSION=$CI_COMMIT_SHA
    - aws s3 cp "dist/app-${VERSION}.tar.gz" "s3://artifacts/app-${VERSION}.tar.gz"
    - ./deploy.sh --release "app-${VERSION}.tar.gz"   # previous version stays available for rollback
```

Source: best-practice · Confidence: high

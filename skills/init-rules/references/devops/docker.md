# Docker (Tier 2)

Guidance for authoring Dockerfiles and container images. Apply the balance policy: match the repo's established base images, stage names, and layout unless a change fixes a security, correctness, or performance defect.

## Image construction

- Use multi-stage builds: a heavy build stage (compilers, dev deps) and a slim runtime stage that copies only the built artifacts. Keeps the shipped image small and free of build tooling.
- Pick a lean runtime base (`-slim`, `-alpine`, or `distroless`) unless the app needs a full OS.
- Pin the base image by digest (`@sha256:...`) or a specific version tag. Never use `latest` — it makes builds non-reproducible and silently pulls breaking changes.
- One concern per container (one long-running process). Use an orchestrator or compose for multi-service setups, not one image running several daemons.

## Security

- Create and switch to a non-root `USER` before the entrypoint. Root in a container is root on a compromised host namespace.
- Never bake secrets into layers or `ENV` — layers are cacheable and inspectable with `docker history`. Inject secrets at runtime (env, mounted files, secret managers) or use build secrets (`--mount=type=secret`).
- Add a `HEALTHCHECK` so orchestrators can detect and restart unhealthy containers.

## Build performance

- Add a `.dockerignore` (`.git`, `node_modules`, build output, secrets) to shrink the build context and avoid leaking files.
- Order layers from least to most frequently changed: copy dependency manifests and install deps BEFORE copying application code, so a code change does not bust the dependency cache.

## Example

```dockerfile
# ❌ Bad: unpinned base, runs as root, deps reinstalled on every code change,
# build tooling shipped to production
FROM node:latest
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]
```

```dockerfile
# ✅ Good: pinned multi-stage build, cached deps, slim non-root runtime
FROM node:20.11.1-slim@sha256:abc123... AS build
WORKDIR /app
# Copy manifests first so deps are cached until they change
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20.11.1-slim@sha256:abc123... AS runtime
WORKDIR /app
ENV NODE_ENV=production
# Install only production deps
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
# Run as the built-in unprivileged user
USER node
HEALTHCHECK --interval=30s --timeout=3s CMD node healthcheck.js
CMD ["node", "dist/server.js"]
```

Source: best-practice · Confidence: high

# Release acceptance checklist

**These checks are not marked completed unless they were actually run.** Local source-only tests cannot certify a live platform.

## Locally tested

- [x] PDF signature, MIME, oversized file rejection, path-traversal filename ignored, storage cleanup.
- [x] Anonymous-session conversation and document ownership tests.
- [x] Disabled sandbox; Docker command security flags verified via test double.
- [x] Provider unavailable returns 503; streaming successes and failures have distinct `done`/`error` events.
- [x] Document-context conversation association and follow-up.
- [x] Python source compilation and 22 backend tests in supplied overlay.
- [x] React/JSX static syntax parsing (not a runtime build).

## Mandatory before making the site public

- [ ] Generate a compatible `frontend/package-lock.json`; run `npm ci`, ESLint, Vitest, Prettier and production `vite build`.
- [ ] Run `docker build` and `docker run` locally and verify actual Docker security flags, timeouts, container termination and network isolation.
- [ ] Confirm legacy actor/critic model IDs are accessible, model weights load and RTX 4060 VRAM usage stays within 8GB, including Pro revision.
- [ ] Benchmark HF Gradio ZeroGPU function duration on real quota, including cold start, multi-user queue and error paths.
- [ ] Configure Neon pooled `DATABASE_URL` and smoke-test persistent chat and document retrieval after a Render restart.
- [ ] Deploy Render Free, verify `/health` and strict CORS for Netlify origin only, then test 429 and 413 production errors.
- [ ] Deploy the actual HF Space and verify server-side token/Space permissions, response schema and stream ordering.
- [ ] Deploy Netlify from branch; verify `VITE_API_BASE_URL` in production and mobile/desktop UX.
- [ ] Run Playwright + axe accessibility audit, manually keyboard test dialog/drawer and check WCAG AA in both themes.
- [ ] Verify real research citations separately before presenting the research workspace as source-grounded.
- [ ] Add proper user identity, privacy notice, retention period and cleanup policy before accepting other people's documents.
- [ ] Configure DB migrations/backup strategy, distributed rate limit if scaling, dependency security scanner and operational metrics.
- [ ] Update UI screenshot placeholders with actual release screenshots.
- [ ] Enable/reconnect GitHub write access and open a pull request; review its complete diff against main.

## Breaking change disclosure

API endpoints require `X-PACE-Session`. Literacy mode associates uploaded document IDs with conversations. `/generate` now produces real incremental SSE frames (and error frames after response headers), while `/predict` returns complete JSON. The local code runner no longer executes on host Python and requires explicit local Docker opt-in. Existing unscoped database consumers and old frontend integration code must be migrated. SQLite table evolution is not handled through Alembic in this package; start with a fresh dev DB or introduce migrations for existing data.

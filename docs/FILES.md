# Phase 2 deliverable: every changed or new file

Each path below is a **full source/configuration file**, not a snippet. This is an overlay against the original PACE GitHub repo.

| Path | Reason |
|---|---|
| `.env.example` | Safe configuration examples, with no embedded service credentials. |
| `.github/workflows/ci.yml` | Python 3.10/3.11 test jobs and frontend lint/unit/build jobs. |
| `.gitignore` | Excludes credentials, model binaries, caches, uploads and SQLite files. |
| `.pre-commit-config.yaml` | Ruff, Black-on-demand and standard hygiene hooks. |
| `PATCH_README.md` | Safe application procedure and breaking-change notice. |
| `README.md` | Honest feature table, architecture, local setup, tests, API and limits. |
| `ai-service/README.md` | HF Space metadata and explicit no-independent-critic disclosure. |
| `ai-service/app.py` | HF ZeroGPU Gradio generator, real pretrained model and optional review pass. |
| `ai-service/requirements.txt` | HF Space runtime libraries and version constraints. |
| `backend/__init__.py` | Package/namespace initializer; keeps original module imports functional. |
| `backend/main.py` | API lifespan, CORS restrictions, rate limiting and safe exception handling. |
| `backend/pace.db` | Supporting project configuration and integration file. |
| `backend/request_limits.py` | ASGI ingress Content-Length and streaming multipart body ceiling. |
| `backend/requirements.txt` | Bounded lean hosting dependencies without forcing PyTorch onto Render. |
| `core/__init__.py` | Package/namespace initializer; keeps original module imports functional. |
| `core/config.py` | Strict env-validated settings for all providers, resource bounds and isolation. |
| `core/sandbox/__init__.py` | Package/namespace initializer; keeps original module imports functional. |
| `core/sandbox/executor.py` | Opt-in Docker runner, AST import constraints, OS limits and timeout cleanup. |
| `docker-compose.yml` | Local API/frontend containers with persistent SQLite volume. |
| `docs/AUDIT_MATRIX.md` | Sixteen original audit issue IDs mapped to fixes and remaining checks. |
| `docs/DEPLOYMENT.md` | Detailed Netlify/Render/HF/Neon deployment and environment tables. |
| `docs/DESIGN_SPEC.md` | Both color palettes, design tokens, spacing, typography and states. |
| `docs/FILES.md` | Complete delivered file inventory and one-line rationale. |
| `docs/RELEASE_CHECKLIST.md` | Verified scope, mandatory release tasks and breaking changes. |
| `frontend/.prettierrc` | Prettier formatting policy. |
| `frontend/Dockerfile.frontend` | Frontend build and static Nginx runtime. |
| `frontend/eslint.config.js` | React Hooks lint rules and unused variable checks. |
| `frontend/index.html` | SPA entry document. |
| `frontend/nginx.conf` | Docker production static server with /api proxy and safe headers. |
| `frontend/package.json` | Bounded React/Vite dependencies and build/test/lint scripts. |
| `frontend/src/App.jsx` | Redesigned responsive workspaces, real states, chat, PDF, optional code runner. |
| `frontend/src/ThemeContext.jsx` | Persisted system/light/dark mode support. |
| `frontend/src/__tests__/api.test.js` | Vitest contracts for stream completeness and truthful error behavior. |
| `frontend/src/__tests__/setup.js` | DOM testing utilities setup. |
| `frontend/src/__tests__/ui.test.jsx` | Vitest accessibility semantics of key reusable controls. |
| `frontend/src/components/ui.jsx` | Button, Card, Input, Tabs, Modal, Toast, Skeleton, Badge and Tooltip. |
| `frontend/src/lib/api.js` | API base URL, opaque session token, retries, actual streamed SSE events. |
| `frontend/src/main.jsx` | React theme provider mount. |
| `frontend/src/styles.css` | Light/dark semantic tokens, component styling, responsive layout and reduced motion. |
| `frontend/vite.config.js` | Local API rewrite and bundle splitting. |
| `infra/docker/Dockerfile.backend` | Least-privilege Python container for API. |
| `infra/docker/Dockerfile.sandbox` | Minimal sandbox Python image. |
| `masteries/api/router.py` | Session-owned routes, document association, real SSE stream and truthful errors. |
| `masteries/api/schemas.py` | Validated FastAPI input and response contracts. |
| `masteries/coding/inference/v4_orchestrator.py` | Supporting project configuration and integration file. |
| `masteries/literacy/inference/v4_orchestrator.py` | Supporting project configuration and integration file. |
| `masteries/research/inference/v4_orchestrator.py` | Supporting project configuration and integration file. |
| `masteries/services/__init__.py` | Package/namespace initializer; keeps original module imports functional. |
| `masteries/services/ai_gateway.py` | HF streaming adapter with real model output and no simulated fallback. |
| `masteries/services/database.py` | SQLAlchemy SQLite/Postgres persistence and scoped documents/conversations. |
| `masteries/services/local_ensemble.py` | Original local actor/critic adapters, requiring independent critique in Review mode. |
| `masteries/services/ollama_provider.py` | Real local CPU/GPU Ollama HTTP streaming and labeled same-model review. |
| `masteries/services/retrieval.py` | Bounded keyword PDF context retrieval; no invented citation engine. |
| `masteries/services/tokenization.py` | Optional Rust extension, explicit Python approximate fallback. |
| `masteries/services/upload_service.py` | UUID PDF ingestion and bounded MuPDF extraction in a worker thread. |
| `netlify.toml` | Netlify SPA build, redirects and response headers. |
| `pytest.ini` | Backend test configuration. |
| `render.yaml` | Free API blueprint with secret environment placeholders. |
| `requirements-dev.txt` | Pytest, HTTPX, Ruff and Black development dependencies. |
| `requirements-local-ai.txt` | Optional native actor/critic Transformers and PyTorch dependencies. |
| `tests/test_inference_contracts.py` | Streaming success/failure, attached document, model snapshot and ingress tests. |
| `tests/test_security_api.py` | Upload, tenant isolation, rate limit, CORS and disabled Docker tests. |

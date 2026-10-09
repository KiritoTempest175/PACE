# PACE Phase 2 — audit finding remediation matrix

**Baseline:** 1 Critical, 5 High, 8 Medium, 2 Low. These IDs are preserved from the Phase 1 PACE audit. “Addressed in code” is not the same as a verified production release. The original upstream repository is unchanged because GitHub branch creation returned a permission error.

| ID | Finding | Status | Resolution file(s) and evidence |
|---|---|---|---|
| C1 | PDF upload path traversal | Addressed; tested | `masteries/services/upload_service.py`: UUID paths, resolved containment, MIME and magic checks, parse verification and deletion; `tests/test_security_api.py` |
| H1 | Host code execution falsely described as a sandbox | Mitigated; Docker not exercised | `core/sandbox/executor.py`: disabled in production/default, Docker-only, no host volumes/network/caps, read-only, limits and timeout cleanup; AST import gate; `tests/test_security_api.py` mocks Docker command. Requires actual adversarial container evaluation. |
| H2 | Conversation ownership missing | Mitigated; no identity accounts | `masteries/api/router.py`, `masteries/services/database.py`: random bearer capability and owner-scoped CRUD, document links; tests exercise cross-session isolation. Not user authentication; stolen browser token confers access. |
| H3 | Unbounded uploads / expensive generation | Partially addressed | `backend/request_limits.py`, `upload_service.py`, `backend/main.py`, `ai-service/app.py`: body/file/page/text bounds, throttling, model token/quota caps. Per-IP limiter is process-local and needs production load tests/edge WAF. |
| H4 | Frontend production API requests misrouted | Configured; unverified live | `frontend/src/lib/api.js`, `netlify.toml`, `frontend/nginx.conf`: explicit API base URL for Netlify and local `/api` proxy. Deployed URL must be provided through `VITE_API_BASE_URL`. |
| H5 | Fabricated “Critic Verified” and fallback code | Addressed along wired paths; integration unverified | `masteries/services/ai_gateway.py`, `local_ensemble.py`, `ollama_provider.py`, `masteries/*/inference/v4_orchestrator.py` and `masteries/api/router.py`: strict provider results, no fake code, no false approval. Provider failures become 503 or SSE `error`. Local models not run on GPU in this delivery. |
| M1 | Extension-only PDF validation | Addressed; tested | `upload_service.py`: MIME, magic and full MuPDF parse checks |
| M2 | PDF processing errors returned as success | Addressed; tested | `upload_service.py`, `masteries/api/router.py`: explicit 400/413 on malformed/oversize PDF |
| M3 | `/predict` leaks model/server errors | Addressed; tested | `masteries/api/router.py`, `ai_gateway.py`: generic 503 and safe logs |
| M4 | In-process lock cannot coordinate multiple workers | Mitigated, scale limitation | `ai-service/app.py` serialized Gradio queue, `render.yaml` one worker. Distributed lock/job scheduler still missing for horizontal scaling. |
| M5 | Repeated SQLite initialization and DB overhead | Addressed in code | `masteries/services/database.py`: shared engine and connection pooling, startup table init, Postgres switch. Alembic migrations still needed for existing populated schema changes. |
| M6 | CI, security and API testing gaps | Partially addressed | `.github/workflows/ci.yml`, `tests/test_security_api.py`, `tests/test_inference_contracts.py`, `frontend/src/__tests__/`: 22 local backend tests pass; JS browser/build/CI run not verified. |
| M7 | “latest” and unrepeatable dependency installs | Partially addressed | `frontend/package.json` bounded ranges; `backend/requirements.txt` bounded ranges. The original `frontend/package-lock.json` is incompatible; generate and commit a replacement on a networked machine. |
| M8 | Inaccessible or generic UI | Implemented, browser audit pending | `frontend/src/App.jsx`, `styles.css`, `ThemeContext.jsx`, `components/ui.jsx`: semantic controls, theme tokens, responsive layout, dialog focus trap, reduced motion. Screen reader and real-device WCAG audits outstanding. |
| L1 | Missing env/config sample | Addressed | `.env.example`, `render.yaml`, `docs/DEPLOYMENT.md` |
| L2 | README promises unsupported features | Addressed in documentation | `README.md`, `ai-service/README.md`, `docs/DEPLOYMENT.md` explicitly distinguish local critic versus cloud single model, and experimental research without sources. |

## Release blockers

- **GitHub write access:** The connected GitHub integration returned `403 Resource not accessible by integration` when creating a branch. No pull request or push could be made.
- **Vite install/build:** npm registry access unavailable in the execution environment. Source files are provided but JS tests, ESLint, actual browser rendering, and lockfile generation are **not** verified.
- **External hosting:** Real accounts/secrets/deployment are not configured here; no HF GPU quota/Render cold-start/Netlify smoke tests ran.
- **ML claims:** The original actors, critics and RTX 4060 footprint have not been re-trained, benchmarked or run. Hosted review is a **same-model** second pass.
- **Security & compliance:** No adversarial Docker test, penetration test, content moderation policy, multi-user auth, automatic data retention policy, database migrations, dependency vulnerability scanner output, or operational monitoring verification.

## Conservative classification for this delivery

| Category | Total | Addressed in code/docs | Mitigated or configured pending verification | Partial |
|---|---:|---:|---:|---:|
| Critical | 1 | 1 | 0 | 0 |
| High | 5 | 1 | 3 | 1 |
| Medium | 8 | 3 | 2 | 3 |
| Low | 2 | 2 | 0 | 0 |
| **Total** | **16** | **7** | **5** | **4** |

These numbers classify remediation implementations, **not verified production closure**.

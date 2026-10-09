# Three-platform deployment guide (October 2026)

These are manual, account-authorized steps. No services were deployed by this patch. Avoid placing tokens in Vite variables; all `VITE_*` values are publicly visible in the browser bundle.

## 1. Persistent database — Neon

1. Create a Neon Free project and a dedicated database for PACE.
2. In Neon, copy the **pooled** PostgreSQL connection URI (TLS enabled).
3. Store it in Render's `DATABASE_URL` secret. The SQLAlchemy driver must be `psycopg`, so use a URI with the scheme `postgresql+psycopg://` while keeping the credentials, host, port, database and query parameters provided by Neon.
4. The FastAPI startup creates the initial tables. This bootstrap is convenient for a portfolio demo but is not a substitute for Alembic migrations on a long-lived service.
5. Do not use Render's ephemeral SQLite file in production. Store no model weights or PDFs in PostgreSQL; only small extracted PDF text and chat messages are persisted.

At the time of writing Neon Free lists 1 GB storage per project and 100 CU-hours/month. Plan cleanup so generated study text does not exceed capacity.

## 2. Hugging Face ZeroGPU Space

1. Ensure your account is eligible to host a free ZeroGPU Space; check the current Hugging Face requirements (verified email, account age, Space limits).
2. Create a **Gradio** Space and select ZeroGPU hardware. The Space must support API access to the backend; prefer a **private** Space with an HF read token if available to your account.
3. Copy `ai-service/app.py`, `ai-service/requirements.txt` and `ai-service/README.md` to the Space repository root (rename the latter to its root `README.md`).
4. Optionally set `PACE_MODEL_ID` to a compatible small public instruction model. The default is `Qwen/Qwen2.5-0.5B-Instruct`.
5. Build the Space and test its public/authorized Gradio API endpoint named `/generate` from the Space's **Use via API** page. The API expects `(prompt, mode, speed, max_new_tokens)` and **streams increasing complete strings** in Fast mode; Review returns its final response.
6. Create a fine-grained token permitted to read the Space. Store it **only** in Render's secret `HF_TOKEN`, never in Netlify variables. Set `HF_SPACE_ID` in Render to the actual `namespace/name` Space ID.
7. Check logs and daily ZeroGPU remaining quota. The app requests short GPU time slices (35s fast, 55s Review) and queues jobs with concurrency one; benchmark slice durations and account quotas on your own hardware. Quota exhaustion results in HTTP 503 from the API rather than fabricated output.

This Space uses **one** pretrained model, with optional same-model second-pass review; fast mode streams actual model progress. No research web browsing or independently trained Critic is included. ZeroGPU requires Gradio and compatible PyTorch/Python versions. Account quotas may be exhausted even when Render is healthy.

## 3. Render Free web service

1. Connect the original GitHub repository after applying these files.
2. Choose the Render Blueprint option using repository root `render.yaml`, or create a Python web service manually.
3. Configure: root `.`; build `pip install -r backend/requirements.txt`; start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1`; plan **Free**; health check `/health`.
4. Set secrets/config exactly as below. Deploy and verify `https://YOUR-SERVICE.onrender.com/health` returns `status=healthy`.
5. The health endpoint describes API process readiness. `ai_configured` indicates configuration, not successful model evaluation.

| Render variable | Value | Secret? |
|---|---|---|
| `ENVIRONMENT` | `production` | No |
| `DATABASE_URL` | Neon pooled SQLAlchemy Postgres URL | **Yes** |
| `CORS_ORIGINS` | `https://pace-ensemble.netlify.app` | No |
| `AI_PROVIDER` | `huggingface` | No |
| `HF_SPACE_ID` | Your actual Space ID | No |
| `HF_TOKEN` | Fine-grained HF token | **Yes** |
| `AI_TIMEOUT_SECONDS` | `90` | No |
| `MAX_UPLOAD_BYTES` | `8388608` | No |
| `MAX_PDF_PAGES` | `80` | No |
| `RATE_LIMIT_PER_MINUTE` | `30` | No |
| `SANDBOX_ENABLED` | `false` | No |
| `TOKENIZER_BACKEND` | `python` | No |

Render Free may spin down after 15 minutes idle and stores no persistent local files. Cold starts may take about a minute. PACE performs exponential-backoff health retries in the frontend. Constant synthetic keep-alive pings are **not** configured, to avoid wasting free-tier instance hours.

## 4. Netlify frontend

1. Configure GitHub continuous deployment of the same repository (or replace the existing site's source branch with the patched source).
2. Use the root `netlify.toml`; it selects base directory `frontend`, `npm ci --no-audit --no-fund`, publish directory `dist`, SPA rewrite and security headers.
3. Set `VITE_API_BASE_URL=https://YOUR-SERVICE.onrender.com` using the actual Render URL. Include the scheme; omit the trailing slash and `/api` path.
4. Redeploy `pace-ensemble.netlify.app`. Verify that requests originate from the expected domain and include `X-PACE-Session`.
5. Ensure the Render `CORS_ORIGINS` exactly matches the browser origin. Preview deploys use other origins and will be rejected until added deliberately.

| Netlify variable | Value | Secret? |
|---|---|---|
| `VITE_API_BASE_URL` | Public Render base URL | No — browser-visible |

Never set `HF_TOKEN` or `DATABASE_URL` in Netlify.

## 5. Local development / local GPU

Create `.env` from `.env.example`. Choose one of:

| Profile | Values | Notes |
|---|---|---|
| API-only | `AI_PROVIDER=disabled` | CRUD/PDF works; generation yields real 503 |
| Local CPU | `AI_PROVIDER=ollama`, `OLLAMA_BASE_URL=http://127.0.0.1:11434` | Install Ollama and pull the model selected with `OLLAMA_MODEL`; API streams actual model tokens |
| RTX 4060 | `AI_PROVIDER=local` | Install `requirements-local-ai.txt` with CUDA PyTorch and original weights; actor+critic may exceed 8 GB; benchmark and use lower-memory model choices if needed |
| Remote inference | `AI_PROVIDER=huggingface` | Supply HF Space ID/token |
| Optional Docker sandbox | `ENVIRONMENT=development`, `SANDBOX_ENABLED=true` | **Only** where Docker CLI and daemon are installed; builds `pace-sandbox:local` from `infra/docker/Dockerfile.sandbox` |

Build sandbox image locally with `docker build -f infra/docker/Dockerfile.sandbox -t pace-sandbox:local .`. Docker Compose intentionally does not expose host Docker to its API container, so the sandbox feature is not enabled there.

**Rust:** The original PACE repository inspected for this patch does not contain a working PyO3 tokenizer implementation. `TOKENIZER_BACKEND=rust` attempts to load an optional native extension and falls back to approximate Python splitting with a warning; actual HF inference uses the model tokenizer. Native parity is not claimed.

## 6. Post-deployment checklist

- [ ] Render health returns healthy, and Netlify reports connected after cold start.
- [ ] One browser session creates chats; an unrelated session cannot read/delete them.
- [ ] Upload a legitimate PDF and verify a `document_id`; delete it afterward.
- [ ] Reject a disguised PDF, oversized PDF, and unsafe filename without leaving files on disk.
- [ ] Literacy mode refuses questions before a document is uploaded.
- [ ] Hugging Face model call returns actual model output; disabled/exhausted model returns an error.
- [ ] Confirm page reload retains your session token and conversations.
- [ ] Verify Render restart preserves history in Neon.
- [ ] Check light/dark contrast, keyboard interactions, reduced-motion, mobile and screen-reader states in a real browser.
- [ ] Generate and commit `frontend/package-lock.json` after an online `npm install` and convert build jobs to `npm ci`.
- [ ] Use a dependency scanner and verify no third-party secrets have been committed.
- [ ] Verify production monitoring, log retention and data deletion policy before accepting real documents.

## 7. Complete platform environment matrix

| Service | Setting | Value / treatment |
|---|---|---|
| **Netlify** | `VITE_API_BASE_URL` | `https://YOUR-RENDER-SERVICE.onrender.com`; public, no `/api` suffix |
| **Netlify** | Build base / command / publish | `frontend` / `npm install && npm run build` / `dist` |
| **Render** | `ENVIRONMENT` / `AI_PROVIDER` | `production` / `huggingface` |
| **Render** | `DATABASE_URL` | Secret pooled Neon URI using SQLAlchemy `postgresql+psycopg://` |
| **Render** | `HF_SPACE_ID` | Space repo ID, for example `owner/pace-ai` (replace with actual ID) |
| **Render** | `HF_TOKEN` | Secret HF read token; never in source or Vite environment |
| **Render** | `CORS_ORIGINS` | `https://pace-ensemble.netlify.app` |
| **Render** | `PYTHON_VERSION` | `3.11.11` per Blueprint |
| **Render** | `AI_TIMEOUT_SECONDS` / `MAX_NEW_TOKENS` | `90` / `128` (tune within quotas) |
| **Render** | `SANDBOX_ENABLED` | `false` |
| **HF Space** | `PACE_MODEL_ID` | `Qwen/Qwen2.5-0.5B-Instruct` default (public model) |
| **HF Space** | SDK / hardware / Python | `Gradio` / eligible `ZeroGPU` / `3.10.13` |
| **Local** | `AI_PROVIDER` | `disabled`, `ollama`, `local`, or `huggingface` |
| **Local** | `OLLAMA_BASE_URL` | Local Ollama URL, e.g. `http://127.0.0.1:11434` |
| **Local** | `OLLAMA_MODEL` | Installed local Ollama model ID |
| **Local** | `SANDBOX_ENABLED` | `false` by default; enable only trusted local development with Docker |

The original upstream `frontend/package-lock.json` is for a different manifest. Regenerate it in a networked environment, commit it, and only then switch builds to `npm ci`. Do **not** upload credentials into repository files or a public Gradio app.

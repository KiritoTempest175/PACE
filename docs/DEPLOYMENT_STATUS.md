# PACE Phase 2 — deployment status

Last updated: 2026-10-09.

This document distinguishes verified work from setup that still requires authorization or a browser-based deployment.

| Component | Actual state | Verified source |
| --- | --- | --- |
| GitHub Phase 2 branch | Pushed to `phase2/production-hardening-20261009` | GitHub commit history |
| CI | Python tests, Ruff, frontend lint/test/Vite build tested on GitHub Actions with committed lockfile | GitHub Actions |
| Render Phase 2 API | Running at https://pace-phase2-api.onrender.com | Render deployment state and startup logs |
| Neon Postgres | Project `long-pond-11147838` / database `pace` in Oregon; DB URL configured only in Render | Neon table listing |
| Neon schema | `conversations`, `messages`, `documents`, `conversation_documents` created | Neon database schema |
| Netlify | Existing https://pace-ensemble.netlify.app remains unchanged | Netlify published-deploy metadata |
| Hugging Face | Existing https://huggingface.co/spaces/Kiritox07/pace remains unchanged; new Space code is in `ai-service/` | Hugging Face repository metadata |

## Boundaries and next steps

- The Render service is a **staging** API with `AI_PROVIDER=disabled`; its CRUD and PDF functionality can use persistent Neon storage, but no hosted model inference has been verified.
- To deploy the frontend, connect the existing Netlify project to `KiritoTempest175/PACE` using the Phase 2 branch first. The repository `netlify.toml` now supplies the public Render API URL and uses `npm ci`. Keep the existing production deployment unchanged until testing succeeds.
- To deploy the AI service, upload `ai-service/app.py` and `ai-service/requirements.txt` into the Hugging Face Space root and provide the correct Space README. Verify model runtime/ZeroGPU eligibility and test the actual Gradio endpoint before enabling `AI_PROVIDER=huggingface` on Render.
- The connected Hugging Face OAuth session currently has read-only repository scopes; its available tools cannot upload Space files. The Netlify connector has no deploy/Git-link action.
- Never expose `DATABASE_URL` or `HF_TOKEN` in GitHub, Netlify browser variables, or documentation.
- Session tokens are anonymous bearer credentials, not registered user authentication. Apply the release checklist before handling sensitive documents.

## Review

- Draft pull request: https://github.com/KiritoTempest175/PACE/pull/1
- Existing backend retained at https://pace-backend-5g2x.onrender.com
- Phase 2 backend: https://pace-phase2-api.onrender.com

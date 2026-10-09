# PACE Desktop — separate experimental branch

This folder accompanies the Tauri v2 Windows client under `frontend/src-tauri/`.
It is intentionally isolated on `feature/tauri-desktop`, not the web production branch.

## What works

- The same PACE React UI, packaged as a Windows WebView2 desktop app
- Coding, Literacy PDF uploads, Research and persisted conversations through a chosen PACE API
- Choose **Hosted API** (`https://pace-phase2-api.onrender.com`) or **Local API** (`http://127.0.0.1:8000`) in Preferences
- Theme preference and anonymous per-endpoint conversation session

The client **does not embed Python, model weights, Ollama or a Docker sandbox**.
Hosted mode needs Internet and the hosted service's free GPU quota. Local mode
requires the user to install and run the backend and an inference provider; it
can work without Internet once local dependencies and model weights are available.
Changing endpoints stores a separate conversation-session token per endpoint.

## Build on Windows

Install Node.js 22, Rust stable, Visual Studio C++ Build Tools and WebView2.
From the repository root:

```powershell
cd frontend
npm ci
npx --yes @tauri-apps/cli@2.12.1 icon src-tauri/icons/icon-source.svg
npx --yes @tauri-apps/cli@2.12.1 dev
npx --yes @tauri-apps/cli@2.12.1 build --bundles nsis
```

Output: `frontend/src-tauri/target/release/bundle/nsis/*-setup.exe`.
A Windows executable cannot be built by simply renaming the web build.
Windows SmartScreen might warn about an unsigned community-built installer.

## Run a local backend

From the repository root in a second terminal, create a virtual environment,
install `backend/requirements.txt`, copy `.env.example` to `.env`, and set:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./backend/pace.db
CORS_ORIGINS=http://tauri.localhost,https://tauri.localhost,http://localhost:5173
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
SANDBOX_ENABLED=false
```

Start Ollama locally and pull the matching model, then run:
`uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
In desktop **Preferences**, select **Local** and save the API endpoint
`http://127.0.0.1:8000`. This is a user-operated service, not one
automatically installed with the desktop app.

## GitHub release workflow

The Windows GitHub Actions workflow `.github/workflows/desktop-release.yml`
builds a signed-*none* NSIS `.exe`, tests the React project and publishes a
**draft GitHub Release** with installer and source packages. It is triggered
only by the desktop release request marker, so desktop releases are separate
from normal web CI. Review the draft release before publishing.

Source code for any tag is also automatically available from GitHub as a
ZIP/tarball. Contributors can fork this branch and edit React or Rust.
The repository is licensed under MIT; review all third-party model/dataset
licenses separately.

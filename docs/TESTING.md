# PACE v0.1.0-rc1 — manual test checklist

Release source: web from `main`, desktop from `feature/tauri-desktop`. **This is a release candidate, not a verified production build.** Report failing steps with OS, screenshot, selected model, error message, and relevant logs. Do not paste API keys or personal PDF content into bug reports.

## Data boundaries and test setup

- **Local web test bundle**: `PACE_Web_Test_dist.zip` was compiled with `VITE_API_BASE_URL=http://127.0.0.1:8000`; it calls a FastAPI server running on your own PC, **not Render or production data**. Set `CORS_ORIGINS=http://127.0.0.1:4173,http://localhost:4173,http://localhost:5173` in local `.env`; `DATABASE_URL=sqlite:///./backend/pace-rc1-test.db` keeps test data in your checkout.
- **Web custom provider**: Browser BYOK calls the selected remote provider directly (never through the PACE backend); an external provider still receives your prompt. Keys are held in browser memory for that tab, not stored durably. Provider CORS restrictions may prevent use.
- **Desktop**: Choose the bundled **Local** backend and Ollama for locally processed prompts/PDFs; selecting **Cloud** sends prompts to the configured remote service. Model downloads and app updates still use the network. Desktop keys use OS keychain where available, not the backend.
- **Never point your test copy at** `https://pace-phase2-api.onrender.com` **if you want to avoid existing hosted data**. The public production web app uses a separate configured backend. If you change the local test URL, explicitly inspect the network tab and identify the actual destination.

## Test the web release candidate using built dist

1. Download `PACE_Web_Test_dist.zip` from the v0.1.0-rc1 GitHub pre-release. Install Python 3.10+, Node 22+, and, optionally, Ollama (for local inference).
2. Clone the web source and create local test environment:
   ```bash
   git clone --branch main https://github.com/KiritoTempest175/PACE.git
   cd PACE
   cp .env.example .env
   ```
   Edit `.env`: set `DATABASE_URL=sqlite:///./backend/pace-rc1-test.db`, `CORS_ORIGINS=http://127.0.0.1:4173,http://localhost:4173,http://localhost:5173`, and `AI_PROVIDER=ollama` with `OLLAMA_MODEL` naming an installed Ollama model. If Ollama is unavailable, use `AI_PROVIDER=disabled`; pages, CRUD and PDFs still work, but generation will correctly report unavailable.
3. Activate the venv and run the API (first terminal):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
   Windows PowerShell alternative for activation: `.venv\Scripts\Activate.ps1`.
4. Unzip `PACE_Web_Test_dist.zip` **directly inside `frontend/dist/`**, so `frontend/dist/index.html` exists. Start the static preview in a second terminal:
   ```bash
   cd frontend
   npm ci
   npm run preview -- --host 127.0.0.1 --port 4173
   ```
5. Open **http://127.0.0.1:4173**. Confirm the browser Network panel sends API requests to **http://127.0.0.1:8000**. No Netlify, Render or Hugging Face deployment is required for this test.
6. If the asset is unavailable, compile the same local-only web build from `main` in `frontend`: `VITE_API_BASE_URL=http://127.0.0.1:8000 npm run build` (PowerShell: `$env:VITE_API_BASE_URL='http://127.0.0.1:8000'; npm run build`), then run `npm run preview -- --host 127.0.0.1 --port 4173`.

## Web and desktop acceptance checks

- [ ] Dashboard loads on first opening; **no blank page**; system status and recent sessions are visible. Verify no horizontal page scroll at phone widths 320 / 375 px and desktop widths 1024 / 1440 px; tablet 768 px.
- [ ] At phone width, hamburger opens a drawer; Tab/Shift+Tab remain inside; Escape closes it; logo returns to Dashboard.
- [ ] Open `/docs` and `/privacy`; enter a nonexistent URL (e.g. `/test-404`) and follow Return to dashboard.
- [ ] Coding: enter a **long** multi-part coding request; check no silent input truncation (oversized input must report a context-budget error). Check output indicates completion or shows an error/Continue option rather than silently stopping.
- [ ] Coding: obtain a fenced code block, confirm language and filename if provided, syntax highlighting, **Copy / Copied** feedback, Wrap toggle, and Download.
- [ ] Literacy: upload a **non-sensitive** PDF, ask a multi-part question, verify answer coverage or explicit insufficient-context/error behavior; delete the document afterwards.
- [ ] Toggle Fast and Pro; verify active version and Actor/Critic indicators, and compare outputs. Pro may review using the same model, not an independent verifier.
- [ ] Models: add a custom provider name, base URL and model ID; enter API key; Test connection where CORS permits. Confirm key is masked and no PACE backend requests carry it. Delete key, then reload and verify no saved browser secret.
- [ ] Settings: Delete my data and verify session conversations/document records are cleared; check reloading does not restore deleted data.
- [ ] Trigger network/API failures and confirm clear error and retry/Continue states without losing all partial output.
- [ ] Inspect browser console for uncaught exceptions, broken links, missing image/icon assets, and accessibility/keyboard defects.

## Desktop-only checks

- [ ] Verify app icon and window title; install, launch and uninstall the unsigned Windows NSIS installer, macOS DMG or Linux AppImage/DEB.
- [ ] Windows: verify bundled API starts without separately installing Python/Node/Rust; use current-user installer.
- [ ] macOS: use **right-click → Open** to accept the unsigned build if blocked, then verify local backend starts. A Gatekeeper bypass is at the user's discretion.
- [ ] Linux: use a graphical application menu or `./PACE*.AppImage` after `chmod +x` (FUSE may be required), or `sudo apt install ./PACE*.deb`. Test an available Secret Service keyring.
- [ ] Choose **Local** and **Cloud** explicitly; read the on-screen active data destination before submitting sensitive data.
- [ ] Rescan installed models: Ollama list, LM Studio, Hugging Face cache and common GGUF paths; verify displayed size, format and quantization. Scanning a GGUF/safetensors file **does not make it executable**.
- [ ] **Ollama**: install/start Ollama; download/select an Actor and optional Critic in Desktop Models; test Fast and Pro generation offline after models are present.
- [ ] **Non-Ollama local runtime**: confirm the UI says **unsupported** for direct GGUF/safetensors rather than claiming it works. This release does not include verified direct loading.
- [ ] **API key**: enter a key for a configured provider and verify the OS keychain stores it; check masked display, deletion and persistence only where intended; test that no key is logged or sent to PACE's hosted backend.

## Report an issue

Open [PACE GitHub Issues](https://github.com/KiritoTempest175/PACE/issues). Include OS/build asset, steps, expected vs actual behavior, anonymized logs, and screenshots. Never include tokens, raw prompts containing sensitive content, or private PDF data. Project contact: huzaifazaman38@gmail.com.

# PACE v0.1.0-rc1 — Desktop + web test candidate

**Pre-release:** this build is intentionally marked **pre-release**, unsigned, and **not** a stable/latest release. Install only if you trust the source. No production Netlify or Render deployment is part of this release.

## What's new
- A cyberpunk dashboard for Coding and PDF Literacy, responsive navigation, system/provider status, Docs and Privacy routes, and a custom 404.
- Fast (one generation pass) and Pro (additional review where supported), plus best-effort Actor/Critic stage indicators and partial-output recovery.
- Coding responses with code-block copy/wrap/download and a local browser Python WebAssembly runner; PDF Literacy with session-based document ingestion.
- Web custom model entry for compatible remote providers, browser-only in-memory BYOK, connection test, key deletion and explicit Local/Cloud indication.
- Desktop local FastAPI/SQLite sidecar, Ollama onboarding, Actor/Reviewer model selection, local installed-model scans, and Tauri OS-keychain integration where available.
- A local-only web **test** build, `PACE_Web_Test_dist.zip`, compiled from `main` with `VITE_API_BASE_URL=http://127.0.0.1:8000`.
- SHA256 checksums for every attached binary/ZIP asset.

## Downloads and installation

Download only the assets **actually attached** to this pre-release. Assets are produced independently; an unavailable platform is not supported by this candidate.

| OS | Asset | Install |
| --- | --- | --- |
| Windows x64 | `*.exe` (NSIS setup) | Run the installer; SmartScreen may warn for an unsigned app. Verify the checksum first. |
| macOS | `*.dmg` | Mount DMG, copy PACE into Applications. This build is **unsigned/unnotarized**; if blocked, **right-click → Open** and approve only if you trust the source. |
| Linux | `*.AppImage` | `chmod +x PACE*.AppImage && ./PACE*.AppImage`. Some distributions need FUSE compatibility libraries. |
| Debian/Ubuntu Linux | `*.deb` | `sudo apt install ./PACE*.deb` or install via the system package manager. |
| Web (isolated local test) | `PACE_Web_Test_dist.zip` | Follow [docs/TESTING.md](https://github.com/KiritoTempest175/PACE/blob/main/docs/TESTING.md) for backend and static preview commands. |

Compare downloaded file SHA256 against `SHA256SUMS.txt`:

```bash
sha256sum -c SHA256SUMS.txt
```
Windows PowerShell for a single file: `Get-FileHash .\PACE-Installer.exe -Algorithm SHA256` and compare to `SHA256SUMS.txt`.

## Connecting an AI model

**Ollama (supported local desktop runtime):** Open Models / Preferences → Manage Ollama & models. Install/start Ollama if needed, click Refresh/Rescan, then download or select an Actor (Generator) and optional Critic (Reviewer). Fast uses the Actor; Pro performs a review stage if a Reviewer is correctly configured. Default lightweight models include `qwen2.5-coder:1.5b` (Actor) and `qwen2.5-coder:3b` (Reviewer). Model files are not bundled; downloading requires an internet connection. After downloading, local Ollama inference need not contact the hosted PACE API when **Local** is selected.

**Non-Ollama local models:** Rescan can discover files under Ollama, LM Studio, Hugging Face cache and common GGUF folders. **Direct GGUF/safetensors model inference is not supported or verified in rc1.** Use Ollama to serve a compatible local model; do not assume that finding a file makes it runnable. There is no verified native non-Ollama backend selector.

**Remote provider / BYOK:** Open Models → Add custom model. Enter a friendly name, provider, base URL where required, model ID and API key; choose Test connection (can incur provider charges). Browser-direct keys live only in page memory and requests go straight to the chosen provider. In desktop builds, OS-keychain integration exists but requires testing for the target platform. If a browser provider blocks CORS, use desktop once its keychain and direct-provider path are tested. Verify the UI says **Cloud** before sending prompts to remote providers; PACE does not host these provider keys.

## Known issues / limitations

- **Unsigned installers**, no Apple notarization; OS warnings are expected. Native builds alone do not prove actual first-launch, microphone, system tray, or keychain functionality.
- On some Linux machines, WebKitGTK/FUSE/Secret Service dependencies are not preinstalled. AppImage may require FUSE; local API/credential integration needs testing.
- Free hosting may sleep or impose request timeouts; zero-cost hosting does not guarantee unrestricted inference. Hosted providers can have quotas, billable calls and incomplete replies.
- Long prompts have an explicit context budget and may receive HTTP 413; no provider can guarantee unlimited output. Ollama supports bounded continuation, but **all-provider SSE replay/reconnect is not implemented**.
- Pro can reuse the same model for a second pass. Actor/Critic stage notifications are not formal evidence of independent review.
- Browser BYOK is ephemeral memory-only. It is not an encrypted browser key vault, and browser extensions with page access remain a risk.
- Direct local GGUF/safetensors loading is unsupported. Displayed discovered files may not fit RAM/VRAM.
- Web-hosted conversations and extracted PDF content reside in the configured FastAPI database. `DELETE /my-data` affects the current anonymous session, not backups or provider copies. `DATA_RETENTION_DAYS` cleanup is startup-based.
- Web/desktop browser quality and performance thresholds require additional Lighthouse and manual acceptance evidence. See testing document for current caveats.

## How to test this release

Follow the full [Web + Desktop test checklist](https://github.com/KiritoTempest175/PACE/blob/main/docs/TESTING.md). In brief:

- [ ] First dashboard paint, no blank screen or horizontal overflow on phone/tablet/desktop.
- [ ] Mobile menu focus/Escape; logo goes Home; 404, Docs, Privacy and footer routes.
- [ ] Coding long prompt, correct code blocks with Copy feedback, no **silent** early cutoff.
- [ ] PDF Literacy upload and complete or explicit insufficient-context/error response.
- [ ] Fast vs Pro and Actor/Critic live stage.
- [ ] Custom model with key, connection test, masked key, Delete key, no key sent to PACE backend.
- [ ] Desktop scan of installed models, Ollama working, non-Ollama correctly labeled unsupported, app icon/installer metadata.
- [ ] Data deletion and repeatability; confirm local web test talks to `127.0.0.1:8000`, not production.

## Bugs and feedback

Use https://github.com/KiritoTempest175/PACE/issues with the OS and exact asset, steps to reproduce, expected and observed outcome, logs with secrets removed, and screenshots. Contact: huzaifazaman38@gmail.com · https://huzaifazaman.com.

**Build provenance:** `v0.1.0-rc1` targets `feature/tauri-desktop`. Windows/macOS/Linux bundles are compiled by GitHub Actions. The web ZIP is compiled separately from `main` with a loopback-only FastAPI URL. The release publisher uploads successful artifacts and reports failures in its workflow logs; do not infer that every platform succeeded if an asset is missing.

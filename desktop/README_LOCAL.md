# PACE Desktop 2.0 — installation and troubleshooting

[Desktop overview](README.md) · [PACE Web](https://pace.huzaifazaman.com/) · [Issues](https://github.com/KiritoTempest175/PACE/issues)

## Download and install

The web dashboard provides direct downloads once version 2.0 is published.

| Platform | Package | Important notes |
| --- | --- | --- |
| Windows 10/11 x64 | `PACE_2.0.0_x64-setup.exe` | Unsigned NSIS installer; SmartScreen warning may appear |
| macOS Apple Silicon | `PACE_2.0.0_aarch64.dmg` | Unsigned and not notarized; use the OS **Open** override only if you trust it |
| Debian/Ubuntu Linux x64 | `PACE_2.0.0_amd64.deb` | System WebKit libraries may be required |
| Portable Linux x64 | `PACE_2.0.0_amd64.AppImage` | Optional build; FUSE/runtime libraries may be needed |

Verify the `SHA256SUMS.txt` release attachment. On Windows use `Get-FileHash .\\PACE_2.0.0_x64-setup.exe -Algorithm SHA256`; on macOS use `shasum -a 256 filename.dmg`; on Linux use `sha256sum filename.deb`.

You do **not** need Node, Python, or Rust to use an installed release. The local AI model weights are separate downloads.

## First launch with Ollama

1. Start PACE. A bundled local Python FastAPI process starts on loopback.
2. Open local model setup. On Windows, **Download & install Ollama** downloads and opens the official installer on explicit request. macOS/Linux may need a separate installation from [ollama.com](https://ollama.com/).
3. Select **Refresh status** or **Start Ollama** as needed.
4. Download or choose a Generator/Actor model. Optionally choose a separate Reviewer/Critic model for Pro mode.
5. Use **Coding** for programs and **Literacy** for everyday chat or optional PDF questions.

Compatible model files can be discovered or imported into Ollama, but scanned GGUF/safetensors files are not necessarily loadable without conversion.

## Active AI service: one selection

The top-right dropdown identifies the active route and allows switching to **Local — Ollama / PACE**, **Hosted — PACE API**, or a configured **API — model name**. The status below shows the actual active provider. Changes take effect directly, reset the on-screen conversation, and are disabled while a model generates.

Add a new external model under **Models → Add custom model**, saving its key in the OS credential vault before selecting it from the dropdown. Supported adapters include OpenAI-compatible, OpenRouter, Anthropic and Google models.

## Privacy, credentials and data

- Local SQLite and generation preferences live in the per-user application-data directory, shown in Preferences.
- API secrets use OS credential service `app.pace.workspaces.byok` with the chosen model UUID as account name. On Windows inspect Credential Manager → Windows Credentials; macOS uses Keychain Access; Linux uses Secret Service.
- Switching to Hosted or a direct external API sends prompts to a remote endpoint and may incur charges.
- The direct-provider integration does not currently forward PDF excerpts to external APIs.
- Uploaded PDF binaries are deleted after text extraction. Extracted text is stored in the selected backend's database and remains subject to its retention policy.
- Review is model-based and generated code may be wrong. Never paste keys into chat or execute untrusted generated programs.

## Build complete installers from source

Use Node.js 22, Python 3.11, Rust stable, platform-native build tools, PyInstaller, Pillow and Tauri CLI 2.12.1.

```bash
git clone --branch feature/tauri-desktop https://github.com/KiritoTempest175/PACE.git
cd PACE
python -m venv .venv
# Activate your venv on the current OS
python -m pip install -r desktop/requirements-local.txt
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
cd frontend
npm ci
npm run lint
npm test
```

A complete build also needs the frozen `desktop/backend_entry.py` executable placed in `frontend/src-tauri/binaries/pace-api-<target-triple>`, generated native icons, and installer artwork. Follow [.github/workflows/desktop-native-ci.yml](../.github/workflows/desktop-native-ci.yml) for exact Windows/macOS/Linux commands; building Tauri alone without the backend sidecar is incomplete.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Local backend unavailable | Restart PACE; check if antivirus quarantined the bundled `pace-api` executable |
| Ollama is offline | Start Ollama, refresh model setup, select an installed model |
| Pro is slow | Use Fast, or choose smaller Generator/Reviewer models |
| API errors | Check saved key, model ID, quota, network, billing and selected provider |
| Wrong local/remote destination | Read the top-bar Active AI service label before sending private prompts |
| macOS app blocked | Use the supported Open override only for an installer you trust |
| Linux fails to launch | Verify WebKit/FUSE dependencies and desktop credential service |

Report issues at [GitHub](https://github.com/KiritoTempest175/PACE/issues), including OS/version, selected service and reproduction steps. Redact secrets and PDF content.

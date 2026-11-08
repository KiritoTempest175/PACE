# PACE Desktop 2.0

**Local-first AI desktop workspace** for Windows, macOS and Linux. Built with Tauri 2, React/Vite, Rust and a bundled Python FastAPI service.

| Feature | How it works |
| --- | --- |
| **Local service** | Bundled FastAPI + SQLite, loopback connection protected by an in-memory secret |
| **Ollama models** | Optional locally installed models; Fast = Generator, Pro = Generator + reviewer |
| **Hosted PACE API** | Switch to the official hosted backend in the top bar |
| **External APIs** | Configure a provider in Models, save its key in the OS credential vault, select it from the top bar |
| **Literacy** | Plain-language chat with optional PDF-grounded answers; not unsolicited code |
| **Coding** | Dedicated code generation/explanation and WebAssembly Python runner |

## Install

Download the verified 2.0.0 installer directly from the **Install PACE** section of [pace.huzaifazaman.com](https://pace.huzaifazaman.com/). Windows supplies an unsigned NSIS `.exe`; Apple Silicon macOS supplies an unsigned `.dmg`; Linux supplies a `.deb` and optionally an `.AppImage`. See [Local setup](README_LOCAL.md) for OS-specific guidance.

## Switch services in a single selection

The desktop title bar displays an **Active AI service** dropdown that identifies the actual destination:
- **Local · Ollama**: bundled backend using local Ollama.
- **Local · PACE model / No model configured**: other local backend states.
- **Hosted PACE API**: remote official PACE backend.
- **Direct PROVIDER API · Model name**: a specific separately configured external provider.

Choose directly from the dropdown; there is no second Apply step. Changing destinations clears the current conversation and document selection, preventing accidental cross-provider context reuse. A switch is disabled while generating.

## Models and providers

The first-run wizard guides optional Ollama installation and model selection. You can choose separate Generator and Reviewer models. No weights are bundled. Model discovery is not proof of direct execution: GGUF import to Ollama is explicit where supported, and safetensors detection is informational.

On **Models**, you may add OpenAI-compatible, OpenRouter, Anthropic, Google or custom HTTPS API endpoints. Keys reside in the native OS credential vault, not source code or WebView localStorage. These providers may charge for usage or retain prompts. Direct API requests do **not** attach locally processed PDFs automatically; select a PACE backend for PDF-based questions.

## Source and limitations

See [detailed setup](README_LOCAL.md), [release notes](RELEASE_NOTES_v2.0.0.md), and the [full branch README](../README.md). The 2.0 release includes both web and desktop editable source ZIPs.

**Limitations:** unsigned OS installers; no guarantee of GPU acceleration or universal GGUF support; model reviews do not verify code; the local Python WebAssembly runner is not a hardened sandbox. Real-machine installation and keychain validation remain necessary.

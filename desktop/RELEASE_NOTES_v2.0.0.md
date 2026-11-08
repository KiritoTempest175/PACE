# PACE Desktop v2.0.0 — local-first AI with clear provider switching

**Version:** 2.0.0 · **Branch:** `feature/tauri-desktop` · **Release:** Stable-version unsigned installers

PACE is a local-first AI workbench with optional hosted inference, general conversation, PDF questions and a dedicated coding workspace.

## What's new

- **Active service is always visible.** The top bar names the actual service: Ollama, local PACE model, hosted PACE API or a specific external provider/model.
- **Switch in one selection.** Choose Local, Hosted or your configured API directly; no second settings screen or Apply button. Chat and PDF context reset on service changes.
- **Literacy stays conversational.** Plain greetings and general questions do not produce unsolicited code; use Coding when programming.
- **Cleaner overflow.** Removes intrusive horizontal scrollbar tracks while preserving access to long content.
- **2.0.0 version alignment.** Rust crate, Tauri installer, release title, package filenames and new documentation match.
- **Full source backups.** The release attaches both complete web and desktop branch source ZIPs.

## Download files

| Asset | Purpose |
| --- | --- |
| `PACE_2.0.0_x64-setup.exe` | Windows x64 NSIS installer, unsigned |
| `PACE_2.0.0_aarch64.dmg` | macOS Apple Silicon DMG, unsigned/not notarized |
| `PACE_2.0.0_amd64.deb` | Debian/Ubuntu x64 |
| `PACE_2.0.0_amd64.AppImage` | Linux portable, only if optional build succeeds |
| `PACE_Desktop_Source_v2.0.0.zip` | Complete editable desktop branch |
| `PACE_Web_Source_v2.0.0.zip` | Complete editable web branch |
| `INSTALLATION.md` | Full setup/troubleshooting |
| `SHA256SUMS.txt` | SHA-256 checksums for all other release files |

**The release workflow must verify successful native Windows, macOS and Linux builds for its exact source commit before publishing.** The website only shows links to assets actually published.

## Limitations

- Installers are unsigned. Your OS may display trust warnings; the macOS build is not notarized.
- A downloaded installer does not install itself. Open it manually and follow your operating system's installation flow.
- No model weights are bundled. The in-app Ollama installer is mainly for Windows; macOS and Linux may require manual Ollama setup.
- External API requests are governed by the chosen provider's security, pricing and data retention policies.
- GGUF import is explicit and safetensors scanning does not guarantee runnable inference.
- Pro review is not compilation or correctness proof. Generated code may still be wrong.
- Passing automated CI does not prove every real PC installation, OS keyring or GPU setup works.

## Setup and support

[Web app](https://pace.huzaifazaman.com/) · [Desktop setup guide](https://github.com/KiritoTempest175/PACE/blob/feature/tauri-desktop/desktop/README_LOCAL.md) · [Report an issue](https://github.com/KiritoTempest175/PACE/issues)

Include OS, CPU/GPU, selected provider and sanitized logs when reporting problems. Never publish secrets.

# PACE Desktop v0.5.0 RC1 — Local-first AI workspace

**Release type:** Public pre-release · **Source branch:** `feature/tauri-desktop` · **Production web app:** unchanged.

PACE is a Tauri desktop application with a bundled local FastAPI backend and a choice of locally installed or external AI models. This is a **release candidate for testing**, not a fully verified production installer.

## Highlights

- **Matching PACE branding:** app icon and Windows NSIS installer use the same PACE monogram, with dark purple/cyan setup artwork. Native Windows permission dialogs retain the operating system theme.
- **Guided first launch:** choose a light, dark, or system appearance; set up Ollama in-app; select separate Generator (Fast) and Reviewer (Review) models; reopen preferences later.
- **Local model library:** choose 1B–8B catalog models or already installed Ollama models. Discover GGUF and safetensors files in recognized model folders; explicitly import compatible GGUF models into Ollama. Scanning is read-only and does not upload weights.
- **Bring your own provider:** configure OpenAI-compatible, OpenRouter, Anthropic, Google, or a custom HTTPS-compatible endpoint. Native Tauri requests read your key from the **OS credential vault**, not a plaintext local configuration file or browser localStorage. Native integrations still need real-PC validation.
- **Transparent local configuration:** display where session files and generation preferences are saved, and where to inspect or delete OS credential entries. Adjust model selection, context size, creativity, API/backend connection and theme from settings.
- **Coding workspace:** separate request, AI explanation, and generated-code panels, with copy/download and selected-request history.
- **Longer local model output:** remove the hard 256-token Ollama output cap; stream until the model stops, with bounded continuation and safety checks. **Not unlimited:** RAM/VRAM, model context, response repetition, timeouts and provider limits still apply.
- **General questions or PDFs:** Literacy supports general inquiries without requiring a document, and can use locally processed PDFs.

## Downloads

| File | Operating system | Notes |
| --- | --- | --- |
| `*_x64-setup.exe` | Windows 10/11 x64 | Tauri NSIS installer; unsigned |
| `*.dmg` | macOS | Unsigned test build; architecture is given in filename |
| `*.deb` | Linux (Debian/Ubuntu) | Requires native desktop/WebKit runtime dependencies |
| `*.AppImage` | Linux | Optional portable build, included only if its build succeeds |
| `SHA256SUMS.txt` | All | SHA-256 for attached artifacts |
| `INSTALLATION.md` | All | Setup instructions and credential storage locations |
| `PACE_Desktop_Source_v0.5.0-rc1.zip` | All | Editable source snapshot; GitHub also provides source archives |

**Use the versioned installers in this release only.** Do not download installers from the earlier v0.4.0 or v0.1.0 release to test these features.

## Install

### Windows
1. Download the Windows `.exe` and check its hash in `SHA256SUMS.txt`.
2. Run setup. The installer is **unsigned**; Windows SmartScreen or UAC may ask for confirmation. Proceed only if you trust the project's source and downloaded artifact.
3. Open PACE and use the first-run wizard. Choose appearance, then either install Ollama from inside PACE or configure a provider in Models.
4. To run locally, use **Refresh status**, download a model and select it as Generator; choose a Reviewer if desired.

### macOS
1. Download the DMG matching your Mac architecture.
2. Open the DMG and install PACE. This test app is unsigned/not notarized; macOS may block first launch. Use the system's supported **Open** override only if you trust the artifact.
3. Start PACE and follow the local model or provider setup instructions. The Ollama in-app installer is currently Windows-focused; macOS users may need to install Ollama separately.

### Linux
1. Download the `.deb` and install using your distribution's package manager. If an `.AppImage` is attached, it may be made executable and launched directly where the required system libraries are present.
2. Local model inference requires Ollama installed and available on the machine. The in-app Windows Ollama installation path is not available on Linux.

## Key storage and privacy

- API secrets use the OS credential manager under service `app.pace.workspaces.byok`; the corresponding entry name is the model UUID. No provider key should be written to `generation-preferences.json` or stored in WebView localStorage.
- On Windows, inspect **Credential Manager → Windows Credentials → Generic Credentials**. On macOS, use Keychain Access; on Linux, use the desktop Secret Service/keyring. Operating systems may restrict viewing plaintext secrets even when stored entries can be inspected/deleted.
- PACE's local SQLite and preferences are stored in your application's per-user data directory, shown inside Preferences.
- External AI provider requests send prompts to your selected provider. Billing and retention are governed by that provider.
- The installer **does not silently download model weights**. Model download or import requires your action.

## Known limitations and test scope

- The build is unsigned; it is a **pre-release** intended for user testing.
- Build and automated tests are not equivalent to verifying installation, Ollama setup, GPU use, local model scanning, BYOK billing or keychain operation on a clean user PC.
- Not all existing GGUF/safetensors models are supported; GGUF import is explicit, while safetensors scanning is informational.
- Model response length is bounded by model/hardware constraints, stream safety checks and timeouts; "unlimited" generation cannot be guaranteed.
- The Python code runner uses a constrained WebAssembly worker, which does not provide every native package or unrestricted system access. Do not execute untrusted code.
- Review mode is a model-assisted second pass, **not verified compilation, tests or mathematical proof**.
- The automatic Ollama installer workflow is designed for Windows. Other operating systems may need manual Ollama installation.

## Report a problem

Open an issue at https://github.com/KiritoTempest175/PACE/issues and include:
OS/version, CPU/GPU/RAM, selected model and inference mode, exact reproduction steps, and sanitized logs/screenshots. **Never publish API keys or private files.**

## Verify files

On Windows PowerShell: `Get-FileHash .\PACE*.exe -Algorithm SHA256`

On macOS/Linux: `shasum -a 256 <downloaded-file>` or `sha256sum <downloaded-file>`; compare the result to `SHA256SUMS.txt`.

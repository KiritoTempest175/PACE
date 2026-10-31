# PACE Desktop — local-first setup (desktop branch)

This build uses Tauri v2 (React) and a bundled FastAPI sidecar. It does not
require end users to install Python, Node.js or Rust. A model is not bundled
because model files vary in license, size and hardware requirements.

## First launch

1. Open the PACE installer and complete the branded Windows setup.
2. Launch PACE. The built-in local backend starts automatically.
3. The onboarding window opens the first time: choose Dark, Light, or System,
   then choose local AI or add an external provider.
4. For local inference, select **Download & install Ollama**. PACE opens the
   official Windows installer after a user click; complete its prompts.
5. Click **Refresh status**, or **Start Ollama** if Ollama is installed but idle.
6. Choose Generator (Fast) and optional Reviewer (Review mode). Choose among
   the 1B–8B model catalog or any Ollama models already installed on the PC.
   Downloads start only after you click and display progress.
7. **Scan this PC for models** searches known LM Studio, Hugging Face, Ollama
   and user model folders without uploading model files. Compatible GGUF
   files may be explicitly imported into Ollama with one click. Safetensors
   files are listed for reference; not every model is compatible with Ollama.

You can reopen the setup window from **Preferences → Manage Ollama & models**
or use the **Models** page to add external AI providers.

## Settings, privacy and stored credentials

- The settings window lets you edit appearance, local or hosted connection,
  model choices, context window and creativity.
- Local preferences are stored in the PACE user application-data directory,
  under `generation-preferences.json` and `models.json`. Their exact paths
  are displayed in the model manager and Preferences.
- External AI provider names/model IDs are stored in the local app WebView
  preferences. **No API secret is written to these JSON files.**
- API secrets are stored in the OS credential vault under service
  `app.pace.workspaces.byok`; the model's UUID is the credential name.
  On Windows check **Credential Manager → Windows Credentials → Generic
  Credentials**. On macOS check **Keychain Access** and on Linux the
  desktop keyring/Secret Service. Credential entries may not reveal the
  plaintext secret in the OS user interface, but can be inspected/deleted.
- API requests for external providers run in the **native Tauri process**,
  using keys read directly from the OS vault. A configured provider may
  charge usage fees. Choose only providers you trust.
- Do not paste passwords or API tokens into ordinary chat prompts.

## Generating long responses

Local Ollama generation uses an automatic output setting rather than a
fixed 256-token cap. The practical maximum still depends on model context,
RAM/VRAM, provider restrictions, and safety deadlines. Generation can fail
when the model exhausts context, runs out of memory, or repeats output.

## Installer/branding notes

The installer and application icon use the PACE P monogram.
The NSIS welcome, finish, and header art use the same dark/cyan/purple look.
Windows-owned dialogs (SmartScreen/UAC, standard buttons) still use Windows
system appearance. The installer is unsigned, so Windows may show warnings.

## Building from source

For contributors only: install Node 22, stable Rust, Python 3.11, Windows
C++ Build Tools, WebView2 and Pillow. After npm dependencies are installed:

```bash
cd frontend
npx @tauri-apps/cli icon src-tauri/icons/icon-source.svg
cd ..
python desktop/build_installer_art.py
cd frontend
npx @tauri-apps/cli build --bundles nsis
```

Native CI builds Windows NSIS, macOS DMG and Linux DEB artifacts separately.
These unsigned artifacts must be verified on clean machines before any release.

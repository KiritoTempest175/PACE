# PACE Desktop 0.2 — bundled local backend

The **Windows installer includes the Python FastAPI backend as an executable
sidecar**. The user does not need to install Python or download separate backend
source files to use local conversation history and PDF extraction. Tauri starts
the sidecar on a random 127.0.0.1 TCP port and terminates it on exit.

Local user data is stored under the application's Windows Local AppData
directory. A per-launch capability header restricts access to the embedded
server; the server never listens on an external network interface.

## AI modes

- **Local (default):** The bundled backend calls an Ollama instance running
  at `http://127.0.0.1:11434`. Users must separately install Ollama and pull
  `qwen2.5-coder:1.5b`. PACE does not ship model weights.
- **Hosted:** The existing Render + Hugging Face services are accessible from
  Preferences when the user has Internet connectivity.

Without Ollama, local chat history, PDF upload and workspace navigation work,
but **AI inference returns an honest unavailable error**, not a fake answer.
The Python execution sandbox is disabled in the desktop bundle.

## Building from source

On Windows install Python 3.11, Node.js 22, Rust stable, Visual Studio C++
Build Tools, and WebView2. From the repository root:

```powershell
python -m pip install -r desktop/requirements-local.txt
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name pace-api --paths . --collect-all pymupdf --hidden-import fitz --hidden-import masteries.services.ollama_provider --hidden-import masteries.services.telemetry desktop/backend_entry.py
New-Item -Type Directory -Force frontend/src-tauri/binaries | Out-Null
Copy-Item dist/pace-api.exe frontend/src-tauri/binaries/pace-api-x86_64-pc-windows-msvc.exe
python desktop/smoke_backend.py dist/pace-api.exe

cd frontend
npm ci
npx --yes @tauri-apps/cli@2.12.1 icon src-tauri/icons/icon-source.svg
npx --yes @tauri-apps/cli@2.12.1 build --bundles nsis
```

The updated GitHub release workflow performs these steps, verifies the NSIS
installer and publishes complete source archives. The Windows installer is
unsigned and should be treated as a prerelease pending manual GUI testing.

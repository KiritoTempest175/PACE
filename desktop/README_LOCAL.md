# PACE Desktop v0.3 — Windows setup

The Windows installer contains the PACE Desktop React/Tauri interface, the
local Python FastAPI executable, SQLite conversation storage and PDF parsing.
You do not need to extract Python or React source files into the install folder.

1. Install the Windows .exe and open PACE.
2. The included local API launches automatically.
3. On first launch PACE detects Ollama. If it is missing, choose
   **Download & install Ollama**. PACE downloads the official Windows
   installer using HTTPS and opens its normal setup wizard after your click.
4. Complete Ollama setup and select **Refresh status** in PACE.
   If required, select **Start Ollama**.
5. Pick any listed **Generator / Actor** model (1B–8B), then select
   **Download & select model**. Download progress appears inside PACE.
6. For **Pro**, select a **Reviewer / Critic** model. A separate AI model
   reviews the Generator draft, but this is not formal code verification.

Models can be downloaded for free; their model-specific licenses, memory
needs and file sizes vary. Initial downloads need Internet and disk space.
Local inference can be used without the hosted API after setup. Hosted mode
remains available under Preferences.

SQLite and the selected model configuration live under Windows Local AppData,
not the installation directory. Ollama stores its model weights in its own
user folder. Uninstalling PACE does not silently delete model downloads.

Preserved: Coding, Literacy/PDF, Research, Fast, Pro, chat history, document
upload, dark/light themes and hosted/local API selection.

This package does not secretly bundle Ollama or large model weights. Its
first-run wizard installs Ollama with explicit user consent and downloads
the user's selected models, without terminal commands. These models are
pretrained Ollama models; the original independently trained PACE actor
and critic weights are not included.

For developers: fork feature/tauri-desktop or download the complete source
archive. Requirements for Windows builds include Node 22, Rust, Python 3.11,
Windows C++ Build Tools and WebView2. GitHub Actions freezes the Python
backend and builds the NSIS installer. The installer is unsigned.

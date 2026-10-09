# PACE Desktop — separate experimental branch

This folder accompanies the Tauri v2 Windows client under `frontend/src-tauri/`.
It is intentionally isolated on `feature/tauri-desktop`, not the web production branch.

## What PACE Desktop installs

Starting with **v0.2.0**, the Windows NSIS installer contains:

- The Tauri v2 native desktop shell and complete React UI
- A **frozen Python FastAPI backend** bundled as `pace-api.exe`
- Local SQLite conversation storage in Windows Local AppData
- Local PDF parsing and document-workspace endpoints
- A per-startup capability header and a randomly selected loopback port

The desktop client starts the backend automatically on launch and stops it on
exit. No separate Python installation is necessary for its bundled features.
It supports offline PDF processing and conversation storage.

**AI requires a model:** Local inference uses Ollama on the same PC. Install
Ollama and run `ollama pull qwen2.5-coder:1.5b` before using Local AI.
The desktop installer deliberately does **not** contain model weights.
Hosted inference remains available as a separate preference.

**Local code execution is disabled.** Running user-supplied Python requires
a properly secured Docker sandbox and is not offered in the packaged app.

## Developer documentation

- [Full local backend configuration and build instructions](README_LOCAL.md)
- `desktop/backend_entry.py` is the explicit bundled backend entrypoint
- `desktop/smoke_backend.py` exercises the real frozen backend on Windows
- `frontend/src-tauri/` owns startup, process shutdown and installer settings
- `frontend/src/` contains the editable React frontend

The release includes complete source ZIPs. Installed app binaries are not
automatically editable source files; download the source archive to customize
and rebuild PACE.

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

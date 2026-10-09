# PACE Desktop Windows package

**Status: v0.2.0 installer built and tested; public GitHub Release requires authorization.**

The original `desktop-v0.1.0` prerelease did **not** embed the Python API and must
not be recommended for local installation. Its replacement was built from the
`feature/tauri-desktop` branch on GitHub Actions run
[37948009714](https://github.com/KiritoTempest175/PACE/actions/runs/37948009714).

## Verification performed

- Windows runner built a PyInstaller `pace-api.exe` sidecar and completed a
  live startup/authentication/SQLite conversation smoke test.
- Tauri v2 successfully compiled the Windows x64 NSIS installer.
- GitHub Actions generated `PACE_Web_Source.zip`, `PACE_Desktop_Source.zip`
  and `PACE_Complete_Source.zip`.
- A separate test silently installed that exact NSIS installer, verified
  `pace-desktop.exe` and `pace-api.exe` as distinct binaries, launched
  the Tauri executable, and observed the bundled backend process start:
  [Windows install + launch verification](https://github.com/KiritoTempest175/PACE/actions/runs/37950332766).

This is **not** equivalent to a human acceptance test of every feature in
the visible Windows GUI. The desktop app uses a local API by default and also
allows the official hosted API. Ollama and model weights are **not** bundled.

## Obtain the package before the release is published

Download the GitHub Actions artifact `PACE-Desktop-Windows-and-Source`
from [Windows build 37948009714](https://github.com/KiritoTempest175/PACE/actions/runs/37948009714).
Extract the outer ZIP to access the Windows `.exe` and the three source ZIPs.
Action artifacts expire, so publish to GitHub Releases for permanent download.

## Publish as a public GitHub prerelease

The original release job failed because GitHub's workflow token returned
`HTTP 403 Resource not accessible by integration` when creating a Release.
The same error occurred on `main`; simply retrying that token cannot fix it.

A manual workflow using a dedicated scoped GitHub personal access token is
now at `.github/workflows/publish-desktop-v0.2.yml` on `main`.

1. In your GitHub account, create a **fine-grained personal access token**
   restricted to the `KiritoTempest175/PACE` repository. Set
   **Contents: Read and write**. Give it the shortest viable expiration.
2. Open [PACE repository Actions secrets](https://github.com/KiritoTempest175/PACE/settings/secrets/actions)
   and save it as a **repository secret** named `PACE_RELEASE_TOKEN`.
   Do not paste tokens into issues, chats, Variables or source files.
3. Open [Publish verified PACE Desktop 0.2](https://github.com/KiritoTempest175/PACE/actions/workflows/publish-desktop-v0.2.yml),
   select `main`, and click **Run workflow**.
4. Verify the published release contains the NSIS executable and all three
   archives before sharing its URL as a public download.

Once the public release is available, mark `desktop-v0.1.0` deprecated or
remove that incomplete installer from your recommended download links.

## Installed files on Windows

An NSIS per-user installation places executable files under
`%LOCALAPPDATA%\\PACE AI Workspaces`. The local API database and its log
file are stored in the app's separate local application-data directory.

**Installed executables are not editable source files.** Fork the
[`feature/tauri-desktop` branch](https://github.com/KiritoTempest175/PACE/tree/feature/tauri-desktop)
or download one of the source ZIPs to modify the project.

To use AI locally, install [Ollama](https://ollama.com) separately and run
`ollama pull qwen2.5-coder:1.5b`. The installer does not silently download
weights and the local Python sandbox remains disabled.

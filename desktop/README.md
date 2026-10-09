# PACE Desktop — independent desktop branch

PACE Desktop v0.3 uses Tauri v2, React and a bundled FastAPI Python sidecar.
All required application files are installed automatically by Windows Setup.
No manually extracted code files are needed to run the application.

At first launch the Ollama setup wizard detects Ollama and guides users
through downloading the official Ollama Windows installer and choosing 1B–8B
AI models inside PACE. Fast runs the selected Generator/Actor; Pro makes a
second pass using the selected Reviewer/Critic. Users may select different
models for the two roles. These are pretrained models, not the independently
trained original PACE ensemble weights.

Local SQLite and PDF functionality work without Ollama; AI requires a
downloaded local model or selecting the hosted PACE API. Local arbitrary
Python execution remains disabled for security.

See README_LOCAL.md, the MIT license and desktop-release GitHub workflow.
Editable source is in the separate source ZIP, not inside compiled .exe files.

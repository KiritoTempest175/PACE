# Contributing to PACE

PACE accepts focused bug fixes, tests and documentation improvements. Open an issue describing the observed failure, expected behavior, branch (`main` web or `feature/tauri-desktop` desktop), and safe reproduction steps before major refactors.

1. Fork and create a branch from the appropriate target.
2. Never include personal credentials, datasets with private information or model weights in a pull request.
3. Run `pytest -q tests`, then `cd frontend && npm ci && npm run lint && npm test && npm run build`.
4. For desktop changes, run Cargo checks and the native Tauri build on the target OS. Do not claim OS compatibility based only on frontend CI.
5. Use conventional commits, e.g. `fix(api): report truncated SSE`, `feat(desktop): discover local models`, `test: verify session deletion`.
6. Document privacy, provider usage, retention and backwards-compatible migrations for any behavioral change.

See [SECURITY.md](SECURITY.md) for private vulnerability reporting.

Maintainer: huzaifazaman38@gmail.com · https://huzaifazaman.com · https://github.com/KiritoTempest175

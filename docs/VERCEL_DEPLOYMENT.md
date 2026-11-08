# PACE web frontend — Vercel deployment (November 2026)

**Production:** https://pace.huzaifazaman.com

| Component | Current location |
| --- | --- |
| Source repository | `KiritoTempest175/PACE` |
| Web branch | `main` |
| Desktop source branch | `feature/tauri-desktop` — not the web production branch |
| Hosting | Vercel project `pace` |
| Frontend | React 18, Vite, client-side SPA routes |
| Frontend directory | `frontend/` |
| API | `https://pace-phase2-api.onrender.com` (Render) |
| Browser API path | `/api` — Vercel reverse proxy to Render |
| Models | Configured on the API backend; no model-provider credentials in the browser |

## Existing, verified routing

`frontend/vercel.json` already contains:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {"source": "/api/:path*", "destination": "https://pace-phase2-api.onrender.com/:path*"},
    {"source": "/(.*)", "destination": "/index.html"}
  ]
}
```

The first rewrite proxies API requests from the browser to Render; the second supports SPA routes such as `/coding`, `/literacy` and `/privacy`. **Do not replace these with Netlify rules.** The Vite API module defaults to `/api`; `VITE_API_BASE_URL` can override it for deliberate test environments. Do not put secret API tokens, provider keys or database credentials in any `VITE_*` variable.

## Building and validation

From the repository root:

```bash
cd frontend
npm ci
npm run lint
npm test
npm run build
```

On a clean machine, Node.js 22 LTS is a suitable development version; Vercel's configured Node version must also satisfy the project's dependency requirements. Check the currently connected Vercel project rather than assuming its version.

GitHub Actions independently runs quality checks. The current production project is Git-connected to `main`, and a push may trigger a production deployment automatically. For production operations, review the current Vercel deployment and commit before making further pushes. Do not deploy `feature/tauri-desktop` to the production web domain.

## Desktop installer downloads on the Vercel site

The web dashboard's **Install PACE** section queries the public GitHub release `desktop-v2.0.0` and builds direct download links from each release asset's exact `browser_download_url`. It does not generate executable URLs or point to GitHub's generic release page. If the release is missing or assets are incomplete, download actions are hidden rather than sending users to nonexistent files.

The release workflow, maintained on the existing desktop branch, verifies native build artifacts before publishing Windows `.exe`, macOS Apple Silicon `.dmg`, Linux `.deb` and optional Linux `.AppImage` packages. Browsers download the files; the OS does not silently install them.

## Deployment verification checklist

- [ ] Current production Vercel deployment uses a tested `main` commit, is READY and is attached to `pace.huzaifazaman.com`.
- [ ] SPA routes (`/`, `/coding`, `/literacy`, `/docs`, `/privacy`) load on refresh.
- [ ] `/api/health` returns the expected backend health response, not HTML.
- [ ] A plain `hello` in Literacy remains in literacy mode and yields a conversational answer rather than code.
- [ ] Coding displays generated files only for a coding request.
- [ ] Desktop installer buttons appear only after the verified GitHub v2.0.0 release contains those exact assets.
- [ ] Mobile screens have no intrusive horizontal scrollbar, while long code remains readable.
- [ ] Backend PDF validation, session isolation, quotas and retention settings are not weakened.
- [ ] Provider secrets remain server-side, never in Vite environment variables or committed files.

## Source backups

Public source archives are available for each existing branch:

- [Web source (main)](https://github.com/KiritoTempest175/PACE/archive/refs/heads/main.zip)
- [Desktop source (feature/tauri-desktop)](https://github.com/KiritoTempest175/PACE/archive/refs/heads/feature/tauri-desktop.zip)

The Desktop 2.0 release workflow also prepares version-tagged web and desktop ZIP archives, plus SHA-256 checksums. The desktop release is built separately from the Vercel web deployment.

**Historic Netlify configuration and instructions** remain in the repository for reference only; Vercel is the active frontend host. Do not alter Netlify or Vercel credentials or Render provider secrets as part of a documentation-only change.

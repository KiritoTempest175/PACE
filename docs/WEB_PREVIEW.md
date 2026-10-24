# PACE web preview — black-screen fix

The blank page was caused by a JavaScript naming collision: the `document` PDF state masked the browser `document` object, so updating `document.title` threw a TypeError during startup. Commit `7ca89d48` fixed the DOM access, with an error recovery screen and startup regression tests added later.

## Easiest deployment: a separate Netlify Drop test site

1. Download `PACE_Web_Netlify_Preview.zip` from the [PACE v0.1.0-rc1 prerelease](https://github.com/KiritoTempest175/PACE/releases/tag/v0.1.0-rc1).
2. Extract the archive. You should see **index.html**, **assets/** and **_redirects** inside the extracted folder (not another nested ZIP).
3. Open [Netlify Drop](https://app.netlify.com/drop). Drag the **extracted folder containing index.html** to Netlify Drop. The new random netlify.app URL is a test site; do not drag it onto the existing `pace-ensemble` project or deploy with `--prod`.
4. Open the URL and check Dashboard, Coding, Docs, Privacy and the custom 404. For the complete tests see [TESTING.md](TESTING.md).

**Data warning:** This ZIP is compiled with `VITE_API_BASE_URL=https://pace-phase2-api.onrender.com`. It communicates with the existing hosted PACE backend, not an isolated database. New sessions use separate anonymous tokens but **test prompts/PDF excerpts will go to that backend and its inference provider**. Use nonsensitive test data. If you want full isolation, use the local web test ZIP from the same release, compiled for `http://127.0.0.1:8000`, and run your own local FastAPI and SQLite database as described in [TESTING.md](TESTING.md).

## Automatic Netlify draft preview (optional)

The GitHub Actions workflow `PACE Main Web Preview (never production)` uses `netlify deploy --dir=frontend/dist` without `--prod`. It currently cannot run because the GitHub environment/repository has no `NETLIFY_AUTH_TOKEN` secret. If you choose this option, generate a limited-scope Netlify personal access token in Netlify, add it as **NETLIFY_AUTH_TOKEN** in GitHub repository Settings → Secrets and variables → Actions (or the `NETLIFY` environment), then run the preview workflow. Never paste the token into a chat, source file or log.

## Quick diagnosis if the preview is blank again

- The network response for `/index.html` should be HTTP 200 and `/assets/*.js` should load as JavaScript (not HTML).
- If you opened `index.html` using `file://`, use Netlify Drop or a local HTTP static server instead.
- Check the browser developer console for a TypeError or denied script request. A visible PACE recovery screen should now appear for React render failures.
- Refresh with Ctrl+Shift+R to bypass old cached assets, or open the preview in a private browsing window.
- An unavailable backend should show **API unavailable** while the dashboard remains visible; it should not black out the page.

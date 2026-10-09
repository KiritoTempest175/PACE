# PACE Python Runner — Web and Desktop

PACE's Coding workspace now includes a **Run Python** control that executes
Python 3 locally in a dedicated Web Worker using a pinned, self-hosted Pyodide
(WebAssembly) runtime. It requires **no backend code-execution permission**
and works with the same React component on Netlify and Windows Tauri.

## Run Python

1. Open **Coding → Python runner**.
2. Enter Python source (e.g. \`print(6 * 7)\`).
3. Select **Run Python** to see stdout or a Python exception.
4. Select **Stop** to cancel a running program. An infinite loop is
   automatically stopped after 8 seconds.

The first execution initializes the bundled Python runtime; later executions
create a fresh worker for independent code state. Runtime assets are copied
into \`frontend/dist/pyodide\` by \`frontend/scripts/vendor-pyodide.mjs\`
during the normal Vite build and are **served from PACE's own origin**.
No runtime CDN and no Ollama installation are needed for this feature.

## Limitations and trust

- This is a convenient local Python executor, **not a hardened sandbox**
  or a secure facility for running malicious third-party scripts.
- Execution time is bounded by terminating the worker; the browser limits
  memory, but there is no enforced per-program RAM/CPU quota.
- It does not execute on the Render server or provide access to the
  Windows process API, shell or filesystem. Browser/WASM features and
  supported Python packages differ from normal desktop CPython.
- Output is capped at 64 KiB and source code at 20,000 characters.
- The separately secured Docker sandbox API remains disabled by default.

## Building and deploying

\`\`\`sh
cd frontend
npm ci
npm run build
\`\`\`

The build fetches and verifies the presence/size/hash of pinned
**Pyodide 0.29.5** assets over HTTPS, then bundles them into \`dist\`.
The files are deliberately excluded from Git source control due to their
size; the exact asset metadata is included in \`dist/pyodide/manifest.json\`.
For deployment, publish the *entire* Vite output, including
\`python-runner.worker.js\` and \`pyodide/\`.

Netlify CSP allows same-origin Web Workers and \`wasm-unsafe-eval\` but
does not enable unrestricted \`unsafe-eval\`; the Tauri CSP is scoped
similarly. See \`frontend/public/_headers\`, \`netlify.toml\`, and
\`frontend/src-tauri/tauri.conf.json\`.

Web browser end-to-end tests execute real code, show Python errors,
terminate infinite loops and run new code after a timeout. See
\`.github/workflows/python-runner-e2e.yml\`.

Pyodide is an Apache-2.0 licensed third-party project.
https://github.com/pyodide/pyodide

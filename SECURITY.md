# Security policy

PACE is experimental software; do not treat it as a validated secret manager or hardened execution environment.

## Report a vulnerability

Contact **huzaifazaman38@gmail.com** privately with the affected branch/version, reproduction steps and impact. Do not publish exploit details or credentials in GitHub issues. There is no committed SLA for security response.

## Current trust boundaries

- **Web:** prompts and extracted PDFs reach the configured FastAPI API and inference provider. Session tokens are anonymous bearer credentials, not authenticated user identities. Data deletion is session-scoped. Retention cleanup runs on API startup, not on a guaranteed timer.
- **Browser BYOK:** direct provider requests with an in-memory credential, which never goes to PACE FastAPI. Browser extensions/XSS and provider CORS remain risks. Disable high-scope credentials.
- **Desktop:** the bundled FastAPI API listens on loopback with an ephemeral capability; user BYOK secrets use native OS credential APIs when available, with no intended plaintext fallback. The native build/runtime and provider-domain audits remain to be completed.
- **Local code execution:** Pyodide web worker is not a hardened malware sandbox. The isolated Docker runner is local-development-only and opt-in; hosted execution remains disabled.
- **Models:** downloaded models are third-party code/data; scan and verify licenses and origin.
- **Uploads:** PDF-only, size/page constraints and UUID paths; do not assume parser exploitation is impossible.
- **Free hosting:** upstream timeouts, quotas and logs are outside the app's control.

Do not store credentials in committed `.env` files, screenshots, CI logs or client bundle variables. If a secret has ever been committed, remove it from history and **rotate** it; merely deleting it in a later commit is insufficient.

Security contact: huzaifazaman38@gmail.com

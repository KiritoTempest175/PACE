# PACE production release audit — 2026-10-24

This checklist distinguishes implemented work from verified behavior. No claim of universal model compatibility, unbounded output, device-local hosted-web storage, or complete privacy is made without end-to-end evidence.

## Verified in repository inspection
- [x] Main web and Tauri desktop branches exist and contain separate app entry points.
- [x] Current FastAPI routes support coding and PDF literacy.
- [x] Existing frontend includes ESLint, Prettier, Vitest and Vite scripts.
- [x] Session history and documents are stored on the configured API database.
- [x] The hosted inference path uses a Hugging Face model; Pro may reuse that model for a second pass.
- [x] Frontend dashboard landing view and shared cyberpunk token overrides committed on both branches.
- [x] User-facing Research navigation removed and request schema now rejects Research (legacy research modules are still present).
- [x] Updated static HTML title/description and Open Graph title/description.

## Not yet complete or proven
- [ ] End-to-end build, lint, test green across both branches after the most recent commits.
- [ ] Remove legacy Research modules, documentation and tests after checking imports and migration semantics.
- [ ] Full route-based UI with Models, Settings and Docs pages, a privacy page, 404 page and accurate per-route metadata.
- [ ] Responsive keyboard-trapped mobile drawer and browser validation at 320, 375, 768, 1024 and 1440 px.
- [ ] Full accessibility, Lighthouse >=90, link-checker and action-by-action test matrix.
- [ ] SVG logo variants, desktop icon bundles, web favicon and PWA images.
- [ ] User-controlled custom providers and model credentials with threat-modeled local-only encryption and keychain integration.
- [ ] Desktop local model discovery, direct GGUF/safetensors loading and VRAM-fit estimation.
- [ ] Fast/Pro stage streaming and provider-specific test coverage.
- [ ] Resume-aware generation, idempotent stitching, keep-alives, reconnect and Continue controls. A hard 100,000-character ceiling, token budget and request timeout remain.
- [ ] Distinct syntax-highlighted downloadable code blocks and multi-file rendering.
- [ ] Complete PWA, install verification and cross-OS desktop distribution.
- [ ] Security scan of full Git history, image optimization, repo cleanup and branch-specific README revisions.
- [ ] Deploy both branches and verify observed public endpoints.

## Privacy accuracy constraints
The existing hosted web implementation sends prompts and PDF extracts to a remote FastAPI API, stores conversations on the API-configured database and invokes a configured inference provider. **Do not state that all prompts remain on the user's machine.** A locally configured desktop instance may stay local when using its bundled backend and local Ollama model, but hosted connection and remote-provider choices transmit content over a network. A server-side Hugging Face token is not a user-provided browser key. No secure BYOK feature has been verified; do not add unencrypted persistent key storage.

## Hosting
Current Netlify project: pace-ensemble (custom hostname pace.huzaifazaman.com). The active Render PACE deployment identified by service name is pace-phase2-api, configured on phase2/production-hardening-20261009 with manual deploys; another older pace-backend service tracks a separate repository. Confirm the live web API target before migrating branches. Netlify free hosting and Render free instances have runtime and proxy limits; long unbounded streaming cannot be guaranteed. Avoid deployments until validation passes.

## Contact
- huzaifazaman38@gmail.com
- https://huzaifazaman.com
- https://github.com/KiritoTempest175

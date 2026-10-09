# PACE Phase 2 Netlify deployment

Existing public site: https://pace-ensemble.netlify.app
Netlify site ID: ba128faa-c6da-43f7-9fcc-4d51db32e87c
Source branch: phase2/production-hardening-20261009

## Option A: Connect this site to GitHub directly

Open https://app.netlify.com/projects/pace-ensemble and select
Project configuration > Build & deploy > Continuous deployment.
Connect the GitHub repository KiritoTempest175/PACE to THIS SITE,
not just the overall Netlify team account. Select the Phase 2 branch.

The root netlify.toml supplies the base directory (frontend), build command
(npm ci --no-audit --no-fund && npm run build), published directory (dist),
the staging Render API URL, a SPA redirect, and browser security headers.

Check the resulting Netlify deployment for a Phase 2 commit before
claiming that the new UI is live. Existing manual uploads are not
automatically replaced merely by authorizing the GitHub account.

## Option B: Use the GitHub Actions deployment workflow

The repo contains .github/workflows/deploy-netlify.yml. It targets
the existing site ID, does not create a second site and does not expose
any credentials in the public frontend bundle.

1. Create a Netlify personal access token at
   https://app.netlify.com/user/applications#personal-access-tokens
2. Save it in GitHub at
   https://github.com/KiritoTempest175/PACE/settings/secrets/actions
   as a REPOSITORY SECRET called NETLIFY_AUTH_TOKEN.
   Alternatively, create a GitHub environment named NETLIFY and save
   NETLIFY_AUTH_TOKEN as an ENVIRONMENT SECRET in that environment.
   The workflow job declares environment: NETLIFY.
   Never save access tokens as plaintext Actions variables.
3. Open the workflow page:
   https://github.com/KiritoTempest175/PACE/actions/workflows/deploy-netlify.yml
4. Run the workflow on branch phase2/production-hardening-20261009 with
   publish_production set to false. It will lint, test, build and create
   a DRAFT deploy. It will not replace the current site.
5. Review the draft URL in the job logs and verify UI, navigation, chat
   storage, PDF flows and connection to pace-phase2-api.onrender.com.
6. Only after acceptance, manually rerun with publish_production=true
   to replace the existing public site.

The same workflow also accepts a push to .github/netlify-preview.request
on the Phase 2 branch as a safe, preview-only deployment trigger.

## Option C: Upload the Vite distribution manually

Passing GitHub CI runs include artifact pace-phase2-frontend-dist,
which contains compiled HTML, JS, CSS and _redirects. Download
the artifact, extract it and upload the contents to the existing
Netlify site. No client secrets are needed. Manual uploads do not
enable Git-based continuous deployment.

## Acceptance boundaries

- The backend staging API is https://pace-phase2-api.onrender.com.
- The Hugging Face Space source has been uploaded separately. Successful
  upload does not prove model readiness or ZeroGPU generation.
- The backend must remain configured with AI_PROVIDER=disabled until
  model output has been verified. This frontend will show an error
  for AI generation while provider is disabled.
- The system uses anonymous, browser-held bearer tokens. It is not
  ready for sensitive document workloads or multi-user production auth.

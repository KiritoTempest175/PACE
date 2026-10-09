# Publish the PACE AI service to a new Hugging Face Space

The existing Space `Kiritox07/pace` is untouched. This workflow creates
`Kiritox07/pace-phase2-ai` as a **public Gradio ZeroGPU Space**, then uploads
the following files from `ai-service/` to the new Space root:

- `app.py`
- `requirements.txt`
- `README.md` (the source is `ai-service/README.md`)

## Required one-time authorization

The connected Hugging Face app has `read-repos` and `jobs` permissions,
not repository write access. A new Space cannot be created or updated with
those permissions.

1. Open https://huggingface.co/settings/tokens and create a **write-capable**
   token authorized to create/manage Spaces in the `Kiritox07` namespace.
   A fine-grained token restricted to an existing repository is insufficient
   to create a new Space: you may need an account-level write token for the
   first run, and then replace it with a fine-grained Space-specific token.
2. Open https://github.com/KiritoTempest175/PACE/settings/secrets/actions
   and add repository secret **`HF_TOKEN`**. Do not paste your token into chat,
   code, issues or GitHub variables.
3. Open https://github.com/KiritoTempest175/PACE/actions/workflows/deploy-hf-space.yml
   (the workflow is on the Phase 2 branch; select that branch in the workflow
   selector) and click **Run workflow**.
4. Watch the workflow and then visit
   https://huggingface.co/spaces/Kiritox07/pace-phase2-ai
   to check the Space build and use the **Use via API** tab to test `/generate`.

The workflow refuses to use paid hardware. It explicitly requests
`zero-a10g`; if ZeroGPU is unavailable for the account, the job fails
instead of silently selecting paid hardware. Free accounts in good standing
can be eligible to host up to two ZeroGPU Spaces, subject to Hugging Face
eligibility requirements and quota.

## Backend integration, **only after successful live inference**

On the Render **staging** service `pace-phase2-api` set:

- `HF_SPACE_ID=Kiritox07/pace-phase2-ai`
- `AI_PROVIDER=huggingface`
- `HF_TOKEN` as a Render secret only if access requires it

The public Space uses one pretrained small instruction model, with a
same-model review pass. It is **not** an independently trained actor/critic
ensemble. Verify quota, queue time, response correctness and that FastAPI's
SSE adapter handles snapshots before turning inference on.

Do not switch production Netlify to the new frontend until the full
end-to-end release checklist is satisfied.

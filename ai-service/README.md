---
title: PACE AI Service
sdk: gradio
python_version: 3.10.13
app_file: app.py
---

# PACE ZeroGPU AI Service

This is a **single pretrained instruction model**, not PACE's independently trained actor-critic ensemble. `fast` yields real incremental text snapshots; `pro` generates one draft and performs a second pass **with the same model**, yielding the final revision (not a separate critic's validation). Model weights load at module import and move to CUDA using ZeroGPU's CUDA emulation.

Select eligible **ZeroGPU** hardware under Space Settings, configure `PACE_MODEL_ID` if a different model is preferred, and grant the backend the necessary Space read permission. The exposed Gradio generator API is `/generate`, accepting `(text, mode, speed, max_new_tokens)` and yielding increasing complete strings for streaming output.

Current ZeroGPU restrictions and account eligibility change; verify compatibility before deploying. Free GPU quotas and queue delays apply. Do not place backend credentials in the public Space. A private Space may require a paid account/plan; if a private Space cannot be hosted free, keep it public without secrets and apply backend-side user quotas.

# Heterogeneous Micro-Agent Ensemble (PACE)
### A Resource-Constrained Multi-Agent AI Microservice

![PACE Workspace](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![React](https://img.shields.io/badge/React-18-blue) ![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_Optimized-orange)

## 📌 Core Thesis
An ensemble of specialized, custom-trained micro-models can eliminate AI hallucinations and outperform massive monolithic LLMs through a rigorous **Actor-Critic validation loop**.

PACE (Pipelined Actor-Critic Ensemble) is engineered from the ground up to operate within strict hardware constraints while delivering state-of-the-art reasoning, code generation, and factual synthesis.

- **Target Hardware**: NVIDIA RTX 4060 (8GB VRAM), 16GB RAM
- **Core Constraint**: Never exceed 8GB VRAM; hot-swap models dynamically
- **Scope**: Engineering Portfolio + Published Research Paper

---

## 1. Masteries Overview

The system is divided into three domain experts ("Masteries"). Each Mastery consists of a paired **Actor** (generator) and **Critic** (validator), forming a self-correcting loop.

| Mastery | Actor (Generator) | Critic (Validator) | Objective Verification |
|---------|-------------------|--------------------|------------------------|
| **Coding** | Writes code from prompt/spec | Checks syntax, logic, test-pass probability | Unit tests execute and pass in isolated sandbox |
| **Literacy** | Summarizes, rewrites, answers from local text | Checks factual consistency, hallucination | Claim-to-source sentence mapping (NLI) |
| **Research (Web-Augmented)** | Synthesizes live web/academic sources into literature reviews | Verifies citation existence and claim accuracy against source | Regex checks citation IDs; NLI verifies claim matches abstract |

**Critical Principle:** Each Critic must have an objective verification mechanism. Without this, the Actor-Critic loop becomes two hallucinators agreeing with each other.

---

## 2. System Architecture

### 2.1 High-Level Request Flow (Fast vs. Pro)
The backend exposes two primary pipelines:
- **Fast Mode (Latency-Optimized)**: Tokenize $\rightarrow$ Load Actor $\rightarrow$ `torch.no_grad()` Inference $\rightarrow$ Unload Actor $\rightarrow$ Return Response.
- **Pro Mode (Accuracy-Optimized)**: Tokenize $\rightarrow$ Load Actor $\rightarrow$ Generate v1 $\rightarrow$ Unload Actor $\rightarrow$ Load Critic $\rightarrow$ Evaluate v1 $\rightarrow$ (If Fail: Inject Feedback into Prompt, Loop back to Actor. Max 5 iterations) $\rightarrow$ Unload Critic $\rightarrow$ Post-Processing $\rightarrow$ Return to Client.

### 2.2 VRAM State Machine
The system enforces a strict invariant: **exactly one model resides in GPU memory at any time.**
- **IDLE** $\rightarrow$ `load_actor()` $\rightarrow$ **ACTOR LOADED** $\rightarrow$ `infer()` $\rightarrow$ `unload()` $\rightarrow$ **IDLE**
- **IDLE** $\rightarrow$ `load_critic()` $\rightarrow$ **CRITIC LOADED** $\rightarrow$ `infer()` $\rightarrow$ `unload()` $\rightarrow$ **IDLE**

> **Key Implementation Rule:** After every inference call, the system executes `del model` followed by `torch.cuda.empty_cache()`.

---

## 3. Repository Structure

```text
micro-agent-ensemble/
|-- .github/workflows/       # Lint, type-check, unit tests
|-- infra/
|   |-- docker/              # FastAPI + PyTorch runtime & Training env
|   |-- scripts/             # Driver/environment verification
|-- core/                    # SHARED - no mastery-specific code
|   |-- vram_scheduler/      # Hot-swap orchestrator & memory profiling
|   |-- tokenizers/          # Rust project manifest (PyO3 & Fast BPE)
|   |-- security/            # Rate limiting, payload caps, watermark
|-- masteries/
|   |-- coding/              # Actor: Code Gen, Critic: QA Reviewer
|   |-- literacy/            # Actor: Summarizer, Critic: Fact Checker
|   |-- research/            # Actor: Synthesizer, Critic: Citation Checker
|-- backend/
|   |-- main.py              # FastAPI application factory
|   |-- middleware/
|   |-- routers/             # Aggregates all mastery routers
|-- frontend/                # React + Vite Premium Cyberpunk UI
|-- research/                # Academic paper source & fixed seeds
|-- tests/                   # Integration & VRAM tests
```

---

## 4. Security Architecture

| Layer | Threat | Mitigation |
|-------|--------|------------|
| **Input Sanitization** | Prompt injection, oversized payloads, unicode bombs | Max token limit (enforced in Rust tokenizer); regex filters; payload size caps. |
| **Model Runtime** | Adversarial inputs causing OOM | Input size caps; inference timeout; VRAM watchdog thread. |
| **API Access** | Unauthorized access; quota abuse | JWT + API key dual auth; tiered quotas for fast vs. pro; rate limiting. |
| **Code Execution** | Arbitrary code execution from generated output | **Mandatory sandboxing**: Docker container with seccomp profile, no network access, read-only filesystem, 5-sec CPU timeout. |

---

## 5. Data Collection Strategy

### 5.1 Coding Mastery
- **Sources**: The Stack v2 (Pre-training), CodeContests, MBPP.
- **Critic Training**: Systematically perturb correct code (delete lines, swap variables). Train Critic to flag `BUG_TYPE` or `CLEAN`.

### 5.2 Literacy Mastery
- **Sources**: CNN/DailyMail, XSum, SQuAD 2.0.
- **Critic Training**: Generate hallucinated summaries (fabricated stats, entity swaps). Train Critic to label `HALLUCINATION` or `CONSISTENT`.

### 5.3 Research Mastery (Web-Augmented)
- **Sources**: arXiv dataset (Offline training), Semantic Scholar Open Research Corpus (S2ORC), PubMed Central.
- **Workflow**: Backend searches API $\rightarrow$ Fetches real Abstracts $\rightarrow$ Actor Generates Review $\rightarrow$ Critic Verifies Citations.
- **Critic Training (Synthetic Misattribution)**: Train critic by swapping citation numbers or mutating statistics to contradict source abstracts. Label as `VALID_CITATION`, `CONTRADICTS_SOURCE`, or `MISSING_CITATION`.

---

## 6. Critical Gaps and Mitigations

| Risk | Why It Matters | Mitigation |
|------|----------------|------------|
| **Training $\rightarrow$ Inference VRAM Gap** | A model training at 6GB may inference at 3GB, but optimizer states during training are massive. | Profile both phases separately. Use gradient accumulation or CPU offloading for training. |
| **Async + PyTorch GIL** | PyTorch CUDA ops block Python's GIL. Naive `async def` blocks all concurrent API requests. | Implemented a global generation thread lock (`threading.Lock()`) in the FastAPI router to prevent concurrent execution and CUDA OOM crashes. |
| **Tokenizer Misalignment** | Rust tokenizer and Python tokenizer producing different token IDs ruins model accuracy. | Unit test: identical string $\rightarrow$ identical token ID sequence in both environments. |
| **Loop Oscillation** | Actor fixes one thing, breaks another; infinite loops possible. | Max 5 iterations; confidence threshold; fallback to "I cannot answer." |

---

## 7. Hardware Budget Analysis (RTX 4060, 8GB)

| Component | Fast Tier (GB) | Pro Tier (GB) |
|-----------|----------------|---------------|
| **Actor Model** (~3B params, FP16) | ~4.5 | ~4.5 |
| **Critic Model** (~1.5B params, FP16) | — | ~2.5 |
| **Activation Cache** (max sequence) | ~0.8 | ~0.8 |
| **PyTorch CUDA Overhead** | ~1.2 | ~1.2 |
| **System / Display Reserve** | ~0.5 | ~0.5 |

> **Key Insight**: The PyTorch CUDA context initialization creates an immediate ~1.2GB floor. Because we hot-swap models and enforce a strict lock, the Peak VRAM usage will never exceed the size of the single largest model + context overhead, ensuring we safely remain under the 8GB limit.

---

## 8. Installation & Environment Verification

### Prerequisites
- NVIDIA driver $\ge$ 535, CUDA $\ge$ 12.1
- Python 3.10+, Node.js 18+

### Setup
1. **Clone the Repo:**
   ```bash
   git clone https://github.com/KiritoTempest175/PACE.git
   cd PACE
   ```
2. **Backend (FastAPI):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn masteries.api.router:router --port 8000
   ```
3. **Frontend (React + Vite):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Verification Checklist
- [x] PyTorch with CUDA support: `torch.cuda.is_available() = True`
- [x] VRAM baseline: `nvidia-smi` shows <500MB at idle
- [x] DVC initialized: `dvc init`, remote storage configured
- [x] Docker builds without errors: `docker compose up --build`

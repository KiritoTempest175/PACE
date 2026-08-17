# PACE (Pipelined Actor-Critic Ensemble)

![PACE Workspace](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![React](https://img.shields.io/badge/React-18-blue) ![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_Optimized-orange)

PACE is a local, on-device AI framework designed to run advanced reasoning workflows on consumer hardware (specifically optimized for **8GB VRAM** limits). It utilizes a dual-engine **Actor-Critic architecture** where an "Actor" model generates content and a "Critic" model iteratively reviews, validates, and critiques the output until it meets a high quality threshold.

## 🌟 Key Features

- **Pipelined Actor-Critic Architecture**: Iterative self-correction without human intervention. The Actor generates, the Critic reviews, and the Actor revises based on the critique.
- **Three Specialized Masteries**:
  - 💻 **Coding Mastery**: Code generation with AST-level validation.
  - 📚 **Literacy Mastery**: Advanced document processing, NLI summaries, and PDF parsing with zero data loss.
  - 🔬 **Research Mastery**: Literature synthesis, factual verification, and citation audits.
- **Execution Modes**:
  - ⚡ **Fast Mode**: Bypasses the Critic for rapid, single-shot Actor generation.
  - 🧠 **Pro Mode**: Engages the full Actor-Critic loop for deep reasoning and validation.
- **Real-Time Telemetry**: Beautiful sidebar telemetry tracking VRAM allocation, GPU compute utilization, and Local Throughput (Tokens/sec).
- **Concurrency & Memory Safety**: Built-in threading locks prevent CUDA Out-Of-Memory (OOM) exceptions by rejecting concurrent generations.
- **Premium Cyberpunk UI**: A dynamic, glassmorphism-inspired dark mode interface that feels responsive and state-of-the-art.

---

## 🏗️ Architecture

### AI Engine (Masteries)
Each mastery operates using a dedicated Orchestrator (`v4_orchestrator.py`) that manages the lifecycle of the models:
- **Coding**: Uses `Qwen2.5-Coder-3B-Instruct` (Actor) & `Qwen2.5-Coder-1.5B-Instruct` (Critic).
- **Research**: Uses `Phi-3-mini-4k-instruct` (Actor) & `Qwen2.5-Coder-1.5B-Instruct` (Critic).
- **Literacy**: Uses `SmolLM2-1.7B-Instruct` (Actor) & `Qwen2.5-Coder-1.5B-Instruct` (Critic).
Models are sequentially loaded and unloaded, with aggressive `gc.collect()` and `torch.cuda.empty_cache()` sweeps to ensure 8GB VRAM constraints are strictly respected.

### Backend (`/backend`)
A fast, asynchronous Python API built with **FastAPI**.
- Manages SQLite database interactions (`pace.db`) for conversation history.
- Streams Server-Sent Events (SSE) for token-by-token generation and real-time telemetry updates.
- Exposes endpoints for PDF chunking and data extraction.

### Frontend (`/frontend`)
A modern **React + Vite** application.
- Utilizes specialized components (`Sidebar.jsx`, `ChatInterface.jsx`, `HardwareMonitor.jsx`).
- Renders code blocks, markdown, and real-time telemetry graphs (Sparklines).

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- An NVIDIA GPU with at least **8GB VRAM** (CUDA Toolkit installed).

### 1. Clone the Repository
```bash
git clone https://github.com/KiritoTempest175/PACE.git
cd PACE
```

### 2. Backend Setup
Create a virtual environment and install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate # On Linux/Mac

pip install -r requirements.txt
```
Run the FastAPI backend:
```bash
uvicorn masteries.api.router:router --port 8000 --reload
# OR (depending on your entrypoint script)
uvicorn backend.main:app --port 8000
```
*Note: If you encounter Hugging Face rate limits, set your `HF_TOKEN` environment variable.*

### 3. Frontend Setup
Open a new terminal window, navigate to the frontend directory, and install dependencies:
```bash
cd frontend
npm install
```
Start the development server:
```bash
npm run dev
```

---

## 💻 Usage

1. Open your browser and navigate to `http://localhost:5173`.
2. **Dashboard**: View your system's real-time VRAM allocation and create a new session.
3. **Select a Mastery**: Choose between Coding, Literacy, or Research based on your task.
4. **Choose a Speed Mode**:
   - Select **Fast** for quick questions.
   - Select **Pro** for complex tasks requiring the Critic's validation.
5. **Chat**: Enter your prompt. The system will stream the response back, detailing the Actor's generation and the Critic's analysis if in Pro mode.

---

## 🛠️ Troubleshooting

- **CUDA Out of Memory (OOM)**: If the system crashes, ensure no other heavy GPU applications are running. PACE is strictly optimized for 8GB VRAM, but concurrent requests are locked to prevent spikes.
- **Proxy Errors (Frontend)**: If the frontend throws `ECONNREFUSED` errors, ensure the Python backend is running on `http://127.0.0.1:8000`.
- **Model Download Delays**: First-time execution will download the model weights (~10GB total across masteries) to your local Hugging Face cache (`~/.cache/huggingface`).

---

## 📜 License
*Proprietary / Internal Use* - Developed for Advanced Agentic Coding / Reasoning Research.

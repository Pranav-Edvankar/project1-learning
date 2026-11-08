# Week 3 Deliverable: Local Inference & Architecture Comparison

**Project:** Project 1: AI Tooling & Model Integration  
**Deliverable:** Week 3 Local LLM Evaluation & llama.cpp Comparison  
**Author:** Pranav Edvankar  

---

## 1. Local Inference Experiment Results (Ollama)
Tested using local Meta `llama3.2:1b` (4-bit quantized) via Ollama REST API (`POST http://localhost:11434/api/generate`):

* **Prompt:** `"Tell me a one-line joke about computers"`
* **Local Output:** *"Why did the computer go to therapy? Because it had a little glitch."*
* **Total Elapsed Time:** 3.08 seconds
* **Tokens Generated:** 16 tokens
* **Local Inference Speed:** 17.33 tokens/second
* **Cloud API Dependency:** None (100% offline on local CPU/RAM)

---

## 2. llama.cpp Overview
* **Role in AI Ecosystem:** Developed in C/C++ to execute raw LLM inference directly on consumer CPUs and GPUs without Python or PyTorch overhead.
* **GGUF Format:** The unified binary format storing model architecture, metadata, and quantized tensors in a single file.
* **Quantization:** Reduces weights from 16-bit to 4-bit (e.g., Q4_K_M), cutting RAM requirements by up to 70% with negligible reasoning loss.
* **Architecture Note:** Ollama embeds and uses `llama.cpp` as its core inference backend.

---

## 3. Comparison Matrix: Ollama vs. llama.cpp

| Attribute | Ollama | llama.cpp |
| :--- | :--- | :--- |
| **Setup Effort** | Minimal: 1-click installer and `ollama run` | Moderate/High: requires prebuilt binaries or CMake build |
| **Model Management** | Built-in registry (pulls models automatically) | Manual download of raw `.gguf` files from Hugging Face |
| **API Server** | Built-in HTTP server on port 11434 | Requires launching separate `server` executable |
| **Resource Control** | Automatic hardware layer detection | Manual flag tuning (CPU threads `-t`, GPU offload `-ngl`) |
| **Speed** | Near-native speed (~17.3 tokens/sec) | Bare-metal speed; slightly faster with custom AVX/CUDA flags |
| **Use Case** | Ideal for rapid prototyping and local application backends | Ideal for edge devices, embedded hardware, and C++ integration |
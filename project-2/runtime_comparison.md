# Project 2 Deliverable: Comparative Report of Large-Model Inference & Offloading Runtimes

**Author:** Pranav Edvankar  
**Project:** Project 2 — Large-Model-on-Light-Hardware Engine  
**Objective:** Evaluate existing open-source inference engines and memory-optimization strategies for executing large parameter models (14B to 70B+) on constrained consumer hardware.

---

## 1. Executive Comparison Matrix of Inference Runtimes

| Runtime / Repository | Primary Hardware Target | Supported Quantization | CPU/GPU Layer Offloading | Disk / NVMe Weight Streaming | Best Use Case in Our Initiative |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[llama.cpp](https://github.com/ggml-org/llama.cpp)** (MIT) | Consumer CPU, Apple Silicon, Hybrid CPU+GPU | GGUF: `Q2_K`, `Q3_K_S`, `Q4_K_M`, `Q5_K_M`, `Q8_0`, `IQ2_XXS` | Yes (`-ngl` layer split across VRAM and system RAM) | Yes (`mmap` OS page cache streaming) | **Primary Engine:** Best all-around runtime for 8 GB to 32 GB consumer laptops with or without discrete GPUs. |
| **[Ollama](https://github.com/ollama/ollama)** (MIT) | Consumer CPU, GPU, Apple Unified Memory | GGUF (`Q4_K_M`, `Q8_0`, custom Modelfiles) | Automatic GPU/CPU layer splitting (`num_gpu`) | Yes (`use_mmap: true` by default) | **Primary Local Daemon:** Wraps `llama.cpp` with an HTTP API (`:11434`) and automatic model lifecycle management. |
| **[MLC LLM](https://github.com/mlc-ai/mlc-llm)** (Apache 2.0) | Apple Metal, Vulkan, WebGPU, Mobile/Edge | 3-bit, 4-bit (`q4f16_1`, `q3f16_1`) via TVM compiler | Partial (targets unified memory and mobile GPUs) | No | **Secondary / Edge:** Useful when targeting WebGPU in-browser execution or mobile/iPad deployments. |
| **[ExLlamaV2](https://github.com/turboderp/exllamav2)** (MIT) | Dedicated NVIDIA GPUs (CUDA) | EXL2 (variable bit-rate: 2.0 to 8.0 bits per weight) | Limited (optimized for pure VRAM execution) | No | **GPU Specialist:** Fastest token generation on workstations with 8 GB to 24 GB NVIDIA RTX cards. |
| **[vLLM](https://github.com/vllm-project/vllm)** (Apache 2.0) | Enterprise / Cloud GPUs (NVIDIA, AMD ROCm) | AWQ, GPTQ, FP8, BitsAndBytes (4-bit) | PagedAttention CPU KV-cache swap | No | **Server / Cloud Scale:** High-throughput multi-user batching on dedicated GPU servers, too heavy for CPU laptops. |
| **[TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM)** (Apache 2.0) | NVIDIA Data Center & RTX GPUs | FP8, INT8, INT4-AWQ | Host memory KV-cache offloading | No | **NVIDIA Enterprise Only:** Maximum hardware-specific optimization on Tensor Core GPUs; not portable to Intel/AMD CPUs. |

---

## 2. Core Optimization Techniques for Constrained Hardware

1. **Sub-4-Bit & K-Quantization (`Q4_K_M`, `Q3_K_S`, `Q2_K`):**
   - An uncompressed 14B model (`FP16`) requires **~28 GB of memory** just for weights, making it impossible to load on a 16 GB laptop.
   - Using `Q4_K_M` (4.5 bits/weight) compresses weights to **~8.5 GB**; `Q2_K` (2.6 bits/weight) compresses weights to **~4.9 GB** while keeping attention super-blocks at higher precision.
2. **Memory-Mapped Weight Streaming (`mmap`):**
   - Instead of copying the entire model file into physical RAM upfront, `mmap` maps the GGUF file directly from NVMe SSD storage into the OS virtual address space. Pages are streamed into RAM on demand, preventing Out-of-Memory (OOM) crashes when free RAM is tight.
3. **Hybrid CPU/GPU Layer Offloading (`num_gpu` / `-ngl`):**
   - Transformer models consist of sequential repeating layers (e.g., 48 layers in Qwen-2.5 14B). Runtimes can place `N` layers in fast GPU VRAM and execute the remaining `48 - N` layers in system RAM.
4. **KV-Cache Quantization & Context Compression:**
   - At long contexts (8k to 32k tokens), the Key-Value (KV) attention cache can consume several gigabytes of RAM. Quantizing the KV cache from 16-bit to 8-bit or 4-bit (`q8_0` / `q4_0`) cuts context memory usage by 50% to 75%.
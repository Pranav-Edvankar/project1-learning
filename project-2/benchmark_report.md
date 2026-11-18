# Project 2: Large-Model-on-Light-Hardware Benchmark & Offloading Report

**Author:** Pranav Edvankar  
**Host System:** Windows 11 (64-bit) | Intel 12 Logical Cores (6 Physical) | 15.82 GB Total RAM (5.83–6.67 GB Free) | Intel UHD Graphics 730 (Shared RAM)  
**Inference Engine:** Bare-metal GGUF / `llama.cpp` runtime (via Ollama) with `use_mmap=True`, `low_vram=True`, and `KV-cache q8_0`  

---

## 1. Reproducible Hardware Benchmark Matrix (1B vs. 3B Scaling)

| Model | Uncompressed FP16 Size | Quantized GGUF Size | Active RAM Delta | Load Time | Time to 1st Token | Generation Speed | Validation Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`llama3.2:1b`** (`Q8_0`) | ~2.5 GB | 1.23 GB | **1,417.49 MB (~1.42 GB)** | 3.13s | 3.39s | **16.20 tok/s** | **Validated by Team (Smooth / Light Load)** |
| **`llama3.2:3b`** (`Q4_K_M`) | ~6.4 GB | 1.88 GB | **3,539.27 MB (~3.54 GB)** | 3.45s | 3.82s | **9.71 tok/s** | **Validated by Team (Moderate / Heavier Load)** |
| **`llama3.1:8b`** (`Q3_K_S` / `Q2_K`) | ~16.0 GB | 3.77 GB | ~4,800 MB (Est) | ~5.2s | ~5.8s | **~6.5 tok/s** | **Experimental (Requires `mmap` + 2K Context)** |
| **`qwen2.5:14b`** (`Q2_K` + Disk `mmap`) | ~28.5 GB | 5.40 GB | ~5,600 MB (Streamed) | ~9.5s | ~11.0s | **~3.2 tok/s** | **Experimental (Beyond-Capacity SSD Offload)** |

---

## 2. Engineering Findings & Definition of Done Verification

1. **Squeezing Models Beyond Native Uncompressed Capacity:**
   - In uncompressed `FP16`, `llama3.2:3b` requires **~6.4 GB of contiguous memory** plus KV-cache (~7.2 GB total), which exceeds the host machine's **5.83 GB of free RAM** and would trigger an Out-of-Memory crash.
   - By combining **4-bit K-quantization (`Q4_K_M`)**, **memory-mapped SSD weight streaming (`use_mmap: true`)**, **low-VRAM buffers (`low_vram: true`)**, and **physical core pinning (`num_thread: 6`)**, the runtime executes `llama3.2:3b` stably inside **3.54 GB of RAM** at **9.71 tokens/second** with zero crashes.
2. **Scaling Law on Consumer CPU RAM:**
   - Tripling parameter count from `1B` to `3B` increased active memory consumption by **2.49x** (`1.42 GB` to `3.54 GB`) and reduced CPU token throughput by **40%** (`16.20 tok/s` to `9.71 tok/s`), confirming that consumer DDR4/DDR5 memory bandwidth (~40 GB/s) is the primary bottleneck.
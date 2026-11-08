# Project 2: Large-Model-on-Light-Hardware Benchmark Report

**Host RAM:** 15.82 GB  
**Benchmark Prompt:** Technical CPU vs GPU architecture comparison (deterministic T=0.0)  
**Inference Engine:** Bare-metal GGUF / llama.cpp runtime (via Ollama)  

---

## 1. Measured Performance Matrix

| Model | Quantization | RAM Usage Delta | Load Time | Time to 1st Token | Speed (Tokens/Sec) | Total Time |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` | Q4_K_M (4-bit) | 2425.1 MB | 3.35s | 3.756s | **10.47 tps** | 29.7s |
| `llama3.2:1b` | Q4_K_M (4-bit) | 1331.6 MB | 2.098s | 2.473s | **16.47 tps** | 19.29s |

---

## 2. Engineering Analysis & Hardware Limits

- **Memory Footprint:** 4-bit quantization allows models to run with negligible memory overhead compared to uncompressed 16-bit baselines.
- **Memory Bandwidth Bottleneck:** Token generation speed is directly constrained by system DDR4/DDR5 RAM bandwidth (~30-60 GB/s on consumer CPUs).
- **Stability:** Zero Out-of-Memory (OOM) crashes observed during continuous generation.

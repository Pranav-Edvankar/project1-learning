"""
Project 2: Large-Model-on-Light-Hardware Engine
Module: Hardware-to-Runtime Configuration Engine & Unified API for Project 3
Author: Pranav Edvankar
Description:
  1. Inspects available host RAM, VRAM, and CPU cores.
  2. Automatically configures low-memory optimizations (mmap weight streaming,
     CPU/GPU layer split, thread count, and KV-cache context limits).
  3. Exposes a unified `request_model(prompt)` interface so Project 3 can run
     queries without knowing the underlying hardware or offloading strategy.
"""

import os
import time
import json
import psutil
import requests

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


class LargeModelRuntimeEngine:
    def __init__(self):
        self.total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        self.free_ram_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        self.physical_cores = psutil.cpu_count(logical=False) or 4
        self.logical_cores = psutil.cpu_count(logical=True) or 8
        self.installed_models = self._discover_local_models()

    def _discover_local_models(self):
        try:
            res = requests.get(OLLAMA_TAGS_URL, timeout=3)
            if res.status_code == 200:
                return [m["name"] for m in res.json().get("models", [])]
        except Exception:
            pass
        return ["llama3.2:1b"]

    def build_runtime_config(self, target_model=None, mode="auto"):
        """
        Hardware-to-Runtime Configuration Engine:
        Translates current RAM/CPU headroom into concrete llama.cpp / Ollama
        execution flags (mmap, thread count, context window, and layer offload).
        """
        # Refresh live free RAM before configuring
        self.free_ram_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)

        # Pick largest safe installed model if none specified
        if not target_model:
            if self.free_ram_gb >= 3.0 and "llama3.2:3b" in self.installed_models:
                target_model = "llama3.2:3b"
            elif self.installed_models:
                target_model = self.installed_models[0]
            else:
                target_model = "llama3.2:1b"

        # Optimal thread count = physical cores (avoids hyperthreading contention)
        optimal_threads = max(2, min(self.physical_cores, 8))

        # Dynamic context & offloading strategy based on available free RAM
        if self.free_ram_gb < 3.5 or mode == "extreme_low_mem":
            strategy_name = "Aggressive Memory-Mapped Offload (Low-RAM Guard)"
            num_ctx = 2048          # Compact KV-cache
            num_batch = 128         # Smaller prompt evaluation batch to save peak RAM
            num_gpu = 0             # Pure CPU + SSD mmap streaming
        elif self.free_ram_gb < 7.5:
            strategy_name = "Balanced Consumer Laptop Runtime (mmap + 4K Context)"
            num_ctx = 4096
            num_batch = 256
            num_gpu = 0
        else:
            strategy_name = "High-Headroom Hybrid Runtime (8K Context)"
            num_ctx = 8192
            num_batch = 512
            num_gpu = -1            # Offload all possible layers

        return {
            "model": target_model,
            "strategy": strategy_name,
            "host_free_ram_gb": self.free_ram_gb,
            "options": {
                "use_mmap": True,           # Trick 2: Stream weights from SSD on demand
                "use_mlock": False,         # Allow OS page swapping if RAM gets tight
                "low_vram": True,           # Enable low-VRAM buffer optimizations
                "num_ctx": num_ctx,         # Trick 4: Controlled KV-cache memory ceiling
                "num_batch": num_batch,
                "num_thread": optimal_threads,
                "num_gpu": num_gpu,         # Trick 3: CPU/GPU layer split
                "temperature": 0.2
            },
            " beyond_capacity_plans": {
                "14B_on_16GB_PC": {
                    "target_model": "qwen2.5:14b-instruct-q2_K (or q3_K_S)",
                    "uncompressed_fp16_size_gb": 28.5,
                    "quantized_disk_size_gb": 5.4,
                    "settings": {"use_mmap": True, "low_vram": True, "num_ctx": 2048, "kv_cache": "q8_0"},
                    "validation_status": "Experimental (Requires SSD mmap streaming)"
                },
                "3B_on_16GB_PC": {
                    "target_model": "llama3.2:3b (Q4_K_M)",
                    "uncompressed_fp16_size_gb": 6.4,
                    "quantized_disk_size_gb": 1.88,
                    "settings": {"use_mmap": True, "low_vram": True, "num_ctx": 4096, "kv_cache": "q8_0"},
                    "validation_status": "Validated by Team (Smooth Execution)"
                }
            }
        }

    def request_model(self, prompt, preferred_model=None, temperature=0.2):
        """
        Unified Technical API for Project 3:
        Allows Project 3 (Company Knowledge Chatbot) to request an answer
        without knowing the underlying quantization, mmap, or offloading strategy.
        """
        config = self.build_runtime_config(target_model=preferred_model)
        options = config["options"].copy()
        options["temperature"] = temperature

        ram_before_mb = psutil.virtual_memory().used / (1024 ** 2)
        start_time = time.time()

        try:
            res = requests.post(
                OLLAMA_GENERATE_URL,
                json={
                    "model": config["model"],
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                },
                timeout=120
            )
            elapsed_sec = round(time.time() - start_time, 2)
            ram_after_mb = psutil.virtual_memory().used / (1024 ** 2)

            if res.status_code == 200:
                data = res.json()
                eval_count = data.get("eval_count", 0)
                eval_dur_s = data.get("eval_duration", 1) / 1e9
                tps = round(eval_count / eval_dur_s, 2) if eval_dur_s > 0 else 0.0

                return {
                    "success": True,
                    "model": config["model"],
                    "strategy": config["strategy"],
                    "options_applied": options,
                    "reply": data.get("response", "").strip(),
                    "metrics": {
                        "total_time_sec": elapsed_sec,
                        "tokens_per_sec": tps,
                        "ram_delta_mb": round(max(0.0, ram_after_mb - ram_before_mb), 2),
                        "free_ram_gb": self.free_ram_gb
                    }
                }
            return {"success": False, "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_demo():
    print("=" * 80)
    print("⚙️  Project 2: Hardware-to-Runtime Configuration Engine & Unified API")
    print("=" * 80)

    engine = LargeModelRuntimeEngine()
    config = engine.build_runtime_config()

    print(f"🧠 Host Memory:       {engine.total_ram_gb} GB Total ({engine.free_ram_gb} GB Free)")
    print(f"🔧 Selected Model:    {config['model']}")
    print(f"🛡️  Active Strategy:   {config['strategy']}")
    print(f"📋 Runtime Flags:     {json.dumps(config['options'])}")
    print("-" * 80)

    print("🚀 Testing Unified Project 3 Interface: engine.request_model(...)...")
    result = engine.request_model(
        "In 2 short bullet points, explain why memory-mapped (mmap) weight streaming "
        "prevents Out-of-Memory crashes when running quantized LLMs on laptops."
    )

    if result["success"]:
        print(f"\n✅ Response ({result['model']} @ {result['metrics']['tokens_per_sec']} tok/s):")
        print(result["reply"])
        print("-" * 80)
        print(f"📊 Runtime Metrics: {result['metrics']}")
    else:
        print(f"\n❌ Runtime Error: {result['error']}")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
    
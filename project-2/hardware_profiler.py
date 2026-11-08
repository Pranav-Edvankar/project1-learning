"""
Project 2: Large-Model-on-Light-Hardware Engine
Module: Hardware Detection & Model Sizing Profiler
Author: Pranav Edvankar
Description: Automatically inspects host CPU, RAM, GPU/VRAM, and storage,
             calculates mathematical memory requirements for various quantization
             formats (FP16, Q8, Q4, Q3, Q2), and outputs feasible model recommendations.
"""

import os
import sys
import json
import platform
import subprocess
import psutil

# 1. Hardware Inspection Engine
def detect_hardware():
    profile = {
        "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        "cpu": {
            "name": platform.processor() or "Unknown CPU",
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
        },
        "ram": {
            "total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024 ** 3), 2),
            "used_gb": round(psutil.virtual_memory().used / (1024 ** 3), 2),
            "percent_used": psutil.virtual_memory().percent
        },
        "disk": {
            "free_gb": round(psutil.disk_usage(".").free / (1024 ** 3), 2),
            "total_gb": round(psutil.disk_usage(".").total / (1024 ** 3), 2)
        },
        "gpu": detect_gpu()
    }
    return profile

def detect_gpu():
    gpu_info = {"type": "CPU Only", "vram_gb": 0.0, "devices": []}

    # Check for NVIDIA GPUs via nvidia-smi
    try:
        smi_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        lines = smi_out.strip().split("\n")
        total_vram = 0.0
        devices = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2:
                name = parts[0]
                vram_mb = float(parts[1])
                vram_gb = round(vram_mb / 1024, 2)
                total_vram += vram_gb
                devices.append({"name": name, "vram_gb": vram_gb})
        if devices:
            gpu_info = {"type": "NVIDIA CUDA", "vram_gb": total_vram, "devices": devices}
            return gpu_info
    except Exception:
        pass

    # Windows WMIC fallback (checks for Intel/AMD/NVIDIA display adapters)
    if platform.system() == "Windows":
        try:
            wmic_out = subprocess.check_output(
                ["powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -Property Name, AdapterRAM"],
                encoding="utf-8"
            )
            for line in wmic_out.split("\n"):
                if "NVIDIA" in line or "AMD" in line or "Radeon" in line or "Intel" in line:
                    gpu_info["devices"].append({"name": line.strip(), "vram_gb": "Shared / System Managed"})
                    gpu_info["type"] = "Integrated / Hybrid"
        except Exception:
            pass

    return gpu_info


# 2. Mathematical Model Sizing & Quantization Sizer
# Formulas based on GGUF tensor layouts and llmfit specification
MODEL_CATALOG = [
    {"family": "Llama-3.2", "params_b": 1.0, "layers": 16},
    {"family": "Llama-3.2", "params_b": 3.0, "layers": 28},
    {"family": "Qwen-2.5",  "params_b": 7.0, "layers": 28},
    {"family": "Llama-3.1", "params_b": 8.0, "layers": 32},
    {"family": "Qwen-2.5",  "params_b": 14.0, "layers": 48},
    {"family": "Qwen-2.5",  "params_b": 32.0, "layers": 64},
    {"family": "Llama-3.1", "params_b": 70.0, "layers": 80},
]

# Approximate bits-per-weight (bpw) and memory multiplier including runtime overhead
QUANT_PROFILES = {
    "FP16":   {"bpw": 16.0, "overhead_gb": 1.5, "desc": "Uncompressed 16-bit baseline"},
    "Q8_0":   {"bpw": 8.5,  "overhead_gb": 1.2, "desc": "High quality 8-bit quantization"},
    "Q4_K_M": {"bpw": 4.5,  "overhead_gb": 1.0, "desc": "Standard recommended 4-bit balance"},
    "Q3_K_S": {"bpw": 3.5,  "overhead_gb": 0.8, "desc": "Aggressive 3-bit space-saving"},
    "Q2_K":   {"bpw": 2.6,  "overhead_gb": 0.6, "desc": "Ultra-compressed 2-bit (extreme offload)"}
}

def calculate_model_memory(params_b, quant_key, context_tokens=4096):
    q = QUANT_PROFILES[quant_key]
    # Weight size = (Parameters * bits per weight) / 8 bits per byte
    weight_gb = (params_b * q["bpw"]) / 8.0
    # Approximate 4k context KV-cache buffer
    kv_cache_gb = (params_b / 7.0) * (context_tokens / 4096.0) * 0.5
    total_required_gb = round(weight_gb + kv_cache_gb + q["overhead_gb"], 2)
    return total_required_gb


# 3. Decision & Compatibility Matrix Generator
def generate_hardware_recommendations(profile):
    usable_ram = profile["ram"]["available_gb"]
    vram = profile["gpu"]["vram_gb"] if isinstance(profile["gpu"]["vram_gb"], (int, float)) else 0.0
    total_unified_memory = usable_ram + vram

    recommendations = []

    for model in MODEL_CATALOG:
        for q_name in ["FP16", "Q8_0", "Q4_K_M", "Q3_K_S", "Q2_K"]:
            mem_needed = calculate_model_memory(model["params_b"], q_name)
            
            # Execution Strategy Assessment
            if vram > 0 and mem_needed <= (vram * 0.9):
                status = "Pure GPU (Fastest: 50-100+ tps)"
                feasible = True
            elif mem_needed <= (total_unified_memory * 0.85):
                if vram > 0:
                    offload_layers = int((vram / mem_needed) * model["layers"])
                    status = f"Hybrid Offload ({offload_layers}/{model['layers']} layers on GPU)"
                else:
                    status = "Pure CPU RAM (15-25 tps)"
                feasible = True
            elif mem_needed <= total_unified_memory:
                status = "Borderline / High OOM Risk"
                feasible = False
            else:
                status = "Infeasible on current RAM (Requires Disk Offload)"
                feasible = False

            if feasible or q_name in ["Q4_K_M", "Q2_K"]:
                recommendations.append({
                    "model": f"{model['family']} ({model['params_b']}B)",
                    "quant": q_name,
                    "ram_required_gb": mem_needed,
                    "status": status,
                    "feasible": feasible
                })

    return recommendations


# 4. Display & Report Output
def run_profiler():
    print("=" * 80)
    print("🔬 Project 2: Host Hardware Profiler & Model Sizing Engine")
    print("=" * 80)

    profile = detect_hardware()
    print(f"🖥️  OS:            {profile['os']}")
    print(f"⚙️  CPU:           {profile['cpu']['name']} ({profile['cpu']['logical_cores']} logical cores)")
    print(f"🧠 System RAM:    {profile['ram']['total_gb']} GB Total ({profile['ram']['available_gb']} GB Free / Available)")
    print(f"🎮 GPU / VRAM:    {profile['gpu']['type']} - {profile['gpu']['vram_gb']} GB VRAM")
    if profile['gpu']['devices']:
        for d in profile['gpu']['devices']:
            print(f"   └─ Device:     {d['name']} ({d['vram_gb']} VRAM)")
    print(f"💾 Storage:       {profile['disk']['free_gb']} GB Free Disk Space")
    print("=" * 80)

    recs = generate_hardware_recommendations(profile)

    print("\n📊 Model Sizing & Execution Feasibility Matrix:")
    print("-" * 80)
    print(f"{'Model Name':<20} | {'Quant':<8} | {'RAM Needed':<12} | {'Recommended Strategy'}")
    print("-" * 80)

    for r in recs:
        marker = "✅" if r["feasible"] else "⚠️"
        print(f"{marker} {r['model']:<18} | {r['quant']:<8} | {str(r['ram_required_gb']) + ' GB':<12} | {r['status']}")

    print("-" * 80)
    print("\n💡 Key Benchmark Takeaway:")
    available = profile['ram']['available_gb']
    print(f"Based on your {available} GB of available memory:")
    feasible_models = [r for r in recs if r["feasible"]]
    if feasible_models:
        best_model = feasible_models[-1]
        print(f"👉 Largest practically executable model on this machine is: {best_model['model']} at {best_model['quant']}")
        print(f"   Requires ~{best_model['ram_required_gb']} GB RAM ({best_model['status']}).")
    print("=" * 80)

    # Save to JSON for dashboard integration
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware_profile.json")
    with open(out_file, "w") as f:
        json.dump({"profile": profile, "recommendations": recs}, f, indent=2)
    print(f"📁 Hardware profile saved to: {out_file}\n")

if __name__ == "__main__":
    run_profiler()
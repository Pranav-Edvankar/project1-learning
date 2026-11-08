"""
Week 3 Mini-Project: Local LLM Inference via Ollama REST API
Author: Pranav Edvankar
Description: Sends a prompt to the local Ollama API server (port 11434)
             and measures local generation speed and token counts.
"""

import requests
import json
import time

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:1b"

def run_local_inference(prompt):
    print("=" * 65)
    print(f"🤖 Sending prompt to Local Ollama ({MODEL_NAME})...")
    print("=" * 65)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False  # Return a single complete JSON response
    }

    start_time = time.time()
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            reply = data.get("response", "").strip()

            # Hardware & generation metrics reported by Ollama
            eval_count = data.get("eval_count", 0)  # Total tokens generated
            eval_duration_ns = data.get("eval_duration", 1)  # Duration in nanoseconds
            eval_duration_sec = eval_duration_ns / 1e9
            tokens_per_sec = eval_count / eval_duration_sec if eval_duration_sec > 0 else 0

            print(f"\nPrompt: '{prompt}'")
            print(f"\nAI Response:\n{reply}\n")
            print("-" * 65)
            print("📊 Local Performance Metrics:")
            print(f"  • Total Time:       {elapsed_time:.2f} seconds")
            print(f"  • Tokens Generated: {eval_count} tokens")
            print(f"  • Generation Speed: {tokens_per_sec:.2f} tokens/second")
            print("-" * 65)
        else:
            print(f"❌ Error {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Ollama.")
        print("Make sure Ollama is running in your Windows taskbar!")

if __name__ == "__main__":
    test_prompt = "Tell me a one-line joke about computers"
    run_local_inference(test_prompt)
    
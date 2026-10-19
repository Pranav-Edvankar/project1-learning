"""
Week 4 Final Capstone: Provider-Agnostic Model Gateway
Author: Pranav Edvankar
Description: Abstract ModelProvider interface with adapters for Groq (Cloud)
             and Ollama (Local). Includes a live status dashboard and provider switcher.
"""

import os
import time
import requests
from abc import ABC, abstractmethod
from flask import Flask, request, jsonify, render_template, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# 1. Load environment variables (searches week-2/.env and root .env)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(current_dir, ".env"))
load_dotenv(os.path.join(parent_dir, ".env"))
load_dotenv(os.path.join(parent_dir, "week-2", ".env"))


# =====================================================================
# 2. Abstract Base Class (The Universal Interface)
# =====================================================================
class ModelProvider(ABC):
    @abstractmethod
    def testConnection(self) -> dict:
        """Pings the provider and returns status and latency."""
        pass

    @abstractmethod
    def getModels(self) -> list:
        """Returns a list of available models."""
        pass

    @abstractmethod
    def generate(self, prompt: str, model: str = None) -> dict:
        """Generates text from the given prompt."""
        pass


# =====================================================================
# 3. Adapter 1: Groq Cloud Provider
# =====================================================================
class GroqProvider(ModelProvider):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.default_model = "openai/gpt-oss-120b"

    def testConnection(self) -> dict:
        if not self.api_key:
            return {"status": "offline", "error": "GROQ_API_KEY missing in .env"}
        start = time.time()
        try:
            r = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            latency = round((time.time() - start) * 1000, 2)
            if r.status_code == 200:
                return {"status": "online", "latency_ms": latency}
            return {"status": "offline", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def getModels(self) -> list:
        if not self.api_key:
            return []
        try:
            r = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            if r.status_code == 200:
                return [m["id"] for m in r.json().get("data", []) if "whisper" not in m["id"]]
        except Exception:
            pass
        return [self.default_model]

    def generate(self, prompt: str, model: str = None) -> dict:
        chosen_model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": chosen_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        start = time.time()
        try:
            r = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=20)
            elapsed = round(time.time() - start, 2)
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"].strip()
                return {"success": True, "provider": "Groq (Cloud)", "model": chosen_model, "reply": text, "time_sec": elapsed}
            return {"success": False, "error": f"Groq Error ({r.status_code}): {r.text}"}
        except Exception as e:
            return {"success": False, "error": f"Groq Connection Error: {str(e)}"}


# =====================================================================
# 4. Adapter 2: Local Ollama Provider
# =====================================================================
class OllamaProvider(ModelProvider):
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.default_model = "llama3.2:1b"

    def testConnection(self) -> dict:
        start = time.time()
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            latency = round((time.time() - start) * 1000, 2)
            if r.status_code == 200:
                return {"status": "online", "latency_ms": latency}
            return {"status": "offline", "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "offline", "error": "Ollama service not running"}

    def getModels(self) -> list:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return [self.default_model]

    def generate(self, prompt: str, model: str = None) -> dict:
        chosen_model = model or self.default_model
        payload = {
            "model": chosen_model,
            "prompt": prompt,
            "stream": False
        }
        start = time.time()
        try:
            r = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            elapsed = round(time.time() - start, 2)
            if r.status_code == 200:
                text = r.json().get("response", "").strip()
                return {"success": True, "provider": "Ollama (Local)", "model": chosen_model, "reply": text, "time_sec": elapsed}
            return {"success": False, "error": f"Ollama Error ({r.status_code}): {r.text}"}
        except Exception as e:
            return {"success": False, "error": f"Ollama Connection Error: {str(e)}"}


# =====================================================================
# 5. The Model Gateway Registry
# =====================================================================
class ModelGateway:
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "ollama": OllamaProvider()
        }

    def get_system_status(self) -> dict:
        report = {}
        for name, provider in self.providers.items():
            report[name] = {
                "connection": provider.testConnection(),
                "models": provider.getModels()
            }
        return report

    def route_generate(self, prompt: str, provider_name: str, model: str = None) -> dict:
        if provider_name not in self.providers:
            return {"success": False, "error": f"Unknown provider: '{provider_name}'"}
        provider = self.providers[provider_name]
        return provider.generate(prompt, model)


# =====================================================================
# 6. Web Application & Dashboard
# =====================================================================
app = Flask(__name__, template_folder=os.path.join(current_dir, "templates"))
CORS(app)
gateway = ModelGateway()


@app.route("/")
def dashboard():
    template_path = os.path.join(current_dir, "templates", "index.html")
    if os.path.exists(template_path):
        return render_template("index.html")
    return "Error: week-4/templates/index.html not found.", 404


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(gateway.get_system_status())


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or body.get("message") or "").strip()
    provider = body.get("provider", "groq")
    model = body.get("model")

    if not prompt:
        return jsonify({"success": False, "error": "Prompt cannot be empty."}), 400

    result = gateway.route_generate(prompt, provider, model)
    return jsonify(result), (200 if result.get("success") else 500)


if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Week 4 Model Gateway running!")
    print("👉 Dashboard: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(debug=True, port=5000)
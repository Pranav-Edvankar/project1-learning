import os
import requests
from flask import Flask, request, jsonify, render_template, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# 1. Automatically locate and load .env in the same folder as server.py
current_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(current_dir, ".env")
env_txt_file = os.path.join(current_dir, ".env.txt")

if os.path.exists(env_file):
    load_dotenv(env_file)
elif os.path.exists(env_txt_file):
    load_dotenv(env_txt_file)
else:
    load_dotenv()

app = Flask(__name__, template_folder=os.path.join(current_dir, "templates"))
CORS(app)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
# Verify API key
key = os.getenv("GROQ_API_KEY")
print("=" * 60)
print(f"✅ GROQ_API_KEY loaded: {key[:7]}... (Length: {len(key) if key else 0})")
print("=" * 60)


# 2. Frontend Web Interface (Nothing OS Design Language)
@app.route("/")
def home():
    template_path = os.path.join(current_dir, "templates", "index.html")
    if os.path.exists(template_path):
        return render_template("index.html")
    return "Error: templates/index.html not found.", 404


@app.route("/api/models", methods=["GET"])
def get_models():
    return jsonify({
        "models": [
            {"id": "openai/gpt-oss-120b", "name": "GPT-120B", "desc": "Flagship Reasoning & Analysis", "tag": "120B"},
            {"id": "openai/gpt-oss-20b", "name": "GPT-20B", "desc": "High-Speed Instant Latency", "tag": "20B"},
            {"id": "qwen/qwen3.8-27b", "name": "QWEN-27B", "desc": "Balanced Multitask Model", "tag": "27B"}
        ]
    }), 200


# 3. Backend Endpoint: POST /api/chat
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Bad Request: 'message' field is required in JSON payload."}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Bad Request: message cannot be empty."}), 400

    model = data.get("model", DEFAULT_MODEL)
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return jsonify({"error": "Unauthorized: GROQ_API_KEY is missing in .env."}), 401

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful, concise AI assistant."},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            ai_reply = result["choices"][0]["message"]["content"]
            return jsonify({"reply": ai_reply, "model": model}), 200
        else:
            provider_error = response.json().get("error", {}).get("message", response.text)
            return jsonify({"error": f"Provider Error: {provider_error}"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Gateway Timeout: Upstream AI model took too long to respond."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection Error: {str(e)}"}), 500


# 4. Start Server
if __name__ == "__main__":
    print("🚀 Week 2 AI Chatbot Server running!")
    print("👉 Serving at: http://127.0.0.1:5000 (Keep this terminal window open!)")
    print("=" * 60)
    app.run(debug=True, port=5000)
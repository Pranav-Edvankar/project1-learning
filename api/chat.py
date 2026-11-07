import os
import json
import requests
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8")) if body else {}

        prompt = data.get("prompt", "").strip()
        model = data.get("model", "openai/gpt-oss-120b")
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "GROQ_API_KEY not configured on Vercel"}).encode())
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=20)
            self.send_response(r.status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if r.status_code == 200:
                reply = r.json()["choices"][0]["message"]["content"].strip()
                self.wfile.write(json.dumps({"success": True, "reply": reply, "provider": "Groq (Cloud)", "model": model}).encode())
            else:
                self.wfile.write(json.dumps({"success": False, "error": r.text}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
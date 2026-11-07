import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode("utf-8")) if body else {}

        # Accept either "prompt" or "message" (supports both frontend styles)
        prompt = data.get("prompt") or data.get("message") or ""
        model = data.get("model") or "openai/gpt-oss-120b"
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            self._send(500, {"success": False, "error": "GROQ_API_KEY not configured in Vercel Environment Variables."})
            return

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                result = json.loads(response.read().decode("utf-8"))
                reply = result["choices"][0]["message"]["content"].strip()
                self._send(200, {"success": True, "reply": reply, "provider": "Groq (Cloud)", "model": model})
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            self._send(e.code, {"success": False, "error": f"Groq Error ({e.code}): {err_msg}"})
        except Exception as e:
            self._send(500, {"success": False, "error": f"Gateway Error: {str(e)}"})

    def _send(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
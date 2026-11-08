# Week 2 Test Documentation: AI Chatbot Backend & Web Interface

**Project:** Project 1: AI Tooling & Model Integration  
**Deliverable:** `week2-tests.md`  
**Target Component:** Week 2 Flask API Server (`server.py`) & Web UI (`templates/index.html`)  

---

## 1. Overview & Architecture

Week 2 integrates a local backend service with cloud-based Large Language Models via Groq's high-speed inference API.

- **Backend:** Flask web server with CORS support (`server.py`)
- **API Provider:** Groq Cloud (`https://api.groq.com/openai/v1/chat/completions`)
- **Frontend UI:** Nothing OS-inspired dark/matrix design interface (`templates/index.html`)
- **Environment & Secrets:** Handled via `.env` and kept safe by `.gitignore`

---

## 2. Environment & Security Verification

### Test 2.1: `.env` Security via `.gitignore`
* **Objective:** Ensure sensitive API credentials (`GROQ_API_KEY`) are protected and never committed to version control.
* **Verification Command:**
  ```bash
  git check-ignore -v week-2/.env
  ```
* **Expected Result:**
  ```text
  .gitignore:1:.env    week-2/.env
  ```
* **Status:** Passed

---

## 3. API Test Suite & Specifications

### Test 3.1: Root Route (Web Interface Delivery)
* **Endpoint:** `GET /`
* **Test Method:**
  ```bash
  curl -I http://127.0.0.1:5000/
  ```
* **Expected Status Code:** `200 OK`
* **Expected Response Header:** `Content-Type: text/html; charset=utf-8`
* **Result:** Successfully serves `week-2/templates/index.html`.

---

### Test 3.2: Model Catalog Endpoint
* **Endpoint:** `GET /api/models`
* **Test Method:**
  ```bash
  curl -s http://127.0.0.1:5000/api/models
  ```
* **Expected Status Code:** `200 OK`
* **Expected JSON Payload:**
  ```json
  {
    "models": [
      {
        "desc": "Flagship Reasoning & Analysis",
        "id": "openai/gpt-oss-120b",
        "name": "GPT-120B",
        "tag": "120B"
      },
      {
        "desc": "High-Speed Instant Latency",
        "id": "openai/gpt-oss-20b",
        "name": "GPT-20B",
        "tag": "20B"
      },
      {
        "desc": "Balanced Multitask Model",
        "id": "qwen/qwen3.8-27b",
        "name": "QWEN-27B",
        "tag": "27B"
      }
    ]
  }
  ```
* **Result:** Verified model options returned correctly.

---

### Test 3.3: Chat Completion API - Standard Request
* **Endpoint:** `POST /api/chat`
* **Headers:** `Content-Type: application/json`
* **PowerShell Test Command:**
  ```powershell
  $body = @{
      message = "Hello! Explain what a token is in one sentence."
      model   = "openai/gpt-oss-120b"
  } | ConvertTo-Json

  Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/chat" -Method Post -Body $body -ContentType "application/json"
  ```
* **cURL Test Command:**
  ```bash
  curl -X POST http://127.0.0.1:5000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello! Explain what a token is in one sentence.", "model": "openai/gpt-oss-120b"}'
  ```
* **Expected Status Code:** `200 OK`
* **Expected Response Format:**
  ```json
  {
    "model": "openai/gpt-oss-120b",
    "reply": "A token is a sub-word chunk or character sequence converted into a numeric identifier that an AI model processes."
  }
  ```
* **Result:** Passed (Inference succeeds with upstream Groq API).

---

### Test 3.4: Chat API - Input Validation (Empty Message)
* **Endpoint:** `POST /api/chat`
* **Test Payload:** `{"message": "   "}`
* **Expected Status Code:** `400 Bad Request`
* **Expected Response:**
  ```json
  {
    "error": "Bad Request: message cannot be empty."
  }
  ```
* **Result:** Handled correctly.

---

### Test 3.5: Chat API - Input Validation (Missing Payload)
* **Endpoint:** `POST /api/chat`
* **Test Payload:** `{}`
* **Expected Status Code:** `400 Bad Request`
* **Expected Response:**
  ```json
  {
    "error": "Bad Request: 'message' field is required in JSON payload."
  }
  ```
* **Result:** Handled correctly.

---

### Test 3.6: Chat API - Unauthorized / Missing Key
* **Condition:** `GROQ_API_KEY` unset or absent in `.env`.
* **Expected Status Code:** `401 Unauthorized`
* **Expected Response:**
  ```json
  {
    "error": "Unauthorized: GROQ_API_KEY is missing in .env."
  }
  ```
* **Result:** Protected against runtime exceptions when unconfigured.

---

### Test 3.7: Chat API - Upstream Timeout Handling
* **Condition:** Network latency > 15s.
* **Expected Status Code:** `504 Gateway Timeout`
* **Expected Response:**
  ```json
  {
    "error": "Gateway Timeout: Upstream AI model took too long to respond."
  }
  ```
* **Result:** Verified timeout guard in requests call.

---

## 4. Test Summary Checklist

| # | Test Case | Target | Expected Status | Result |
|---|-----------|--------|-----------------|--------|
| 1 | Web Page Serving | `GET /` | `200 OK` | ✅ Passed |
| 2 | Model Directory Listing | `GET /api/models` | `200 OK` | ✅ Passed |
| 3 | AI Chat Inference | `POST /api/chat` | `200 OK` | ✅ Passed |
| 4 | Empty String Validation | `POST /api/chat` | `400 Bad Request` | ✅ Passed |
| 5 | Missing Field Validation | `POST /api/chat` | `400 Bad Request` | ✅ Passed |
| 6 | Missing Credentials Guard | `POST /api/chat` | `401 Unauthorized` | ✅ Passed |
| 7 | Git Isolation for `.env` | `.gitignore` | Ignored | ✅ Passed |

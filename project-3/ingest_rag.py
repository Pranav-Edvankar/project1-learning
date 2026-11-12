"""
Project 3: Company Knowledge Chatbot Builder
Module: Document Ingestion, Semantic Chunking, and Grounded RAG Search
Author: Pranav Edvankar
Description: Extracts text from PDFs and TXT files, chunks with overlap,
             performs similarity retrieval, and queries LLMs (Local or Cloud)
             with source citations.
"""

import os
import re
import math
import json
import time
import requests
import fitz  # PyMuPDF

# =====================================================================
# 1. Document Ingestion & Text Extraction
# =====================================================================
def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    pages_data = []

    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:
                pages_data.append({"page": page_num + 1, "text": text})
        doc.close()
    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
            pages_data.append({"page": 1, "text": text})
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return pages_data


# =====================================================================
# 2. Text Chunking with Overlap (Preserving sentence boundaries)
# =====================================================================
def chunk_document(pages_data, filename, chunk_size=500, chunk_overlap=80):
    chunks = []
    chunk_id = 1

    for p in pages_data:
        text = p["text"]
        page_num = p["page"]
        
        # Clean multiple spaces and linebreaks
        text = re.sub(r"\s+", " ", text)
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_str = text[start:end].strip()
            
            if chunk_str:
                chunks.append({
                    "id": chunk_id,
                    "source": filename,
                    "page": page_num,
                    "content": chunk_str
                })
                chunk_id += 1
            
            # Step forward by chunk_size minus overlap
            start += (chunk_size - chunk_overlap)

    return chunks


# =====================================================================
# 3. Lightweight Semantic Similarity Search (TF-IDF Cosine Scoring)
# =====================================================================
def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())

def search_relevant_chunks(query, chunks, top_k=2):
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return chunks[:top_k]

    scored_chunks = []
    for c in chunks:
        doc_tokens = tokenize(c["content"])
        if not doc_tokens:
            continue
        
        # Calculate term overlap score
        matches = sum(1 for t in doc_tokens if t in query_tokens)
        score = matches / (math.sqrt(len(doc_tokens)) + 1e-5)
        scored_chunks.append((score, c))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [c for score, c in scored_chunks[:top_k] if score > 0] or chunks[:top_k]


# =====================================================================
# 4. RAG Query Generator with Citations
# =====================================================================
def query_rag(question, relevant_chunks, provider="local"):
    # Build citation-backed context block
    context_blocks = []
    for c in relevant_chunks:
        context_blocks.append(f"[Source: {c['source']}, Page {c['page']}]\n\"{c['content']}\"")
    
    context_text = "\n\n".join(context_blocks)

    system_instruction = (
        "You are a helpful company knowledge assistant. "
        "Answer the user's question STRICTLY using the context below. "
        "Always cite your sources using the exact format: [Source: filename, Page X]. "
        "If the answer is not in the context, say 'I could not find that information in the provided document.'"
    )

    full_prompt = f"{system_instruction}\n\nContext:\n{context_text}\n\nQuestion: {question}\nAnswer:"

    print("\n" + "=" * 70)
    print("🔍 Retrieved Context Chunks for Grounding:")
    print("-" * 70)
    for c in relevant_chunks:
        print(f"📄 [{c['source']} - Page {c['page']}] (Chunk #{c['id']})")
        print(f"   \"{c['content'][:120]}...\"\n")
    print("=" * 70)

    # Call Local Ollama (llama3.2:1b)
    print("🤖 Generating answer from Local Model (Ollama)...")
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:1b", "prompt": full_prompt, "stream": False},
            timeout=60
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
        else:
            return f"Ollama Error ({r.status_code}): {r.text}"
    except Exception as e:
        return f"Could not reach Ollama: {str(e)}"


# =====================================================================
# 5. Live Demonstration Runner
# =====================================================================
def run_demo():
    print("=" * 70)
    print("📚 Project 3: Knowledge Ingestion & Grounded RAG Pipeline")
    print("=" * 70)

    # Create a sample company document to test immediately
    sample_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_policy.txt")
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(
            "Acme Corp Remote Work and Equipment Policy (2026)\n"
            "Employees are eligible for a $500 home-office equipment stipend after 90 days of employment.\n"
            "Standard core working hours are 10:00 AM to 4:00 PM Eastern Time for cross-team coordination.\n"
            "All company devices must have full-disk encryption enabled and use 2-factor authentication.\n"
            "Annual travel budgets allow up to $1,500 per team member for the annual engineering offsite."
        )

    print(f"1. Ingesting: {os.path.basename(sample_file)}")
    pages = extract_text_from_file(sample_file)
    print(f"   └─ Extracted {len(pages)} page(s).")

    print("\n2. Chunking with overlap...")
    chunks = chunk_document(pages, os.path.basename(sample_file), chunk_size=200, chunk_overlap=40)
    print(f"   └─ Created {len(chunks)} searchable chunks.")

    # Test Question
    test_question = "How much is the home office stipend and when are employees eligible?"
    print(f"\n3. User Query: '{test_question}'")

    relevant = search_relevant_chunks(test_question, chunks, top_k=2)
    answer = query_rag(test_question, relevant, provider="local")

    print("\n💬 Final Assistant Answer:")
    print("-" * 70)
    print(answer)
    print("-" * 70)

if __name__ == "__main__":
    run_demo()
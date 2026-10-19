# Week 1 Study Notes: LLM Fundamentals & Git Workflow

**Project:** Project 1: AI Tooling & Model Integration  
**Deliverable:** `week1-notes.md`  
**Author:** Intern  

---

## 1. What is an LLM? (In Plain English)
A **Large Language Model (LLM)** is essentially a very powerful **autocomplete system**.

* **Two Main Components:**
  1. **Weights File (The Brain/Memory):** Billions of numbers (parameters) saved on disk that store patterns of human language learned from reading the internet.
  2. **Inference Code (The Runner):** A small program that loads those numbers and runs math equations to predict text.
* **Core Rule:** An LLM does not think in full sentences or possess feelings. Given some starting text, it simply calculates which word or piece of a word is most likely to come next.

---

## 2. What is Inference?
**Inference** is when you actually run the model to generate an answer.
* **Training** = The model studying for months to learn language (weights change).
* **Inference** = The model taking the test (weights are frozen, it only generates answers).

### The Inference Loop (How AI Writes)
The AI generates text **one single token at a time**:
1. You provide a prompt: `"The sky is"`
2. The model scans its dictionary and calculates probabilities for every possible next piece.
3. It picks the most likely piece (e.g., `"blue"`).
4. It attaches `"blue"` to your prompt: `"The sky is blue"`.
5. It repeats the process to pick the next piece (e.g., `"."`) until it hits a hidden stop signal (`<|end_of_text|>`).

---

## 3. What is a Token?
Computers cannot read letters or words directly—they only understand numbers.

A **token** is a chunk of text that has been converted into a unique number ID.
* **1 Token ≈ 4 characters** in English (~0.75 words).
* **100 Tokens ≈ 75 English words**.
* **Why not letters?** Reading letter-by-letter takes too many steps and too much memory.
* **Why not full dictionary words?** Dictionaries cannot handle slang, typos, usernames, or code.
* **The Solution (Sub-words):** Common words get their own single token (`"apple"`). Rare or long words are built out of smaller pieces (`"un" + "believ" + "able"`).

---

## 4. The 4 Big Settings & Terms

### 1. Parameters (Brain Size)
* **What it is:** The number of internal connections in the neural network (e.g., 8B = 8 Billion, 70B = 70 Billion).
* **Rule of thumb:** More parameters = smarter reasoning, but requires much more computer memory (RAM/VRAM) to run.

### 2. Context Window (Desk Space)
* **What it is:** The maximum number of tokens the model can hold in its working memory at one time.
* **Rule of thumb:** If a conversation grows longer than the context window, the model forgets the earliest messages.

### 3. Temperature (The Creativity Dial)
* **What it is:** A setting from `0.0` to `1.0` (or higher) that controls randomness.
  * **Temperature = 0.0 (Cold):** Strict, deterministic, and predictable. Always picks the top-ranked token. Best for math, coding, and factual tasks.
  * **Temperature = 0.7 – 1.0 (Warm):** Creative and varied. Allows lower-ranked words to be picked. Best for brainstorming, creative writing, and chat.

### 4. Hallucination (Confident Guessing)
* **What it is:** When an AI gives a completely false answer with total confidence.
* **Why it happens:** The model is optimized to sound fluent and plausible, not to verify truth. If it does not know a fact, it continues the language pattern with believable-sounding fiction.

---

## 5. Tokenizer Experiment: Results & Observations

Tested using the standard `cl100k_base` tokenizer (GPT-4 / modern chat models):

| Category | Input String | Token Count | Token IDs | Why the Count Differs |
| :--- | :--- | :---: | :--- | :--- |
| **Normal Word** | `'apple'` | 1 | `[45434]` | Common word seen millions of times; assigned a single token. |
| **Normal Phrase** | `'artificial intelligence'` | 2 | `[472, 8316]` | Common two-word phrase; each word is 1 token. |
| **Punctuation** | `'Hello, world!'` | 4 | `[9906, 11, 1917, 0]` | Punctuation marks (`,`, `!`) are split into distinct tokens. |
| **Repeated Punctuation** | `'Wait... what?!?!'` | 6 | `[14273, 2307, 3624, 0, 9362, 0]` | Repeated symbols are split into separate symbol combinations. |
| **No Leading Space** | `'apple'` | 1 | `[45434]` | Starts immediately with letters. |
| **With Leading Space** | `' apple'` | 1 | `[17255]` | Spaces are attached to words. Has a completely different token ID than `'apple'`. |
| **Multiple Spaces** | `'apple    banana'` | 3 | `[45434, 1856, 44265]` | Extra consecutive spaces are grouped into separate whitespace tokens. |
| **Short Number** | `'42'` | 1 | `[4735]` | 1-to-2 digit common numbers often fit in a single token. |
| **Long Number** | `'1234567890'` | 3 | `[2360, 24198, 220]` | Numbers are split into 1-to-3 digit chunks, making mental math hard for LLMs. |
| **Single Emoji** | `'🔥'` | 3 | `[9468, 243, 237]` | Emojis are multi-byte UTF-8 characters; each byte sequence becomes a token. |
| **Multiple Emojis** | `'🚀🤖🎉'` | 9 | `[9468, ...]` | 3 emojis require 9 tokens (roughly 3 tokens per emoji). |

---

## 6. Git & GitHub Workflow Summary

### Why We Use Branches:
* The `main` branch is reserved for stable, working code.
* Features and experiments are built on separate **feature branches** so that broken experimental code never damages the main project.

### The 4 Standard Commands Used:
1. **Create Branch:**
   ```bash
   git checkout -b feature/tokenizer-experiment
   ```
2. **Stage Changes:**
   ```bash
   git add .
   ```
3. **Commit Changes:**
   ```bash
   git commit -m "Add tokenizer experiment and study notes"
   ```
4. **Push to Remote:**
   ```bash
   git push -u origin feature/tokenizer-experiment
   ```

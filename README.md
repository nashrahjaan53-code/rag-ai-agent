# 🚀 Recimotech Enterprise RAG AI Agent

An advanced, conversational Retrieval-Augmented Generation (RAG) AI Agent engineered to provide organic, fluid, and context-aware interactions utilizing a company's complete unstructured knowledge base.

## 🔥 Key Architectural Upgrades
* **True Generative RAG:** Moves away from rigid FAQ-matching to dynamic context synthesis using `gemini-2.5-flash`.
* **Stateful Session Memory:** Remembers conversational timeline context over multiple exchanges (e.g., handles pronouns like "it", "duration", or "fees" relative to the active topic).
* **Dynamic File Ingestion:** Completely separates data from code logic by loading and embedding text assets directly from `company_knowledge.txt` on server startup.
* **Intent-Driven Lead Routing:** Out-of-the-box system rules designed to flag transactional intent and collect user profile data seamlessly.

## 🛠️ Tech Stack
* **Backend:** Python, FastAPI, Uvicorn
* **AI & Embeddings:** `google-genai` SDK, `sentence-transformers` (`all-MiniLM-L6-v2`), Scikit-Learn (Cosine Similarity)
* **Frontend:** HTML5, Tailwind CSS, Native JavaScript ES6+

## 🚀 Quick Start Local Execution
1. Install system requirements:
```bash
   pip install fastapi uvicorn sentence-transformers scikit-learn numpy google-genai python-dotenv

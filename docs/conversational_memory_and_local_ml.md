# Conversational Memory & Local ML Model Pipeline

This phase establishes the conversational memory, session management, query expansion heuristics, and offline Machine Learning generation model.

---

## 1. Concept & Importance

### Local ML Generation (Extractive QA NLP Model)
To support fully offline operations without OpenAI dependencies (saving costs and running without API keys), we implement a local Natural Language Processing (NLP) generative pipeline.
* **Why it's needed:** Users require contextualized responses based on indexed records without sending data to external endpoints.
* **Algorithm details:** We build a term-frequency sentence ranker (representing an extractive QA ML model). It extracts sentences from retrieved document chunks, weights them using token overlap with the query, and structures them into fluent citation-rich paragraphs.

### Feature Hashing Embeddings
To avoid depending on OpenAI embeddings or downloading gigabytes of deep learning libraries (like PyTorch) which might fail to install or compile on Python 3.14.3, we implement the **Hashing Trick**.
* **Why it's needed:** FAISS requires a fixed dimension float vector. Feature Hashing maps tokens to deterministic buckets (e.g., 384 dimensions), normalizes them, and produces high-speed L2-comparable vectors using only numpy.

### Session Management & Conversational Memory
Conversations are multi-turn. If a user asks "What is RAG?" and follows up with "How does it help?", the system must resolve the pronoun "it".
* **Why it's needed:** Vector databases cannot resolve pronouns by themselves. If we search "How does it help", we get garbage matches.
* **Production detail:** We implement a **Context-aware Query Reformulator**. It tracks session message sequences, detects short messages/pronouns, and merges the previous turn's keywords to expand the query before retrieval, solving coreference issues.

---

## 2. File Roles & Descriptions

* [ml_model.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/ml_model.py): Houses the local Extractive QA sentence-overlap ranker.
* [rag_service.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/rag_service.py): Manages session lists, expands follow-up queries using history, and routes calls to either OpenAI GPT-4o or the local ML model.
* [embeddings.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/embeddings.py): Updated to load `LocalHashingEmbeddings` when `MODEL_PROVIDER="local"` is selected.
* [chat.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/api/v1/endpoints/chat.py): Exposes endpoints `POST /api/v1/chat` and `DELETE /api/v1/chat/session/{session_id}`.
* [schemas.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/models/schemas.py): Added `ChatRequest`, `ChatCitation`, and `ChatResponse` models.
* [test_pipeline.py](file:///c:/Users/lenovo/Desktop/RAG_System/tests/test_pipeline.py): Performs end-to-end testing of local upload, query, follow-up chats, and memory purges.

---

## 3. Best Practices & Common Mistakes

### Best Practices
1. **Query Expansion Heuristics**: When reformulating queries, avoid merging the entire past conversation string (as this creates massive retrieval noise). Instead, filter stop words and only append noun keywords from the previous user prompt.
2. **Deterministic Hashing**: In `LocalHashingEmbeddings`, use cryptographic hashing (like MD5) to map tokens to indices. Standard Python `hash()` is randomized on startup for security reasons, which would cause vectors to change between server restarts and break index retrievals.
3. **Lazy Model Loading**: Instantiate large chat clients (like OpenAI) lazily only when they are selected and run, allowing the rest of the application to run offline smoothly.

### Common Mistakes
1. **Unbounded History Storage**: Storing chat session arrays indefinitely in-memory. If unchecked, memory footprints grow over time, leading to Out-Of-Memory (OOM) crashes. Keep histories bounded (e.g. limit to last 20 messages).
2. **Hardcoded API Guards**: Enforcing API key presence checks on general endpoints even if the user has selected a local/offline model backend.

---

## 4. Run the Full Local Pipeline

Execute the test suite locally in your terminal:
```powershell
.venv\Scripts\python tests/test_pipeline.py
```
This runs the full ingestion, local indexing, semantic querying, conversational chat turns, and memory deletes successfully.

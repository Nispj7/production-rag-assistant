# AI Knowledge Assistant (Production RAG System)

A production-ready, highly modular Retrieval-Augmented Generation (RAG) system built with **FastAPI**, **LangChain**, and **FAISS**.

The system features dual execution modes:
1. **Cloud Mode (OpenAI)**: Uses OpenAI Embeddings (`text-embedding-3-small`) and Chat Completions (`gpt-4o`) for premium contextual generation.
2. **Local/Offline Mode**: Uses a custom **Feature Hashing Embedding** model (384-dimensional dense vectors) and a local **Extractive QA NLP** sentence ranker. This allows the entire pipeline to run 100% locally on CPU without API keys, external downloads (no PyTorch required), or network requirements.

---

## Key Features

* **Multi-Format Loader**: Ingests and processes `.txt`, `.pdf` (via `pypdf`), and `.docx` (via `docx2txt`) files.
* **Token-based Splitter**: Splits document texts precisely by token count using `tiktoken` rather than simple characters.
* **Metadata & Citations**: Tracks file origins and chunk sequence indexes across splits, returning detailed source attribution.
* **Embedding Cache**: Implements persistent disk-based caching (`LocalFileStore`) to avoid redundant OpenAI API costs.
* **Centralized Exceptions**: Global FastAPI exception handlers return standard JSON error models, shielding system debug files.
* **Session Memory**: Tracks conversation session IDs, applying a local coreference/query expansion heuristic to follow-up questions.
* **Dockerized Setup**: Multi-platform production containerization equipped with container health probes and volume persistence.

---

## Project Structure

```
RAG_System/
│
├── app/
│   ├── api/
│   │   ├── deps.py               # FastAPI Dependency Providers
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── chat.py       # Session Chat Endpoints
│   │       │   └── document.py   # Document Upload & Search Endpoints
│   │       └── router.py         # Master Route Grouping
│   │
│   ├── core/
│   │   ├── config.py             # Pydantic Settings Validation
│   │   ├── exceptions.py         # Centralized Exception Handler
│   │   └── logging.py            # Structured Application Logger
│   │
│   ├── models/
│   │   └── schemas.py            # Pydantic Request/Response Models
│   │
│   ├── services/
│   │   ├── chunking.py           # tiktoken text splitter service
│   │   ├── document_loader.py    # Multi-format File parsing service
│   │   ├── embeddings.py         # Local Hashing & OpenAI Embeddings
│   │   ├── ml_model.py           # Local Extractive QA Model
│   │   ├── rag_service.py        # Conversational Memory coordinator
│   │   └── vectorstore.py        # FAISS Persistent Store / Chroma stub
│   │
│   └── main.py                   # FastAPI Application Bootstrap
│
├── data/                         # Upload and Vector Store Persistent Directories
├── docs/                         # Project walkthroughs and designs
├── tests/
│   └── test_pipeline.py          # End-to-end integration tests
│
├── .dockerignore
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites
* Python 3.11+
* Docker & Docker Compose (optional, for containerized run)

### Method 1: Local Development Setup
1. **Initialize Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate       # On Windows Powershell
   source .venv/bin/activate     # On Unix/macOS
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and set your preferred settings:
   ```bash
   cp .env.example .env
   ```
   * Set `MODEL_PROVIDER="local"` to run completely offline without an OpenAI key.
   * Set `MODEL_PROVIDER="openai"` and insert `OPENAI_API_KEY="..."` to run with cloud generation.

4. **Run Integration Tests**:
   ```bash
   python -u tests/test_pipeline.py
   ```

5. **Start Application Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
   ```

### Method 2: Running with Docker Compose
1. **Build and Start Container**:
   ```bash
   docker-compose up --build -d
   ```
2. **Logs Monitoring**:
   ```bash
   docker logs -f rag_assistant_api
   ```
3. **Shutdown Container**:
   ```bash
   docker-compose down
   ```

---

## API Documentation & Sample Commands

Once the server is running, the interactive Swagger docs are available at: `http://localhost:8000/docs`

### 1. Ingest a Document
Upload a document (PDF, TXT, or DOCX) to parse, chunk, and index into the database.

* **Method**: `POST`
* **URL**: `/api/v1/document/upload`
* **Headers**: `Content-Type: multipart/form-data`
* **Form-data**: `file: @path/to/your/document.txt`

**Sample curl request**:
```bash
curl -X POST "http://localhost:8000/api/v1/document/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample.txt"
```

---

### 2. Query Vector Store (Similarity Search)
Directly query raw vector index to check semantic extraction matches and L2 scores.

* **Method**: `POST`
* **URL**: `/api/v1/document/query`
* **Headers**: `Content-Type: application/json`

**Sample Body**:
```json
{
  "query": "What is superposition?",
  "k": 2
}
```

**Sample curl request**:
```bash
curl -X POST "http://localhost:8000/api/v1/document/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is superposition?", "k": 2}'
```

---

### 3. Session RAG Chat
Engage in a session-based multi-turn conversation with memory query expansion.

* **Method**: `POST`
* **URL**: `/api/v1/chat`
* **Headers**: `Content-Type: application/json`

**Sample Body**:
```json
{
  "session_id": "session-xyz",
  "query": "How does RAG reduce hallucinations?",
  "k": 2
}
```

**Sample curl request**:
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-xyz", "query": "How does RAG reduce hallucinations?", "k": 2}'
```

---

### 4. Clear Chat Session Memory
Wipe the chat interaction history for a given session.

* **Method**: `DELETE`
* **URL**: `/api/v1/chat/session/session-xyz`

**Sample curl request**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/chat/session/session-xyz"
```

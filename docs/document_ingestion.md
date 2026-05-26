# Document Ingestion, Chunking & Vector Persistence

This phase covers document processing, text splitting (chunking), embedding caching, and local vector indexing (FAISS).

---

## 1. Concept & Importance

### Document Loading & Parsing
Raw documents (PDFs, Word files, text docs) contain unstructured text and layout information. Extracting text cleanly is the first step in any RAG system.
* **Why it's needed:** We must extract raw content from arbitrary binary structures (`.pdf`, `.docx`) into standard strings that the embedding model can consume.
* **Production detail:** Running heavy parsing synchronously will freeze FastAPI's single-threaded event loop. We use `asyncio.get_running_loop().run_in_executor()` to run parsers inside a thread pool, keeping the API responsive for concurrent requests.

### Chunking (Text Splitting)
Large documents cannot be fed into the LLM context or embedded in one piece. We must break them down.
* **Why it's needed:** Smaller chunks make embeddings more semantically specific. A vector of a 1000-page book represents an "average" of all topics, losing details. A chunk representing single paragraphs retains high-fidelity semantics.
* **Production detail:** We use `RecursiveCharacterTextSplitter` configured with a `tiktoken` length estimator. This splits documents exactly by token counts, preventing chunks from exceeding OpenAI/database embedding limit ceilings.

### Embedding Caching
Generating embeddings is a paid API call and an I/O operation.
* **Why it's needed:** If we update documents or query the database, re-generating embeddings for existing chunks creates redundant cost and latency. Caching stores the embeddings on disk (`data/vectorstore/cache`), pulling from disk on subsequent index runs.

---

## 2. File Roles & Descriptions

* [document_loader.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/document_loader.py): Parses PDF, DOCX, and TXT files, wrapping text inside LangChain `Document` objects. Uses thread pools to offload parsing execution.
* [chunking.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/chunking.py): Splits documents using a token-based RecursiveCharacterTextSplitter and injects citation index numbers.
* [embeddings.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/embeddings.py): Instantiates `OpenAIEmbeddings` and wraps it in a file-system backed byte-store cache.
* [vectorstore.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/vectorstore.py): Directs database calls. Manages FAISS indices (local loading/saving) and provides a factory for ChromaDB.
* [ingestion.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/services/ingestion.py): Orchestrates the workflow: Loader -> Splitter -> Vector Indexing.
* [schemas.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/models/schemas.py): Contains Pydantic models validating upload responses and vector queries.
* [document.py](file:///c:/Users/lenovo/Desktop/RAG_System/app/api/v1/endpoints/document.py): Routes for `/upload` (multipart forms) and `/query` (semantic search checks).
* [test_pipeline.py](file:///c:/Users/lenovo/Desktop/RAG_System/tests/test_pipeline.py): Verifies routing, file writes, and exception returns in memory.

---

## 3. Best Practices & Common Mistakes

### Best Practices
1. **Thread Delegation**: Never run blocking CPU operations (like parsing complex PDF shapes or docx parsing) directly in an `async def` handler without offloading to executors.
2. **Metadata Enrichment**: Always inject positional indexes (`chunk_index` and `total_chunks`) into chunk metadata. This makes source tracking and citation presentation in the chat response possible.
3. **Caching namespaces**: Namespace your embedding caches based on the model name. If you switch models (e.g. from `text-embedding-3-small` to `text-embedding-3-large`), a unified cache namespace will return incorrect vector dimensions, triggering database search failures.

### Common Mistakes
1. **Hardcoding chunk characters**: Splitting text based on character counts instead of token counts. Since token sizes vary from character sizes depending on text characteristics, character splitters can unexpectedly overflow OpenAI's limit.
2. **Uncleaned Uploads**: Leaving temporary uploaded files on the server's disk if the ingestion pipeline crashes, which can eventually exhaust server disk space.

---

## 4. Run the Pipeline Verification

You can test the pipeline (which validates error handling and API routing) using:
```powershell
.venv\Scripts\python tests/test_pipeline.py
```
Outputs will show the health check succeeding and the upload failing gracefully with an `AuthenticationError (500/VectorStoreError)` due to the placeholder API key.

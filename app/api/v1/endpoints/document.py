import os
import uuid
import shutil
import logging
import time
from fastapi import APIRouter, UploadFile, File, Depends
from app.core.config import settings
from app.core.exceptions import DocumentLoadError, VectorStoreError
from app.models.schemas import UploadResponse, QueryRequest, QueryResponse, ChunkResult, SourceMetadata
from app.services.ingestion import IngestionService
from app.services.vectorstore import VectorStoreService
from app.api.deps import get_ingestion_service, get_vector_service

router = APIRouter(prefix="/document", tags=["Documents"])
logger = logging.getLogger("app.api.v1.document")

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(get_ingestion_service)
):
    """
    Uploads a document (PDF, TXT, or DOCX) to parse, chunk, 
    and index it into the vector database.
    """
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    
    # 1. Validate file extension
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected upload of unsupported file format: %s", ext)
        raise DocumentLoadError(
            f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # 2. Ensure directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # 3. Create unique path on filesystem to avoid overlaps
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # 4. Save incoming file stream to local disk
    try:
        logger.info("Saving uploaded file to temporary disk storage: %s", file_path)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.exception("Failed to write uploaded file content to disk.")
        raise DocumentLoadError(f"Failed to save file upload to disk: {str(e)}")
        
    # 5. Ingest file into vector database
    try:
        chunk_count, duration = await ingestion_service.ingest_file(file_path)
        return UploadResponse(
            success=True,
            filename=filename,
            chunk_count=chunk_count,
            execution_time_sec=round(duration, 4),
            message=f"Ingestion successful. Generated and indexed {chunk_count} chunks."
        )
    except Exception as e:
        # Cleanup uploaded file if the pipeline broke mid-way
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Deleted temporary upload file after pipeline ingestion failure: %s", file_path)
        raise


@router.post("/query", response_model=QueryResponse)
async def query_vectorstore(
    request: QueryRequest,
    vector_service: VectorStoreService = Depends(get_vector_service)
):
    """
    Performs similarity search against indexed document chunks.
    Returns matched chunks along with L2 distance scores and source citation metadata.
    """
    start_time = time.perf_counter()
    
    # Check if OpenAI Key is configured only if using OpenAI provider
    if settings.MODEL_PROVIDER == "openai" and not settings.is_openai_key_configured:
        raise VectorStoreError(
            "OpenAI API Key is not configured. Vector operations cannot run. "
            "Please configure a valid OPENAI_API_KEY in the .env file."
        )
        
    try:
        results = vector_service.similarity_search_with_score(
            query=request.query,
            k=request.k
        )
        
        chunk_results = []
        for doc, score in results:
            meta = doc.metadata
            chunk_results.append(
                ChunkResult(
                    content=doc.page_content,
                    metadata=SourceMetadata(
                        source=meta.get("source", "unknown"),
                        file_type=meta.get("file_type", "unknown"),
                        chunk_index=meta.get("chunk_index", 0),
                        total_chunks=meta.get("total_chunks", 0),
                        token_count=meta.get("token_count", 0)
                    ),
                    score=float(score)
                )
            )
            
        latency = time.perf_counter() - start_time
        return QueryResponse(
            query=request.query,
            results=chunk_results,
            latency_sec=round(latency, 4)
        )
    except VectorStoreError:
        raise
    except Exception as e:
        logger.exception("Vector similarity search failed.")
        raise VectorStoreError(f"Vector search failed: {str(e)}")

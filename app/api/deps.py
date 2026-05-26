from fastapi import Depends
from app.services.document_loader import DocumentLoaderService
from app.services.chunking import ChunkingService
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.ingestion import IngestionService
from app.services.ml_model import LocalMLModelService
from app.services.rag_service import RAGChatService

# Private module-level variables for singleton instances
_embedding_service = None
_vector_service = None
_loader_service = None
_chunking_service = None
_ingestion_service = None
_local_ml_service = None
_chat_service = None

def get_embedding_service() -> EmbeddingService:
    """Lazy-instantiated singleton helper for the embedding generator."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_vector_service(
    embed_service: EmbeddingService = Depends(get_embedding_service)
) -> VectorStoreService:
    """Lazy-instantiated singleton helper for the vector database."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorStoreService(embed_service)
    return _vector_service


def get_loader_service() -> DocumentLoaderService:
    """Lazy-instantiated singleton helper for file parsers."""
    global _loader_service
    if _loader_service is None:
        _loader_service = DocumentLoaderService()
    return _loader_service


def get_chunking_service() -> ChunkingService:
    """Lazy-instantiated singleton helper for text splitters."""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service


def get_ingestion_service(
    loader: DocumentLoaderService = Depends(get_loader_service),
    chunker: ChunkingService = Depends(get_chunking_service),
    vector_store: VectorStoreService = Depends(get_vector_service)
) -> IngestionService:
    """Lazy-instantiated singleton helper for coordinating the document ingestion pipeline."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService(loader, chunker, vector_store)
    return _ingestion_service


def get_local_ml_service() -> LocalMLModelService:
    """Lazy-instantiated singleton helper for the local extractive QA ML model."""
    global _local_ml_service
    if _local_ml_service is None:
        _local_ml_service = LocalMLModelService()
    return _local_ml_service


def get_chat_service(
    vector_store: VectorStoreService = Depends(get_vector_service),
    local_ml: LocalMLModelService = Depends(get_local_ml_service)
) -> RAGChatService:
    """Lazy-instantiated singleton helper for RAG chat session service."""
    global _chat_service
    if _chat_service is None:
        _chat_service = RAGChatService(vector_store, local_ml)
    return _chat_service


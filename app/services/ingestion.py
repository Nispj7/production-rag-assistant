import os
import time
import logging
from typing import Tuple

from app.services.document_loader import DocumentLoaderService
from app.services.chunking import ChunkingService
from app.services.vectorstore import VectorStoreService

logger = logging.getLogger("app.services.ingestion")

class IngestionService:
    """
    Pipeline coordinator that handles loading raw file types, splitting them
    into contextual chunks, and indexing them in the active vector database.
    """
    
    def __init__(
        self,
        loader_service: DocumentLoaderService,
        chunking_service: ChunkingService,
        vector_service: VectorStoreService
    ) -> None:
        self.loader = loader_service
        self.chunker = chunking_service
        self.vector_store = vector_service

    async def ingest_file(self, file_path: str) -> Tuple[int, float]:
        """
        Executes the full ingestion pipeline: Loader -> Chunker -> Vector Store Indexing.
        Tracks pipeline latency for analytics.
        
        Args:
            file_path: The local path of the document to ingest.
            
        Returns:
            Tuple of (total chunks generated, pipeline duration in seconds).
        """
        start_time = time.perf_counter()
        filename = os.path.basename(file_path)
        logger.info("Executing ingestion pipeline for file: %s", filename)
        
        # Step 1: Load file content based on file extension
        raw_documents = await self.loader.load_document(file_path)
        
        # Step 2: Split text into token-bounded chunks
        chunks = self.chunker.split_documents(raw_documents)
        
        # Step 3: Embed chunks and index them into the Vector Database
        # (This stage utilizes the filesystem cache to prevent duplicate embedding costs)
        self.vector_store.add_documents(chunks)
        
        elapsed_time = time.perf_counter() - start_time
        logger.info(
            "Completed ingestion pipeline for '%s'. Indexed %d chunks in %.4f seconds.",
            filename, len(chunks), elapsed_time
        )
        
        return len(chunks), elapsed_time

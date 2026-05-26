import os
import logging
import hashlib
import numpy as np
from typing import List
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore

from app.core.config import settings

logger = logging.getLogger("app.services.embeddings")

class LocalHashingEmbeddings(Embeddings):
    """
    A local Machine Learning text encoder using the Hashing Trick (Feature Hashing).
    Produces deterministic 384-dimensional dense vectors representing text features.
    Enables local vector search with FAISS without requiring PyTorch or external API keys.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _embed_text(self, text: str) -> List[float]:
        # Simple tokenization
        words = text.lower().split()
        if not words:
            return [0.0] * self.dimension
            
        vector = np.zeros(self.dimension)
        for word in words:
            # Generate a deterministic index using MD5 hash
            h = hashlib.md5(word.encode("utf-8")).hexdigest()
            index = int(h, 16) % self.dimension
            vector[index] += 1.0  # Term frequency weighting
            
        # L2 Normalization (unit length) to support cosine similarity / L2 search
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


class EmbeddingService:
    """
    Service responsible for loading and configuring the Embedding Model.
    Dynamically loads either local HuggingFace NLP models or Cache-Backed OpenAI Embeddings
    based on the current configuration settings.
    """
    
    def __init__(self) -> None:
        self.provider = settings.MODEL_PROVIDER
        
        if self.provider == "local":
            logger.info("Initializing Local HuggingFace Embeddings (all-MiniLM-L6-v2)...")
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
        else:
            logger.info("Initializing OpenAI Embeddings Cache...")
            # Initialize the underlying OpenAI Embeddings
            self.underlying_embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Define directory path for filesystem embedding caching
            self.cache_dir = os.path.join(settings.VECTOR_STORE_DIR, "cache")
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Create Local File Store for embedding caching
            self.store = LocalFileStore(self.cache_dir)
            
            # Initialize CacheBackedEmbeddings using namespace mapping to prevent model collisions
            self.embeddings = CacheBackedEmbeddings.from_bytes_store(
                underlying_embeddings=self.underlying_embeddings,
                document_embedding_cache=self.store,
                namespace=settings.EMBEDDING_MODEL_NAME
            )
            logger.info(
                "EmbeddingService configured with OpenAI model '%s'. Disk cache: %s",
                settings.EMBEDDING_MODEL_NAME, self.cache_dir
            )
        
    def get_embeddings(self) -> Embeddings:
        """
        Returns the active embedding generator instance.
        """
        return self.embeddings

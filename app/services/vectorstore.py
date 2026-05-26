import os
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.core.config import settings
from app.services.embeddings import EmbeddingService
from app.core.exceptions import VectorStoreError

logger = logging.getLogger("app.services.vectorstore")

class BaseVectorStore(ABC):
    """
    Abstract Base Class defining the contract for all vector store adapters.
    This enables seamless switching between FAISS, ChromaDB, or cloud providers.
    """
    
    @abstractmethod
    def load(self) -> None:
        """Loads the persistent index from disk."""
        pass

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Adds a list of LangChain Documents to the vector database and persists the index."""
        pass

    @abstractmethod
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Performs similarity search returning matched documents and their distance scores.
        
        Returns:
            List of tuples (Document, score).
        """
        pass


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS-cpu implementation of the Vector Store.
    Stores indexes locally as binary files.
    """
    
    def __init__(self, embeddings_model, persist_dir: str):
        self.embeddings = embeddings_model
        self.persist_dir = persist_dir
        self.db: Optional[FAISS] = None
        self.load()

    def load(self) -> None:
        index_file = os.path.join(self.persist_dir, "index.faiss")
        if os.path.exists(index_file):
            try:
                logger.info("Loading existing FAISS index from disk at %s...", self.persist_dir)
                # allow_dangerous_deserialization is required for local FAISS file loading
                self.db = FAISS.load_local(
                    self.persist_dir,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("FAISS index loaded successfully.")
            except Exception as e:
                logger.error("Failed to load FAISS index: %s", str(e))
                raise VectorStoreError(f"Failed to load FAISS index: {str(e)}")
        else:
            logger.info("No existing FAISS index found at %s. Operating in uninitialized mode.", index_file)
            self.db = None

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            logger.warning("No documents provided to index.")
            return

        try:
            if self.db is None:
                logger.info("Initializing new FAISS index with %d chunks...", len(documents))
                self.db = FAISS.from_documents(documents, self.embeddings)
            else:
                logger.info("Adding %d chunks to existing FAISS index...", len(documents))
                self.db.add_documents(documents)
            
            # Save the updated index back to the persistent directory
            os.makedirs(self.persist_dir, exist_ok=True)
            self.db.save_local(self.persist_dir)
            logger.info("FAISS index persisted to disk at %s.", self.persist_dir)
        except Exception as e:
            logger.exception("Failed to add documents to FAISS index.")
            raise VectorStoreError(f"Failed to index documents into FAISS: {str(e)}")

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        if self.db is None:
            logger.warning("Similarity search attempted on an uninitialized vector store.")
            return []
            
        try:
            logger.info("Performing similarity search for query (k=%d)...", k)
            # FAISS returns L2 distance score (lower is closer/better)
            results = self.db.similarity_search_with_score(query, k=k)
            logger.info("Similarity search completed. Found %d matches.", len(results))
            return results
        except Exception as e:
            logger.exception("FAISS similarity search execution failed.")
            raise VectorStoreError(f"Failed searching FAISS index: {str(e)}")


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB implementation of the Vector Store.
    Stores indexes locally as sqlite3 databases in a 'chroma' subfolder.
    """
    
    def __init__(self, embeddings_model, persist_dir: str):
        self.embeddings = embeddings_model
        # We append 'chroma' to ensure FAISS and Chroma don't collide in the same dir
        self.persist_dir = os.path.join(persist_dir, "chroma")
        self.db = None
        self.load()

    def load(self) -> None:
        try:
            # We import locally so the app can boot without chroma if VECTOR_DB_TYPE=faiss
            from langchain_chroma import Chroma
            
            logger.info("Initializing ChromaDB connection at %s...", self.persist_dir)
            self.db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings
            )
            logger.info("ChromaDB index loaded successfully.")
        except ImportError:
            logger.error("Chroma dependencies not installed. Please run pip install langchain-chroma chromadb")
            raise VectorStoreError("Chroma dependencies missing.")
        except Exception as e:
            logger.error("Failed to load ChromaDB index: %s", str(e))
            raise VectorStoreError(f"Failed to load ChromaDB index: {str(e)}")

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            logger.warning("No documents provided to index.")
            return

        try:
            logger.info("Adding %d chunks to ChromaDB index...", len(documents))
            self.db.add_documents(documents)
            logger.info("ChromaDB index persisted successfully.")
        except Exception as e:
            logger.exception("Failed to add documents to ChromaDB index.")
            raise VectorStoreError(f"Failed to index documents into ChromaDB: {str(e)}")

    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        if self.db is None:
            logger.warning("Similarity search attempted on an uninitialized Chroma vector store.")
            return []
            
        try:
            logger.info("Performing similarity search via ChromaDB for query (k=%d)...", k)
            # Chroma returns L2 distance score
            results = self.db.similarity_search_with_score(query, k=k)
            logger.info("ChromaDB similarity search completed. Found %d matches.", len(results))
            return results
        except Exception as e:
            logger.exception("ChromaDB similarity search execution failed.")
            raise VectorStoreError(f"Failed searching ChromaDB index: {str(e)}")


class VectorStoreService:
    """
    Orchestration layer that abstracts the active database type (FAISS vs ChromaDB)
    from the rest of the application.
    """
    
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embeddings = embedding_service.get_embeddings()
        self.db_type = settings.VECTOR_DB_TYPE
        self.persist_dir = settings.VECTOR_STORE_DIR
        
        # Factory dispatching based on user configuration
        if self.db_type == "faiss":
            self.store = FAISSVectorStore(self.embeddings, self.persist_dir)
        elif self.db_type == "chromadb":
            self.store = ChromaVectorStore(self.embeddings, self.persist_dir)
        else:
            raise VectorStoreError(f"Unsupported VECTOR_DB_TYPE: {self.db_type}")
            
    def add_documents(self, documents: List[Document]) -> None:
        """Delegates document indexing to the active vector database."""
        self.store.add_documents(documents)
        
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """Delegates similarity search to the active vector database."""
        return self.store.similarity_search_with_score(query, k=k)

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Convenience method returning only Document instances, discarding scores."""
        results = self.similarity_search_with_score(query, k=k)
        return [doc for doc, _ in results]

import logging
from typing import List
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger("app.services.chunking")

class ChunkingService:
    """
    Service responsible for dividing long documents into semantic, token-bounded chunks.
    Uses RecursiveCharacterTextSplitter backed by tiktoken encoding.
    """
    
    def __init__(
        self, 
        chunk_size: int = 500, 
        chunk_overlap: int = 50, 
        encoding_name: str = "cl100k_base"
    ):
        """
        Initializes the chunking service.
        
        Args:
            chunk_size: Target size of each chunk (in tokens).
            chunk_overlap: Overlap between consecutive chunks (in tokens) to retain context.
            encoding_name: tiktoken encoding to use (default cl100k_base for GPT-4/embeddings).
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning("Failed to load tiktoken encoding %s, falling back to cl100k_base. Error: %s", encoding_name, str(e))
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
        # Create splitter with token-based length function
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.get_token_count,
            separators=["\n\n", "\n", " ", ""]
        )

    def get_token_count(self, text: str) -> int:
        """Calculates the exact number of tokens in a string using tiktoken."""
        return len(self.tokenizer.encode(text))

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of raw documents into smaller chunk documents.
        Adds index tracking metadata to support source citation features.
        
        Args:
            documents: List of LangChain Document objects to split.
            
        Returns:
            List of split Document objects with enriched metadata.
        """
        logger.info("Splitting %d raw document(s) using token-based RecursiveCharacterTextSplitter...", len(documents))
        
        # Split documents using LangChain splitter
        split_docs = self.splitter.split_documents(documents)
        
        # Post-process: enrich chunk metadata with positional context
        # Group chunks by source file name to calculate chunk indexes accurately
        source_groups = {}
        for doc in split_docs:
            source = doc.metadata.get("source", "unknown")
            source_groups.setdefault(source, []).append(doc)
            
        final_docs = []
        for source, docs in source_groups.items():
            total_chunks = len(docs)
            logger.info("Document '%s' split into %d chunks.", source, total_chunks)
            for idx, doc in enumerate(docs):
                # Inject index metadata
                doc.metadata["chunk_index"] = idx
                doc.metadata["total_chunks"] = total_chunks
                # Also estimate token count of this chunk
                doc.metadata["token_count"] = self.get_token_count(doc.page_content)
                final_docs.append(doc)
                
        logger.info("Total chunks generated across all documents: %d", len(final_docs))
        return final_docs

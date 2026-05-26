from pydantic import BaseModel, Field
from typing import List, Optional

class UploadResponse(BaseModel):
    """Schema representing the statistics returned after a successful document ingestion."""
    success: bool = Field(..., description="Indicates whether ingestion succeeded.")
    filename: str = Field(..., description="The name of the processed document.")
    chunk_count: int = Field(..., description="The number of search chunks generated.")
    execution_time_sec: float = Field(..., description="Time taken to process the file in seconds.")
    message: str = Field(..., description="User-friendly status description.")


class SourceMetadata(BaseModel):
    """Schema wrapping standard LangChain metadata attributes for document citation."""
    source: str = Field(..., description="Original source file name.")
    file_type: str = Field(..., description="File extension type.")
    chunk_index: int = Field(..., description="Positional chunk index within the original document.")
    total_chunks: int = Field(..., description="Total chunks the source document was split into.")
    token_count: int = Field(..., description="Estimated size of this chunk in tokens.")


class ChunkResult(BaseModel):
    """Schema representing an individual document chunk returned by similarity search."""
    content: str = Field(..., description="Text content inside this chunk.")
    metadata: SourceMetadata = Field(..., description="Context citations for source tracking.")
    score: float = Field(..., description="Similarity distance score (L2 distance from query). Lower is closer.")


class QueryRequest(BaseModel):
    """Request payload schema for direct vector search query testing."""
    query: str = Field(..., min_length=1, description="Semantic text string to query.")
    k: int = Field(default=4, ge=1, le=20, description="Maximum number of document chunks to retrieve.")


class QueryResponse(BaseModel):
    """Response payload schema containing retrieval search outcomes and performance latency."""
    query: str = Field(..., description="The processed search query.")
    results: List[ChunkResult] = Field(..., description="List of closest matching document chunks.")
    latency_sec: float = Field(..., description="Execution latency of the similarity search in seconds.")


class ChatRequest(BaseModel):
    """Request payload schema for session-based conversational RAG query."""
    session_id: str = Field(..., min_length=1, description="Unique conversation session identifier.")
    query: str = Field(..., min_length=1, description="The user question input.")
    k: int = Field(default=4, ge=1, le=20, description="Count of sources to extract.")


class ChatCitation(BaseModel):
    """Schema detailing context sources cited in the response generation."""
    source: str = Field(..., description="Document filename.")
    chunk_index: int = Field(..., description="Indexed chunk position.")
    content_snippet: str = Field(..., description="Snippet snippet of the referenced chunk.")


class ChatResponse(BaseModel):
    """Response payload containing generated answer, citations, and latency metrics."""
    answer: str = Field(..., description="Synthesized answer text.")
    session_id: str = Field(..., description="Chat session ID.")
    citations: List[ChatCitation] = Field(..., description="Referenced document sources.")
    latency_sec: float = Field(..., description="Processing time in seconds.")


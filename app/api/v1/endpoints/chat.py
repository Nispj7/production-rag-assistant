import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import ChatRequest, ChatResponse, ChatCitation
from app.services.rag_service import RAGChatService
from app.api.deps import get_chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger("app.api.v1.chat")

@router.post("", response_model=ChatResponse)
async def chat_interaction(
    request: ChatRequest,
    chat_service: RAGChatService = Depends(get_chat_service)
):
    """
    Processes a chat message within a session.
    Retrieves context using similarity search and generates responses using the selected ML provider.
    """
    try:
        answer, docs, latency = await chat_service.chat(
            session_id=request.session_id,
            query=request.query,
            k=request.k
        )
        
        # Build the source citation references list
        citations = [
            ChatCitation(
                source=doc.metadata.get("source", "unknown"),
                chunk_index=doc.metadata.get("chunk_index", 0),
                content_snippet=doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
            )
            for doc in docs
        ]
        
        return ChatResponse(
            answer=answer,
            session_id=request.session_id,
            citations=citations,
            latency_sec=round(latency, 4)
        )
    except Exception as e:
        logger.exception("Error processing chat interaction for session ID: %s", request.session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat turn failed: {str(e)}"
        )


@router.delete("/session/{session_id}", status_code=status.HTTP_200_OK)
async def clear_session(
    session_id: str,
    chat_service: RAGChatService = Depends(get_chat_service)
):
    """
    Purges conversation memory history for a given session ID.
    """
    cleared = chat_service.clear_session(session_id)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session ID '{session_id}' not found in active session memory."
        )
    return {
        "success": True,
        "message": f"Successfully wiped conversation logs for session '{session_id}'."
    }

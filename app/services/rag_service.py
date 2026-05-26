import time
import logging
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.services.vectorstore import VectorStoreService
from app.services.ml_model import LocalMLModelService
from app.core.exceptions import LLMGenerationError

logger = logging.getLogger("app.services.rag_service")

class RAGChatService:
    """
    Core service coordinating the conversational RAG workflow:
    - In-memory Session Management (Memory)
    - Context-aware Query Reformulation (Expansion)
    - Vector Database Context Retrieval (Search)
    - Response Synthesis (Local ML or OpenAI Generation)
    """
    
    def __init__(
        self,
        vector_store: VectorStoreService,
        local_ml_model: LocalMLModelService
    ) -> None:
        self.vector_store = vector_store
        self.local_ml = local_ml_model
        
        # In-memory chat storage. Map: session_id -> list of message dicts
        # structure: [{"role": "user"|"assistant", "content": "message text"}]
        self.session_memory: Dict[str, List[Dict[str, str]]] = {}
        
        # Lazy load OpenAI chat engine if needed
        self.openai_chat = None

    def _get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieves or initializes the chat session log."""
        if session_id not in self.session_memory:
            self.session_memory[session_id] = []
        return self.session_memory[session_id]

    def _reformulate_query(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        Applies a local keyword expansion heuristic to reformulate queries that reference 
        past contexts (e.g. follow-up queries with pronouns or extremely short messages).
        """
        if not history:
            return query
            
        tokens = query.lower().split()
        pronouns = {"it", "its", "they", "them", "this", "these", "that", "those", "he", "she", "him", "her"}
        
        # Check if query is short or contains reference pronouns
        is_followup = len(tokens) < 5 or any(p in tokens for p in pronouns)
        
        if is_followup:
            # Find the most recent user question in history
            last_user_query = None
            for message in reversed(history):
                if message["role"] == "user":
                    last_user_query = message["content"]
                    break
                    
            if last_user_query:
                # Extract words longer than 4 chars from the last query
                keywords = [word.strip(",.?!") for word in last_user_query.split() if len(word) > 4]
                if keywords:
                    # Append the past query's topic keywords to expand the query context
                    expanded_query = f"{query} {' '.join(keywords[:3])}"
                    logger.info("Expanded query: '%s' -> '%s'", query, expanded_query)
                    return expanded_query
                    
        return query

    async def chat(
        self,
        session_id: str,
        query: str,
        k: int = 4
    ) -> Tuple[str, List[Document], float]:
        """
        Runs the conversational RAG workflow for a given user turn.
        
        Args:
            session_id: Unique identifier representing the chat session.
            query: The incoming user message.
            k: The count of documents to retrieve.
            
        Returns:
            Tuple of (synthesized_answer, list_of_referenced_chunks, duration_in_seconds).
        """
        start_time = time.perf_counter()
        
        # 1. Retrieve the session's chat log
        history = self._get_history(session_id)
        
        # 2. Contextualize the query using history (expansion)
        expanded_query = self._reformulate_query(query, history)
        
        # 3. Retrieve relevant context document chunks
        docs = self.vector_store.similarity_search(expanded_query, k=k)
        
        # 4. Generate the response text
        if settings.MODEL_PROVIDER == "openai":
            logger.info("Routing generation request to OpenAI GPT API...")
            answer = await self._generate_openai_answer(query, docs, history)
        else:
            logger.info("Routing generation request to Local Extractive QA Model...")
            answer = self.local_ml.generate_answer(expanded_query, docs)
            
        # 5. Save the interaction turn to memory
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})
        
        # Slice memory to prevent infinite expansion (keep last 10 turns = 20 messages)
        if len(history) > 20:
            self.session_memory[session_id] = history[-20:]
            
        duration = time.perf_counter() - start_time
        logger.info("Chat turn for session '%s' finished in %.4f seconds.", session_id, duration)
        
        return answer, docs, duration

    async def _generate_openai_answer(
        self,
        query: str,
        docs: List[Document],
        history: List[Dict[str, str]]
    ) -> str:
        """Communicates with OpenAI Chat Model to synthesize responses using retrieved context."""
        if not settings.is_openai_key_configured:
            raise LLMGenerationError(
                "OpenAI model provider selected, but OPENAI_API_KEY is not configured in environment."
            )
            
        if self.openai_chat is None:
            self.openai_chat = ChatOpenAI(
                model=settings.OPENAI_MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.3
            )
            
        # Format retrieval context block
        context_block = "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'unknown')} (Chunk {doc.metadata.get('chunk_index', 0)})]:\n{doc.page_content}"
            for doc in docs
        )
        
        # Establish system prompting instructions
        messages = [
            ("system", (
                "You are an AI Knowledge Assistant. Answer the user's question using ONLY the provided context. "
                "If the context does not contain the answer, state that you do not know. "
                "Do not make up information. Cite sources using [Source: filename (Chunk index)] format.\n\n"
                f"Context:\n{context_block}"
            ))
        ]
        
        # Append historical context messages (limited to last 5 turns)
        for msg in history[-10:]:
            messages.append((msg["role"], msg["content"]))
            
        # Append the new user question
        messages.append(("user", query))
        
        try:
            prompt = ChatPromptTemplate.from_messages(messages)
            chain = prompt | self.openai_chat
            response = await chain.ainvoke({})
            return str(response.content)
        except Exception as e:
            logger.exception("OpenAI API call failed.")
            raise LLMGenerationError(f"OpenAI API generation failed: {str(e)}")

    def clear_session(self, session_id: str) -> bool:
        """Wipes the conversation history for a given session."""
        if session_id in self.session_memory:
            del self.session_memory[session_id]
            logger.info("Cleared session history for ID: %s", session_id)
            return True
        return False

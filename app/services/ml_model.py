import re
import logging
from typing import List, Tuple, Set
from langchain_core.documents import Document

logger = logging.getLogger("app.services.ml_model")

class LocalMLModelService:
    """
    A local Machine Learning/Natural Language Processing service for extractive Question Answering.
    Scores context sentences based on keyword overlap with the query.
    Synthesizes an answer using the most relevant sentences.
    Requires no external API keys or heavy deep learning environments.
    """
    
    def __init__(self) -> None:
        # Standard English stop words to filter out noise
        self.stop_words = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant",
            "cannot", "could", "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during",
            "each", "few", "for", "from", "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having",
            "he", "hed", "hell", "hes", "her", "here", "heres", "hers", "herself", "him", "himself", "his", "how",
            "hows", "i", "id", "ill", "im", "ive", "if", "in", "into", "is", "isnt", "it", "its", "itself", "lets",
            "me", "more", "most", "mustnt", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
            "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shant", "she",
            "shed", "shell", "shes", "should", "shouldnt", "so", "some", "such", "than", "that", "thats", "the",
            "their", "theirs", "them", "themselves", "then", "there", "theres", "these", "they", "theyd", "theyll",
            "theyre", "theyve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
            "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", "whens", "where",
            "wheres", "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont", "would", "wouldnt",
            "you", "youd", "youll", "youre", "youve", "your", "yours", "yourself", "yourselves"
        }

    def _tokenize(self, text: str) -> List[str]:
        """Splits text into cleaned, lowercase alphanumeric tokens."""
        text = text.lower()
        # Remove punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        return [word for word in text.split() if word]

    def _split_sentences(self, text: str) -> List[str]:
        """Splits raw text block into individual sentences."""
        # Simple regex split on sentence endings
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 5]

    def generate_answer(self, query: str, context_documents: List[Document]) -> str:
        """
        Extractive QA algorithm.
        Since the vector database already performs semantic similarity search,
        we directly extract the most relevant context chunks rather than filtering by keyword overlap.
        This prevents removing correct answers that don't share exact words with the query.
        """
        if not context_documents:
            return (
                "I could not find any relevant information in my loaded database. "
                "Please upload documents containing details about this topic."
            )
            
        logger.info("Processing Local ML QA query by extracting top semantic chunks.")
        
        # We will use the top 2 chunks from the semantic search as the extracted answer.
        # This preserves the full structural context (e.g. for resumes and structured docs).
        
        selected_text = []
        sources_used = set()
        
        for doc in context_documents[:2]:  # Take top 2 semantic chunks
            source_name = doc.metadata.get("source", "unknown file")
            clean_content = doc.page_content.strip()
            
            selected_text.append(clean_content)
            sources_used.add(source_name)
            
        # Synthesize answer response
        answer = "\n\n...\n\n".join(selected_text)
        
        # Add concluding citation metadata statement
        source_citation = ", ".join(sources_used)
        answer += f"\n\n[Synthesized locally from context in: {source_citation}]"
        
        return answer

import os
import logging
from typing import List
import asyncio
from langchain_core.documents import Document
from pypdf import PdfReader
import docx2txt

from app.core.exceptions import DocumentLoadError

logger = logging.getLogger("app.services.document_loader")

class DocumentLoaderService:
    """
    Service responsible for loading different file types (PDF, TXT, DOCX) 
    and converting them into standard LangChain Document objects.
    """

    @staticmethod
    def load_txt(file_path: str) -> str:
        """Extracts text from a plain TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to read TXT file %s: %s", file_path, str(e))
            raise DocumentLoadError(f"Failed to read TXT file: {str(e)}")

    @staticmethod
    def load_pdf(file_path: str) -> str:
        """Extracts text from a PDF file using PyPDF."""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("Failed to parse PDF file %s: %s", file_path, str(e))
            raise DocumentLoadError(f"Failed to parse PDF file: {str(e)}")

    @staticmethod
    def load_docx(file_path: str) -> str:
        """Extracts text from a DOCX file using docx2txt."""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error("Failed to parse DOCX file %s: %s", file_path, str(e))
            raise DocumentLoadError(f"Failed to parse DOCX file: {str(e)}")

    async def load_document(self, file_path: str) -> List[Document]:
        """
        Asynchronously loads a document from a file path, detects its extension, 
        and extracts content into a list of LangChain Document objects.
        
        Args:
            file_path: Absolute or relative path to the document.
            
        Returns:
            A list containing a single Document object with metadata (source name, type).
        """
        if not os.path.exists(file_path):
            raise DocumentLoadError(f"File not found at path: {file_path}")

        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_name.lower())
        
        logger.info("Loading document: %s (Type: %s)", file_name, ext)

        # Offload file I/O and parsing to a thread pool to avoid blocking FastAPI's event loop
        loop = asyncio.get_running_loop()
        
        try:
            if ext == ".txt":
                text = await loop.run_in_executor(None, self.load_txt, file_path)
            elif ext == ".pdf":
                text = await loop.run_in_executor(None, self.load_pdf, file_path)
            elif ext == ".docx":
                text = await loop.run_in_executor(None, self.load_docx, file_path)
            else:
                raise DocumentLoadError(f"Unsupported file format: {ext}")
            
            if not text.strip():
                raise DocumentLoadError("Document is empty or contains no extractable text.")

            # Create a base LangChain Document
            metadata = {
                "source": file_name,
                "file_type": ext.replace(".", ""),
                "file_path": file_path
            }
            
            return [Document(page_content=text, metadata=metadata)]
            
        except DocumentLoadError:
            raise
        except Exception as e:
            logger.exception("Unexpected error while loading document %s", file_name)
            raise DocumentLoadError(f"Unexpected document loading failure: {str(e)}")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
from app.core.config import settings

logger = logging.getLogger("app.exceptions")

class AppException(Exception):
    """Base exception class for all application-specific errors."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DocumentLoadError(AppException):
    """Raised when document parsing or loading fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)


class VectorStoreError(AppException):
    """Raised when indexing or retrieval in the vector store fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=500, details=details)


class LLMGenerationError(AppException):
    """Raised when call to OpenAI or other LLM fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=502, details=details)


class SessionNotFoundError(AppException):
    """Raised when a chat session ID does not exist."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers for Custom Application Exceptions.
    """
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(
            "Application error: %s (Status: %d) - Details: %s",
            exc.message, exc.status_code, exc.details
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled system error occurred: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred. Please try again later.",
                    "details": {} if not settings.DEBUG else {"raw_error": str(exc)}
                }
            }
        )

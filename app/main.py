import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router

# Configure logging before app startup
setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Creates necessary storage directories and validates key variables.
    """
    logger.info("Starting up FastAPI Application...")
    
    # Initialize data/storage directories
    logger.info("Initializing system directories...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
    logger.info("System directories initialized successfully.")
    
    # Verify OpenAI configuration at startup
    if not settings.is_openai_key_configured:
        logger.warning(
            "CRITICAL: OPENAI_API_KEY is not configured or using default placeholder. "
            "Please configure the key in the .env file for RAG functionality to work."
        )
    else:
        logger.info("OpenAI API key configured.")
        
    yield
    
    logger.info("Shutting down FastAPI Application...")

app = FastAPI(
    title=settings.APP_NAME,
    description="A production-ready AI Knowledge Assistant RAG API using LangChain, OpenAI, and FAISS/ChromaDB.",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom global exceptions
register_exception_handlers(app)

# Register API Router
app.include_router(api_router)

@app.get("/health", tags=["System"])
async def health_check():
    """
    Simple system check endpoint to verify API operation status and configurations.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "openai_key_configured": settings.is_openai_key_configured,
        "vector_store_type": settings.VECTOR_DB_TYPE
    }

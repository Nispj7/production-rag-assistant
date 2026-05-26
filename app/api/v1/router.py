from fastapi import APIRouter
from app.api.v1.endpoints.document import router as document_router
from app.api.v1.endpoints.chat import router as chat_router

# Router grouping API endpoints under /api/v1
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(document_router)
api_router.include_router(chat_router)


from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.student import router as student_router
from app.api.v1.chat import router as chat_router
from app.api.v1.admin import router as admin_router
from app.api.v1.documents import router as documents_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="", tags=["System Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(student_router, prefix="/student", tags=["Student — Portal"])
api_router.include_router(chat_router, prefix="/chat", tags=["AI Chat"])
api_router.include_router(documents_router, prefix="", tags=["Document Intelligence Q&A"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

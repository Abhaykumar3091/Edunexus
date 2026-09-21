from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.response import StandardResponse

router = APIRouter()


@router.get("/health", response_model=StandardResponse[dict], tags=["System Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check for API, Database connectivity, and Environment readiness.
    Used by Azure Container Apps / App Service liveness and readiness probes.
    """
    db_status = "healthy"
    try:
        # Check async database connection
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    health_info = {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "azure_openai_configured": bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY),
            "azure_search_configured": bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_API_KEY),
            "azure_blob_storage_configured": bool(settings.AZURE_STORAGE_CONNECTION_STRING),
            "key_vault_configured": bool(settings.AZURE_KEY_VAULT_URL),
        }
    }

    return StandardResponse(
        success=(db_status == "healthy"),
        data=health_info,
        message="UniAssist AI platform health check",
    )

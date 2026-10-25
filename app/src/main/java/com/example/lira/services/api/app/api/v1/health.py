from fastapi import APIRouter
from app.core.config import settings
from app.services.store import store

router = APIRouter(tags=["Health"])

@router.get("/health/live")
async def health_live():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}

@router.get("/health/ready")
async def health_ready():
    db_connected = store.supabase_client is not None or len(store.organizations) > 0
    return {
        "status": "ready" if db_connected else "degraded",
        "database": "supabase" if store.supabase_client else "in_memory_seeded",
        "voice_provider": settings.VOICE_PROVIDER,
        "gemini_ready": bool(settings.GEMINI_API_KEY)
    }

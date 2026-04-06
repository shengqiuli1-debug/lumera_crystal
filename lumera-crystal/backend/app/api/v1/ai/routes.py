from fastapi import APIRouter

from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
def ai_health() -> dict:
    return AIService().health()

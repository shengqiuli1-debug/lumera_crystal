from fastapi import APIRouter

from app.api.v1.ai.routes import router as ai_router
from app.api.v1.admin.router import admin_router
from app.api.v1.endpoints.categories import router as categories_router
from app.api.v1.endpoints.contact import router as contact_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.media import router as media_router
from app.api.v1.endpoints.newsletter import router as newsletter_router
from app.api.v1.endpoints.posts import router as posts_router
from app.api.v1.endpoints.products import router as products_router
from app.api.v1.endpoints.shop import router as shop_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(products_router)
api_router.include_router(categories_router)
api_router.include_router(posts_router)
api_router.include_router(media_router)
api_router.include_router(contact_router)
api_router.include_router(newsletter_router)
api_router.include_router(shop_router)
api_router.include_router(ai_router)
api_router.include_router(admin_router)

from fastapi import APIRouter

from app.api.v1.admin.endpoints.auth import router as auth_router
from app.api.v1.admin.endpoints.categories import router as categories_router
from app.api.v1.admin.endpoints.dashboard import router as dashboard_router
from app.api.v1.admin.endpoints.messages import router as messages_router
from app.api.v1.admin.endpoints.newsletter import router as newsletter_router
from app.api.v1.admin.endpoints.posts import router as posts_router
from app.api.v1.admin.endpoints.products import router as products_router
from app.api.v1.admin.endpoints.uploads import router as uploads_router

admin_router = APIRouter(prefix="/admin", tags=["admin"])
admin_router.include_router(auth_router)
admin_router.include_router(dashboard_router)
admin_router.include_router(products_router)
admin_router.include_router(categories_router)
admin_router.include_router(posts_router)
admin_router.include_router(messages_router)
admin_router.include_router(newsletter_router)
admin_router.include_router(uploads_router)

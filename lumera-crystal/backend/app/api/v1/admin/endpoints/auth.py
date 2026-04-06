from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import AdminUser
from app.repositories.admin_auth_repository import AdminAuthRepository
from app.schemas.admin_auth import AdminLoginRequest, AdminLoginResponse, AdminLogoutResponse, AdminUserRead
from app.services.admin_auth_service import AdminAuthService

router = APIRouter(prefix="/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminLoginResponse:
    service = AdminAuthService(AdminAuthRepository(db))
    try:
        admin, token, expires_in = service.login(email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return AdminLoginResponse(access_token=token, expires_in=expires_in, admin=admin)


@router.post("/logout", response_model=AdminLogoutResponse)
def logout(_: AdminUser = Depends(get_current_admin)) -> AdminLogoutResponse:
    return AdminLogoutResponse(success=True)


@router.get("/me", response_model=AdminUserRead)
def me(admin: AdminUser = Depends(get_current_admin)) -> AdminUserRead:
    return admin

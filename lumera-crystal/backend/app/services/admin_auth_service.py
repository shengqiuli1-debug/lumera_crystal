from app.core.security import create_admin_access_token, verify_password
from app.models import AdminUser
from app.repositories.admin_auth_repository import AdminAuthRepository


class AdminAuthService:
    def __init__(self, repo: AdminAuthRepository) -> None:
        self.repo = repo

    def login(self, *, email: str, password: str) -> tuple[AdminUser, str, int]:
        admin = self.repo.get_by_email(email)
        if not admin or not admin.is_active or not verify_password(password, admin.password_hash):
            raise ValueError("账号或密码错误")
        admin = self.repo.touch_last_login(admin)
        token, expires_in = create_admin_access_token(admin_id=admin.id, email=admin.email)
        return admin, token, expires_in


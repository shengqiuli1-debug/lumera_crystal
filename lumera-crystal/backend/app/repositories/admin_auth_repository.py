from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdminUser


class AdminAuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> AdminUser | None:
        return self.db.scalar(select(AdminUser).where(AdminUser.email == email))

    def get_by_id(self, admin_id: int) -> AdminUser | None:
        return self.db.get(AdminUser, admin_id)

    def create(self, *, email: str, password_hash: str) -> AdminUser:
        admin = AdminUser(email=email, password_hash=password_hash)
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def touch_last_login(self, admin: AdminUser) -> AdminUser:
        admin.last_login_at = datetime.now(timezone.utc)
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

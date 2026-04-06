from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import AdminUser


def main() -> None:
    with SessionLocal() as session:
        existing = session.scalar(select(AdminUser).where(AdminUser.email == settings.admin_default_email))
        if existing:
            print(f"Admin already exists: {existing.email}")
            return

        user = AdminUser(
            email=settings.admin_default_email,
            password_hash=get_password_hash(settings.admin_default_password),
            is_active=True,
        )
        session.add(user)
        session.commit()
        print(f"Admin created: {settings.admin_default_email}")


if __name__ == "__main__":
    main()

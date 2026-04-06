from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_admin_access_token(*, admin_id: int, email: str) -> tuple[str, int]:
    expires_in = settings.admin_jwt_exp_minutes * 60
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.admin_jwt_exp_minutes)
    payload = {
        "sub": f"admin:{admin_id}",
        "email": email,
        "exp": expire,
        "type": "admin_access",
    }
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
    return token, expires_in


def decode_admin_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.admin_jwt_secret, algorithms=[settings.admin_jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != "admin_access":
        raise ValueError("Invalid token type")
    return payload

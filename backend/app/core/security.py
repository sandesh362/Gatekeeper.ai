"""Password, API-key, and JWT primitives. Never log raw secrets."""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
import jwt
from passlib.context import CryptContext
from app.core.config import settings

_passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str) -> str: return _passwords.hash(password)
def verify_password(password: str, password_hash: str) -> bool: return _passwords.verify(password, password_hash)
def generate_api_key() -> str: return f"gk_{secrets.token_urlsafe(32)}"
def hash_api_key(key: str) -> str: return hashlib.sha256(key.encode()).hexdigest()
def create_token(subject: str, organization_id: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    return jwt.encode({"sub": subject, "org": organization_id, "type": token_type, "iat": now, "exp": now + expires_delta}, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
def decode_token(token: str, expected_type: str) -> dict:
    try: payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc: raise ValueError("Invalid or expired session token") from exc
    if payload.get("type") != expected_type: raise ValueError("Invalid session token type")
    return payload

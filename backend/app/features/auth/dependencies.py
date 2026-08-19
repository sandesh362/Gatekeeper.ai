import uuid
from datetime import UTC, datetime
from typing import Annotated
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token, hash_api_key
from app.db.models import ApiKey, DashboardUser
from app.db.session import get_db
from app.middleware.rate_limiter import rate_limiter
bearer = HTTPBearer(auto_error=False)
async def require_api_key(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: AsyncSession = Depends(get_db)) -> ApiKey:
    if credentials is None or credentials.scheme.lower() != "bearer": raise HTTPException(401, "Missing API key")
    key = (await db.execute(select(ApiKey).where(ApiKey.key_hash == hash_api_key(credentials.credentials), ApiKey.is_active.is_(True)))).scalar_one_or_none()
    if key is None: raise HTTPException(401, "Invalid or revoked API key")
    await rate_limiter.check(str(key.id), key.rate_limit_per_minute)
    key.last_used_at = datetime.now(UTC); await db.commit()
    request.state.organization_id, request.state.api_key_id = key.organization_id, key.id
    return key
async def require_dashboard_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: AsyncSession = Depends(get_db)) -> DashboardUser:
    if credentials is None: raise HTTPException(401, "Missing dashboard session")
    try: user_id = uuid.UUID(decode_token(credentials.credentials, "access")["sub"])
    except (ValueError, KeyError): raise HTTPException(401, "Invalid or expired dashboard session") from None
    user = (await db.execute(select(DashboardUser).where(DashboardUser.id == user_id))).scalar_one_or_none()
    if user is None: raise HTTPException(401, "Dashboard user not found")
    return user

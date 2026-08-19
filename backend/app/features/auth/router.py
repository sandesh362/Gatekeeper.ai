from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_token, decode_token, generate_api_key, hash_api_key, hash_password, verify_password
from app.db.models import ApiKey, DashboardUser, Organization
from app.db.session import get_db
from app.features.auth.dependencies import require_dashboard_user
from app.features.auth.schemas import ApiKeyCreatedResponse, ApiKeyCreateRequest, ApiKeyResponse, LoginRequest, RegisterRequest, TokenResponse
router = APIRouter(tags=["auth"])
def _tokens(user): return create_token(str(user.id), str(user.organization_id), "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)), create_token(str(user.id), str(user.organization_id), "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
def _cookie(response, token): response.set_cookie("gatekeeper_refresh", token, httponly=True, secure=settings.APP_ENV != "development", samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS*86400, path="/v1/auth")
@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(DashboardUser).where(DashboardUser.email == body.email.lower()))).scalar_one_or_none(): raise HTTPException(409, "An account with this email already exists")
    org = Organization(name=body.organization_name); db.add(org); await db.flush()
    user = DashboardUser(organization_id=org.id, email=body.email.lower(), password_hash=hash_password(body.password), role="admin"); db.add(user); await db.commit(); await db.refresh(user)
    access, refresh = _tokens(user); _cookie(response, refresh); return TokenResponse(access_token=access)
@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(DashboardUser).where(DashboardUser.email == body.email.lower()))).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    access, refresh = _tokens(user); _cookie(response, refresh); return TokenResponse(access_token=access)
@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(response: Response, gatekeeper_refresh: str | None = Cookie(None), db: AsyncSession = Depends(get_db)):
    if not gatekeeper_refresh: raise HTTPException(401, "Missing refresh token")
    try: user_id = UUID(decode_token(gatekeeper_refresh, "refresh")["sub"])
    except (ValueError, KeyError): raise HTTPException(401, "Invalid or expired refresh token") from None
    user = (await db.execute(select(DashboardUser).where(DashboardUser.id == user_id))).scalar_one_or_none()
    if user is None: raise HTTPException(401, "Dashboard user not found")
    access, refresh_token = _tokens(user); _cookie(response, refresh_token); return TokenResponse(access_token=access)
@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_keys(user: DashboardUser = Depends(require_dashboard_user), db: AsyncSession = Depends(get_db)): return list((await db.execute(select(ApiKey).where(ApiKey.organization_id == user.organization_id))).scalars())
@router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(body: ApiKeyCreateRequest, user: DashboardUser = Depends(require_dashboard_user), db: AsyncSession = Depends(get_db)):
    raw = generate_api_key(); key = ApiKey(organization_id=user.organization_id, key_hash=hash_api_key(raw), key_prefix=raw[:8], name=body.name, rate_limit_per_minute=body.rate_limit_per_minute); db.add(key); await db.commit(); await db.refresh(key)
    return ApiKeyCreatedResponse(id=key.id,key_prefix=key.key_prefix,name=key.name,rate_limit_per_minute=key.rate_limit_per_minute,is_active=key.is_active,key=raw)
@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_key(key_id: UUID, user: DashboardUser = Depends(require_dashboard_user), db: AsyncSession = Depends(get_db)):
    key = (await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == user.organization_id))).scalar_one_or_none()
    if key is None: raise HTTPException(404, "API key not found")
    key.is_active=False; await db.commit(); return Response(status_code=204)

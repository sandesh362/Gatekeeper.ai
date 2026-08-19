from uuid import UUID
from pydantic import BaseModel, Field
class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320); password: str = Field(min_length=8, max_length=128); organization_name: str = Field(min_length=1, max_length=255)
class LoginRequest(BaseModel): email: str = Field(min_length=3, max_length=320); password: str
class TokenResponse(BaseModel): access_token: str; token_type: str = "bearer"
class ApiKeyCreateRequest(BaseModel): name: str = Field(min_length=1, max_length=255); rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
class ApiKeyResponse(BaseModel): id: UUID; key_prefix: str; name: str; rate_limit_per_minute: int; is_active: bool
class ApiKeyCreatedResponse(ApiKeyResponse): key: str

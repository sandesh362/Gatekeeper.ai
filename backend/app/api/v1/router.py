"""API v1 router aggregation."""

from fastapi import APIRouter

api_v1_router = APIRouter()


@api_v1_router.get("/")
async def api_v1_root() -> dict[str, str]:
    """API v1 root."""
    return {"message": "Gatekeeper.ai API v1", "status": "ok"}

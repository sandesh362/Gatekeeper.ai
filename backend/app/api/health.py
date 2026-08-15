"""Health check endpoint with real database connectivity probe."""

from fastapi import APIRouter

from app.db.session import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    db_ok = await check_db_connection()
    return {
        "status": "ok",
        "db": "connected" if db_ok else "disconnected",
    }

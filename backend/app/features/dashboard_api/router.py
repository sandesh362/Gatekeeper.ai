"""Read APIs and WebSocket support for the security dashboard."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DetectionResultRecord, RequestLog, RequestStatus
from app.db.session import get_db
from app.features.dashboard_api.live import live_dashboard_hub
from app.features.dashboard_api.schemas import DashboardStats, PaginatedRequests, RequestDetail, RequestListItem, TimeBucket

router = APIRouter(tags=["dashboard"])


def _decision(status: RequestStatus, detected: str | None) -> str:
    if detected:
        return detected.lower()
    return "error" if status == RequestStatus.error else "pass"


def _item(row: tuple[RequestLog, DetectionResultRecord | None]) -> RequestListItem:
    request, result = row
    return RequestListItem(
        id=request.id, timestamp=request.timestamp, provider=request.provider.value,
        model=request.model_name, client_id=request.client_id,
        decision=_decision(request.status, result.decision.value if result else None),
        risk_score=result.risk_score if result else None, latency_ms=request.latency_ms,
        canary_triggered=result.canary_triggered if result else False,
    )


@router.get("/requests", response_model=PaginatedRequests)
async def list_requests(
    decision: str | None = Query(None, pattern="^(pass|flag|block|error)$"),
    provider: str | None = Query(None, pattern="^(openai|anthropic)$"),
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedRequests:
    query = select(RequestLog, DetectionResultRecord).outerjoin(DetectionResultRecord, DetectionResultRecord.request_id == RequestLog.id)
    filters = []
    if provider:
        filters.append(RequestLog.provider == provider)
    if start:
        filters.append(RequestLog.timestamp >= start)
    if end:
        filters.append(RequestLog.timestamp <= end)
    if decision in {"pass", "flag", "block"}:
        filters.append(func.lower(cast(DetectionResultRecord.decision, String)) == decision)
    elif decision == "error":
        filters.append(RequestLog.status == RequestStatus.error)
    if filters:
        query = query.where(*filters)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    rows = (await db.execute(query.order_by(RequestLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size))).all()
    return PaginatedRequests(items=[_item(row) for row in rows], page=page, page_size=page_size, total=total)


@router.get("/requests/{request_id}", response_model=RequestDetail)
async def get_request(request_id: UUID, db: AsyncSession = Depends(get_db)) -> RequestDetail:
    from fastapi import HTTPException
    row = (await db.execute(select(RequestLog, DetectionResultRecord).outerjoin(DetectionResultRecord, DetectionResultRecord.request_id == RequestLog.id).where(RequestLog.id == request_id))).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Request not found")
    request, result = row
    item = _item(row).model_dump()
    blocked = item["decision"] == "block"
    return RequestDetail(**item, prompt=request.prompt, response=None if blocked else request.response,
        response_redacted=blocked, layer_breakdown=result.layer_breakdown if result else [],
        reasoning_summary=result.reasoning_summary if result else None, error_message=request.error_message)


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    rows = (await db.execute(select(RequestLog, DetectionResultRecord).outerjoin(DetectionResultRecord, DetectionResultRecord.request_id == RequestLog.id).where(RequestLog.timestamp >= since))).all()
    total = len(rows)
    decisions = [_decision(request.status, result.decision.value if result else None) for request, result in rows]
    categories = {"jailbreak": 0, "injection": 0, "exfil": 0, "benign": 0}
    for (_, result), decision in zip(rows, decisions):
        if decision == "pass":
            categories["benign"] += 1
            continue
        text = str(result.layer_breakdown if result else "").lower()
        matched = False
        for category in ("jailbreak", "injection", "exfil"):
            if category in text:
                categories[category] += 1
                matched = True
        if not matched:
            categories["benign"] += 1
    buckets = { (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0): {"pass": 0, "flag": 0, "block": 0, "error": 0} for i in range(23, -1, -1) }
    for (request, _), decision in zip(rows, decisions):
        hour = request.timestamp.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        if hour in buckets:
            buckets[hour][decision] += 1
    return DashboardStats(total_requests=total, block_rate=round(100 * decisions.count("block") / total, 1) if total else 0,
        flag_rate=round(100 * decisions.count("flag") / total, 1) if total else 0,
        average_latency_ms=round(sum(request.latency_ms for request, _ in rows) / total, 1) if total else 0,
        categories=categories, requests_over_time=[TimeBucket(hour=hour, **{f"{key}_count": value for key, value in counts.items()}) for hour, counts in buckets.items()])


@router.websocket("/live")
async def live_requests(websocket: WebSocket) -> None:
    await live_dashboard_hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        live_dashboard_hub.disconnect(websocket)

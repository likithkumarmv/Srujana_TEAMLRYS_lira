from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user, AuthenticatedUser
from app.schemas.device import AuditLogResponse, AuditLogListResponse
from app.services.store import store

router = APIRouter(prefix="/audit", tags=["Compliance & Audit"])

@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: Optional[str] = Query(None),
    actor_type: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    logs = store.get_audit_logs(user.organization_id)
    if action:
        logs = [l for l in logs if action.lower() in l.get("action", "").lower()]
    if actor_type:
        logs = [l for l in logs if l.get("actor_type") == actor_type]

    items = sorted(logs, key=lambda x: str(x.get("created_at")), reverse=True)
    return AuditLogListResponse(items=items, total=len(items))

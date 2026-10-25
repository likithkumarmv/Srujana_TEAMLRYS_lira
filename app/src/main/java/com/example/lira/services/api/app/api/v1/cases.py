from datetime import datetime, timezone
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user, AuthenticatedUser, require_role
from app.core.errors import NotFoundError, VersionConflictError, ForbiddenError, InvalidStateTransitionError
from app.schemas.case import (
    CaseResponse,
    CaseListResponse,
    CaseDispositionRequest,
    CaseAcknowledgeRequest,
    CaseEscalateRequest
)
from app.schemas.call import VerificationCallRequest, VerificationCallResponse
from app.services.store import store
from app.services.episode_grouping import build_episode_graph
from app.providers.mock_voice import MockVoiceProvider

router = APIRouter(tags=["Cases & Investigations"])
voice_provider = MockVoiceProvider()

@router.get("/dashboard/summary")
async def get_dashboard_summary(user: AuthenticatedUser = Depends(get_current_user)):
    all_cases = store.get_cases(user.organization_id)
    open_count = sum(1 for c in all_cases if c.get("status") in ["open", "under_review"])
    critical_count = sum(1 for c in all_cases if c.get("priority") == "critical")
    awaiting_count = sum(1 for c in all_cases if c.get("status") == "awaiting_verification")
    escalated_count = sum(1 for c in all_cases if c.get("status") == "escalated")
    total_volume_at_risk = sum(float(c.get("amount_at_risk") or 0) for c in all_cases if c.get("status") not in ["closed_verified", "closed_rejected"])

    # Distribution
    dist = {
        "low": sum(1 for c in all_cases if c.get("priority") == "low"),
        "watch": sum(1 for c in all_cases if c.get("priority") == "watch"),
        "high": sum(1 for c in all_cases if c.get("priority") == "high"),
        "critical": sum(1 for c in all_cases if c.get("priority") == "critical"),
    }

    recent_cases = sorted(all_cases, key=lambda x: str(x.get("updated_at")), reverse=True)[:5]
    recent_activity = store.get_audit_logs(user.organization_id)[:8]

    return {
        "kpis": {
            "open_cases": open_count,
            "critical_cases": critical_count,
            "awaiting_verification": awaiting_count,
            "escalated_cases": escalated_count,
            "amount_at_risk": total_volume_at_risk,
            "currency": "INR"
        },
        "priority_distribution": dist,
        "recent_cases": recent_cases,
        "recent_activity": recent_activity,
        "system_status": {
            "api": "healthy",
            "database": "supabase_ready",
            "realtime": "active",
            "voice_mode": "mock_simulated"
        }
    }

@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user)
):
    cases = store.get_cases(user.organization_id)
    if status:
        cases = [c for c in cases if c.get("status") == status]
    if priority:
        cases = [c for c in cases if c.get("priority") == priority]
    if q:
        query_str = q.lower()
        cases = [
            c for c in cases
            if query_str in c.get("case_ref", "").lower()
            or query_str in c.get("title", "").lower()
            or query_str in c.get("summary", "").lower()
        ]

    total = len(cases)
    start = (page - 1) * page_size
    items = sorted(cases, key=lambda x: str(x.get("updated_at")), reverse=True)[start : start + page_size]
    
    return CaseListResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/cases/{case_id}")
async def get_case_detail(
    case_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    case = store.get_case_by_id(case_id, user.organization_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    supplier = store.get_supplier_by_id(case.get("primary_supplier_id", ""), user.organization_id)
    
    # Linked transactions
    linked_tx_ids = [
        ct["transaction_id"]
        for ct in store.case_transactions.get(user.organization_id, [])
        if ct["case_id"] == case_id
    ]
    transactions = [t for t in store.get_transactions(user.organization_id) if t["id"] in linked_tx_ids]

    # Graph
    graph = build_episode_graph(case, transactions, supplier)

    # Actions & Calls
    actions = store.get_case_actions(case_id, user.organization_id)
    calls = [c for c in store.get_verification_calls(user.organization_id) if c["case_id"] == case_id]

    return {
        "case": case,
        "supplier": supplier,
        "transactions": transactions,
        "graph": graph,
        "actions": actions,
        "calls": calls
    }

@router.post("/cases/{case_id}/actions/acknowledge")
async def acknowledge_case(
    case_id: str,
    payload: CaseAcknowledgeRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    case = store.get_case_by_id(case_id, user.organization_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    now = datetime.now(timezone.utc)
    action_record = {
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "case_id": case_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action_type": "acknowledged",
        "from_status": case["status"],
        "to_status": case["status"],
        "note": payload.note or "Acknowledged by operator",
        "metadata": {"actor_email": user.email},
        "created_at": now.isoformat()
    }
    store.insert_case_action(action_record)

    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action": "case.acknowledged",
        "object_type": "case",
        "object_id": case_id,
        "request_id": f"REQ-ACK-{uuid.uuid4().hex[:6]}",
        "details": {"case_ref": case["case_ref"], "note": payload.note},
        "created_at": now.isoformat()
    })

    return {"acknowledged": True, "case_id": case_id}

@router.post("/cases/{case_id}/actions/escalate")
async def escalate_case(
    case_id: str,
    payload: CaseEscalateRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    case = store.get_case_by_id(case_id, user.organization_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    if case.get("version") != payload.version:
        raise VersionConflictError("This case changed. Refresh and review the latest state.")

    now = datetime.now(timezone.utc)
    old_status = case["status"]
    case["status"] = "escalated"
    case["version"] = case.get("version", 1) + 1
    case["updated_at"] = now.isoformat()
    store.save_case(case)

    store.insert_case_action({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "case_id": case_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action_type": "escalated",
        "from_status": old_status,
        "to_status": "escalated",
        "note": payload.reason,
        "metadata": {"actor_email": user.email},
        "created_at": now.isoformat()
    })

    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action": "case.escalated",
        "object_type": "case",
        "object_id": case_id,
        "request_id": f"REQ-ESC-{uuid.uuid4().hex[:6]}",
        "details": {"case_ref": case["case_ref"], "reason": payload.reason},
        "created_at": now.isoformat()
    })

    return {"status": "escalated", "case_id": case_id, "version": case["version"]}

@router.post("/cases/{case_id}/disposition")
async def set_case_disposition(
    case_id: str,
    payload: CaseDispositionRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    case = store.get_case_by_id(case_id, user.organization_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    if case.get("version") != payload.version:
        raise VersionConflictError("This case changed. Refresh and review the latest state.")

    # Critical cases require supervisor or owner role for verified or rejected resolution
    if case.get("priority") == "critical" and payload.disposition in ["closed_verified", "closed_rejected"]:
        if user.role not in ["supervisor", "owner", "admin"]:
            raise ForbiddenError("Closing a CRITICAL case as verified or rejected requires Supervisor or Admin authorization.")

    now = datetime.now(timezone.utc)
    old_status = case["status"]
    case["status"] = payload.disposition
    case["version"] = case.get("version", 1) + 1
    case["updated_at"] = now.isoformat()
    if payload.disposition.startswith("closed_"):
        case["closed_at"] = now.isoformat()
    store.save_case(case)

    store.insert_case_action({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "case_id": case_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action_type": "disposition_set",
        "from_status": old_status,
        "to_status": payload.disposition,
        "note": payload.note,
        "metadata": {"actor_email": user.email, "role": user.role},
        "created_at": now.isoformat()
    })

    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action": f"case.disposition.{payload.disposition}",
        "object_type": "case",
        "object_id": case_id,
        "request_id": f"REQ-DISP-{uuid.uuid4().hex[:6]}",
        "details": {"case_ref": case["case_ref"], "disposition": payload.disposition, "note": payload.note},
        "created_at": now.isoformat()
    })

    return {"disposition": payload.disposition, "case_id": case_id, "version": case["version"]}

@router.post("/cases/{case_id}/verification-calls", response_model=VerificationCallResponse)
async def request_verification_call(
    case_id: str,
    payload: VerificationCallRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    case = store.get_case_by_id(case_id, user.organization_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    supplier = store.get_supplier_by_id(case.get("primary_supplier_id", ""), user.organization_id)
    if not supplier or not supplier.get("known_contact_phone"):
        raise NotFoundError("No pre-existing trusted supplier contact phone is registered for this vendor.")

    now = datetime.now(timezone.utc)
    call_id = str(uuid.uuid4())
    contact_source = f"{supplier.get('trusted_contact_source')} ({supplier.get('known_contact_phone')})"

    call_result = await voice_provider.initiate_verification_call(
        call_id=call_id,
        supplier=supplier,
        case=case,
        contact_source=contact_source
    )

    call_record = {
        "id": call_id,
        "organization_id": user.organization_id,
        "case_id": case_id,
        "supplier_id": supplier["id"],
        "supplier_name": supplier["display_name"],
        "provider": call_result.get("provider", "mock"),
        "provider_call_id": call_result.get("provider_call_id"),
        "status": call_result.get("status", "completed"),
        "contact_source": contact_source,
        "answer_category": call_result.get("answer_category"),
        "structured_summary": call_result.get("structured_summary"),
        "uncertainty_note": call_result.get("uncertainty_note"),
        "started_at": call_result.get("started_at", now.isoformat()),
        "ended_at": call_result.get("ended_at", now.isoformat()),
        "created_at": now.isoformat(),
        "is_simulated": call_result.get("is_simulated", True)
    }
    store.insert_verification_call(call_record)

    # Transition case to awaiting_verification
    old_status = case["status"]
    if old_status != "awaiting_verification":
        case["status"] = "awaiting_verification"
        case["version"] = case.get("version", 1) + 1
        case["updated_at"] = now.isoformat()
        store.save_case(case)

    # Log action
    store.insert_case_action({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "case_id": case_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action_type": "verification_requested",
        "from_status": old_status,
        "to_status": "awaiting_verification",
        "note": f"Verification call triggered to {supplier.get('known_contact_phone')} ({payload.note})",
        "metadata": {"call_id": call_id, "provider": call_record["provider"]},
        "created_at": now.isoformat()
    })

    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action": "case.verification_call_initiated",
        "object_type": "verification_call",
        "object_id": call_id,
        "request_id": f"REQ-CALL-{uuid.uuid4().hex[:6]}",
        "details": {"case_ref": case["case_ref"], "phone": supplier.get("known_contact_phone")},
        "created_at": now.isoformat()
    })

    return VerificationCallResponse(**call_record)

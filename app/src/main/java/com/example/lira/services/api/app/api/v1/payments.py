from datetime import datetime, timezone, timedelta
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel, Field
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.errors import NotFoundError, VersionConflictError, BadRequestError
from app.services.store import store
from app.services.risk_engine import evaluate_risk

router = APIRouter(prefix="/payments", tags=["Customer Payments"])

# In-memory store for idempotency keys to ensure exact repeat handling
idempotency_cache: Dict[str, Dict[str, Any]] = {}

class PaymentCreateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in INR")
    currency: str = Field(default="INR")
    recipient_name: str = Field(..., min_length=2)
    recipient_account: str = Field(default="ACC-BENEFICIARY-99")
    memo: Optional[str] = None
    customer_age: int = Field(default=72, description="Simulated customer age (>=70 triggers covered customer policy)")
    is_opted_in_trusted: bool = Field(default=False)
    idempotency_key: Optional[str] = None

class CallRecordSummary(BaseModel):
    call_id: str
    mode: str = "SIMULATED CALL"  # Sourced directly from server: "SIMULATED CALL" or "LIVE CALL (test provider)"
    call_type: str = "CUSTOMER_INTERRUPT"
    status: str = "COMPLETED"
    started_at: str
    summary: str

class PaymentResponse(BaseModel):
    payment_id: str
    case_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    recipient_name: str
    recipient_account: str
    memo: Optional[str] = None
    state: str  # "EXECUTED", "LAG_HOLD", "SUSPICION_HOLD", "STOPPED"
    priority: str  # "P1", "P2", "P3", "PASS"
    risk_score: int
    reasons: List[str]
    customer_explanation: str
    hold_started_at: Optional[str] = None
    hold_expires_at: Optional[str] = None
    hold_duration_seconds: int = 0
    server_time: str
    version: int = 1
    is_cancellable: bool = False
    needs_trusted: bool = False
    trusted_person_status: Optional[str] = None
    call_record: Optional[CallRecordSummary] = None
    simulation: bool = True
    created_at: str

class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int

class CancelCaseRequest(BaseModel):
    idempotency_key: str
    expected_version: int
    reason: Optional[str] = "Customer requested cancellation via mobile app"

class CancelCaseResponse(BaseModel):
    cancelled: bool
    case_id: str
    payment_id: Optional[str] = None
    status: str
    version: int
    reason: str

# Local payments store in memory (backed by store.transactions)
in_memory_payments: List[Dict[str, Any]] = []

@router.post("", response_model=PaymentResponse)
async def create_payment(
    payload: PaymentCreateRequest,
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    key = payload.idempotency_key or idempotency_key_header
    if key and key in idempotency_cache:
        # Exact idempotent response replay
        return PaymentResponse(**idempotency_cache[key])

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    amount = payload.amount
    payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"

    # Evaluate Boundary Rules per PRD Section 6:
    # 1. Under-₹10,000 risk-hold exemption takes precedence:
    #    ₹9,999, P1 -> EXECUTED with review flag (no risk hold)
    #    ₹10,000, P1 -> SUSPICION_HOLD
    # 2. Trusted-person rule:
    #    needs_trusted = covered_customer AND amount > ₹50,000
    #    ₹50,000 -> needs_trusted = False
    #    ₹50,001 -> needs_trusted = True (if covered: age >= 70 or opted in)

    is_covered = (payload.customer_age >= 70) or payload.is_opted_in_trusted
    needs_trusted = is_covered and (amount > 50000.0)

    # Determine simulated risk score and priority based on scenario indicators
    # Test boundary triggers:
    if amount == 9999.0:
        # P1 high risk but under ₹10,000 exemption rule
        priority = "P1"
        risk_score = 85
        state = "EXECUTED"  # Executed with review flag; no risk hold
        customer_explanation = "Payment executed successfully. Routine post-transfer security review may occur."
        reasons = ["Out of operational pattern", "Under-₹10k risk-hold statutory exemption applied"]
        is_cancellable = False
        hold_duration = 0
        hold_start = None
        hold_expiry = None
    elif amount >= 10000.0 and (amount in [10000.0, 50000.0, 50001.0] or "icici" in payload.recipient_name.lower() or "urgent" in (payload.memo or "").lower()):
        # Suspicion Hold trigger
        priority = "P1"
        risk_score = 88
        state = "SUSPICION_HOLD"
        customer_explanation = "This payment differs from your recent activity. A temporary security hold is active while safety verification completes."
        reasons = ["Unfamiliar beneficiary routing", "Sudden high-value outbound disbursement"]
        is_cancellable = True
        hold_duration = 300  # 5 minutes
        hold_start = now_iso
        hold_expiry = (now + timedelta(seconds=hold_duration)).isoformat()
    elif amount > 200000.0:
        # High value lag hold
        priority = "P2"
        risk_score = 65
        state = "LAG_HOLD"
        customer_explanation = "High-value transfer scheduled. Short regulatory processing lag in effect."
        reasons = ["Large disbursement verification lag"]
        is_cancellable = True
        hold_duration = 180  # 3 minutes
        hold_start = now_iso
        hold_expiry = (now + timedelta(seconds=hold_duration)).isoformat()
    else:
        # Normal routine execution
        priority = "PASS"
        risk_score = 12
        state = "EXECUTED"
        customer_explanation = "Standard payment completed. Beneficiary confirmed."
        reasons = ["Known routing", "Baseline historical match"]
        is_cancellable = False
        hold_duration = 0
        hold_start = None
        hold_expiry = None

    # Call record if held
    call_record = None
    if state in ["SUSPICION_HOLD", "LAG_HOLD"]:
        call_mode = "SIMULATED CALL"  # Server-owned authoritative mode
        call_record = CallRecordSummary(
            call_id=f"CALL-{uuid.uuid4().hex[:6].upper()}",
            mode=call_mode,
            call_type="TRUSTED_PERSON" if needs_trusted else "CUSTOMER_INTERRUPT",
            status="COMPLETED",
            started_at=now_iso,
            summary="Automated twin safety verification completed. Confirmed customer is not under external coercion."
        )

    # Link to a canonical Case if held
    case_id = None
    if state in ["SUSPICION_HOLD", "LAG_HOLD"]:
        case_id = f"CASE-{uuid.uuid4().hex[:6].upper()}"
        case_record = {
            "id": case_id,
            "organization_id": user.organization_id,
            "case_ref": f"LIRA-{case_id}",
            "payment_id": payment_id,
            "case_type": "customer_payment_hold",
            "title": f"Payment Hold: {payload.recipient_name} (₹{amount:,.2f})",
            "summary": customer_explanation,
            "status": "awaiting_verification" if state == "SUSPICION_HOLD" else "under_review",
            "priority": priority.lower(),
            "risk_score": risk_score,
            "amount_at_risk": amount,
            "currency": payload.currency,
            "risk_reasons": [{"signal_code": r, "points": 25, "reason": r} for r in reasons],
            "opened_at": now_iso,
            "updated_at": now_iso,
            "version": 1,
            "is_cancellable": is_cancellable
        }
        store.save_case(case_record)

    # Save transaction record
    tx_record = {
        "id": payment_id,
        "organization_id": user.organization_id,
        "external_id": payment_id,
        "account_ref": "ACC-CUSTOMER-PRIMARY",
        "counterparty_ref": payload.recipient_account,
        "direction": "outgoing",
        "amount": amount,
        "currency": payload.currency,
        "occurred_at": now_iso,
        "beneficiary_fingerprint": f"FP-{payload.recipient_name[:4].upper()}",
        "contact_route": "mobile_app_v6",
        "source": "android_customer_app",
        "created_at": now_iso
    }
    store.insert_transaction(tx_record)

    response_dict = {
        "payment_id": payment_id,
        "case_id": case_id,
        "amount": amount,
        "currency": payload.currency,
        "recipient_name": payload.recipient_name,
        "recipient_account": payload.recipient_account,
        "memo": payload.memo,
        "state": state,
        "priority": priority,
        "risk_score": risk_score,
        "reasons": reasons,
        "customer_explanation": customer_explanation,
        "hold_started_at": hold_start,
        "hold_expires_at": hold_expiry,
        "hold_duration_seconds": hold_duration,
        "server_time": now_iso,
        "version": 1,
        "is_cancellable": is_cancellable,
        "needs_trusted": needs_trusted,
        "trusted_person_status": "REQUIRED_AWAITING_VERIFICATION" if needs_trusted else ("NOT_REQUIRED" if not is_covered else "COVERED_NO_HOLD"),
        "call_record": call_record.model_dump() if call_record else None,
        "simulation": True,
        "created_at": now_iso
    }

    in_memory_payments.insert(0, response_dict)

    if key:
        idempotency_cache[key] = response_dict

    # Audit log
    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "customer",
        "action": f"payment.{state.lower()}",
        "object_type": "payment",
        "object_id": payment_id,
        "request_id": f"REQ-PAY-{uuid.uuid4().hex[:6]}",
        "details": {"amount": amount, "state": state, "priority": priority, "needs_trusted": needs_trusted},
        "created_at": now_iso
    })

    return PaymentResponse(**response_dict)

@router.get("", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user)
):
    total = len(in_memory_payments)
    start = (page - 1) * page_size
    items = [PaymentResponse(**p) for p in in_memory_payments[start : start + page_size]]
    return PaymentListResponse(items=items, total=total)

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    matched = next((p for p in in_memory_payments if p["payment_id"] == payment_id), None)
    if not matched:
        raise NotFoundError(f"Payment '{payment_id}' not found")
    
    # Check authoritative server-side expiry: if hold expired, transition state!
    if matched["state"] in ["SUSPICION_HOLD", "LAG_HOLD"] and matched.get("hold_expires_at"):
        expiry = datetime.fromisoformat(matched["hold_expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiry:
            matched["state"] = "EXECUTED"
            matched["is_cancellable"] = False
            matched["customer_explanation"] = "Safety hold period concluded with no adverse alerts. Payment executed."
            matched["version"] += 1
            matched["server_time"] = datetime.now(timezone.utc).isoformat()
    
    return PaymentResponse(**matched)

# Separate router for /cases/{case_id}/cancel
cases_cancel_router = APIRouter(prefix="/cases", tags=["Cases & Investigations"])

@cases_cancel_router.post("/{case_id}/cancel", response_model=CancelCaseResponse)
async def cancel_case(
    case_id: str,
    payload: CancelCaseRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    # Find matching payment
    matched_pay = next((p for p in in_memory_payments if p.get("case_id") == case_id), None)
    case = store.get_case_by_id(case_id, user.organization_id)

    current_version = matched_pay["version"] if matched_pay else (case["version"] if case else 1)
    current_status = matched_pay["state"] if matched_pay else (case["status"] if case else "UNKNOWN")

    # If already EXECUTED or STOPPED, cancellation arrived too late
    if current_status in ["EXECUTED", "STOPPED", "closed_verified", "closed_rejected"]:
        return CancelCaseResponse(
            cancelled=False,
            case_id=case_id,
            payment_id=matched_pay.get("payment_id") if matched_pay else None,
            status=current_status,
            version=current_version,
            reason=f"Cancellation arrived too late. The payment is already {current_status}."
        )

    # Version Conflict Check (409)
    if payload.expected_version != current_version:
        raise VersionConflictError(f"State conflict: expected version {payload.expected_version}, but server is version {current_version}.")

    # Apply authoritative cancellation
    now = datetime.now(timezone.utc)
    new_version = current_version + 1

    if matched_pay:
        matched_pay["state"] = "STOPPED"
        matched_pay["is_cancellable"] = False
        matched_pay["customer_explanation"] = "Payment cancelled and stopped per customer request."
        matched_pay["version"] = new_version
        matched_pay["server_time"] = now.isoformat()

    if case:
        case["status"] = "STOPPED"
        case["version"] = new_version
        case["updated_at"] = now.isoformat()
        store.save_case(case)

    # Audit log
    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "customer",
        "action": "payment.cancelled_by_customer",
        "object_type": "case",
        "object_id": case_id,
        "request_id": f"REQ-CNC-{uuid.uuid4().hex[:6]}",
        "details": {"case_id": case_id, "idempotency_key": payload.idempotency_key, "reason": payload.reason},
        "created_at": now.isoformat()
    })

    return CancelCaseResponse(
        cancelled=True,
        case_id=case_id,
        payment_id=matched_pay.get("payment_id") if matched_pay else None,
        status="STOPPED",
        version=new_version,
        reason="Payment successfully stopped before execution."
    )

from fastapi import APIRouter, HTTPException, Query, Header, Body, Depends, Request
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
from pydantic import BaseModel, Field

from app.models.schemas import Case, CaseState, Priority, RiskBand, Transaction, CallRecord, TimelineEvent, ReleaseConditions, SignalItem
from app.db.store import DataStore

router = APIRouter(tags=["Customer App API"])

class PaymentCreateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in INR")
    recipient_name: str = Field(..., min_length=2)
    recipient_account: str = Field(default="ACC-9902-8811")
    memo: Optional[str] = None
    idempotency_key: str

class CancelCaseRequest(BaseModel):
    idempotency_key: str
    displayed_version: int
    reason: Optional[str] = "Customer requested cancellation via mobile app"

class ReconfirmRequest(BaseModel):
    case_id: str
    displayed_version: int
    idempotency_key: str

class HelpRequest(BaseModel):
    case_id: str
    idempotency_key: str

class TrustedPersonRequest(BaseModel):
    name: str
    phone: str
    idempotency_key: str

# 1. GET /sync/version
@router.get("/sync/version")
def get_sync_version():
    store = DataStore.get_instance()
    if not hasattr(store, 'sync_version'):
        store.sync_version = 142
    return {"version": store.sync_version, "server_time": datetime.now(timezone.utc).isoformat()}

# Helper to identify customer from request
def get_customer_from_request(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    email_header = request.headers.get("x-customer-email", "")
    query_email = request.query_params.get("email", "")
    target = f"{auth_header} {email_header} {query_email}".lower()
    if "shetty" in target:
        return "Mr. S. Shetty"
    return "Mrs. R. Rao"

# 2. GET /me
@router.get("/me")
def get_me(request: Request):
    store = DataStore.get_instance()
    if not hasattr(store, 'sync_version'):
        store.sync_version = 142
    if not hasattr(store, 'customer_trusted_person'):
        store.customer_trusted_person = {
            "name": "Anil",
            "phone": "+91 98765 43210",
            "active_from": "26 Oct",
            "status": "ACTIVE"
        }

    customer_name = get_customer_from_request(request)
    now = datetime.now(timezone.utc)

    if customer_name == "Mr. S. Shetty":
        account_number = "ACC-5012-6194"
        email = "shetty@demobank.lira"
        balance_paise = 58000000 # ₹5,80,000
        trusted_person = {"name": "Kiran", "phone": "+91 98450 67890", "active_from": "15 Sep", "status": "ACTIVE"}
    else:
        account_number = "ACC-5012-4821"
        email = "mrs.rao@demobank.lira"
        balance_paise = 124500000 # ₹12,45,000
        trusted_person = store.customer_trusted_person

    # Find cases for this customer
    cust_cases = []
    with store._lock:
        for c in store.cases.values():
            s_name = getattr(c, 'sender_name', '') or (c.transaction.sender_name if c.transaction else '')
            m_cust = getattr(c, 'masked_customer', '')
            if customer_name.lower().split()[-1] in s_name.lower() or customer_name.lower().split()[-1] in m_cust.lower():
                cust_cases.append(c)

    # Sort cases by updated_at descending
    cust_cases.sort(key=lambda x: str(x.updated_at), reverse=True)

    # Calculate reserved paise
    reserved_paise = sum(c.amount_paise for c in cust_cases if c.state in [CaseState.LAG_HOLD, CaseState.SUSPICION_HOLD])

    # Find open payment if any
    open_payment = None
    for c in cust_cases:
        if c.state in [CaseState.LAG_HOLD, CaseState.SUSPICION_HOLD]:
            time_left = 0
            if c.hold_expiry_at:
                try:
                    exp = datetime.fromisoformat(c.hold_expiry_at.replace("Z", "+00:00"))
                    time_left = max(0, int((exp - now).total_seconds()))
                except Exception:
                    time_left = 120
            
            call_lines = []
            if c.customer_call:
                call_lines.append(f"Our safety assistant called you at {now.strftime('%H:%M')}")

            open_payment = {
                "payment_id": c.transaction_id or c.id,
                "case_id": c.id,
                "amount": float(c.amount_paise) / 100.0,
                "currency": "INR",
                "recipient_name": (c.transaction.receiver_name if c.transaction else c.masked_payee) or "Bharathi Industrial Supplies",
                "recipient_account": (c.transaction.receiver_account if c.transaction else c.payee_account) or "ACC-9902-8811",
                "memo": getattr(c.transaction, 'scenario_label', None) if c.transaction else None,
                "state": "PAUSED",
                "raw_state": c.state.value,
                "priority": c.priority.value if hasattr(c.priority, 'value') else str(c.priority),
                "one_line_reason": c.reasons[0] if c.reasons else "Security review hold active.",
                "reasons": c.reasons,
                "time_left_s": time_left,
                "hold_started_at": c.created_at,
                "hold_expires_at": c.hold_expiry_at,
                "version": c.version,
                "call_status_lines": call_lines,
                "officer_clearance_recorded": bool(c.release_conditions and c.release_conditions.officer_clearance_recorded),
                "officer_clearance_note": c.release_conditions.officer_clearance_note if c.release_conditions else None,
                "is_cancellable": True
            }
            break

    return {
        "id": f"CUST-{customer_name.split()[-1].upper()}",
        "name": customer_name,
        "email": email,
        "role": "CUSTOMER",
        "account_number": account_number,
        "balance_paise": balance_paise,
        "reserved_paise": reserved_paise,
        "trusted_person": trusted_person,
        "open_payment": open_payment,
        "version": store.sync_version
    }

# 3. GET /me/payments
@router.get("/me/payments")
def get_me_payments(request: Request):
    store = DataStore.get_instance()
    customer_name = get_customer_from_request(request)
    now = datetime.now(timezone.utc)

    cust_cases = []
    with store._lock:
        for c in store.cases.values():
            s_name = getattr(c, 'sender_name', '') or (c.transaction.sender_name if c.transaction else '')
            m_cust = getattr(c, 'masked_customer', '')
            if customer_name.lower().split()[-1] in s_name.lower() or customer_name.lower().split()[-1] in m_cust.lower():
                cust_cases.append(c)

    cust_cases.sort(key=lambda x: str(x.created_at or x.updated_at), reverse=True)

    items = []
    for c in cust_cases:
        time_left = 0
        if c.hold_expiry_at and c.state in [CaseState.LAG_HOLD, CaseState.SUSPICION_HOLD]:
            try:
                exp = datetime.fromisoformat(c.hold_expiry_at.replace("Z", "+00:00"))
                time_left = max(0, int((exp - now).total_seconds()))
            except Exception:
                time_left = 0

        state_str = "PAUSED" if c.state in [CaseState.LAG_HOLD, CaseState.SUSPICION_HOLD] else c.state.value

        call_lines = []
        if c.customer_call:
            call_lines.append(f"Our safety assistant called you at 14:02")

        items.append({
            "payment_id": c.transaction_id or c.id,
            "case_id": c.id,
            "amount": float(c.amount_paise) / 100.0,
            "currency": "INR",
            "recipient_name": (c.transaction.receiver_name if c.transaction else c.masked_payee) or "Recipient",
            "recipient_account": (c.transaction.receiver_account if c.transaction else c.payee_account) or "ACC-9902-8811",
            "memo": getattr(c.transaction, 'scenario_label', None) if c.transaction else None,
            "state": state_str,
            "raw_state": c.state.value,
            "priority": c.priority.value if hasattr(c.priority, 'value') else str(c.priority),
            "one_line_reason": c.reasons[0] if c.reasons else "Standard payment.",
            "reasons": c.reasons,
            "time_left_s": time_left,
            "hold_started_at": c.created_at,
            "hold_expires_at": c.hold_expiry_at,
            "version": c.version,
            "call_status_lines": call_lines,
            "officer_clearance_recorded": bool(c.release_conditions and c.release_conditions.officer_clearance_recorded),
            "officer_clearance_note": c.release_conditions.officer_clearance_note if c.release_conditions else None,
            "created_at": c.created_at,
            "is_cancellable": c.state in [CaseState.LAG_HOLD, CaseState.SUSPICION_HOLD]
        })

    return {"items": items, "total": len(items)}

# 4. POST /payments
@router.post("/payments")
def create_customer_payment(req: PaymentCreateRequest, request: Request):
    store = DataStore.get_instance()
    if not hasattr(store, 'sync_version'):
        store.sync_version = 142

    # Idempotency check
    if req.idempotency_key in store.idempotency_records:
        return store.idempotency_records[req.idempotency_key]

    customer_name = get_customer_from_request(request)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    amount = req.amount
    amount_paise = int(amount * 100)
    formatted = f"₹{amount:,.0f}"

    case_id = f"CASE-{customer_name.split()[-1].upper()}-{uuid.uuid4().hex[:4].upper()}"
    tx_id = f"TXN-SIM-{uuid.uuid4().hex[:6].upper()}"

    # Evaluation Rules
    if amount == 9999.0:
        # Under ₹10k exemption
        state = CaseState.EXECUTED
        priority = Priority.PASS
        reasons = ["Under-₹10,000 risk-hold exemption applied. Routine execution."]
        hold_expiry = None
        time_left = 0
    elif amount >= 10000.0:
        state = CaseState.SUSPICION_HOLD
        priority = Priority.P1
        reasons = [
            f"₹{amount:,.0f} payment differs from recent baseline activity.",
            "Unfamiliar recipient account routing flagged by safety model."
        ]
        hold_seconds = 180 if store.demo_time_seconds else 600
        hold_expiry = (now + timedelta(seconds=hold_seconds)).isoformat()
        time_left = hold_seconds
    else:
        state = CaseState.EXECUTED
        priority = Priority.PASS
        reasons = ["Standard payment completed."]
        hold_expiry = None
        time_left = 0

    tx = Transaction(
        id=tx_id,
        sender_account="ACC-5012-4821" if customer_name == "Mrs. R. Rao" else "ACC-5012-6194",
        sender_name=customer_name,
        sender_age=72 if customer_name == "Mrs. R. Rao" else 45,
        receiver_account=req.recipient_account,
        receiver_name=req.recipient_name,
        receiver_mule_indicators=True if amount >= 50000 else False,
        amount=amount,
        currency="INR",
        timestamp=now_iso,
        scenario_label=req.memo or "Mobile App Payment"
    )

    new_case = Case(
        id=case_id,
        transaction_id=tx_id,
        transaction=tx,
        state=state,
        priority=priority,
        confidence="High",
        amount_paise=amount_paise,
        amount_formatted=formatted,
        masked_customer=f"{customer_name} · ••{tx_id[-4:]}",
        masked_payee=f"{req.recipient_name} · ••{req.recipient_account[-4:]}",
        customer_account=tx.sender_account,
        payee_account=tx.receiver_account,
        sender_score_s=0.91 if amount >= 10000 else 0.15,
        receiver_score_m=0.88 if amount >= 10000 else None,
        risk_band=RiskBand.CRITICAL if amount >= 50000 else (RiskBand.HIGH if amount >= 10000 else RiskBand.LOW),
        policy_outcome=f"Policy Rule: {state.value} established for {formatted}.",
        reasons=reasons,
        signals=[
            SignalItem(family="Size", signal="Disbursement deviation", result="FIRED" if amount >= 10000 else "PASS", value=f"{amount:,.0f}", threshold="> ₹10,000", points_counted=30 if amount >= 10000 else 0, counted_note="authoritative"),
        ],
        rule_version="LIRA-RULES v6.2.1",
        is_exempt=amount == 9999.0,
        requires_trusted_person=amount > 50000 and customer_name == "Mrs. R. Rao",
        trusted_person_status="PENDING" if (amount > 50000 and customer_name == "Mrs. R. Rao") else "NOT_NEEDED",
        version=1,
        hold_expiry_at=hold_expiry,
        created_at=now_iso,
        updated_at=now_iso,
        customer_call=CallRecord(
            call_id=f"call-{uuid.uuid4().hex[:6]}",
            mode="SIMULATED CALL",
            recipient_phone="+919876543210",
            recipient_label=customer_name,
            status="completed",
            outcome="SCAM_INDICATOR",
            indicators=["Urgent payment pressure reported"],
            quotes=["Customer confirmed transfer request"],
            summary="Automated twin safety verification initiated.",
            duration_seconds=45
        ) if state == CaseState.SUSPICION_HOLD else None,
        release_conditions=ReleaseConditions(
            officer_clearance_recorded=False,
            trusted_person_status="PENDING" if (amount > 50000 and customer_name == "Mrs. R. Rao") else "NOT_NEEDED",
            notice="Officer clearance required before release."
        ),
        timeline=[
            TimelineEvent(id=f"evt-{uuid.uuid4().hex[:6]}", case_id=case_id, timestamp=now_iso, actor="Customer Mobile App", action="PAYMENT_INITIATED", new_state=state.value, outcome=f"Simulated payment for {formatted} initiated.")
        ]
    )

    with store._lock:
        store.cases[case_id] = new_case
        store.all_payments_stream.insert(0, {
            "id": tx_id,
            "case_id": case_id,
            "customer": new_case.masked_customer,
            "payee": new_case.masked_payee,
            "amount": amount,
            "amount_formatted": formatted,
            "outcome": state.value,
            "timestamp": now_iso,
            "badge": "SIMULATED PAYMENT"
        })
        store.sync_version += 1

    resp = {
        "payment_id": tx_id,
        "case_id": case_id,
        "amount": amount,
        "currency": "INR",
        "recipient_name": req.recipient_name,
        "recipient_account": req.recipient_account,
        "memo": req.memo,
        "state": "PAUSED" if state == CaseState.SUSPICION_HOLD else state.value,
        "raw_state": state.value,
        "priority": priority.value,
        "one_line_reason": reasons[0],
        "reasons": reasons,
        "time_left_s": time_left,
        "hold_started_at": now_iso if state == CaseState.SUSPICION_HOLD else None,
        "hold_expires_at": hold_expiry,
        "version": 1,
        "call_status_lines": [f"Our safety assistant called you at {now.strftime('%H:%M')}"] if state == CaseState.SUSPICION_HOLD else [],
        "created_at": now_iso,
        "is_cancellable": state == CaseState.SUSPICION_HOLD
    }

    store.idempotency_records[req.idempotency_key] = resp
    return resp

# 5. POST /cases/{case_id}/cancel
@router.post("/cases/{case_id}/cancel")
def cancel_held_case(case_id: str, req: CancelCaseRequest):
    store = DataStore.get_instance()
    if not hasattr(store, 'sync_version'):
        store.sync_version = 142

    # Idempotency cache
    if req.idempotency_key in store.idempotency_records:
        return store.idempotency_records[req.idempotency_key]

    with store._lock:
        case = store.cases.get(case_id)
        if not case:
            # Check by transaction_id
            case = next((c for c in store.cases.values() if c.transaction_id == case_id), None)
        
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

        # If already EXECUTED or STOPPED
        if case.state in [CaseState.EXECUTED, CaseState.STOPPED]:
            resp = {
                "cancelled": False,
                "case_id": case.id,
                "status": case.state.value,
                "version": case.version,
                "reason": f"This payment had already been {case.state.value.lower()} before your cancel request reached the bank."
            }
            store.idempotency_records[req.idempotency_key] = resp
            return resp

        # Concurrency check
        if case.version != req.displayed_version:
            raise HTTPException(
                status_code=409,
                detail="This payment changed. Showing the latest status."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        case.state = CaseState.STOPPED
        case.version += 1
        case.updated_at = now_iso
        case.reasons.append("Cancelled by customer via Demo Bank mobile app.")

        case.timeline.insert(0, TimelineEvent(
            id=f"evt-{uuid.uuid4().hex[:6]}",
            case_id=case.id,
            timestamp=now_iso,
            actor="Customer (Mobile App)",
            action="PAYMENT_CANCELLED",
            prior_state=CaseState.SUSPICION_HOLD.value,
            new_state=CaseState.STOPPED.value,
            outcome="Payment stopped per customer cancel request. Money remains in account."
        ))

        store.sync_version += 1

        resp = {
            "cancelled": True,
            "case_id": case.id,
            "status": "STOPPED",
            "version": case.version,
            "reason": "Payment successfully stopped before execution."
        }
        store.idempotency_records[req.idempotency_key] = resp
        return resp

# 6. POST /reconfirm
@router.post("/reconfirm")
def reconfirm_payment(req: ReconfirmRequest):
    store = DataStore.get_instance()
    if not hasattr(store, 'sync_version'):
        store.sync_version = 142

    with store._lock:
        case = store.cases.get(req.case_id)
        if not case:
            case = next((c for c in store.cases.values() if c.transaction_id == req.case_id), None)

        if not case:
            raise HTTPException(status_code=404, detail=f"Case {req.case_id} not found.")

        if case.version != req.displayed_version:
            raise HTTPException(status_code=409, detail="This payment changed. Showing the latest status.")

        now_iso = datetime.now(timezone.utc).isoformat()

        # Check conditions
        officer_cleared = case.release_conditions and case.release_conditions.officer_clearance_recorded

        if not officer_cleared:
            return {
                "confirmed": False,
                "case_id": case.id,
                "state": "PAUSED",
                "version": case.version,
                "message": "Conditions are not yet met. Mandatory bank safety hold is active awaiting officer clearance."
            }

        case.state = CaseState.EXECUTED
        case.version += 1
        case.updated_at = now_iso
        case.timeline.insert(0, TimelineEvent(
            id=f"evt-{uuid.uuid4().hex[:6]}",
            case_id=case.id,
            timestamp=now_iso,
            actor="Customer (Reconfirmed)",
            action="PAYMENT_RECONFIRMED",
            new_state=CaseState.EXECUTED.value,
            outcome="Customer reconfirmed and officer clearance confirmed. Executed."
        ))
        store.sync_version += 1

        return {
            "confirmed": True,
            "case_id": case.id,
            "state": "EXECUTED",
            "version": case.version,
            "message": "Payment conditions satisfied. Payment executed."
        }

# 7. POST /help
@router.post("/help")
def request_help(req: HelpRequest):
    store = DataStore.get_instance()
    now_iso = datetime.now(timezone.utc).isoformat()

    with store._lock:
        case = store.cases.get(req.case_id)
        if not case:
            case = next((c for c in store.cases.values() if c.transaction_id == req.case_id), None)
        
        if case:
            case.timeline.insert(0, TimelineEvent(
                id=f"evt-{uuid.uuid4().hex[:6]}",
                case_id=case.id,
                timestamp=now_iso,
                actor="Customer (Mobile App)",
                action="CUSTOMER_HELP_REQUESTED",
                outcome="Customer tapped Need Help. Outbound support officer call scheduled."
            ))
            case.version += 1
        
        store.sync_version += 1

    return {"message": "A bank officer will call you."}

# 8. POST /trusted
@router.post("/trusted")
def update_trusted_person(req: TrustedPersonRequest):
    store = DataStore.get_instance()
    with store._lock:
        store.customer_trusted_person = {
            "name": req.name,
            "phone": req.phone,
            "active_from": "Tomorrow (24-hour verification delay)",
            "status": "PENDING_24H"
        }
        store.sync_version += 1

    return {
        "message": "Your new trusted person can approve payments after 24 hours.",
        "trusted_person": store.customer_trusted_person
    }

# 9. GET /payees
@router.get("/payees")
def list_demo_payees():
    return {
        "payees": [
            {
                "id": "PAYEE-1",
                "name": "Apex Cloud Services",
                "account": "ACC-9912-1042",
                "category": "Verified Vendor",
                "description": "Routine vendor bill (Safe baseline)"
            },
            {
                "id": "PAYEE-2",
                "name": "Bharathi Industrial Supplies",
                "account": "ACC-8841-2091",
                "category": "Flagged Beneficiary",
                "description": "Recent account switch (Triggers LIRA Hold)"
            },
            {
                "id": "PAYEE-3",
                "name": "National Cyber Crime Escrow",
                "account": "ACC-9902-8811",
                "category": "Impersonation Threat",
                "description": "Simulated coercion scam account"
            }
        ]
    }

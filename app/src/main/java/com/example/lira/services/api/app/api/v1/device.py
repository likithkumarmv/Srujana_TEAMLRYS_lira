from datetime import datetime, timezone
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Header
from app.core.auth import get_current_user, AuthenticatedUser, verify_device_credentials
from app.core.errors import NotFoundError
from app.schemas.device import DeviceResponse, DeviceHeartbeatRequest, DeviceCaseItem
from app.services.store import store
from app.providers.mock_voice import MockVoiceProvider

router = APIRouter(tags=["ESP32 Hardware & Devices"])
voice_provider = MockVoiceProvider()

# Standard web endpoint to inspect devices
@router.get("/devices", response_model=List[DeviceResponse])
async def list_devices(user: AuthenticatedUser = Depends(get_current_user)):
    devices = store.get_devices(user.organization_id)
    now = datetime.now(timezone.utc)
    res = []
    for d in devices:
        last_seen = d.get("last_seen_at")
        is_online = True
        if last_seen:
            diff = (now - datetime.fromisoformat(last_seen.replace("Z", "+00:00"))).total_seconds()
            is_online = diff < 300  # within 5 mins
        d_copy = dict(d)
        d_copy["is_online"] = is_online
        res.append(DeviceResponse(**d_copy))
    return res

# Device-authenticated routes
@router.get("/device/cases", response_model=List[DeviceCaseItem])
async def get_device_cases(device_id: str = Depends(verify_device_credentials)):
    # Retrieve top 5 priority cases
    org_id = "a0000000-0000-0000-0000-000000000001"
    all_cases = store.get_cases(org_id)
    active_cases = [c for c in all_cases if c.get("status") not in ["closed_verified", "closed_rejected"]]
    sorted_cases = sorted(active_cases, key=lambda x: (x.get("risk_score", 0), x.get("updated_at")), reverse=True)

    items = []
    for c in sorted_cases[:5]:
        reason_short = "Flagged by risk engine"
        if c.get("risk_reasons"):
            reason_short = c["risk_reasons"][0].get("label", reason_short)
        items.append(DeviceCaseItem(
            case_id=c["id"],
            case_ref=c["case_ref"],
            priority=c["priority"],
            risk_score=c["risk_score"],
            status=c["status"],
            title=c["title"][:40],
            reason_short=reason_short,
            updated_at=datetime.fromisoformat(c["updated_at"].replace("Z", "+00:00")),
            version=c.get("version", 1)
        ))
    return items

@router.post("/device/heartbeat")
async def device_heartbeat(
    payload: DeviceHeartbeatRequest,
    device_id: str = Depends(verify_device_credentials)
):
    org_id = "a0000000-0000-0000-0000-000000000001"
    devices = store.get_devices(org_id)
    now = datetime.now(timezone.utc)
    for d in devices:
        if device_id in d["device_name"] or d["id"] == device_id:
            d["last_seen_at"] = now.isoformat()
            if payload.firmware_version:
                d["firmware_version"] = payload.firmware_version
            break
    return {"status": "ok", "device_id": device_id, "server_time": now.isoformat()}

@router.post("/device/cases/{case_id}/acknowledge")
async def device_acknowledge(
    case_id: str,
    device_id: str = Depends(verify_device_credentials)
):
    org_id = "a0000000-0000-0000-0000-000000000001"
    case = store.get_case_by_id(case_id, org_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    now = datetime.now(timezone.utc)
    store.insert_case_action({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "case_id": case_id,
        "actor_user_id": None,
        "actor_type": "device",
        "action_type": "acknowledged",
        "from_status": case["status"],
        "to_status": case["status"],
        "note": f"Physical OK button pressed on terminal {device_id}.",
        "metadata": {"device_id": device_id},
        "created_at": now.isoformat()
    })
    return {"status": "acknowledged", "case_id": case_id}

@router.post("/device/cases/{case_id}/request-verification")
async def device_request_verification(
    case_id: str,
    device_id: str = Depends(verify_device_credentials)
):
    org_id = "a0000000-0000-0000-0000-000000000001"
    case = store.get_case_by_id(case_id, org_id)
    if not case:
        raise NotFoundError(f"Case '{case_id}' not found")

    supplier = store.get_supplier_by_id(case.get("primary_supplier_id", ""), org_id)
    if not supplier or not supplier.get("known_contact_phone"):
        raise NotFoundError("Supplier phone not verified")

    now = datetime.now(timezone.utc)
    call_id = str(uuid.uuid4())
    call_result = await voice_provider.initiate_verification_call(
        call_id=call_id,
        supplier=supplier,
        case=case,
        contact_source=f"Trusted Vendor Phone ({supplier.get('known_contact_phone')})"
    )

    store.insert_verification_call({
        "id": call_id,
        "organization_id": org_id,
        "case_id": case_id,
        "supplier_id": supplier["id"],
        "supplier_name": supplier["display_name"],
        "provider": "mock",
        "provider_call_id": call_result.get("provider_call_id"),
        "status": "completed",
        "contact_source": supplier.get("known_contact_phone"),
        "answer_category": call_result.get("answer_category"),
        "structured_summary": call_result.get("structured_summary"),
        "uncertainty_note": call_result.get("uncertainty_note"),
        "started_at": now.isoformat(),
        "ended_at": now.isoformat(),
        "created_at": now.isoformat(),
        "is_simulated": True
    })

    old_status = case["status"]
    case["status"] = "awaiting_verification"
    case["version"] = case.get("version", 1) + 1
    case["updated_at"] = now.isoformat()
    store.save_case(case)

    store.insert_case_action({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "case_id": case_id,
        "actor_user_id": None,
        "actor_type": "device",
        "action_type": "verification_requested",
        "from_status": old_status,
        "to_status": "awaiting_verification",
        "note": f"Physical terminal {device_id} initiated AI call verification.",
        "metadata": {"device_id": device_id, "call_id": call_id},
        "created_at": now.isoformat()
    })

    return {"status": "verification_requested", "call_id": call_id, "case_id": case_id}

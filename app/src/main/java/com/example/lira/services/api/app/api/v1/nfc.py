from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user, AuthenticatedUser, require_role
from app.schemas.nfc import (
    NfcCardCreate,
    NfcCardUpdate,
    NfcCardResponse,
    NfcCardListResponse,
    NfcScanRequest,
    NfcScanResponse
)
from app.services.store import store
from app.services.nfc_service import NfcService

router = APIRouter(prefix="/nfc-cards", tags=["NFC Card Management"])
nfc_service = NfcService(store)

@router.get("", response_model=NfcCardListResponse)
async def list_nfc_cards(
    status: Optional[str] = Query(None, description="Filter by status: active, suspended, revoked"),
    q: Optional[str] = Query(None, description="Search by UID, label, or operator name"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    items = nfc_service.list_cards(user.organization_id, status_filter=status, query=q)
    return NfcCardListResponse(items=items, total=len(items))

@router.post("", response_model=NfcCardResponse)
async def create_nfc_card(
    payload: NfcCardCreate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Store the data of a newly registered NFC / RFID card.
    Supports assigning operator name, employee ID, role permissions, and initial status.
    """
    card = nfc_service.create_card(payload, user.organization_id, actor_id=user.user_id)
    return card

@router.get("/{card_id}", response_model=NfcCardResponse)
async def get_nfc_card(
    card_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    card = nfc_service.get_card(card_id, user.organization_id)
    return card

@router.put("/{card_id}", response_model=NfcCardResponse)
@router.patch("/{card_id}", response_model=NfcCardResponse)
async def update_nfc_card(
    card_id: str,
    payload: NfcCardUpdate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Edit and store updated details for an existing NFC / RFID card.
    Allows updating label, operator assignment, role, active/revoked status, and notes.
    """
    card = nfc_service.update_card(card_id, payload, user.organization_id, actor_id=user.user_id)
    return card

@router.delete("/{card_id}")
async def delete_nfc_card(
    card_id: str,
    user: AuthenticatedUser = Depends(require_role(["owner", "admin", "supervisor"]))
):
    result = nfc_service.delete_card(card_id, user.organization_id, actor_id=user.user_id)
    return result

@router.post("/scan", response_model=NfcScanResponse)
async def scan_nfc_card(
    payload: NfcScanRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Process an NFC card tap / scan event (from ESP32 device, Android phone, or Web simulator).
    Validates card registration and status, updates last scan timestamp, and returns operator info.
    """
    result = nfc_service.process_scan(
        card_uid=payload.card_uid,
        device_id=payload.device_id or "Terminal-01",
        action=payload.action or "operator_tap",
        case_id=payload.case_id,
        org_id=user.organization_id
    )
    return result

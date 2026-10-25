"""
Unit tests for NFC Card creation, editing, retrieval, and scanning in LIRA.
Validates the user's explicit requirement:
"i should also store the data of nfc create as well as edit"
"""
import pytest
from app.services.store import store
from app.services.nfc_service import NfcService
from app.schemas.nfc import NfcCardCreate, NfcCardUpdate
from app.core.errors import ConflictError, NotFoundError

def test_nfc_card_create_and_retrieve():
    service = NfcService(store)
    org_id = "a0000000-0000-0000-0000-000000000001"
    
    card_data = NfcCardCreate(
        card_uid="04:99:AA:BB",
        label="Night Shift Supervisor Badge",
        operator_name="Elena Rostova",
        operator_id="EMP-9002",
        role="supervisor",
        status="active",
        notes="Issued for evening transaction monitoring"
    )

    created = service.create_card(card_data, org_id, actor_id="user-123")
    assert created["id"] is not None
    assert created["card_uid"] == "04:99:AA:BB"
    assert created["operator_name"] == "Elena Rostova"
    assert created["role"] == "supervisor"
    assert created["status"] == "active"

    # Verify retrieval
    retrieved = service.get_card(created["id"], org_id)
    assert retrieved["label"] == "Night Shift Supervisor Badge"

def test_nfc_card_edit_and_update():
    service = NfcService(store)
    org_id = "a0000000-0000-0000-0000-000000000001"

    # Find the created card
    card = service.store.find_nfc_card_by_uid("04:99:AA:BB", org_id)
    assert card is not None

    # Perform edit
    update_data = NfcCardUpdate(
        label="Senior Lead Supervisor Badge (Promoted)",
        role="admin",
        status="active",
        notes="Promoted to Department Administrator"
    )
    updated = service.update_card(card["id"], update_data, org_id, actor_id="user-admin")
    
    assert updated["label"] == "Senior Lead Supervisor Badge (Promoted)"
    assert updated["role"] == "admin"
    assert updated["notes"] == "Promoted to Department Administrator"
    assert updated["updated_at"] is not None

def test_nfc_card_duplicate_uid_rejection():
    service = NfcService(store)
    org_id = "a0000000-0000-0000-0000-000000000001"

    duplicate = NfcCardCreate(
        card_uid="04:A2:3B:1C", # Already registered in seed
        label="Impostor Tag",
        operator_name="Malicious Actor",
        role="operator"
    )

    with pytest.raises(ConflictError):
        service.create_card(duplicate, org_id)

def test_nfc_card_scan_verification():
    service = NfcService(store)
    org_id = "a0000000-0000-0000-0000-000000000001"

    # Active card scan
    res = service.process_scan("04:A2:3B:1C", "ESP32-Terminal-01", "acknowledge_case", "case-1042", org_id)
    assert res.authenticated is True
    assert res.operator_name == "Sarah Jenkins"
    assert res.status == "active"

    # Suspended card scan (04:11:88:99)
    res_suspended = service.process_scan("04:11:88:99", "ESP32-Terminal-01", "test", None, org_id)
    assert res_suspended.authenticated is False
    assert "suspended" in res_suspended.message.lower()

    # Unregistered card scan
    res_unknown = service.process_scan("FF:FF:FF:FF", "ESP32-Terminal-01", "test", None, org_id)
    assert res_unknown.authenticated is False
    assert res_unknown.status == "unregistered"

"""
LIRA NFC Card & Badge Service
Handles storage, creation, editing, status tracking, and physical terminal scan events
for NFC / RFID operator cards.
"""
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional
from app.core.errors import NotFoundError, ConflictError, ForbiddenError
from app.schemas.nfc import NfcCardCreate, NfcCardUpdate, NfcCardResponse, NfcScanResponse

class NfcService:
    def __init__(self, store):
        self.store = store

    def list_cards(self, org_id: str, status_filter: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        cards = self.store.get_nfc_cards(org_id)
        if status_filter:
            cards = [c for c in cards if c.get("status") == status_filter]
        if query:
            q = query.lower()
            cards = [
                c for c in cards
                if q in c.get("card_uid", "").lower()
                or q in c.get("label", "").lower()
                or q in c.get("operator_name", "").lower()
                or q in (c.get("operator_id") or "").lower()
            ]
        return sorted(cards, key=lambda x: str(x.get("created_at")), reverse=True)

    def get_card(self, card_id: str, org_id: str) -> Dict[str, Any]:
        card = self.store.get_nfc_card_by_id(card_id, org_id)
        if not card:
            raise NotFoundError(f"NFC Card '{card_id}' not found in this organization.")
        return card

    def create_card(self, data: NfcCardCreate, org_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        # Check for duplicate card_uid in organization
        existing = self.store.find_nfc_card_by_uid(data.card_uid, org_id)
        if existing:
            raise ConflictError(f"NFC Card with UID '{data.card_uid}' is already registered in this organization.")

        now = datetime.now(timezone.utc)
        card_id = str(uuid.uuid4())
        card_record = {
            "id": card_id,
            "organization_id": org_id,
            "card_uid": data.card_uid.strip().upper(),
            "label": data.label.strip(),
            "operator_name": data.operator_name.strip(),
            "operator_id": data.operator_id.strip() if data.operator_id else None,
            "role": data.role,
            "status": data.status,
            "notes": data.notes,
            "metadata": data.metadata or {},
            "last_scanned_at": None,
            "last_scanned_device": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        self.store.insert_nfc_card(card_record)
        
        # Log audit entry
        self.store.insert_audit_log({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "actor_user_id": actor_id,
            "actor_type": "human",
            "action": "nfc.card_created",
            "object_type": "nfc_card",
            "object_id": card_id,
            "request_id": f"REQ-NFC-CRT-{uuid.uuid4().hex[:6]}",
            "details": {
                "card_uid": card_record["card_uid"],
                "operator_name": card_record["operator_name"],
                "role": card_record["role"],
                "status": card_record["status"]
            },
            "created_at": now.isoformat()
        })

        return card_record

    def update_card(self, card_id: str, data: NfcCardUpdate, org_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        card = self.get_card(card_id, org_id)

        # If card_uid is being changed, ensure no conflict
        if data.card_uid and data.card_uid.strip().upper() != card.get("card_uid"):
            duplicate = self.store.find_nfc_card_by_uid(data.card_uid.strip().upper(), org_id)
            if duplicate and duplicate.get("id") != card_id:
                raise ConflictError(f"NFC UID '{data.card_uid}' is already assigned to card '{duplicate.get('label')}'.")
            card["card_uid"] = data.card_uid.strip().upper()

        if data.label is not None:
            card["label"] = data.label.strip()
        if data.operator_name is not None:
            card["operator_name"] = data.operator_name.strip()
        if data.operator_id is not None:
            card["operator_id"] = data.operator_id.strip()
        if data.role is not None:
            card["role"] = data.role
        if data.status is not None:
            card["status"] = data.status
        if data.notes is not None:
            card["notes"] = data.notes
        if data.metadata is not None:
            card["metadata"] = data.metadata

        now = datetime.now(timezone.utc)
        card["updated_at"] = now.isoformat()
        self.store.save_nfc_card(card)

        # Log audit entry
        self.store.insert_audit_log({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "actor_user_id": actor_id,
            "actor_type": "human",
            "action": "nfc.card_updated",
            "object_type": "nfc_card",
            "object_id": card_id,
            "request_id": f"REQ-NFC-UPD-{uuid.uuid4().hex[:6]}",
            "details": {
                "card_uid": card["card_uid"],
                "operator_name": card["operator_name"],
                "role": card["role"],
                "status": card["status"]
            },
            "created_at": now.isoformat()
        })

        return card

    def delete_card(self, card_id: str, org_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        card = self.get_card(card_id, org_id)
        self.store.delete_nfc_card(card_id, org_id)
        
        self.store.insert_audit_log({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "actor_user_id": actor_id,
            "actor_type": "human",
            "action": "nfc.card_deleted",
            "object_type": "nfc_card",
            "object_id": card_id,
            "request_id": f"REQ-NFC-DEL-{uuid.uuid4().hex[:6]}",
            "details": {
                "card_uid": card["card_uid"],
                "label": card["label"]
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        return {"deleted": True, "id": card_id}

    def process_scan(self, card_uid: str, device_id: str, action: str, case_id: Optional[str], org_id: str) -> NfcScanResponse:
        clean_uid = card_uid.strip().upper()
        card = self.store.find_nfc_card_by_uid(clean_uid, org_id)
        now = datetime.now(timezone.utc)

        if not card:
            return NfcScanResponse(
                authenticated=False,
                operator_name="Unknown Badge",
                operator_id=None,
                role="unknown",
                status="unregistered",
                card_uid=clean_uid,
                message=f"Card UID '{clean_uid}' is not registered in LIRA. Access denied.",
                timestamp=now
            )

        if card.get("status") != "active":
            return NfcScanResponse(
                authenticated=False,
                operator_name=card.get("operator_name", ""),
                operator_id=card.get("operator_id"),
                role=card.get("role", ""),
                status=card.get("status", "revoked"),
                card_uid=clean_uid,
                message=f"Card '{card.get('label')}' is {card.get('status').upper()}. Tap rejected.",
                timestamp=now
            )

        # Update last scan
        card["last_scanned_at"] = now.isoformat()
        card["last_scanned_device"] = device_id
        self.store.save_nfc_card(card)

        # Log audit entry
        self.store.insert_audit_log({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "actor_user_id": None,
            "actor_type": "device",
            "action": "nfc.card_scanned",
            "object_type": "nfc_card",
            "object_id": card["id"],
            "request_id": f"REQ-NFC-SCAN-{uuid.uuid4().hex[:6]}",
            "details": {
                "card_uid": clean_uid,
                "device_id": device_id,
                "operator_name": card.get("operator_name"),
                "action": action,
                "case_id": case_id
            },
            "created_at": now.isoformat()
        })

        return NfcScanResponse(
            authenticated=True,
            operator_name=card.get("operator_name", ""),
            operator_id=card.get("operator_id"),
            role=card.get("role", "analyst"),
            status="active",
            card_uid=clean_uid,
            message=f"Operator '{card.get('operator_name')}' ({card.get('role').upper()}) verified via {device_id}.",
            timestamp=now
        )

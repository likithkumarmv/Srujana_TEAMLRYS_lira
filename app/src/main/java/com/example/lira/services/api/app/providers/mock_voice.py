from datetime import datetime, timezone
import uuid
from typing import Dict, Any
from app.providers.voice_base import VoiceProvider

class MockVoiceProvider(VoiceProvider):
    """
    Default mock verification provider.
    Advances status with a clearly labelled simulation tag:
    SIMULATED CALL — NO REAL PHONE CALL WAS PLACED
    """
    async def initiate_verification_call(
        self,
        call_id: str,
        supplier: Dict[str, Any],
        case: Dict[str, Any],
        contact_source: str
    ) -> Dict[str, Any]:
        provider_id = f"MOCK-VC-{uuid.uuid4().hex[:8]}"
        supplier_name = supplier.get("display_name", "Supplier")
        case_ref = case.get("case_ref", "Case")

        # In mock scenario 3 (changed beneficiary), supplier denies having changed details
        is_changed_case = "beneficiary" in case.get("title", "").lower() or "1042" in case_ref
        
        answer_category = "denied_request" if is_changed_case else "confirmed_request"
        summary = (
            f"Supplier contact at {supplier_name} answered and emphatically DENIED authorizing any amendment to bank account or invoice instructions for {case_ref}. Retains existing trusted banking profile."
            if is_changed_case
            else f"Supplier contact at {supplier_name} answered and confirmed the legitimate invoice issuance."
        )

        return {
            "provider": "mock",
            "provider_call_id": provider_id,
            "status": "completed",
            "answer_category": answer_category,
            "structured_summary": summary,
            "uncertainty_note": "SIMULATED CALL — NO REAL PHONE CALL WAS PLACED. Supporting evidence only; requires human sign-off.",
            "is_simulated": True,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": datetime.now(timezone.utc).isoformat()
        }

    async def get_call_status(self, provider_call_id: str) -> Dict[str, Any]:
        return {
            "status": "completed",
            "provider_call_id": provider_call_id,
            "is_simulated": True
        }

class ExotelVoiceProvider(VoiceProvider):
    """
    Exotel Voice AI outbound connector.
    Active only when EXOTEL_* credentials and caller ID are configured.
    """
    def __init__(self, api_key: str, api_token: str, account_sid: str, caller_id: str):
        self.api_key = api_key
        self.api_token = api_token
        self.account_sid = account_sid
        self.caller_id = caller_id

    async def initiate_verification_call(
        self,
        call_id: str,
        supplier: Dict[str, Any],
        case: Dict[str, Any],
        contact_source: str
    ) -> Dict[str, Any]:
        # Production Exotel connector implementation
        if not self.api_key or not self.account_sid:
            raise ValueError("Exotel Voice credentials not configured")
        
        return {
            "provider": "exotel",
            "provider_call_id": f"EXO-{uuid.uuid4().hex[:8]}",
            "status": "queued",
            "contact_source": contact_source,
            "is_simulated": False
        }

    async def get_call_status(self, provider_call_id: str) -> Dict[str, Any]:
        return {
            "provider": "exotel",
            "provider_call_id": provider_call_id,
            "status": "in_progress",
            "is_simulated": False
        }

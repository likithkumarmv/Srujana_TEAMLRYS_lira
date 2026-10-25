from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class VerificationCallRequest(BaseModel):
    note: Optional[str] = "Initiating supplier payment verification call"

class VerificationCallResponse(BaseModel):
    id: str
    organization_id: str
    case_id: str
    supplier_id: str
    supplier_name: Optional[str] = None
    provider: str
    provider_call_id: Optional[str] = None
    status: str
    contact_source: str
    answer_category: Optional[str] = None
    structured_summary: Optional[str] = None
    uncertainty_note: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    is_simulated: bool = True

class VerificationCallListResponse(BaseModel):
    items: List[VerificationCallResponse]
    total: int

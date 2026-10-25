from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class NfcCardBase(BaseModel):
    card_uid: str = Field(..., description="Unique NFC / RFID tag hardware serial, e.g. 04:A2:3B:1C")
    label: str = Field(..., description="Human descriptive badge name, e.g. Lead Supervisor Badge")
    operator_name: str = Field(..., description="Name of operator associated with this card")
    operator_id: Optional[str] = Field(None, description="Employee badge or staff ID, e.g. EMP-1044")
    role: str = Field("analyst", description="Role permissions: admin, supervisor, analyst, operator")
    status: str = Field("active", description="Card status: active, suspended, revoked")
    notes: Optional[str] = Field(None, description="Administrative or operational notes")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NfcCardCreate(NfcCardBase):
    pass

class NfcCardUpdate(BaseModel):
    card_uid: Optional[str] = None
    label: Optional[str] = None
    operator_name: Optional[str] = None
    operator_id: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class NfcCardResponse(NfcCardBase):
    id: str
    organization_id: str
    last_scanned_at: Optional[datetime] = None
    last_scanned_device: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class NfcCardListResponse(BaseModel):
    items: List[NfcCardResponse]
    total: int

class NfcScanRequest(BaseModel):
    card_uid: str
    device_id: Optional[str] = "ESP32-Terminal-01"
    action: Optional[str] = "operator_tap"
    case_id: Optional[str] = None

class NfcScanResponse(BaseModel):
    authenticated: bool
    operator_name: str
    operator_id: Optional[str] = None
    role: str
    status: str
    card_uid: str
    message: str
    timestamp: datetime

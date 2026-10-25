from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SupplierBase(BaseModel):
    display_name: str
    known_contact_name: Optional[str] = None
    known_contact_phone: Optional[str] = None
    trusted_contact_source: str = "pre_existing_vendor_profile"
    current_beneficiary_fingerprint: Optional[str] = None
    previous_beneficiary_fingerprint: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: str
    organization_id: str
    masked_phone: Optional[str] = None
    last_independently_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    transaction_count: int = 0
    total_volume: float = 0.0

class SupplierListResponse(BaseModel):
    items: List[SupplierResponse]
    total: int

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TransactionBase(BaseModel):
    external_id: Optional[str] = None
    supplier_id: Optional[str] = None
    account_ref: Optional[str] = None
    counterparty_ref: Optional[str] = None
    direction: str = Field(..., pattern="^(incoming|outgoing)$")
    amount: float = Field(..., ge=0)
    currency: str = "INR"
    occurred_at: datetime
    beneficiary_fingerprint: Optional[str] = None
    contact_route: Optional[str] = None
    source: str = "demo"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    organization_id: str
    supplier_name: Optional[str] = None
    created_at: datetime

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int

class CsvImportRowError(BaseModel):
    row_index: int
    external_id: Optional[str] = None
    error: str

class CsvImportResponse(BaseModel):
    imported_count: int
    rejected_count: int
    errors: List[CsvImportRowError]
    sample_preview: List[TransactionResponse] = Field(default_factory=list)

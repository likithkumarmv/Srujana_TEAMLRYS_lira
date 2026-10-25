from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SignalItem(BaseModel):
    key: str
    label: str
    severity: str
    points: int
    observed: bool
    evidence_refs: List[str] = Field(default_factory=list)
    explanation: str

class RiskAssessmentSchema(BaseModel):
    id: Optional[str] = None
    case_id: str
    score: int = Field(..., ge=0, le=100)
    priority: str
    engine_version: str = "lira-rules-1.0"
    signals: List[SignalItem]
    missing_evidence: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None

class CaseBase(BaseModel):
    case_ref: str
    case_type: str
    title: str
    summary: str
    status: str = "open"
    priority: str = "watch"
    risk_score: int = Field(..., ge=0, le=100)
    evidence_confidence: int = Field(..., ge=0, le=100)
    data_completeness: int = Field(..., ge=0, le=100)
    amount_at_risk: Optional[float] = None
    currency: str = "INR"
    primary_supplier_id: Optional[str] = None
    risk_reasons: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_action: Optional[str] = None

class CaseCreate(CaseBase):
    pass

class CaseDispositionRequest(BaseModel):
    disposition: str = Field(..., description="closed_verified, closed_rejected, closed_inconclusive, escalated, under_review")
    note: str = Field(..., min_length=5, description="Human reviewer rationale")
    version: int = Field(..., description="Optimistic concurrency version check")

class CaseAcknowledgeRequest(BaseModel):
    note: Optional[str] = "Acknowledged by operator"

class CaseEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    version: int

class CaseResponse(CaseBase):
    id: str
    organization_id: str
    version: int
    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    assessment: Optional[RiskAssessmentSchema] = None
    transactions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    calls: List[Dict[str, Any]] = Field(default_factory=list)

class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Device Schemas
class DeviceResponse(BaseModel):
    id: str
    organization_id: str
    device_name: str
    active: bool
    last_seen_at: Optional[datetime] = None
    firmware_version: Optional[str] = "1.0.0"
    created_at: datetime
    is_online: bool = True

class DeviceHeartbeatRequest(BaseModel):
    firmware_version: Optional[str] = "1.0.4"
    status: Optional[str] = "ok"

class DeviceCaseItem(BaseModel):
    case_id: str
    case_ref: str
    priority: str
    risk_score: int
    status: str
    title: str
    reason_short: str
    updated_at: datetime
    version: int

# Audit Schemas
class AuditLogResponse(BaseModel):
    id: str
    organization_id: str
    actor_user_id: Optional[str] = None
    actor_type: str
    action: str
    object_type: str
    object_id: Optional[str] = None
    request_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int

# Simulation Schemas
class SimulationScenarioRunRequest(BaseModel):
    scenario_key: str = Field(..., description="normal_payment, changed_beneficiary, changed_beneficiary_urgent, velocity_structuring, passthrough_rapid, missing_evidence")
    persist: bool = True

class SimulationScenarioRunResponse(BaseModel):
    scenario_key: str
    scenario_name: str
    case_created: Optional[Dict[str, Any]] = None
    transactions_generated: List[Dict[str, Any]] = Field(default_factory=list)
    risk_score: int
    priority: str
    signals_fired: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_confidence: int
    data_completeness: int
    disclaimer: str = "Prototype heuristic evaluation only — not a legally validated fraud probability model."

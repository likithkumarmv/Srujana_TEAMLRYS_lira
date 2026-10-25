from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

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

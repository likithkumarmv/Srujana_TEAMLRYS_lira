from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

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

from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class GeminiAnalysisRequest(BaseModel):
    case_id: str
    supplier_context: Optional[Dict[str, Any]] = None
    transaction_context: Optional[List[Dict[str, Any]]] = None
    custom_prompt: Optional[str] = None

class GeminiAnalysisResponse(BaseModel):
    case_id: str
    is_live_gemini: bool
    risk_summary: str
    pattern_explanation: str
    recommended_interview_questions: List[str]
    investigative_leads: List[str]
    disposition_guidance: str

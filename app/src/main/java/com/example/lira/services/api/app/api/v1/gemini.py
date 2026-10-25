from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.errors import NotFoundError
from app.schemas.gemini import GeminiAnalysisRequest, GeminiAnalysisResponse
from app.services.store import store
from app.services.gemini_service import analyze_case_with_gemini, is_gemini_configured

router = APIRouter(prefix="/gemini", tags=["Gemini AI Intelligence"])

@router.get("/status")
async def gemini_status():
    return {
        "configured": is_gemini_configured(),
        "model": "gemini-1.5-flash" if is_gemini_configured() else "mock-heuristic-fallback",
        "message": "Live Gemini reasoning enabled." if is_gemini_configured() else "Gemini API key not yet set. Operating in structured heuristic demonstration mode."
    }

@router.post("/analyze-case", response_model=GeminiAnalysisResponse)
async def analyze_case(
    payload: GeminiAnalysisRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    case = store.get_case_by_id(payload.case_id, user.organization_id)
    if not case:
        raise NotFoundError(f"Case '{payload.case_id}' not found.")
    
    supplier = store.get_supplier_by_id(case.get("primary_supplier_id", ""), user.organization_id)
    transactions = [t for t in store.get_transactions(user.organization_id) if t.get("supplier_id") == case.get("primary_supplier_id")]

    result = await analyze_case_with_gemini(
        case_data=case,
        supplier_data=supplier,
        transactions=transactions
    )
    return GeminiAnalysisResponse(**result)

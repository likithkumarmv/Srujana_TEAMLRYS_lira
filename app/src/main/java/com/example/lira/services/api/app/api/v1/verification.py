from typing import Optional, List
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.errors import NotFoundError
from app.schemas.call import VerificationCallResponse, VerificationCallListResponse
from app.services.store import store

router = APIRouter(prefix="/verification-calls", tags=["Verification"])

@router.get("", response_model=VerificationCallListResponse)
async def list_verification_calls(user: AuthenticatedUser = Depends(get_current_user)):
    calls = store.get_verification_calls(user.organization_id)
    items = sorted(calls, key=lambda x: str(x.get("created_at")), reverse=True)
    return VerificationCallListResponse(items=items, total=len(items))

@router.get("/{call_id}", response_model=VerificationCallResponse)
async def get_verification_call(call_id: str, user: AuthenticatedUser = Depends(get_current_user)):
    calls = store.get_verification_calls(user.organization_id)
    for c in calls:
        if c.get("id") == call_id:
            return VerificationCallResponse(**c)
    raise NotFoundError(f"Verification call '{call_id}' not found")

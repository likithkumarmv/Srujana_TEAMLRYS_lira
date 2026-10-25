from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, AuthenticatedUser
from app.services.store import store

router = APIRouter(tags=["Auth & Onboarding"])

@router.get("/me")
async def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    org = store.organizations.get(user.organization_id, {"id": user.organization_id, "name": "Acme FinTech Corp"})
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "organization_name": org.get("name"),
        "active": True
    }

@router.post("/onboarding/bootstrap")
async def onboarding_bootstrap(user: AuthenticatedUser = Depends(get_current_user)):
    # Bootstraps tenant workspace if needed
    store.seed_demo_data(user.organization_id)
    return {
        "bootstrapped": True,
        "organization_id": user.organization_id,
        "message": "Organization workspace configured and seeded with baseline rules."
    }

@router.post("/demo/seed")
async def demo_seed(user: AuthenticatedUser = Depends(get_current_user)):
    store.seed_demo_data(user.organization_id)
    return {
        "seeded": True,
        "organization_id": user.organization_id,
        "case_count": len(store.get_cases(user.organization_id)),
        "transaction_count": len(store.get_transactions(user.organization_id)),
        "supplier_count": len(store.get_suppliers(user.organization_id)),
        "nfc_card_count": len(store.get_nfc_cards(user.organization_id))
    }

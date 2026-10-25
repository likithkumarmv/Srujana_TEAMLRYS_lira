from typing import Optional, List
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, AuthenticatedUser
from app.core.errors import NotFoundError
from app.schemas.supplier import SupplierResponse, SupplierListResponse
from app.services.store import store

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

def mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone or len(phone) < 6:
        return phone
    return phone[:4] + "****" + phone[-2:]

@router.get("", response_model=SupplierListResponse)
async def list_suppliers(user: AuthenticatedUser = Depends(get_current_user)):
    suppliers = store.get_suppliers(user.organization_id)
    items = []
    all_txs = store.get_transactions(user.organization_id)

    for sup in suppliers:
        sup_txs = [t for t in all_txs if t.get("supplier_id") == sup["id"]]
        volume = sum(float(t.get("amount", 0)) for t in sup_txs)
        sup_copy = dict(sup)
        sup_copy["masked_phone"] = mask_phone(sup.get("known_contact_phone"))
        sup_copy["transaction_count"] = len(sup_txs)
        sup_copy["total_volume"] = volume
        items.append(SupplierResponse(**sup_copy))

    return SupplierListResponse(items=items, total=len(items))

@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier_detail(
    supplier_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    supplier = store.get_supplier_by_id(supplier_id, user.organization_id)
    if not supplier:
        raise NotFoundError(f"Supplier '{supplier_id}' not found")

    sup_txs = [t for t in store.get_transactions(user.organization_id) if t.get("supplier_id") == supplier_id]
    volume = sum(float(t.get("amount", 0)) for t in sup_txs)
    sup_copy = dict(supplier)
    sup_copy["masked_phone"] = mask_phone(supplier.get("known_contact_phone"))
    sup_copy["transaction_count"] = len(sup_txs)
    sup_copy["total_volume"] = volume

    return SupplierResponse(**sup_copy)

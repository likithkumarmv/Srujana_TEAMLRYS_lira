import io
import csv
from datetime import datetime, timezone
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import PlainTextResponse
from app.core.auth import get_current_user, AuthenticatedUser
from app.schemas.transaction import (
    TransactionResponse,
    TransactionListResponse,
    CsvImportResponse,
    CsvImportRowError
)
from app.services.store import store

router = APIRouter(prefix="/transactions", tags=["Transactions"])

CSV_HEADER = "external_id,occurred_at,direction,amount,currency,supplier_name,beneficiary_fingerprint,contact_route,account_ref,counterparty_ref"

@router.get("/csv-template", response_class=PlainTextResponse)
async def get_csv_template():
    sample_content = (
        f"{CSV_HEADER}\n"
        "TX-IMPORT-101,2026-10-24T10:00:00Z,outgoing,250000.00,INR,Apex Cloud Solutions Pvt Ltd,FP-HDFC-9912,known_vendor_portal,ACC-CORP-01,CP-APEX-9912\n"
        "TX-IMPORT-102,2026-10-24T11:30:00Z,outgoing,485000.00,INR,Bharathi Industrial Supplies,FP-ICIC-8841,unsolicited_email_attachment,ACC-CORP-01,CP-IND-8841\n"
        "TX-IMPORT-103,2026-10-24T12:00:00Z,incoming,850000.00,INR,,FP-INFLOW-01,wire_transfer,ACC-SETTLE-09,CP-EXT-IN-01\n"
    )
    return PlainTextResponse(content=sample_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=lira_transactions_template.csv"})

@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    direction: Optional[str] = Query(None),
    supplier_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user)
):
    txs = store.get_transactions(user.organization_id)
    if direction:
        txs = [t for t in txs if t.get("direction") == direction]
    if supplier_id:
        txs = [t for t in txs if t.get("supplier_id") == supplier_id]
    if q:
        query_str = q.lower()
        txs = [
            t for t in txs
            if query_str in (t.get("external_id") or "").lower()
            or query_str in (t.get("beneficiary_fingerprint") or "").lower()
            or query_str in (t.get("account_ref") or "").lower()
        ]

    total = len(txs)
    start = (page - 1) * page_size
    items = sorted(txs, key=lambda x: str(x.get("occurred_at")), reverse=True)[start : start + page_size]
    
    # Enrich with supplier display name
    for it in items:
        if it.get("supplier_id"):
            sup = store.get_supplier_by_id(it["supplier_id"], user.organization_id)
            if sup:
                it["supplier_name"] = sup.get("display_name")

    return TransactionListResponse(items=items, total=total, page=page, page_size=page_size)

@router.post("/import-csv", response_model=CsvImportResponse)
async def import_transactions_csv(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user)
):
    content = await file.read()
    decoded = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(decoded))

    imported = []
    errors = []
    row_idx = 1

    suppliers_by_name = {s["display_name"].lower(): s for s in store.get_suppliers(user.organization_id)}

    for row in reader:
        row_idx += 1
        ext_id = row.get("external_id", "").strip() or f"CSV-{uuid.uuid4().hex[:6]}"
        try:
            amt_str = row.get("amount", "").strip()
            if not amt_str:
                raise ValueError("Missing 'amount'")
            amount = float(amt_str)
            if amount < 0:
                raise ValueError("Amount cannot be negative")

            direction = row.get("direction", "outgoing").strip().lower()
            if direction not in ["incoming", "outgoing"]:
                raise ValueError(f"Invalid direction '{direction}'. Must be incoming or outgoing.")

            occ_str = row.get("occurred_at", "").strip()
            occurred_at = datetime.fromisoformat(occ_str.replace("Z", "+00:00")) if occ_str else datetime.now(timezone.utc)

            sup_name = row.get("supplier_name", "").strip()
            supplier_id = None
            if sup_name:
                matched_sup = suppliers_by_name.get(sup_name.lower())
                if matched_sup:
                    supplier_id = matched_sup["id"]

            tx_record = {
                "id": str(uuid.uuid4()),
                "organization_id": user.organization_id,
                "external_id": ext_id,
                "supplier_id": supplier_id,
                "account_ref": row.get("account_ref", "").strip() or "ACC-DEFAULT",
                "counterparty_ref": row.get("counterparty_ref", "").strip() or "CP-EXT",
                "direction": direction,
                "amount": amount,
                "currency": row.get("currency", "INR").strip().upper() or "INR",
                "occurred_at": occurred_at.isoformat(),
                "beneficiary_fingerprint": row.get("beneficiary_fingerprint", "").strip() or None,
                "contact_route": row.get("contact_route", "").strip() or "csv_import",
                "source": "csv_import",
                "metadata": {"imported_row": row_idx, "filename": file.filename},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            store.insert_transaction(tx_record)
            imported.append(tx_record)
        except Exception as e:
            errors.append(CsvImportRowError(row_index=row_idx, external_id=ext_id, error=str(e)))

    # Log audit entry
    store.insert_audit_log({
        "id": str(uuid.uuid4()),
        "organization_id": user.organization_id,
        "actor_user_id": user.user_id,
        "actor_type": "human",
        "action": "transactions.csv_imported",
        "object_type": "batch_import",
        "object_id": None,
        "request_id": f"REQ-CSV-{uuid.uuid4().hex[:6]}",
        "details": {"filename": file.filename, "imported_count": len(imported), "error_count": len(errors)},
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return CsvImportResponse(
        imported_count=len(imported),
        rejected_count=len(errors),
        errors=errors,
        sample_preview=imported[:5]
    )

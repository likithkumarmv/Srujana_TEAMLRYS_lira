from datetime import datetime, timezone
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user, AuthenticatedUser
from app.schemas.simulation import SimulationScenarioRunRequest, SimulationScenarioRunResponse
from app.services.store import store
from app.services.risk_engine import evaluate_risk

router = APIRouter(prefix="/simulations", tags=["Simulation Sandbox"])

SCENARIOS_META = {
    "normal_payment": {
        "name": "Normal Routine Supplier Payment",
        "description": "Routine monthly retainer to Apex Cloud Solutions with unchanged HDFC beneficiary.",
        "amount": 125000.0,
        "contact_route": "known_vendor_portal",
        "beneficiary": "FP-HDFC-9912",
        "urgency": "low",
        "supplier_idx": 0
    },
    "changed_beneficiary": {
        "name": "Changed Beneficiary Details",
        "description": "Supplier beneficiary details modified from SBI baseline to ICICI destination.",
        "amount": 280000.0,
        "contact_route": "known_vendor_portal",
        "beneficiary": "FP-ICIC-8841",
        "urgency": "normal",
        "supplier_idx": 1
    },
    "changed_beneficiary_urgent": {
        "name": "Flagship BEC: Changed Beneficiary + Untrusted Route + Urgency",
        "description": "Invoice INV-2026-781 received via unsolicited email attachment requesting immediate clearance to new bank.",
        "amount": 485000.0,
        "contact_route": "unsolicited_email_attachment",
        "beneficiary": "FP-ICIC-8841",
        "urgency": "high",
        "supplier_idx": 1
    },
    "velocity_structuring": {
        "name": "Structuring / Rapid Burst Velocity",
        "description": "Series of 3 consecutive outbound transfers just under ₹50,000 threshold within 120 minutes.",
        "amount": 49800.0,
        "contact_route": "api_batch",
        "beneficiary": "FP-YESB-7712",
        "urgency": "normal",
        "supplier_idx": None,
        "is_burst": True
    },
    "passthrough_rapid": {
        "name": "Pass-through Rapid Inflow / Outflow Dispersal",
        "description": "Inbound settlement of ₹850,000 followed by rapid disbursement to linked counterparties.",
        "amount": 850000.0,
        "contact_route": "wire_transfer",
        "beneficiary": "FP-OUTFLOW-01",
        "urgency": "high",
        "supplier_idx": None,
        "is_passthrough": True
    },
    "missing_evidence": {
        "name": "Missing Historical Baseline / Uncertainty",
        "description": "New supplier with zero historical transaction records; triggers uncertainty warnings.",
        "amount": 210000.0,
        "contact_route": "new_vendor_agreement",
        "beneficiary": "FP-AXIS-3319",
        "urgency": "normal",
        "supplier_idx": 3
    }
}

@router.post("/run", response_model=SimulationScenarioRunResponse)
async def run_simulation_scenario(
    payload: SimulationScenarioRunRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    key = payload.scenario_key
    meta = SCENARIOS_META.get(key, SCENARIOS_META["changed_beneficiary_urgent"])
    now = datetime.now(timezone.utc)

    suppliers = store.get_suppliers(user.organization_id)
    supplier = None
    if meta["supplier_idx"] is not None and meta["supplier_idx"] < len(suppliers):
        supplier = suppliers[meta["supplier_idx"]]

    tx_id = str(uuid.uuid4())
    synthetic_tx = {
        "id": tx_id,
        "organization_id": user.organization_id,
        "external_id": f"SIM-{uuid.uuid4().hex[:6].upper()}",
        "supplier_id": supplier["id"] if supplier else None,
        "account_ref": "ACC-CORP-01",
        "counterparty_ref": "CP-SIM-01",
        "direction": "outgoing",
        "amount": meta["amount"],
        "currency": "INR",
        "occurred_at": now.isoformat(),
        "beneficiary_fingerprint": meta["beneficiary"],
        "contact_route": meta["contact_route"],
        "source": "simulator",
        "metadata": {
            "scenario": key,
            "urgency": meta["urgency"],
            "burst_id": "BST-SIM" if meta.get("is_burst") else None,
            "is_passthrough": meta.get("is_passthrough", False)
        },
        "created_at": now.isoformat()
    }

    # Evaluate risk with the pure risk engine
    history = [t for t in store.get_transactions(user.organization_id) if t.get("supplier_id") == (supplier["id"] if supplier else None)]
    eval_result = evaluate_risk(
        transaction=synthetic_tx,
        supplier=supplier,
        history=history if key != "missing_evidence" else []
    )

    case_record = None
    if payload.persist:
        store.insert_transaction(synthetic_tx)
        
        # Create case if watch, high, or critical
        case_id = str(uuid.uuid4())
        case_ref = f"LIRA-SIM-{uuid.uuid4().hex[:4].upper()}"
        case_record = {
            "id": case_id,
            "organization_id": user.organization_id,
            "case_ref": case_ref,
            "case_type": "supplier_payment_risk" if supplier else "transaction_sequence",
            "title": f"Simulation: {meta['name']}",
            "summary": meta["description"],
            "status": "awaiting_verification" if eval_result["priority"] == "critical" else "open",
            "priority": eval_result["priority"],
            "risk_score": eval_result["score"],
            "evidence_confidence": eval_result["evidence_confidence"],
            "data_completeness": eval_result["data_completeness"],
            "amount_at_risk": meta["amount"],
            "currency": "INR",
            "primary_supplier_id": supplier["id"] if supplier else None,
            "risk_reasons": eval_result["signals"],
            "recommended_action": "Review simulator output and corroborate with vendor profile.",
            "opened_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "closed_at": None,
            "version": 1
        }
        store.save_case(case_record)

        # Link transaction
        store.case_transactions.setdefault(user.organization_id, []).append({
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "transaction_id": tx_id,
            "relationship_label": "simulated_trigger"
        })

        # Audit log
        store.insert_audit_log({
            "id": str(uuid.uuid4()),
            "organization_id": user.organization_id,
            "actor_user_id": user.user_id,
            "actor_type": "human",
            "action": "simulation.scenario_run",
            "object_type": "scenario",
            "object_id": case_id,
            "request_id": f"REQ-SIM-{uuid.uuid4().hex[:6]}",
            "details": {"scenario": key, "risk_score": eval_result["score"], "priority": eval_result["priority"]},
            "created_at": now.isoformat()
        })

    return SimulationScenarioRunResponse(
        scenario_key=key,
        scenario_name=meta["name"],
        case_created=case_record,
        transactions_generated=[synthetic_tx],
        risk_score=eval_result["score"],
        priority=eval_result["priority"],
        signals_fired=eval_result["signals"],
        evidence_confidence=eval_result["evidence_confidence"],
        data_completeness=eval_result["data_completeness"]
    )

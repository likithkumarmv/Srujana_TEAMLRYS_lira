"""
LIRA Explainable Risk Engine
Implements deterministic, transparent risk scoring based on Section 5 of the LIRA specification.
Points are transparent priority indicators, NOT statistically calibrated fraud probabilities.
"""
from typing import Dict, Any, List, Optional
import math

DEFAULT_WEIGHTS = {
    "beneficiary_changed": 24,
    "contact_route_mismatch": 18,
    "new_beneficiary": 14,
    "velocity_structuring": 12,
    "amount_drift": 10,
    "unusual_timing": 8,
    "network_passthrough": 9,
    "prior_risk_context": 5,
}

PRIORITY_THRESHOLDS = {
    "low_max": 24,
    "watch_max": 49,
    "high_max": 74,
    "critical_min": 75,
}

ENGINE_VERSION = "lira-rules-1.0"

def calculate_priority(score: int) -> str:
    if score >= PRIORITY_THRESHOLDS["critical_min"]:
        return "critical"
    elif score > PRIORITY_THRESHOLDS["watch_max"]:
        return "high"
    elif score > PRIORITY_THRESHOLDS["low_max"]:
        return "watch"
    return "low"

def evaluate_risk(
    transaction: Dict[str, Any],
    supplier: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    weights: Optional[Dict[str, int]] = None,
    related_cases_count: int = 0
) -> Dict[str, Any]:
    w = weights or DEFAULT_WEIGHTS
    signals = []
    missing_evidence = []
    total_points = 0.0

    tx_beneficiary = transaction.get("beneficiary_fingerprint")
    contact_route = transaction.get("contact_route", "unknown")
    amount = float(transaction.get("amount", 0.0))
    metadata = transaction.get("metadata", {})
    history = history or []

    # 1. Beneficiary changed (Max 24 pts)
    if supplier and supplier.get("previous_beneficiary_fingerprint"):
        prev_fp = supplier.get("previous_beneficiary_fingerprint")
        curr_fp = supplier.get("current_beneficiary_fingerprint")
        if tx_beneficiary and prev_fp and tx_beneficiary != prev_fp:
            pts = w.get("beneficiary_changed", 24)
            total_points += pts
            signals.append({
                "key": "beneficiary_changed",
                "label": "Beneficiary details changed",
                "severity": "high",
                "points": pts,
                "observed": true_val(True),
                "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
                "explanation": f"Destination fingerprint '{tx_beneficiary}' differs from established supplier profile '{prev_fp}'."
            })
    elif not supplier and tx_beneficiary:
        # No established supplier
        pass

    # 2. Contact route mismatch (Max 18 pts)
    untrusted_routes = [
        "unsolicited_email_attachment",
        "email_change_request",
        "unknown_channel",
        "sms_link",
        "unverified_chat"
    ]
    if contact_route in untrusted_routes:
        pts = w.get("contact_route_mismatch", 18)
        total_points += pts
        signals.append({
            "key": "contact_route_mismatch",
            "label": "Contact route mismatch",
            "severity": "high",
            "points": pts,
            "observed": true_val(True),
            "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
            "explanation": f"Payment instructions arrived via unverified channel ('{contact_route}') instead of verified supplier portal."
        })
    elif contact_route == "unknown":
        missing_evidence.append("Channel/route origin of payment instructions not recorded.")

    # 3. New or unseen beneficiary (Max 14 pts)
    is_new = False
    if supplier and not supplier.get("previous_beneficiary_fingerprint"):
        is_new = True
    elif not supplier:
        is_new = True

    if is_new and tx_beneficiary:
        pts = w.get("new_beneficiary", 14)
        total_points += pts
        signals.append({
            "key": "new_beneficiary",
            "label": "New or unseen recipient account",
            "severity": "high",
            "points": pts,
            "observed": true_val(True),
            "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
            "explanation": f"Beneficiary destination '{tx_beneficiary}' has no prior transaction history in corporate records."
        })

    # 4. Velocity / possible structuring (Max 12 pts)
    # Check if multiple transactions occur under dual-authorization limits (e.g., 40k-50k bursts)
    if metadata.get("burst_id") or metadata.get("is_sequence"):
        pts = w.get("velocity_structuring", 12)
        total_points += pts
        signals.append({
            "key": "velocity_structuring",
            "label": "Velocity / possible structuring pattern",
            "severity": "high",
            "points": pts,
            "observed": true_val(True),
            "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
            "explanation": "Multiple outbound transfers executed in rapid succession within threshold monitoring boundaries."
        })

    # 5. Amount drift (Max 10 pts)
    if history and len(history) >= 3:
        historical_amounts = [float(h.get("amount", 0)) for h in history if float(h.get("amount", 0)) > 0]
        if historical_amounts:
            mean_amt = sum(historical_amounts) / len(historical_amounts)
            if mean_amt > 0 and amount > (mean_amt * 2.0):
                pts = w.get("amount_drift", 10)
                total_points += pts
                signals.append({
                    "key": "amount_drift",
                    "label": "Amount drift from historical baseline",
                    "severity": "medium",
                    "points": pts,
                    "observed": true_val(True),
                    "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
                    "explanation": f"Current amount of ₹{amount:,.2f} deviates significantly (>200%) from historic mean of ₹{mean_amt:,.2f}."
                })
    else:
        if not history:
            missing_evidence.append("Insufficient historical transaction samples to establish numerical baseline (minimum 3 required).")

    # 6. Urgency / unusual timing (Max 8 pts)
    if metadata.get("urgency") == "high" or metadata.get("immediate_clearing"):
        pts = w.get("unusual_timing", 8)
        total_points += pts
        signals.append({
            "key": "unusual_timing",
            "label": "Urgency flagged in payment request",
            "severity": "high",
            "points": pts,
            "observed": true_val(True),
            "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
            "explanation": "Urgent immediate settlement requested outside standard invoice terms."
        })

    # 7. Network / pass-through relationship (Max 9 pts)
    if metadata.get("transit_delay_min") or metadata.get("is_passthrough"):
        pts = w.get("network_passthrough", 9)
        total_points += pts
        signals.append({
            "key": "network_passthrough",
            "label": "Network pass-through relationship",
            "severity": "high",
            "points": pts,
            "observed": true_val(True),
            "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
            "explanation": "Inbound funds rapidly redirected into distinct secondary accounts within minutes."
        })

    # 8. Relevant prior risk context (Max 5 pts)
    if related_cases_count > 0:
        pts = w.get("prior_risk_context", 5)
        total_points += pts
        signals.append({
            "key": "prior_risk_context",
            "label": "Prior documented risk events",
            "severity": "medium",
            "points": pts,
            "observed": true_val(True),
            "evidence_refs": [transaction.get("external_id") or "TX-REQ"],
            "explanation": f"{related_cases_count} related open or escalated risk cases found for this vendor or entity."
        })

    # Bounded score 0-100
    final_score = min(100, max(0, int(round(total_points))))
    priority = calculate_priority(final_score)

    # Data completeness computation
    expected_fields = ["amount", "occurred_at", "direction", "beneficiary_fingerprint", "contact_route", "supplier_id"]
    present_fields = sum(1 for field in expected_fields if transaction.get(field))
    completeness_pct = int(round((present_fields / len(expected_fields)) * 100))
    if len(history) < 3:
        completeness_pct = max(30, completeness_pct - 15)

    # Evidence confidence computation
    confidence_pct = 85
    if contact_route in untrusted_routes:
        confidence_pct -= 20
    if not supplier or not supplier.get("last_independently_verified_at"):
        confidence_pct -= 15
    confidence_pct = max(20, min(100, confidence_pct))

    if not supplier or not supplier.get("known_contact_phone"):
        missing_evidence.append("Independent supplier phone contact not validated.")

    return {
        "score": final_score,
        "priority": priority,
        "evidence_confidence": confidence_pct,
        "data_completeness": completeness_pct,
        "engine_version": ENGINE_VERSION,
        "signals": signals,
        "missing_evidence": missing_evidence
    }

def true_val(v: bool) -> bool:
    return v

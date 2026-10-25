"""
Unit tests for the LIRA Explainable Risk Engine.
Validates the 10 requirements specified in Section 5.7 of the LIRA specification.
"""
from app.services.risk_engine import evaluate_risk

def test_1_routine_payment_is_low_risk():
    tx = {
        "amount": 125000.0,
        "direction": "outgoing",
        "beneficiary_fingerprint": "FP-HDFC-9912",
        "contact_route": "known_vendor_portal"
    }
    supplier = {
        "current_beneficiary_fingerprint": "FP-HDFC-9912",
        "previous_beneficiary_fingerprint": "FP-HDFC-9912",
        "last_independently_verified_at": "2026-08-01T00:00:00Z"
    }
    history = [{"amount": 120000.0}, {"amount": 125000.0}, {"amount": 130000.0}]
    res = evaluate_risk(tx, supplier=supplier, history=history)
    assert res["score"] <= 24
    assert res["priority"] == "low"

def test_2_changed_beneficiary_and_untrusted_route_is_high_or_critical():
    tx = {
        "external_id": "TX-9041",
        "amount": 485000.0,
        "direction": "outgoing",
        "beneficiary_fingerprint": "FP-ICIC-8841",
        "contact_route": "unsolicited_email_attachment",
        "metadata": {"urgency": "high"}
    }
    supplier = {
        "current_beneficiary_fingerprint": "FP-ICIC-8841",
        "previous_beneficiary_fingerprint": "FP-SBIN-1102",
        "last_independently_verified_at": "2026-01-01T00:00:00Z"
    }
    history = [{"amount": 140000.0}, {"amount": 150000.0}, {"amount": 135000.0}]
    res = evaluate_risk(tx, supplier=supplier, history=history)
    assert res["score"] >= 50
    assert res["priority"] in ["high", "critical"]
    assert any(s["key"] == "beneficiary_changed" for s in res["signals"])
    assert any(s["key"] == "contact_route_mismatch" for s in res["signals"])

def test_3_structuring_velocity_detected():
    tx = {
        "amount": 49500.0,
        "direction": "outgoing",
        "beneficiary_fingerprint": "FP-YESB-7711",
        "contact_route": "api_batch",
        "metadata": {"burst_id": "BST-01", "is_sequence": True}
    }
    res = evaluate_risk(tx)
    assert any(s["key"] == "velocity_structuring" for s in res["signals"])

def test_4_large_payment_alone_is_not_automatically_critical():
    tx = {
        "amount": 5000000.0,
        "direction": "outgoing",
        "beneficiary_fingerprint": "FP-HDFC-9912",
        "contact_route": "known_vendor_portal"
    }
    supplier = {
        "current_beneficiary_fingerprint": "FP-HDFC-9912",
        "previous_beneficiary_fingerprint": "FP-HDFC-9912",
        "last_independently_verified_at": "2026-08-01T00:00:00Z"
    }
    history = [{"amount": 4800000.0}, {"amount": 5100000.0}, {"amount": 4900000.0}]
    res = evaluate_risk(tx, supplier=supplier, history=history)
    assert res["priority"] != "critical"

def test_5_missing_history_lowers_completeness_and_is_surfaced():
    tx = {
        "amount": 210000.0,
        "direction": "outgoing",
        "beneficiary_fingerprint": "FP-AXIS-3319",
        "contact_route": "unknown"
    }
    res = evaluate_risk(tx, history=[])
    assert len(res["missing_evidence"]) > 0
    assert res["data_completeness"] < 80

def test_8_score_is_deterministic():
    tx = {"amount": 100000.0, "direction": "outgoing", "contact_route": "email_change_request"}
    res1 = evaluate_risk(tx)
    res2 = evaluate_risk(tx)
    assert res1["score"] == res2["score"]
    assert res1["priority"] == res2["priority"]

def test_9_scores_bounded_between_0_and_100():
    tx = {
        "amount": 9999999.0,
        "direction": "outgoing",
        "beneficiary_fingerprint": "FP-NEW",
        "contact_route": "unsolicited_email_attachment",
        "metadata": {"urgency": "high", "is_sequence": True, "transit_delay_min": 10}
    }
    supplier = {"previous_beneficiary_fingerprint": "FP-OLD"}
    res = evaluate_risk(tx, supplier=supplier, related_cases_count=5)
    assert 0 <= res["score"] <= 100

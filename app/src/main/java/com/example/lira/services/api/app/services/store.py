"""
LIRA Store — Single Source of Truth Repository
Supports live Supabase PostgreSQL when credentials are provided,
and seamless in-memory/JSON state when offline/local demo seed is running.
"""
from datetime import datetime, timezone, timedelta
import uuid
import copy
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

DEFAULT_ORG_ID = "a0000000-0000-0000-0000-000000000001"

class DataStore:
    def __init__(self):
        self.supabase_client = None
        self._init_supabase()

        # In-memory collections keyed by organization_id
        self.organizations: Dict[str, Dict[str, Any]] = {}
        self.members: Dict[str, List[Dict[str, Any]]] = {}
        self.suppliers: Dict[str, List[Dict[str, Any]]] = {}
        self.transactions: Dict[str, List[Dict[str, Any]]] = {}
        self.cases: Dict[str, List[Dict[str, Any]]] = {}
        self.case_transactions: Dict[str, List[Dict[str, Any]]] = {}
        self.risk_assessments: Dict[str, List[Dict[str, Any]]] = {}
        self.verification_calls: Dict[str, List[Dict[str, Any]]] = {}
        self.case_actions: Dict[str, List[Dict[str, Any]]] = {}
        self.audit_log: Dict[str, List[Dict[str, Any]]] = {}
        self.devices: Dict[str, List[Dict[str, Any]]] = {}
        self.nfc_cards: Dict[str, List[Dict[str, Any]]] = {}
        self.rule_configs: Dict[str, Dict[str, Any]] = {}

        # Preload demo data
        self.seed_demo_data(DEFAULT_ORG_ID)

    def _init_supabase(self):
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                from supabase import create_client, Client
                self.supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY
                )
                logger.info("Connected to remote Supabase database at %s", settings.SUPABASE_URL)
            except Exception as e:
                logger.warning("Could not initialize Supabase client: %s; using local store.", str(e))
                self.supabase_client = None

    def seed_demo_data(self, org_id: str):
        now = datetime.now(timezone.utc)
        
        # Org
        self.organizations[org_id] = {
            "id": org_id,
            "name": "Acme FinTech Corp",
            "created_at": (now - timedelta(days=30)).isoformat()
        }

        # Suppliers
        sup1_id = "d0000000-0000-0000-0000-000000000001"
        sup2_id = "d0000000-0000-0000-0000-000000000002"
        sup3_id = "d0000000-0000-0000-0000-000000000003"
        sup4_id = "d0000000-0000-0000-0000-000000000004"

        self.suppliers[org_id] = [
            {
                "id": sup1_id,
                "organization_id": org_id,
                "display_name": "Apex Cloud Solutions Pvt Ltd",
                "known_contact_name": "Rohan Mehta",
                "known_contact_phone": "+919876543210",
                "trusted_contact_source": "pre_existing_vendor_profile",
                "current_beneficiary_fingerprint": "FP-HDFC-9912",
                "previous_beneficiary_fingerprint": "FP-HDFC-9912",
                "last_independently_verified_at": (now - timedelta(days=60)).isoformat(),
                "created_at": (now - timedelta(days=90)).isoformat(),
                "updated_at": (now - timedelta(days=60)).isoformat()
            },
            {
                "id": sup2_id,
                "organization_id": org_id,
                "display_name": "Bharathi Industrial Supplies",
                "known_contact_name": "Deepak Verma",
                "known_contact_phone": "+919823456789",
                "trusted_contact_source": "pre_existing_vendor_profile",
                "current_beneficiary_fingerprint": "FP-ICIC-8841",
                "previous_beneficiary_fingerprint": "FP-SBIN-1102",
                "last_independently_verified_at": (now - timedelta(days=180)).isoformat(),
                "created_at": (now - timedelta(days=200)).isoformat(),
                "updated_at": (now - timedelta(hours=4)).isoformat()
            },
            {
                "id": sup3_id,
                "organization_id": org_id,
                "display_name": "Kavita Logistics & Freight",
                "known_contact_name": "Kavita Nair",
                "known_contact_phone": "+919811223344",
                "trusted_contact_source": "pre_existing_vendor_profile",
                "current_beneficiary_fingerprint": "FP-KKBK-4421",
                "previous_beneficiary_fingerprint": "FP-KKBK-4421",
                "last_independently_verified_at": (now - timedelta(days=15)).isoformat(),
                "created_at": (now - timedelta(days=120)).isoformat(),
                "updated_at": (now - timedelta(days=15)).isoformat()
            },
            {
                "id": sup4_id,
                "organization_id": org_id,
                "display_name": "Nova Tech Components",
                "known_contact_name": "Vikram Rao",
                "known_contact_phone": "+919845012345",
                "trusted_contact_source": "pre_existing_vendor_profile",
                "current_beneficiary_fingerprint": "FP-AXIS-3319",
                "previous_beneficiary_fingerprint": None,
                "last_independently_verified_at": None,
                "created_at": (now - timedelta(days=2)).isoformat(),
                "updated_at": (now - timedelta(days=2)).isoformat()
            }
        ]

        # Transactions
        tx1_id = "t0000000-0000-0000-0000-000000000001"
        tx2_id = "t0000000-0000-0000-0000-000000000002"
        tx3_id = "t0000000-0000-0000-0000-000000000003"
        tx4_id = "t0000000-0000-0000-0000-000000000004"
        tx5_id = "t0000000-0000-0000-0000-000000000005"
        tx6_id = "t0000000-0000-0000-0000-000000000006"
        tx7_id = "t0000000-0000-0000-0000-000000000007"
        tx8_id = "t0000000-0000-0000-0000-000000000008"

        self.transactions[org_id] = [
            {
                "id": tx1_id,
                "organization_id": org_id,
                "external_id": "TX-2026-9041",
                "supplier_id": sup2_id,
                "account_ref": "ACC-CORP-01",
                "counterparty_ref": "CP-IND-8841",
                "direction": "outgoing",
                "amount": 485000.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=4)).isoformat(),
                "beneficiary_fingerprint": "FP-ICIC-8841",
                "contact_route": "unsolicited_email_attachment",
                "source": "demo",
                "metadata": {"invoice_no": "INV-2026-781", "urgency": "high"},
                "created_at": (now - timedelta(hours=4)).isoformat()
            },
            {
                "id": tx2_id,
                "organization_id": org_id,
                "external_id": "TX-2026-9022",
                "supplier_id": sup1_id,
                "account_ref": "ACC-CORP-01",
                "counterparty_ref": "CP-APEX-9912",
                "direction": "outgoing",
                "amount": 125000.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(days=1)).isoformat(),
                "beneficiary_fingerprint": "FP-HDFC-9912",
                "contact_route": "known_vendor_portal",
                "source": "demo",
                "metadata": {"invoice_no": "APX-8820"},
                "created_at": (now - timedelta(days=1)).isoformat()
            },
            {
                "id": tx3_id,
                "organization_id": org_id,
                "external_id": "TX-2026-8801",
                "supplier_id": None,
                "account_ref": "ACC-OPS-04",
                "counterparty_ref": "CP-SHADOW-11",
                "direction": "outgoing",
                "amount": 49500.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=6)).isoformat(),
                "beneficiary_fingerprint": "FP-YESB-7711",
                "contact_route": "api_batch",
                "source": "demo",
                "metadata": {"burst_id": "BST-01", "is_sequence": True},
                "created_at": (now - timedelta(hours=6)).isoformat()
            },
            {
                "id": tx4_id,
                "organization_id": org_id,
                "external_id": "TX-2026-8802",
                "supplier_id": None,
                "account_ref": "ACC-OPS-04",
                "counterparty_ref": "CP-SHADOW-12",
                "direction": "outgoing",
                "amount": 49800.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=5)).isoformat(),
                "beneficiary_fingerprint": "FP-YESB-7712",
                "contact_route": "api_batch",
                "source": "demo",
                "metadata": {"burst_id": "BST-01", "is_sequence": True},
                "created_at": (now - timedelta(hours=5)).isoformat()
            },
            {
                "id": tx5_id,
                "organization_id": org_id,
                "external_id": "TX-2026-8803",
                "supplier_id": None,
                "account_ref": "ACC-OPS-04",
                "counterparty_ref": "CP-SHADOW-13",
                "direction": "outgoing",
                "amount": 49200.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=4)).isoformat(),
                "beneficiary_fingerprint": "FP-YESB-7713",
                "contact_route": "api_batch",
                "source": "demo",
                "metadata": {"burst_id": "BST-01", "is_sequence": True},
                "created_at": (now - timedelta(hours=4)).isoformat()
            },
            {
                "id": tx6_id,
                "organization_id": org_id,
                "external_id": "TX-2026-7701",
                "supplier_id": None,
                "account_ref": "ACC-SETTLE-09",
                "counterparty_ref": "CP-EXT-IN-01",
                "direction": "incoming",
                "amount": 850000.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=10)).isoformat(),
                "beneficiary_fingerprint": "FP-INFLOW-01",
                "contact_route": "wire_transfer",
                "source": "demo",
                "metadata": {"clearing": "immediate"},
                "created_at": (now - timedelta(hours=10)).isoformat()
            },
            {
                "id": tx7_id,
                "organization_id": org_id,
                "external_id": "TX-2026-7702",
                "supplier_id": None,
                "account_ref": "ACC-SETTLE-09",
                "counterparty_ref": "CP-EXT-OUT-01",
                "direction": "outgoing",
                "amount": 420000.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=9)).isoformat(),
                "beneficiary_fingerprint": "FP-OUTFLOW-01",
                "contact_route": "wire_transfer",
                "source": "demo",
                "metadata": {"transit_delay_min": 45, "is_passthrough": True},
                "created_at": (now - timedelta(hours=9)).isoformat()
            },
            {
                "id": tx8_id,
                "organization_id": org_id,
                "external_id": "TX-2026-7703",
                "supplier_id": None,
                "account_ref": "ACC-SETTLE-09",
                "counterparty_ref": "CP-EXT-OUT-02",
                "direction": "outgoing",
                "amount": 415000.00,
                "currency": "INR",
                "occurred_at": (now - timedelta(hours=9)).isoformat(),
                "beneficiary_fingerprint": "FP-OUTFLOW-02",
                "contact_route": "wire_transfer",
                "source": "demo",
                "metadata": {"transit_delay_min": 52, "is_passthrough": True},
                "created_at": (now - timedelta(hours=9)).isoformat()
            }
        ]

        # Cases
        case1_id = "c1000000-0000-0000-0000-000000000001"
        case2_id = "c1000000-0000-0000-0000-000000000002"
        case3_id = "c1000000-0000-0000-0000-000000000003"
        case4_id = "c1000000-0000-0000-0000-000000000004"

        self.cases[org_id] = [
            {
                "id": case1_id,
                "organization_id": org_id,
                "case_ref": "LIRA-1042",
                "case_type": "supplier_payment_risk",
                "title": "Beneficiary Details Changed on Pending Supplier Invoice",
                "summary": "Bharathi Industrial Supplies payment instruction indicates a changed bank destination (ICICI instead of SBI) requested via an unsolicited email attachment with marked urgency.",
                "status": "awaiting_verification",
                "priority": "critical",
                "risk_score": 78,
                "evidence_confidence": 68,
                "data_completeness": 75,
                "amount_at_risk": 485000.00,
                "currency": "INR",
                "primary_supplier_id": sup2_id,
                "risk_reasons": [
                    {"key": "beneficiary_changed", "label": "Beneficiary details changed", "severity": "high", "points": 24, "observed": True, "explanation": "Destination fingerprint FP-ICIC-8841 differs from trusted baseline FP-SBIN-1102."},
                    {"key": "contact_route_mismatch", "label": "Contact route mismatch", "severity": "high", "points": 18, "observed": True, "explanation": "Payment instructions submitted via unsolicited email attachment rather than pre-registered vendor portal."},
                    {"key": "new_beneficiary", "label": "New beneficiary account", "severity": "high", "points": 14, "observed": True, "explanation": "Beneficiary fingerprint has zero payment history in company ledger."},
                    {"key": "amount_drift", "label": "Amount drift from baseline", "severity": "medium", "points": 10, "observed": True, "explanation": "Requested amount ₹485,000 exceeds 6-month historical mean of ₹140,000."},
                    {"key": "unusual_timing", "label": "Urgency flagged in request", "severity": "high", "points": 8, "observed": True, "explanation": "Urgent immediate clearance requested outside regular vendor cycle."}
                ],
                "recommended_action": "Initiate independent supplier phone callback using trusted directory number (+919823456789). Do not release funds until confirmed.",
                "opened_at": (now - timedelta(hours=4)).isoformat(),
                "updated_at": (now - timedelta(minutes=30)).isoformat(),
                "closed_at": None,
                "version": 2
            },
            {
                "id": case2_id,
                "organization_id": org_id,
                "case_ref": "LIRA-1039",
                "case_type": "transaction_sequence",
                "title": "Rapid Sequence of Sub-threshold Outgoing Transfers",
                "summary": "Three consecutive transfers of ~₹49,000 each originated from ACC-OPS-04 within 2 hours, staying just below standard ₹50,000 dual-authorization threshold.",
                "status": "under_review",
                "priority": "high",
                "risk_score": 64,
                "evidence_confidence": 82,
                "data_completeness": 90,
                "amount_at_risk": 148500.00,
                "currency": "INR",
                "primary_supplier_id": None,
                "risk_reasons": [
                    {"key": "velocity_structuring", "label": "Velocity / possible structuring", "severity": "high", "points": 12, "observed": True, "explanation": "3 transfers under ₹50,000 executed within 120 minutes."},
                    {"key": "new_beneficiary", "label": "Unregistered destination accounts", "severity": "high", "points": 14, "observed": True, "explanation": "3 newly created recipient endpoints in Yes Bank."}
                ],
                "recommended_action": "Review operator credentials and verify business justification for splitting transfers.",
                "opened_at": (now - timedelta(hours=6)).isoformat(),
                "updated_at": (now - timedelta(hours=2)).isoformat(),
                "closed_at": None,
                "version": 1
            },
            {
                "id": case3_id,
                "organization_id": org_id,
                "case_ref": "LIRA-1035",
                "case_type": "network_anomaly",
                "title": "Immediate Inflow / Outflow Pass-through Pattern",
                "summary": "Inflow of ₹850,000 was dispersed within 52 minutes into two separate destination accounts with no intermediate business holding time.",
                "status": "open",
                "priority": "watch",
                "risk_score": 48,
                "evidence_confidence": 70,
                "data_completeness": 65,
                "amount_at_risk": 835000.00,
                "currency": "INR",
                "primary_supplier_id": None,
                "risk_reasons": [
                    {"key": "network_passthrough", "label": "Network pass-through relationship", "severity": "high", "points": 9, "observed": True, "explanation": "98.2% of inbound funds redirected within 60 minutes."}
                ],
                "recommended_action": "Inquire with settlement desk regarding designated escrow contract.",
                "opened_at": (now - timedelta(hours=10)).isoformat(),
                "updated_at": (now - timedelta(hours=5)).isoformat(),
                "closed_at": None,
                "version": 1
            },
            {
                "id": case4_id,
                "organization_id": org_id,
                "case_ref": "LIRA-1031",
                "case_type": "supplier_payment_risk",
                "title": "Monthly Infrastructure Retainer Payment",
                "summary": "Standard recurring monthly payment to Apex Cloud Solutions matching registered contract and unchanging HDFC beneficiary details.",
                "status": "closed_verified",
                "priority": "low",
                "risk_score": 12,
                "evidence_confidence": 95,
                "data_completeness": 100,
                "amount_at_risk": 125000.00,
                "currency": "INR",
                "primary_supplier_id": sup1_id,
                "risk_reasons": [],
                "recommended_action": "Payment approved in accordance with standard accounts payable workflow.",
                "opened_at": (now - timedelta(days=1)).isoformat(),
                "updated_at": (now - timedelta(hours=18)).isoformat(),
                "closed_at": (now - timedelta(hours=18)).isoformat(),
                "version": 2
            }
        ]

        # Case Transactions Links
        self.case_transactions[org_id] = [
            {"id": "ct1", "case_id": case1_id, "transaction_id": tx1_id, "relationship_label": "initiating_payment"},
            {"id": "ct2", "case_id": case2_id, "transaction_id": tx3_id, "relationship_label": "structuring_leg_1"},
            {"id": "ct3", "case_id": case2_id, "transaction_id": tx4_id, "relationship_label": "structuring_leg_2"},
            {"id": "ct4", "case_id": case2_id, "transaction_id": tx5_id, "relationship_label": "structuring_leg_3"},
            {"id": "ct5", "case_id": case3_id, "transaction_id": tx6_id, "relationship_label": "inflow_seed"},
            {"id": "ct6", "case_id": case3_id, "transaction_id": tx7_id, "relationship_label": "outflow_dispersal_1"},
            {"id": "ct7", "case_id": case3_id, "transaction_id": tx8_id, "relationship_label": "outflow_dispersal_2"},
            {"id": "ct8", "case_id": case4_id, "transaction_id": tx2_id, "relationship_label": "initiating_payment"}
        ]

        # Verification Calls
        call1_id = "vc000000-0000-0000-0000-000000000001"
        self.verification_calls[org_id] = [
            {
                "id": call1_id,
                "organization_id": org_id,
                "case_id": case1_id,
                "supplier_id": sup2_id,
                "provider": "mock",
                "provider_call_id": "MOCK-CALL-9821",
                "status": "completed",
                "contact_source": "pre_existing_vendor_profile (+919823456789)",
                "answer_category": "denied_request",
                "structured_summary": "Supplier contact Deepak Verma explicitly stated that Bharathi Industrial Supplies continues to bank exclusively with SBI and did NOT send invoice INV-2026-781 requesting ICICI transfer.",
                "uncertainty_note": "Call was simulated under standard demo sandbox protocol. Findings are supporting evidence; human review required.",
                "started_at": (now - timedelta(hours=2)).isoformat(),
                "ended_at": (now - timedelta(hours=1, minutes=57)).isoformat(),
                "created_at": (now - timedelta(hours=2)).isoformat()
            }
        ]

        # Case Actions
        self.case_actions[org_id] = [
            {
                "id": "ca1",
                "organization_id": org_id,
                "case_id": case1_id,
                "actor_user_id": "c0000000-0000-0000-0000-000000000003",
                "actor_type": "human",
                "action_type": "acknowledged",
                "from_status": "open",
                "to_status": "open",
                "note": "Case acknowledged by analyst Marcus Vance via Web Workbench.",
                "metadata": {"channel": "web"},
                "created_at": (now - timedelta(hours=3, minutes=45)).isoformat()
            },
            {
                "id": "ca2",
                "organization_id": org_id,
                "case_id": case1_id,
                "actor_user_id": None,
                "actor_type": "device",
                "action_type": "verification_requested",
                "from_status": "open",
                "to_status": "awaiting_verification",
                "note": "Verification call requested via physical ESP32 terminal (Operator card 04:A2:3B:1C tapped).",
                "metadata": {"device": "ESP32-Terminal-01", "operator": "Sarah Jenkins", "card_uid": "04:A2:3B:1C"},
                "created_at": (now - timedelta(hours=2)).isoformat()
            }
        ]

        # Audit Log
        self.audit_log[org_id] = [
            {
                "id": "al1",
                "organization_id": org_id,
                "actor_user_id": None,
                "actor_type": "system",
                "action": "system.bootstrap",
                "object_type": "organization",
                "object_id": org_id,
                "request_id": "REQ-BOOT-001",
                "details": {"environment": "production-demo", "rules_version": "lira-rules-1.0"},
                "created_at": (now - timedelta(days=30)).isoformat()
            },
            {
                "id": "al2",
                "organization_id": org_id,
                "actor_user_id": "c0000000-0000-0000-0000-000000000002",
                "actor_type": "human",
                "action": "case.acknowledged",
                "object_type": "case",
                "object_id": case1_id,
                "request_id": "REQ-ACK-041",
                "details": {"case_ref": "LIRA-1042", "priority": "critical"},
                "created_at": (now - timedelta(hours=3, minutes=45)).isoformat()
            },
            {
                "id": "al3",
                "organization_id": org_id,
                "actor_user_id": None,
                "actor_type": "device",
                "action": "nfc.scanned",
                "object_type": "nfc_card",
                "object_id": "f0000000-0000-0000-0000-000000000001",
                "request_id": "REQ-NFC-881",
                "details": {"card_uid": "04:A2:3B:1C", "device": "ESP32-Terminal-01", "operator": "Sarah Jenkins", "action": "verification_requested"},
                "created_at": (now - timedelta(hours=2)).isoformat()
            }
        ]

        # Devices (ESP32)
        self.devices[org_id] = [
            {
                "id": "d1000000-0000-0000-0000-000000000001",
                "organization_id": org_id,
                "device_name": "ESP32-Terminal-01 (HQ Floor 3)",
                "token_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
                "active": True,
                "last_seen_at": (now - timedelta(minutes=2)).isoformat(),
                "firmware_version": "1.0.4",
                "created_at": (now - timedelta(days=20)).isoformat()
            },
            {
                "id": "d1000000-0000-0000-0000-000000000002",
                "organization_id": org_id,
                "device_name": "ESP32-Terminal-02 (Branch B)",
                "token_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
                "active": True,
                "last_seen_at": (now - timedelta(minutes=28)).isoformat(),
                "firmware_version": "1.0.4",
                "created_at": (now - timedelta(days=10)).isoformat()
            }
        ]

        # NFC Cards (User's explicit requirement: NFC create as well as edit storage)
        self.nfc_cards[org_id] = [
            {
                "id": "f0000000-0000-0000-0000-000000000001",
                "organization_id": org_id,
                "card_uid": "04:A2:3B:1C",
                "label": "Lead Supervisor NFC Badge",
                "operator_name": "Sarah Jenkins",
                "operator_id": "EMP-1044",
                "role": "supervisor",
                "status": "active",
                "notes": "Authorized for case escalation and disposition sign-off",
                "last_scanned_at": (now - timedelta(hours=2)).isoformat(),
                "last_scanned_device": "ESP32-Terminal-01",
                "metadata": {"dept": "Risk Operations", "tier": "L3"},
                "created_at": (now - timedelta(days=20)).isoformat(),
                "updated_at": (now - timedelta(hours=2)).isoformat()
            },
            {
                "id": "f0000000-0000-0000-0000-000000000002",
                "organization_id": org_id,
                "card_uid": "04:E8:9F:4D",
                "label": "Senior Analyst Keycard",
                "operator_name": "Marcus Vance",
                "operator_id": "EMP-2190",
                "role": "analyst",
                "status": "active",
                "notes": "Primary review analyst for vendor payments",
                "last_scanned_at": (now - timedelta(hours=5)).isoformat(),
                "last_scanned_device": "ESP32-Terminal-01",
                "metadata": {"dept": "Financial Crime Intelligence"},
                "created_at": (now - timedelta(days=15)).isoformat(),
                "updated_at": (now - timedelta(days=1)).isoformat()
            },
            {
                "id": "f0000000-0000-0000-0000-000000000003",
                "organization_id": org_id,
                "card_uid": "04:77:C2:55",
                "label": "Operations Terminal Card",
                "operator_name": "Priya Sharma",
                "operator_id": "EMP-3801",
                "role": "operator",
                "status": "active",
                "notes": "Stationed at physical verification desk",
                "last_scanned_at": (now - timedelta(days=1)).isoformat(),
                "last_scanned_device": "ESP32-Terminal-02",
                "metadata": {"shift": "Day"},
                "created_at": (now - timedelta(days=10)).isoformat(),
                "updated_at": (now - timedelta(days=1)).isoformat()
            },
            {
                "id": "f0000000-0000-0000-0000-000000000004",
                "organization_id": org_id,
                "card_uid": "04:11:88:99",
                "label": "Backup Shift Keycard",
                "operator_name": "Temporary Float",
                "operator_id": "EMP-TEMP",
                "role": "analyst",
                "status": "suspended",
                "notes": "Suspended pending quarterly audit",
                "last_scanned_at": None,
                "last_scanned_device": None,
                "metadata": {},
                "created_at": (now - timedelta(days=5)).isoformat(),
                "updated_at": (now - timedelta(days=2)).isoformat()
            }
        ]

    # Accessors for Cases
    def get_cases(self, org_id: str) -> List[Dict[str, Any]]:
        return self.cases.get(org_id, [])

    def get_case_by_id(self, case_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        for c in self.get_cases(org_id):
            if c.get("id") == case_id:
                return c
        return None

    def save_case(self, case: Dict[str, Any]):
        org_id = case["organization_id"]
        for idx, existing in enumerate(self.cases.get(org_id, [])):
            if existing["id"] == case["id"]:
                self.cases[org_id][idx] = case
                return
        self.cases.setdefault(org_id, []).append(case)

    # Accessors for Transactions
    def get_transactions(self, org_id: str) -> List[Dict[str, Any]]:
        return self.transactions.get(org_id, [])

    def insert_transaction(self, tx: Dict[str, Any]):
        org_id = tx["organization_id"]
        self.transactions.setdefault(org_id, []).append(tx)

    # Accessors for Suppliers
    def get_suppliers(self, org_id: str) -> List[Dict[str, Any]]:
        return self.suppliers.get(org_id, [])

    def get_supplier_by_id(self, supplier_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        for s in self.get_suppliers(org_id):
            if s.get("id") == supplier_id:
                return s
        return None

    # Accessors for NFC Cards
    def get_nfc_cards(self, org_id: str) -> List[Dict[str, Any]]:
        return self.nfc_cards.get(org_id, [])

    def get_nfc_card_by_id(self, card_id: str, org_id: str) -> Optional[Dict[str, Any]]:
        for c in self.get_nfc_cards(org_id):
            if c.get("id") == card_id:
                return c
        return None

    def find_nfc_card_by_uid(self, card_uid: str, org_id: str) -> Optional[Dict[str, Any]]:
        clean_uid = card_uid.strip().upper()
        for c in self.get_nfc_cards(org_id):
            if c.get("card_uid", "").strip().upper() == clean_uid:
                return c
        return None

    def insert_nfc_card(self, card: Dict[str, Any]):
        org_id = card["organization_id"]
        self.nfc_cards.setdefault(org_id, []).append(card)

    def save_nfc_card(self, card: Dict[str, Any]):
        org_id = card["organization_id"]
        for idx, existing in enumerate(self.nfc_cards.get(org_id, [])):
            if existing["id"] == card["id"]:
                self.nfc_cards[org_id][idx] = card
                return
        self.nfc_cards.setdefault(org_id, []).append(card)

    def delete_nfc_card(self, card_id: str, org_id: str):
        if org_id in self.nfc_cards:
            self.nfc_cards[org_id] = [c for c in self.nfc_cards[org_id] if c["id"] != card_id]

    # Accessors for Calls, Actions, Audit, Devices
    def get_verification_calls(self, org_id: str) -> List[Dict[str, Any]]:
        return self.verification_calls.get(org_id, [])

    def insert_verification_call(self, call: Dict[str, Any]):
        org_id = call["organization_id"]
        self.verification_calls.setdefault(org_id, []).append(call)

    def save_verification_call(self, call: Dict[str, Any]):
        org_id = call["organization_id"]
        for idx, existing in enumerate(self.verification_calls.get(org_id, [])):
            if existing["id"] == call["id"]:
                self.verification_calls[org_id][idx] = call
                return
        self.verification_calls.setdefault(org_id, []).append(call)

    def get_case_actions(self, case_id: str, org_id: str) -> List[Dict[str, Any]]:
        return [a for a in self.case_actions.get(org_id, []) if a.get("case_id") == case_id]

    def insert_case_action(self, action: Dict[str, Any]):
        org_id = action["organization_id"]
        self.case_actions.setdefault(org_id, []).append(action)

    def get_audit_logs(self, org_id: str) -> List[Dict[str, Any]]:
        return sorted(self.audit_log.get(org_id, []), key=lambda x: str(x.get("created_at")), reverse=True)

    def insert_audit_log(self, log_entry: Dict[str, Any]):
        org_id = log_entry["organization_id"]
        self.audit_log.setdefault(org_id, []).append(log_entry)

    def get_devices(self, org_id: str) -> List[Dict[str, Any]]:
        return self.devices.get(org_id, [])

# Singleton data store
store = DataStore()

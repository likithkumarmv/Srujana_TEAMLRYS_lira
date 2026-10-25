-- ==============================================================================
-- LIRA — Financial Fraud Detection & Investigation Platform
-- Seed Data: supabase/seed.sql
-- Repeatable, idempotent realistic synthetic demonstration data
-- ==============================================================================

-- 1. Demo Organization
insert into organizations (id, name, created_at)
values ('a0000000-0000-0000-0000-000000000001', 'Acme FinTech Corp', now() - interval '30 days')
on conflict (id) do nothing;

-- 2. Demo Organization Members
insert into organization_members (id, organization_id, user_id, role, active, created_at)
values 
  ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'owner', true, now() - interval '30 days'),
  ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000002', 'supervisor', true, now() - interval '25 days'),
  ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000003', 'analyst', true, now() - interval '20 days')
on conflict (organization_id, user_id) do nothing;

-- 3. Demo Suppliers (Synthetic names, masked fingerprints, synthetic phone numbers)
insert into suppliers (id, organization_id, display_name, known_contact_name, known_contact_phone, trusted_contact_source, current_beneficiary_fingerprint, previous_beneficiary_fingerprint, last_independently_verified_at)
values
  ('d0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'Apex Cloud Solutions Pvt Ltd', 'Rohan Mehta', '+919876543210', 'pre_existing_vendor_profile', 'FP-HDFC-9912', 'FP-HDFC-9912', now() - interval '60 days'),
  ('d0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'Bharathi Industrial Supplies', 'Deepak Verma', '+919823456789', 'pre_existing_vendor_profile', 'FP-ICIC-8841', 'FP-SBIN-1102', now() - interval '180 days'),
  ('d0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'Kavita Logistics & Freight', 'Kavita Nair', '+919811223344', 'pre_existing_vendor_profile', 'FP-KKBK-4421', 'FP-KKBK-4421', now() - interval '15 days'),
  ('d0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'Nova Tech Components', 'Vikram Rao', '+919845012345', 'pre_existing_vendor_profile', 'FP-AXIS-3319', null, null)
on conflict (id) do nothing;

-- 4. Demo Risk Rule Configurations
insert into risk_rule_configs (id, organization_id, rule_set_name, engine_version, weights, thresholds, enabled_signals)
values (
  'e0000000-0000-0000-0000-000000000001',
  'a0000000-0000-0000-0000-000000000001',
  'default',
  'lira-rules-1.0',
  '{"beneficiary_changed": 24, "contact_route_mismatch": 18, "new_beneficiary": 14, "velocity_structuring": 12, "amount_drift": 10, "unusual_timing": 8, "network_passthrough": 9, "prior_risk_context": 5}'::jsonb,
  '{"low_max": 24, "watch_max": 49, "high_max": 74, "critical_min": 75}'::jsonb,
  '["beneficiary_changed", "contact_route_mismatch", "new_beneficiary", "velocity_structuring", "amount_drift", "unusual_timing", "network_passthrough", "prior_risk_context"]'::jsonb
)
on conflict (organization_id, rule_set_name) do nothing;

-- 5. NFC Cards & Badges (Storing NFC create & edit data)
insert into nfc_cards (id, organization_id, card_uid, label, operator_name, operator_id, role, status, notes, last_scanned_at, last_scanned_device)
values
  ('f0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', '04:A2:3B:1C', 'Lead Supervisor NFC Badge', 'Sarah Jenkins', 'EMP-1044', 'supervisor', 'active', 'Authorized for case escalation and disposition sign-off', now() - interval '2 hours', 'ESP32-Terminal-01'),
  ('f0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', '04:E8:9F:4D', 'Senior Analyst Keycard', 'Marcus Vance', 'EMP-2190', 'analyst', 'active', 'Primary review analyst for vendor payments', now() - interval '5 hours', 'ESP32-Terminal-01'),
  ('f0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', '04:77:C2:55', 'Operations Terminal Card', 'Priya Sharma', 'EMP-3801', 'operator', 'active', 'Stationed at physical verification desk', now() - interval '1 day', 'ESP32-Terminal-02'),
  ('f0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', '04:11:88:99', 'Backup Shift Keycard', 'Temporary Float', 'EMP-TEMP', 'analyst', 'suspended', 'Suspended pending quarterly audit', null, null)
on conflict (organization_id, card_uid) do nothing;

-- 6. Demo Device Registry (ESP32 DevKit Terminals)
insert into device_registry (id, organization_id, device_name, token_hash, active, last_seen_at, firmware_version)
values
  ('d1000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'ESP32-Terminal-01 (HQ Floor 3)', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', true, now() - interval '2 minutes', '1.0.4'),
  ('d1000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'ESP32-Terminal-02 (Branch B)', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', true, now() - interval '28 minutes', '1.0.4')
on conflict (id) do nothing;

-- 7. Demo Transactions (Supporting the 6 demo scenarios)
insert into transactions (id, organization_id, external_id, supplier_id, account_ref, counterparty_ref, direction, amount, currency, occurred_at, beneficiary_fingerprint, contact_route, source, metadata)
values
  -- Scenario 3 (Flagship): LIRA-1042 Bharathi Industrial beneficiary change + untrusted email
  ('t0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-9041', 'd0000000-0000-0000-0000-000000000002', 'ACC-CORP-01', 'CP-IND-8841', 'outgoing', 485000.00, 'INR', now() - interval '4 hours', 'FP-ICIC-8841', 'unsolicited_email_attachment', 'demo', '{"invoice_no": "INV-2026-781", "urgency": "high"}'::jsonb),
  
  -- Scenario 1: Routine known payment to Apex Cloud Solutions
  ('t0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-9022', 'd0000000-0000-0000-0000-000000000001', 'ACC-CORP-01', 'CP-APEX-9912', 'outgoing', 125000.00, 'INR', now() - interval '1 day', 'FP-HDFC-9912', 'known_vendor_portal', 'demo', '{"invoice_no": "APX-8820"}'::jsonb),
  
  -- Scenario 4: Structuring velocity pattern (Multiple small transfers below threshold)
  ('t0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-8801', null, 'ACC-OPS-04', 'CP-SHADOW-11', 'outgoing', 49500.00, 'INR', now() - interval '6 hours', 'FP-YESB-7711', 'api_batch', 'demo', '{"burst_id": "BST-01"}'::jsonb),
  ('t0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-8802', null, 'ACC-OPS-04', 'CP-SHADOW-12', 'outgoing', 49800.00, 'INR', now() - interval '5 hours', 'FP-YESB-7712', 'api_batch', 'demo', '{"burst_id": "BST-01"}'::jsonb),
  ('t0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-8803', null, 'ACC-OPS-04', 'CP-SHADOW-13', 'outgoing', 49200.00, 'INR', now() - interval '4 hours', 'FP-YESB-7713', 'api_batch', 'demo', '{"burst_id": "BST-01"}'::jsonb),

  -- Scenario 5: Pass-through candidate (Incoming 850k followed immediately by outgoing dispersal)
  ('t0000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-7701', null, 'ACC-SETTLE-09', 'CP-EXT-IN-01', 'incoming', 850000.00, 'INR', now() - interval '10 hours', 'FP-INFLOW-01', 'wire_transfer', 'demo', '{"clearing": "immediate"}'::jsonb),
  ('t0000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-7702', null, 'ACC-SETTLE-09', 'CP-EXT-OUT-01', 'outgoing', 420000.00, 'INR', now() - interval '9 hours', 'FP-OUTFLOW-01', 'wire_transfer', 'demo', '{"transit_delay_min": 45}'::jsonb),
  ('t0000000-0000-0000-0000-000000000008', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-7703', null, 'ACC-SETTLE-09', 'CP-EXT-OUT-02', 'outgoing', 415000.00, 'INR', now() - interval '9 hours', 'FP-OUTFLOW-02', 'wire_transfer', 'demo', '{"transit_delay_min": 52}'::jsonb),

  -- Scenario 6: Missing evidence / legitimate seasonal payment
  ('t0000000-0000-0000-0000-000000000009', 'a0000000-0000-0000-0000-000000000001', 'TX-2026-6601', 'd0000000-0000-0000-0000-000000000004', 'ACC-CORP-01', 'CP-NOVA-3319', 'outgoing', 210000.00, 'INR', now() - interval '2 days', 'FP-AXIS-3319', 'new_vendor_agreement', 'demo', '{"baseline_count": 1}'::jsonb)
on conflict (organization_id, external_id) do nothing;

-- 8. Demo Cases
insert into cases (id, organization_id, case_ref, case_type, title, summary, status, priority, risk_score, evidence_confidence, data_completeness, amount_at_risk, currency, primary_supplier_id, risk_reasons, recommended_action, opened_at, updated_at, version)
values
  -- Case 1: Flagship LIRA-1042 (Bharathi Industrial)
  (
    'c1000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'LIRA-1042',
    'supplier_payment_risk',
    'Beneficiary Details Changed on Pending Supplier Invoice',
    'Bharathi Industrial Supplies payment instruction indicates a changed bank destination (ICICI instead of SBI) requested via an unsolicited email attachment with marked urgency.',
    'awaiting_verification',
    'critical',
    78,
    68,
    75,
    485000.00,
    'INR',
    'd0000000-0000-0000-0000-000000000002',
    '[
      {"key": "beneficiary_changed", "label": "Beneficiary details changed", "severity": "high", "points": 24, "observed": true, "explanation": "Destination fingerprint FP-ICIC-8841 differs from trusted baseline FP-SBIN-1102"},
      {"key": "contact_route_mismatch", "label": "Contact route mismatch", "severity": "high", "points": 18, "observed": true, "explanation": "Payment instructions submitted via unsolicited email attachment rather than pre-registered vendor portal"},
      {"key": "new_beneficiary", "label": "New beneficiary account", "severity": "high", "points": 14, "observed": true, "explanation": "Beneficiary fingerprint has zero payment history in company ledger"},
      {"key": "amount_drift", "label": "Amount drift from baseline", "severity": "medium", "points": 10, "observed": true, "explanation": "Requested amount ₹485,000 exceeds 6-month historical mean of ₹140,000"},
      {"key": "unusual_timing", "label": "Urgency flagged in request", "severity": "high", "points": 8, "observed": true, "explanation": "Urgent immediate clearance requested outside regular vendor cycle"}
    ]'::jsonb,
    'Initiate independent supplier phone callback using trusted directory number (+919823456789). Do not release funds until confirmed.',
    now() - interval '4 hours',
    now() - interval '30 minutes',
    2
  ),
  
  -- Case 2: LIRA-1039 Structuring velocity episode
  (
    'c1000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'LIRA-1039',
    'transaction_sequence',
    'Rapid Sequence of Sub-threshold Outgoing Transfers',
    'Three consecutive transfers of ~₹49,000 each originated from ACC-OPS-04 within 2 hours, staying just below the standard ₹50,000 dual-authorization threshold.',
    'under_review',
    'high',
    64,
    82,
    90,
    148500.00,
    'INR',
    null,
    '[
      {"key": "velocity_structuring", "label": "Velocity / possible structuring", "severity": "high", "points": 12, "observed": true, "explanation": "3 transfers under ₹50,000 executed within 120 minutes"},
      {"key": "new_beneficiary", "label": "Unregistered destination accounts", "severity": "high", "points": 14, "observed": true, "explanation": "3 newly created recipient endpoints in Yes Bank"},
      {"key": "unusual_timing", "label": "Burst activity pattern", "severity": "high", "points": 8, "observed": true, "explanation": "Automated batch submission burst"}
    ]'::jsonb,
    'Review operator credentials and verify business justification for splitting transfers.',
    now() - interval '6 hours',
    now() - interval '2 hours',
    1
  ),

  -- Case 3: LIRA-1035 Pass-through Rapid Dispersal
  (
    'c1000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'LIRA-1035',
    'network_anomaly',
    'Immediate Inflow / Outflow Pass-through Pattern',
    'Inflow of ₹850,000 was dispersed within 52 minutes into two separate destination accounts with no intermediate business holding time.',
    'open',
    'watch',
    48,
    70,
    65,
    835000.00,
    'INR',
    null,
    '[
      {"key": "network_passthrough", "label": "Network pass-through relationship", "severity": "high", "points": 9, "observed": true, "explanation": "98.2% of inbound funds redirected within 60 minutes"},
      {"key": "amount_drift", "label": "Unusual volume for settlement node", "severity": "medium", "points": 10, "observed": true, "explanation": "Account typically maintains 72-hour escrow balance"}
    ]'::jsonb,
    'Inquire with settlement desk regarding designated escrow contract.',
    now() - interval '10 hours',
    now() - interval '5 hours',
    1
  ),

  -- Case 4: LIRA-1031 Routine payment to Apex Cloud (Closed Verified)
  (
    'c1000000-0000-0000-0000-000000000004',
    'a0000000-0000-0000-0000-000000000001',
    'LIRA-1031',
    'supplier_payment_risk',
    'Monthly Infrastructure Retainer Payment',
    'Standard recurring monthly payment to Apex Cloud Solutions matching registered contract and unchanging HDFC beneficiary details.',
    'closed_verified',
    'low',
    12,
    95,
    100,
    125000.00,
    'INR',
    'd0000000-0000-0000-0000-000000000001',
    '[
      {"key": "amount_drift", "label": "Within expected historical variance", "severity": "low", "points": 0, "observed": false, "explanation": "Amount is within 2% of 12-month average"},
      {"key": "beneficiary_changed", "label": "Beneficiary unchanged", "severity": "low", "points": 0, "observed": false, "explanation": "Matches registered profile FP-HDFC-9912"}
    ]'::jsonb,
    'Payment approved in accordance with standard accounts payable workflow.',
    now() - interval '1 day',
    now() - interval '18 hours',
    2
  )
on conflict (organization_id, case_ref) do nothing;

-- 9. Case Transactions Links
insert into case_transactions (id, organization_id, case_id, transaction_id, relationship_label, sequence_order)
values
  ('ct000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000001', 't0000000-0000-0000-0000-000000000001', 'initiating_payment', 1),
  ('ct000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000002', 't0000000-0000-0000-0000-000000000003', 'structuring_leg_1', 1),
  ('ct000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000002', 't0000000-0000-0000-0000-000000000004', 'structuring_leg_2', 2),
  ('ct000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000002', 't0000000-0000-0000-0000-000000000005', 'structuring_leg_3', 3),
  ('ct000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000003', 't0000000-0000-0000-0000-000000000006', 'inflow_seed', 1),
  ('ct000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000003', 't0000000-0000-0000-0000-000000000007', 'outflow_dispersal_1', 2),
  ('ct000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000003', 't0000000-0000-0000-0000-000000000008', 'outflow_dispersal_2', 3),
  ('ct000000-0000-0000-0000-000000000008', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000004', 't0000000-0000-0000-0000-000000000002', 'initiating_payment', 1)
on conflict (case_id, transaction_id) do nothing;

-- 10. Demo Risk Assessments
insert into risk_assessments (id, organization_id, case_id, score, priority, engine_version, signals, missing_evidence)
values (
  'ra000000-0000-0000-0000-000000000001',
  'a0000000-0000-0000-0000-000000000001',
  'c1000000-0000-0000-0000-000000000001',
  78,
  'critical',
  'lira-rules-1.0',
  '[
    {"key": "beneficiary_changed", "label": "Beneficiary details changed", "severity": "high", "points": 24, "observed": true, "evidence_refs": ["TX-2026-9041"], "explanation": "Proposed destination FP-ICIC-8841 differs from trusted baseline FP-SBIN-1102."},
    {"key": "contact_route_mismatch", "label": "Contact route mismatch", "severity": "high", "points": 18, "observed": true, "evidence_refs": ["TX-2026-9041"], "explanation": "Instruction received via unsolicited external email attachment."},
    {"key": "new_beneficiary", "label": "New beneficiary destination", "severity": "high", "points": 14, "observed": true, "evidence_refs": ["TX-2026-9041"], "explanation": "Recipient account has no established ledger history."},
    {"key": "amount_drift", "label": "Amount drift from historical baseline", "severity": "medium", "points": 10, "observed": true, "evidence_refs": ["TX-2026-9041"], "explanation": "Payment exceeds average historical payout by 246%."},
    {"key": "unusual_timing", "label": "Urgency flagged in request", "severity": "high", "points": 8, "observed": true, "evidence_refs": ["TX-2026-9041"], "explanation": "Request marked with emergency settlement priority."}
  ]'::jsonb,
  '["Independent voice verification with authorized vendor finance officer pending", "Dual approval documentation not yet signed"]'::jsonb
)
on conflict (id) do nothing;

-- 11. Demo Verification Call (Simulated for Bharathi Industrial)
insert into verification_calls (id, organization_id, case_id, supplier_id, provider, provider_call_id, status, requested_by, contact_source, answer_category, structured_summary, uncertainty_note, started_at, ended_at)
values (
  'vc000000-0000-0000-0000-000000000001',
  'a0000000-0000-0000-0000-000000000001',
  'c1000000-0000-0000-0000-000000000001',
  'd0000000-0000-0000-0000-000000000002',
  'mock',
  'MOCK-CALL-9821',
  'completed',
  'b0000000-0000-0000-0000-000000000002',
  'pre_existing_vendor_profile (+919823456789)',
  'denied_request',
  'Supplier contact Deepak Verma explicitly stated that Bharathi Industrial Supplies continues to bank exclusively with SBI and did NOT send invoice INV-2026-781 requesting ICICI transfer.',
  'Call was simulated under standard demo sandbox protocol. Findings are supporting evidence; human review required.',
  now() - interval '2 hours',
  now() - interval '1 hour 57 minutes'
)
on conflict (id) do nothing;

-- 12. Demo Case Actions
insert into case_actions (id, organization_id, case_id, actor_user_id, actor_type, action_type, from_status, to_status, note, metadata)
values
  ('ca000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000003', 'human', 'acknowledged', 'open', 'open', 'Case acknowledged by analyst Marcus Vance via Web Workbench.', '{"channel": "web"}'::jsonb),
  ('ca000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'c1000000-0000-0000-0000-000000000002', 'device', 'verification_requested', 'open', 'awaiting_verification', 'Verification call requested via physical ESP32 terminal (Operator card 04:A2:3B:1C tapped).', '{"device": "ESP32-Terminal-01", "operator": "Sarah Jenkins", "card_uid": "04:A2:3B:1C"}'::jsonb)
on conflict (id) do nothing;

-- 13. Audit Log
insert into audit_log (id, organization_id, actor_user_id, actor_type, action, object_type, object_id, request_id, details)
values
  ('al000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'system', 'system.bootstrap', 'organization', 'a0000000-0000-0000-0000-000000000001', 'REQ-BOOT-001', '{"environment": "production-demo", "rules_version": "lira-rules-1.0"}'::jsonb),
  ('al000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000002', 'human', 'case.acknowledged', 'case', 'c1000000-0000-0000-0000-000000000001', 'REQ-ACK-041', '{"case_ref": "LIRA-1042", "priority": "critical"}'::jsonb),
  ('al000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', null, 'device', 'nfc.scanned', 'nfc_card', 'f0000000-0000-0000-0000-000000000001', 'REQ-NFC-881', '{"card_uid": "04:A2:3B:1C", "device": "ESP32-Terminal-01", "operator": "Sarah Jenkins", "action": "verification_requested"}'::jsonb)
on conflict (id) do nothing;

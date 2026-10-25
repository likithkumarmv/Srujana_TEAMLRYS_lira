-- ==============================================================================
-- LIRA — Financial Fraud Detection & Investigation Platform
-- Migration: 0001_lira_schema.sql
-- Single Source of Truth Database Schema with RLS, Constraints, and NFC Tracking
-- ==============================================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- 1. Organizations
create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

-- 2. Organization Members
create table if not exists organization_members (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  user_id uuid not null,
  role text not null check (role in ('owner','admin','supervisor','analyst','viewer')),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (organization_id, user_id)
);

-- 3. Suppliers
create table if not exists suppliers (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  display_name text not null,
  known_contact_name text null,
  known_contact_phone text null,
  trusted_contact_source text not null default 'pre_existing_vendor_profile',
  current_beneficiary_fingerprint text null,
  previous_beneficiary_fingerprint text null,
  last_independently_verified_at timestamptz null,
  business_hours jsonb null default '{"start": "09:00", "end": "18:00", "tz": "Asia/Kolkata"}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 4. Transactions
create table if not exists transactions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  external_id text null,
  supplier_id uuid null references suppliers(id) on delete set null,
  account_ref text null,
  counterparty_ref text null,
  direction text not null check (direction in ('incoming','outgoing')),
  amount numeric(14,2) not null check (amount >= 0),
  currency char(3) not null default 'INR',
  occurred_at timestamptz not null,
  beneficiary_fingerprint text null,
  contact_route text null,
  source text not null default 'demo',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (organization_id, external_id)
);

-- 5. Cases
create table if not exists cases (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  case_ref text not null,
  case_type text not null check (case_type in ('supplier_payment_risk','transaction_sequence','beneficiary_change','network_anomaly')),
  title text not null,
  summary text not null,
  status text not null check (status in ('open','awaiting_verification','under_review','escalated','closed_verified','closed_rejected','closed_inconclusive')) default 'open',
  priority text not null check (priority in ('low','watch','high','critical')) default 'watch',
  risk_score integer not null check (risk_score between 0 and 100),
  evidence_confidence integer not null check (evidence_confidence between 0 and 100),
  data_completeness integer not null check (data_completeness between 0 and 100),
  amount_at_risk numeric(14,2) null,
  currency char(3) not null default 'INR',
  primary_supplier_id uuid null references suppliers(id) on delete set null,
  risk_reasons jsonb not null default '[]'::jsonb,
  recommended_action text null,
  opened_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  closed_at timestamptz null,
  version integer not null default 1,
  unique (organization_id, case_ref)
);

-- 6. Case Transactions (Many-to-Many linking episodes)
create table if not exists case_transactions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  case_id uuid not null references cases(id) on delete cascade,
  transaction_id uuid not null references transactions(id) on delete restrict,
  relationship_label text null,
  sequence_order integer null default 1,
  unique (case_id, transaction_id)
);

-- 7. Risk Assessments (Versioned signal snapshots)
create table if not exists risk_assessments (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  case_id uuid not null references cases(id) on delete cascade,
  score integer not null check (score between 0 and 100),
  priority text not null,
  engine_version text not null default 'lira-rules-1.0',
  signals jsonb not null,
  missing_evidence jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

-- 8. Verification Calls (AI Calling agent records)
create table if not exists verification_calls (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  case_id uuid not null references cases(id) on delete cascade,
  supplier_id uuid not null references suppliers(id) on delete cascade,
  provider text not null default 'mock',
  provider_call_id text null,
  status text not null check (status in ('requested','queued','dialing','answered','no_answer','busy','failed','completed','cancelled')) default 'requested',
  requested_by uuid null,
  contact_source text not null default 'pre_existing_vendor_profile',
  answer_category text null check (answer_category in ('confirmed_request','denied_request','unclear','no_response','not_applicable')),
  structured_summary text null,
  uncertainty_note text null,
  started_at timestamptz null,
  ended_at timestamptz null,
  created_at timestamptz not null default now()
);

-- 9. Case Actions (State changes & transitions)
create table if not exists case_actions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  case_id uuid not null references cases(id) on delete cascade,
  actor_user_id uuid null,
  actor_type text not null check (actor_type in ('human','device','system','voice_provider')),
  action_type text not null check (action_type in ('acknowledged','verification_requested','escalated','disposition_set','note_added','risk_recalculated')),
  from_status text null,
  to_status text null,
  note text null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- 10. Audit Log (Append-only compliance trail)
create table if not exists audit_log (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  actor_user_id uuid null,
  actor_type text not null,
  action text not null,
  object_type text not null,
  object_id uuid null,
  request_id text null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- 11. Device Registry (ESP32 terminals & hardware)
create table if not exists device_registry (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  device_name text not null,
  token_hash text not null,
  active boolean not null default true,
  last_seen_at timestamptz null,
  firmware_version text null default '1.0.0',
  created_at timestamptz not null default now()
);

-- 12. Risk Rule Configurations
create table if not exists risk_rule_configs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  rule_set_name text not null default 'default',
  engine_version text not null default 'lira-rules-1.0',
  weights jsonb not null,
  thresholds jsonb not null,
  enabled_signals jsonb not null,
  updated_by uuid null,
  updated_at timestamptz not null default now(),
  unique (organization_id, rule_set_name)
);

-- 13. NFC Cards & Operator Badges (Storage for NFC Create & Edit operations)
create table if not exists nfc_cards (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  card_uid text not null,
  label text not null,
  operator_name text not null,
  operator_id text null,
  role text not null check (role in ('admin','supervisor','analyst','operator')) default 'analyst',
  status text not null check (status in ('active','suspended','revoked')) default 'active',
  notes text null,
  last_scanned_at timestamptz null,
  last_scanned_device text null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, card_uid)
);

-- ==============================================================================
-- Indexes for Performance & Filter Security
-- ==============================================================================
create index if not exists idx_org_members_user on organization_members (user_id);
create index if not exists idx_suppliers_org on suppliers (organization_id);
create index if not exists idx_transactions_org_occurred on transactions (organization_id, occurred_at desc);
create index if not exists idx_transactions_supplier on transactions (supplier_id);
create index if not exists idx_cases_org_status on cases (organization_id, status);
create index if not exists idx_cases_org_priority on cases (organization_id, priority);
create index if not exists idx_cases_org_updated on cases (organization_id, updated_at desc);
create index if not exists idx_case_transactions_case on case_transactions (case_id);
create index if not exists idx_case_transactions_tx on case_transactions (transaction_id);
create index if not exists idx_verification_calls_case on verification_calls (case_id);
create index if not exists idx_case_actions_case on case_actions (case_id);
create index if not exists idx_audit_log_org on audit_log (organization_id, created_at desc);
create index if not exists idx_device_registry_org on device_registry (organization_id);
create index if not exists idx_nfc_cards_org on nfc_cards (organization_id);
create index if not exists idx_nfc_cards_uid on nfc_cards (organization_id, card_uid);

-- ==============================================================================
-- Row Level Security (RLS) Policies
-- ==============================================================================
alter table organizations enable row level security;
alter table organization_members enable row level security;
alter table suppliers enable row level security;
alter table transactions enable row level security;
alter table cases enable row level security;
alter table case_transactions enable row level security;
alter table risk_assessments enable row level security;
alter table verification_calls enable row level security;
alter table case_actions enable row level security;
alter table audit_log enable row level security;
alter table device_registry enable row level security;
alter table risk_rule_configs enable row level security;
alter table nfc_cards enable row level security;

-- Helper function to check organization membership for auth.uid()
create or replace function is_org_member(org_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from organization_members
    where organization_id = org_id
      and user_id = auth.uid()
      and active = true
  );
$$;

-- RLS SELECT Policies for authenticated users
create policy "Members can view their organizations" on organizations
  for select using (id in (select organization_id from organization_members where user_id = auth.uid() and active = true));

create policy "Members can view organization members" on organization_members
  for select using (is_org_member(organization_id));

create policy "Members can view suppliers" on suppliers
  for select using (is_org_member(organization_id));

create policy "Members can view transactions" on transactions
  for select using (is_org_member(organization_id));

create policy "Members can view cases" on cases
  for select using (is_org_member(organization_id));

create policy "Members can view case transactions" on case_transactions
  for select using (is_org_member(organization_id));

create policy "Members can view risk assessments" on risk_assessments
  for select using (is_org_member(organization_id));

create policy "Members can view verification calls" on verification_calls
  for select using (is_org_member(organization_id));

create policy "Members can view case actions" on case_actions
  for select using (is_org_member(organization_id));

create policy "Members can view audit logs" on audit_log
  for select using (is_org_member(organization_id));

create policy "Members can view device registry" on device_registry
  for select using (is_org_member(organization_id));

create policy "Members can view risk rules" on risk_rule_configs
  for select using (is_org_member(organization_id));

create policy "Members can view NFC cards" on nfc_cards
  for select using (is_org_member(organization_id));

-- Realtime publication for cases, actions, and NFC cards
do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    alter publication supabase_realtime add table cases;
    alter publication supabase_realtime add table case_actions;
    alter publication supabase_realtime add table verification_calls;
    alter publication supabase_realtime add table nfc_cards;
  end if;
exception
  when others then null;
end $$;

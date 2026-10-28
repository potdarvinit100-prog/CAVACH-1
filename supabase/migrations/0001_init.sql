-- AI Cyber Guardian — Supabase schema (Postgres + RLS)
-- Apply in Supabase SQL Editor. Test RLS with two separate accounts before presentation.
-- No secrets, credentials, OTPs, PINs or passwords are ever stored in these tables.
-- Raw audio / private message bodies: store only when the user explicitly submits
-- them for analysis, and prefer storing extracted indicators + a redacted excerpt.

create extension if not exists "pgcrypto";
create extension if not exists "vector";

-- Profiles: one row per auth user, created on sign-up (app or trigger).
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  preferred_language text not null default 'en' check (preferred_language in ('en', 'mr', 'hi')),
  created_at timestamptz not null default now()
);

create table public.investigations (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  status text not null default 'open' check (status in ('open', 'reported', 'closed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.submitted_artifacts (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  artifact_type text not null check (artifact_type in ('message', 'url', 'voice_context', 'payment_text', 'document_note')),
  content_redacted text not null,
  language text check (language in ('en', 'mr', 'hi', 'unknown')),
  created_at timestamptz not null default now()
);

create table public.detection_findings (
  id uuid primary key default gen_random_uuid(),
  artifact_id uuid not null references public.submitted_artifacts (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  signal text not null,
  weight int not null check (weight >= 0),
  evidence text not null,
  created_at timestamptz not null default now()
);

create table public.threat_indicators (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  indicator_type text not null check (indicator_type in ('domain', 'url', 'upi_suffix', 'narrative', 'phone_label')),
  value text not null,
  created_at timestamptz not null default now()
);

create table public.threat_relationships (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  from_artifact_id uuid references public.submitted_artifacts (id) on delete set null,
  to_artifact_id uuid references public.submitted_artifacts (id) on delete set null,
  relationship_type text not null check (relationship_type in ('confirmed', 'possible', 'unknown')),
  basis text not null,
  created_at timestamptz not null default now()
);

create table public.risk_assessments (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  band text not null check (band in ('Low concern', 'Suspicious', 'High concern', 'Insufficient evidence')),
  score int not null,
  next_action text not null,
  next_action_marathi text,
  limitations text not null,
  created_at timestamptz not null default now()
);

create table public.alerts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  investigation_id uuid references public.investigations (id) on delete set null,
  title text not null,
  reason text not null,
  monitored_source text not null,
  acknowledged boolean not null default false,
  created_at timestamptz not null default now()
);

create table public.workflow_runs (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid references public.investigations (id) on delete set null,
  owner_id uuid references auth.users (id) on delete cascade,
  workflow_name text not null,
  status text not null check (status in ('running', 'succeeded', 'failed', 'needs_review')),
  error_text text,
  created_at timestamptz not null default now()
);

create table public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  source_url text not null,
  source_name text not null,
  chunk_text text not null,
  embedding vector(1536),
  created_at timestamptz not null default now()
);

create table public.incident_response_cases (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  checklist_state jsonb not null default '{}'::jsonb,
  reported_to_1930 boolean not null default false,
  portal_reference text,
  created_at timestamptz not null default now()
);

create table public.user_consents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  consent_type text not null check (consent_type in ('monitoring', 'third_party_enrichment', 'storage')),
  granted boolean not null,
  created_at timestamptz not null default now()
);

create table public.audit_events (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references auth.users (id) on delete cascade,
  event_type text not null,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index investigations_owner_idx on public.investigations (owner_id, created_at desc);
create index artifacts_investigation_idx on public.submitted_artifacts (investigation_id);
create index findings_artifact_idx on public.detection_findings (artifact_id);
create index indicators_investigation_idx on public.threat_indicators (investigation_id);
create index assessments_investigation_idx on public.risk_assessments (investigation_id, created_at desc);

-- RLS: every user-owned table is isolated to its owner.
alter table public.profiles enable row level security;
alter table public.investigations enable row level security;
alter table public.submitted_artifacts enable row level security;
alter table public.detection_findings enable row level security;
alter table public.threat_indicators enable row level security;
alter table public.threat_relationships enable row level security;
alter table public.risk_assessments enable row level security;
alter table public.alerts enable row level security;
alter table public.workflow_runs enable row level security;
alter table public.incident_response_cases enable row level security;
alter table public.user_consents enable row level security;
alter table public.audit_events enable row level security;
alter table public.knowledge_documents enable row level security;

-- Profiles: a user manages only their own row.
create policy "own profile" on public.profiles for all using (id = auth.uid()) with check (id = auth.uid());

-- Generic owner policies (all tables below carry owner_id).
create policy "own investigations" on public.investigations for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own artifacts" on public.submitted_artifacts for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own findings" on public.detection_findings for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own indicators" on public.threat_indicators for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own relationships" on public.threat_relationships for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own assessments" on public.risk_assessments for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own alerts" on public.alerts for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own workflow runs" on public.workflow_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own incident cases" on public.incident_response_cases for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own consents" on public.user_consents for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "own audit read" on public.audit_events for select using (owner_id = auth.uid());
create policy "own audit insert" on public.audit_events for insert with check (owner_id = auth.uid());

-- Knowledge base: readable by signed-in users, written only via service role.
create policy "knowledge read" on public.knowledge_documents for select to authenticated using (true);

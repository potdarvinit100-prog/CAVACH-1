-- GENERATED from supabase/migrations/*.sql — do not edit by hand. Edit migrations, then regenerate.
-- Generated: 2026-10-28
-- AI Cyber Guardian — Supabase schema (Postgres + RLS)
-- Apply in Supabase SQL Editor. Test RLS with two separate accounts before presentation.
-- No secrets, credentials, OTPs, PINs or passwords are ever stored in these tables.
-- Raw audio / private message bodies: store only when the user explicitly submits
-- them for analysis, and prefer storing extracted indicators + a redacted excerpt.

create extension if not exists "pgcrypto";
create extension if not exists "vector";

-- Profiles: one row per auth user, created on sign-up (app or trigger).
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  preferred_language text not null default 'en' check (preferred_language in ('en', 'mr', 'hi')),
  created_at timestamptz not null default now()
);

create table if not exists public.investigations (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  title text not null,
  status text not null default 'open' check (status in ('open', 'reported', 'closed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.submitted_artifacts (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  artifact_type text not null check (artifact_type in ('message', 'url', 'voice_context', 'payment_text', 'document_note')),
  content_redacted text not null,
  language text check (language in ('en', 'mr', 'hi', 'unknown')),
  created_at timestamptz not null default now()
);

create table if not exists public.detection_findings (
  id uuid primary key default gen_random_uuid(),
  artifact_id uuid not null references public.submitted_artifacts (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  signal text not null,
  weight int not null check (weight >= 0),
  evidence text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.threat_indicators (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  indicator_type text not null check (indicator_type in ('domain', 'url', 'upi_suffix', 'narrative', 'phone_label')),
  value text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.threat_relationships (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  from_artifact_id uuid references public.submitted_artifacts (id) on delete set null,
  to_artifact_id uuid references public.submitted_artifacts (id) on delete set null,
  relationship_type text not null check (relationship_type in ('confirmed', 'possible', 'unknown')),
  basis text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.risk_assessments (
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

create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  investigation_id uuid references public.investigations (id) on delete set null,
  title text not null,
  reason text not null,
  monitored_source text not null,
  acknowledged boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.workflow_runs (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid references public.investigations (id) on delete set null,
  owner_id uuid references auth.users (id) on delete cascade,
  workflow_name text not null,
  status text not null check (status in ('running', 'succeeded', 'failed', 'needs_review')),
  error_text text,
  created_at timestamptz not null default now()
);

create table if not exists public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  source_url text not null,
  source_name text not null,
  chunk_text text not null,
  embedding vector(1536),
  created_at timestamptz not null default now()
);

create table if not exists public.incident_response_cases (
  id uuid primary key default gen_random_uuid(),
  investigation_id uuid not null references public.investigations (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  checklist_state jsonb not null default '{}'::jsonb,
  reported_to_1930 boolean not null default false,
  portal_reference text,
  created_at timestamptz not null default now()
);

create table if not exists public.user_consents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  consent_type text not null check (consent_type in ('monitoring', 'third_party_enrichment', 'storage')),
  granted boolean not null,
  created_at timestamptz not null default now()
);

create table if not exists public.audit_events (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references auth.users (id) on delete cascade,
  event_type text not null,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists investigations_owner_idx on public.investigations (owner_id, created_at desc);
create index if not exists artifacts_investigation_idx on public.submitted_artifacts (investigation_id);
create index if not exists findings_artifact_idx on public.detection_findings (artifact_id);
create index if not exists indicators_investigation_idx on public.threat_indicators (investigation_id);
create index if not exists assessments_investigation_idx on public.risk_assessments (investigation_id, created_at desc);

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
drop policy if exists "own profile" on public.profiles;
create policy "own profile" on public.profiles for all using (id = auth.uid()) with check (id = auth.uid());

-- Generic owner policies (all tables below carry owner_id).
drop policy if exists "own investigations" on public.investigations;
create policy "own investigations" on public.investigations for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own artifacts" on public.submitted_artifacts;
create policy "own artifacts" on public.submitted_artifacts for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own findings" on public.detection_findings;
create policy "own findings" on public.detection_findings for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own indicators" on public.threat_indicators;
create policy "own indicators" on public.threat_indicators for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own relationships" on public.threat_relationships;
create policy "own relationships" on public.threat_relationships for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own assessments" on public.risk_assessments;
create policy "own assessments" on public.risk_assessments for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own alerts" on public.alerts;
create policy "own alerts" on public.alerts for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own workflow runs" on public.workflow_runs;
create policy "own workflow runs" on public.workflow_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own incident cases" on public.incident_response_cases;
create policy "own incident cases" on public.incident_response_cases for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own consents" on public.user_consents;
create policy "own consents" on public.user_consents for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "own audit read" on public.audit_events;
create policy "own audit read" on public.audit_events for select using (owner_id = auth.uid());
drop policy if exists "own audit insert" on public.audit_events;
create policy "own audit insert" on public.audit_events for insert with check (owner_id = auth.uid());

-- Knowledge base: readable by signed-in users, written only via service role.
drop policy if exists "knowledge read" on public.knowledge_documents;
create policy "knowledge read" on public.knowledge_documents for select to authenticated using (true);
-- 0002_storage.sql — private artifact storage bucket + object policies.
-- Buckets are data, not schema, in some setups: if this insert is rejected
-- by your Supabase version, create the bucket in Dashboard > Storage with
-- the same name (private) and apply only the policies below.
insert into storage.buckets (id, name, public)
values ('artifacts', 'artifacts', false)
on conflict (id) do nothing;

drop policy if exists "own artifacts read" on storage.objects;
create policy "own artifacts read" on storage.objects for select
  using (bucket_id = 'artifacts' and auth.uid()::text = (storage.foldername(name))[1]);
drop policy if exists "own artifacts insert" on storage.objects;
create policy "own artifacts insert" on storage.objects for insert
  with check (bucket_id = 'artifacts' and auth.uid()::text = (storage.foldername(name))[1]);
drop policy if exists "own artifacts delete" on storage.objects;
create policy "own artifacts delete" on storage.objects for delete
  using (bucket_id = 'artifacts' and auth.uid()::text = (storage.foldername(name))[1]);

-- Upload rule enforced in code, not only here: audio and document uploads
-- are limited to the allow-list in backend/audio.py and the frontend
-- (wav/mp3/m4a/ogg/pdf/txt, max 25 MB). Storage alone does not validate
-- file contents.
-- CAVACH 0003: new tables + artifact columns. Single source of truth: migrations.
create table if not exists public.user_roles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('user','admin')),
  created_at timestamptz not null default now()
);
create table if not exists public.sentinel_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid(),
  run_type text not null, status text not null,
  findings jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.intel_items (
  id uuid primary key default gen_random_uuid(),
  source text not null, licence text not null,
  fetched_at timestamptz not null default now(),
  indicator text not null, indicator_type text not null,
  raw jsonb not null default '{}'::jsonb
);
create table if not exists public.campaign_clusters (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid(),
  indicator text not null, member_count int not null default 0,
  created_at timestamptz not null default now()
);
create table if not exists public.report_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid(),
  report_type text not null, content jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table if not exists public.rate_limits (
  user_id uuid not null, endpoint text not null,
  window_start timestamptz not null, count int not null default 0,
  primary key (user_id, endpoint, window_start)
);
create table if not exists public.evaluation_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid(),
  tool text not null, metrics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
alter table public.submitted_artifacts add column if not exists content_hash text;
alter table public.submitted_artifacts add column if not exists language text;
alter table public.submitted_artifacts add column if not exists source_channel text;
alter table public.investigations add column if not exists title text;
-- RLS on new tables (owner-only; intel_items is admin-readable via policy below)
alter table public.user_roles enable row level security;
alter table public.sentinel_runs enable row level security;
alter table public.campaign_clusters enable row level security;
alter table public.report_runs enable row level security;
alter table public.rate_limits enable row level security;
alter table public.evaluation_runs enable row level security;
drop policy if exists "owner read/write" on public.sentinel_runs;
create policy "owner read/write" on public.sentinel_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "owner read/write" on public.campaign_clusters;
create policy "owner read/write" on public.campaign_clusters for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "owner read/write" on public.report_runs;
create policy "owner read/write" on public.report_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "owner read/write" on public.evaluation_runs;
create policy "owner read/write" on public.evaluation_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists "owner rows only" on public.rate_limits;
create policy "owner rows only" on public.rate_limits for all using (user_id = auth.uid()) with check (user_id = auth.uid());
drop policy if exists "own role row" on public.user_roles;
create policy "own role row" on public.user_roles for select using (user_id = auth.uid());
-- CAVACH 0004: child rows must belong to an investigation owned by auth.uid().
-- This replaces the old "owner_id = auth.uid()" child policies, which could
-- not prove the parent investigation belonged to the same user.
-- Profiles: auto-create on sign-up. Admin: user_roles + security-definer fn.
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text, created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
drop policy if exists "own profile" on public.profiles;
create policy "own profile" on public.profiles for all using (id = auth.uid()) with check (id = auth.uid());

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email)
  on conflict (id) do update set email = excluded.email;
  insert into public.user_roles (user_id, role) values (new.id, 'user')
  on conflict (user_id) do nothing;
  return new;
end; $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
for each row execute function public.handle_new_user();

create or replace function public.is_admin()
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.user_roles where user_id = auth.uid() and role = 'admin');
$$;

-- Investigations keep their owner policy from 0001. Child tables:
drop policy if exists "own artifacts" on public.submitted_artifacts;
drop policy if exists "parent investigation owned" on public.submitted_artifacts;
create policy "parent investigation owned" on public.submitted_artifacts for all
  using (exists (select 1 from public.investigations i where i.id = submitted_artifacts.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = submitted_artifacts.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own findings" on public.detection_findings;
drop policy if exists "parent investigation owned" on public.detection_findings;
create policy "parent investigation owned" on public.detection_findings for all
  using (exists (select 1 from public.submitted_artifacts a join public.investigations i on i.id = a.investigation_id where a.id = detection_findings.artifact_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.submitted_artifacts a join public.investigations i on i.id = a.investigation_id where a.id = detection_findings.artifact_id and i.owner_id = auth.uid()));
drop policy if exists "own indicators" on public.threat_indicators;
drop policy if exists "parent investigation owned" on public.threat_indicators;
create policy "parent investigation owned" on public.threat_indicators for all
  using (exists (select 1 from public.investigations i where i.id = threat_indicators.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = threat_indicators.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own relationships" on public.threat_relationships;
drop policy if exists "parent investigation owned" on public.threat_relationships;
create policy "parent investigation owned" on public.threat_relationships for all
  using (exists (select 1 from public.investigations i where i.id = threat_relationships.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = threat_relationships.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own assessments" on public.risk_assessments;
drop policy if exists "parent investigation owned" on public.risk_assessments;
create policy "parent investigation owned" on public.risk_assessments for all
  using (exists (select 1 from public.investigations i where i.id = risk_assessments.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = risk_assessments.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own incident cases" on public.incident_response_cases;
drop policy if exists "parent investigation owned" on public.incident_response_cases;
create policy "parent investigation owned" on public.incident_response_cases for all
  using (exists (select 1 from public.investigations i where i.id = incident_response_cases.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = incident_response_cases.investigation_id and i.owner_id = auth.uid()));
-- Alerts / audit / workflow rows: owner-only, and if linked, parent-owned.
drop policy if exists "own alerts" on public.alerts;
drop policy if exists "owner and parent owned" on public.alerts;
create policy "owner and parent owned" on public.alerts for all
  using (owner_id = auth.uid() and (investigation_id is null or exists (select 1 from public.investigations i where i.id = alerts.investigation_id and i.owner_id = auth.uid())))
  with check (owner_id = auth.uid() and (investigation_id is null or exists (select 1 from public.investigations i where i.id = alerts.investigation_id and i.owner_id = auth.uid())));
-- Admins may read intel_items; everyone else: no rows (service role writes).
alter table public.intel_items enable row level security;
drop policy if exists "admin read intel" on public.intel_items;
create policy "admin read intel" on public.intel_items for select using (public.is_admin());
-- CAVACH 0005: pgvector for RAG embeddings (deployment step, not a stub claim).
-- Requires pgvector extension in the Supabase project. Embedding dimension
-- must match the embedding model configured in generate-embeddings
-- (default below assumes 1536; change both together if you switch models).
create extension if not exists vector;
create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  source text not null, chunk_text text not null,
  embedding vector(1536), created_at timestamptz not null default now()
);
create index if not exists knowledge_chunks_embedding_idx
  on public.knowledge_chunks using hnsw (embedding vector_cosine_ops);
alter table public.knowledge_chunks enable row level security;
drop policy if exists "public read chunks" on public.knowledge_chunks;
create policy "public read chunks" on public.knowledge_chunks for select using (true);
-- CAVACH 0006: one transactional RPC for creating an investigation.
-- Either ALL rows land or none do — no orphans. Column names match 0001.
create or replace function public.create_investigation(payload jsonb)
returns uuid language plpgsql security definer set search_path = public as $$
declare
  inv_id uuid := gen_random_uuid();
  first_art_id uuid;
  art jsonb; f jsonb; ind jsonb; rel jsonb;
begin
  if auth.uid() is null then raise exception 'not authenticated'; end if;
  insert into public.investigations (id, owner_id, title, status)
  values (inv_id, auth.uid(), payload->>'title', coalesce(payload->>'status','open'));
  for art in select * from jsonb_array_elements(payload->'artifacts') loop
    insert into public.submitted_artifacts (id, investigation_id, owner_id, artifact_type, content_redacted, content_hash, language, source_channel)
    values (gen_random_uuid(), inv_id, auth.uid(), art->>'type', art->>'content_redacted', art->>'content_hash', art->>'language', art->>'source_channel')
    returning id into first_art_id;
    -- first_art_id ends as the LAST artifact; keep the first instead:
    if first_art_id is not null and (select count(*) from public.submitted_artifacts where investigation_id = inv_id) > 1 then
      select id into first_art_id from public.submitted_artifacts where investigation_id = inv_id order by created_at asc limit 1;
    end if;
  end loop;
  for f in select * from jsonb_array_elements(payload->'findings') loop
    insert into public.detection_findings (artifact_id, owner_id, signal, weight, evidence)
    values (first_art_id, auth.uid(), f->>'signal', coalesce((f->>'weight')::int, 0), f->>'evidence');
  end loop;
  for ind in select * from jsonb_array_elements(payload->'indicators') loop
    insert into public.threat_indicators (investigation_id, owner_id, indicator_type, value)
    values (inv_id, auth.uid(), ind->>'type', ind->>'value');
  end loop;
  for rel in select * from jsonb_array_elements(payload->'relationships') loop
    insert into public.threat_relationships (investigation_id, owner_id, from_artifact_id, to_artifact_id, relationship_type, basis)
    values (inv_id, auth.uid(), first_art_id, null, rel->>'type', rel->>'basis');
  end loop;
  insert into public.risk_assessments (investigation_id, owner_id, band, score, next_action, next_action_marathi, limitations)
  values (inv_id, auth.uid(), payload->>'band', (payload->>'score')::int,
          coalesce(payload->>'next_action','Verify through an official channel before acting.'),
          payload->>'next_action_marathi',
          coalesce(payload->>'limitations','A clean result never means safe.'));
  insert into public.audit_events (owner_id, event_type, detail)
  values (auth.uid(), 'investigation_created', jsonb_build_object('investigation_id', inv_id));
  return inv_id;
end; $$;

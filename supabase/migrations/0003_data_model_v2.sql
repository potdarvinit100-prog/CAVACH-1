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
create policy "owner read/write" on public.sentinel_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "owner read/write" on public.campaign_clusters for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "owner read/write" on public.report_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "owner read/write" on public.evaluation_runs for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "owner rows only" on public.rate_limits for all using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own role row" on public.user_roles for select using (user_id = auth.uid());

alter table public.workflow_runs add column if not exists content_hash text;

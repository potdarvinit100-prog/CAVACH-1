-- CAVACH 0004: child rows must belong to an investigation owned by auth.uid().
-- This replaces the old "owner_id = auth.uid()" child policies, which could
-- not prove the parent investigation belonged to the same user.
-- Profiles: auto-create on sign-up. Admin: user_roles + security-definer fn.
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text, created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
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
create policy "parent investigation owned" on public.submitted_artifacts for all
  using (exists (select 1 from public.investigations i where i.id = submitted_artifacts.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = submitted_artifacts.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own findings" on public.detection_findings;
create policy "parent investigation owned" on public.detection_findings for all
  using (exists (select 1 from public.submitted_artifacts a join public.investigations i on i.id = a.investigation_id where a.id = detection_findings.artifact_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.submitted_artifacts a join public.investigations i on i.id = a.investigation_id where a.id = detection_findings.artifact_id and i.owner_id = auth.uid()));
drop policy if exists "own indicators" on public.threat_indicators;
create policy "parent investigation owned" on public.threat_indicators for all
  using (exists (select 1 from public.investigations i where i.id = threat_indicators.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = threat_indicators.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own relationships" on public.threat_relationships;
create policy "parent investigation owned" on public.threat_relationships for all
  using (exists (select 1 from public.investigations i where i.id = threat_relationships.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = threat_relationships.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own assessments" on public.risk_assessments;
create policy "parent investigation owned" on public.risk_assessments for all
  using (exists (select 1 from public.investigations i where i.id = risk_assessments.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = risk_assessments.investigation_id and i.owner_id = auth.uid()));
drop policy if exists "own incident cases" on public.incident_response_cases;
create policy "parent investigation owned" on public.incident_response_cases for all
  using (exists (select 1 from public.investigations i where i.id = incident_response_cases.investigation_id and i.owner_id = auth.uid()))
  with check (exists (select 1 from public.investigations i where i.id = incident_response_cases.investigation_id and i.owner_id = auth.uid()));
-- Alerts / audit / workflow rows: owner-only, and if linked, parent-owned.
drop policy if exists "own alerts" on public.alerts;
create policy "owner and parent owned" on public.alerts for all
  using (owner_id = auth.uid() and (investigation_id is null or exists (select 1 from public.investigations i where i.id = alerts.investigation_id and i.owner_id = auth.uid())))
  with check (owner_id = auth.uid() and (investigation_id is null or exists (select 1 from public.investigations i where i.id = alerts.investigation_id and i.owner_id = auth.uid())));
-- Admins may read intel_items; everyone else: no rows (service role writes).
alter table public.intel_items enable row level security;
create policy "admin read intel" on public.intel_items for select using (public.is_admin());

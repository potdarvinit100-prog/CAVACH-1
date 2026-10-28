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

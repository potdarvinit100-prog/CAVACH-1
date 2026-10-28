-- 0002_storage.sql — private artifact storage bucket + object policies.
-- Buckets are data, not schema, in some setups: if this insert is rejected
-- by your Supabase version, create the bucket in Dashboard > Storage with
-- the same name (private) and apply only the policies below.
insert into storage.buckets (id, name, public)
values ('artifacts', 'artifacts', false)
on conflict (id) do nothing;

create policy "own artifacts read" on storage.objects for select
  using (bucket_id = 'artifacts' and auth.uid()::text = (storage.foldername(name))[1]);
create policy "own artifacts insert" on storage.objects for insert
  with check (bucket_id = 'artifacts' and auth.uid()::text = (storage.foldername(name))[1]);
create policy "own artifacts delete" on storage.objects for delete
  using (bucket_id = 'artifacts' and auth.uid()::text = (storage.foldername(name))[1]);

-- Upload rule enforced in code, not only here: audio and document uploads
-- are limited to the allow-list in backend/audio.py and the frontend
-- (wav/mp3/m4a/ogg/pdf/txt, max 25 MB). Storage alone does not validate
-- file contents.

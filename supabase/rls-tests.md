# RLS isolation test guide — run against a real Supabase project only.
# No project is connected in this repo, so these steps are a checklist,
# not a claimed test result.

## Setup
1. Apply `migrations/0001_init.sql` then `0002_storage.sql` in SQL Editor.
2. Create two accounts in Auth: alice@example.com and bob@example.com.
   (Use test accounts only, never real user data.)

## Test 1 — investigations are owner-isolated
1. Sign in as Alice. Insert one investigation via the app (or SQL as Alice
   through the API with her JWT; `owner_id` must equal her auth id).
2. Sign in as Bob. List investigations through the app / PostgREST with
   Bob's JWT.
3. Expected: Bob sees zero rows. Alice's row must not appear, and a direct
   select by id with Bob's JWT must return zero rows (RLS, not app filtering).

## Test 2 — artifacts and findings follow the investigation
1. As Alice, submit an investigation with one artifact and confirm findings
   and a risk assessment are created.
2. As Bob, attempt to read that artifact id, its findings, and its
   assessment directly.
3. Expected: zero rows for all three tables.

## Test 3 — knowledge base is read-only for users
1. As Alice, attempt an insert into `knowledge_documents` via PostgREST.
2. Expected: rejected by RLS (only the service role may write it).

## Test 4 — storage isolation
1. As Alice, upload to `artifacts/<alice-id>/test.txt` (private bucket).
2. As Bob, attempt to read that object path.
3. Expected: denied.

Record the date, project ref, and pass/fail for each test before any
presentation claim about RLS is made. Until then the claim is: "RLS policies
are written in the migrations; isolation tests are documented, not yet run
against a live project."

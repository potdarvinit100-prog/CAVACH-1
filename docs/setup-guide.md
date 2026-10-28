# CAVACH setup guide

## 1. Frontend (no keys needed)
```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
npm test && npm run build
```

## 2. Supabase (required for cloud save, auth, enrichment, RAG vectors)
1. Create a project. In the SQL Editor, run migrations **in order**: `supabase/migrations/0001_init.sql` … `0006_create_investigation_rpc.sql`. (Do not hand-edit `supabase/schema.sql` — it is generated from the migrations.)
2. Storage: create a private bucket named `artifacts` (per-user-folder policies are in `0002_storage.sql`).
3. Deploy Edge Functions: `analyze-explanation`, `enrich-url`, `generate-embeddings`. Set secrets: `ALLOWED_ORIGIN` (your app origin, exact), `LLM_API_KEY`/`LLM_API_URL`/`LLM_MODEL` (optional — without them, explanations use the labelled deterministic fallback), `SAFE_BROWSING_API_KEY` (optional — without it, enrichment is `not_checked`; check Google Safe Browsing terms: the free API is non-commercial, Web Risk is the commercial option), `EMBEDDING_API_URL`/`EMBEDDING_API_KEY`/`EMBEDDING_MODEL` (for pgvector; dimension must match `0005_pgvector.sql`'s `vector(1536)` or change both).
4. Frontend env: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, then rebuild.

## 3. RLS isolation test (recorded, not assumed)
```bash
SUPABASE_URL=... SUPABASE_ANON_KEY=... USER_A_JWT=... USER_B_JWT=... python3 supabase/rls_test.py
# Result lands in supabase/rls_test_results.json. A pass means: B cannot read A's investigation.
# Current recorded result in this repo: not_run (no project configured here).
```

## 4. n8n
Import `n8n/ai-cyber-guardian-pipeline.json` and `n8n/sentinel-daily.json`. Set env vars `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` in n8n, and create the webhook header-auth credential (no secret lives in the JSON files).

## 5. Python service (optional, for a deployed API)
```bash
pip install fastapi uvicorn pydantic
uvicorn api:app --port 8000   # from backend/
```

## 6. Delete my data / delete account
- Device rows: Dashboard → "Delete my data (this row)".
- Cloud rows: delete from `investigations` (cascades to artifacts/findings/indicators/relationships/assessments/cases) under your `owner_id`.
- Account: Supabase Auth account deletion is an admin action in the Supabase dashboard (no self-serve delete-account endpoint is shipped in this build — stated plainly).

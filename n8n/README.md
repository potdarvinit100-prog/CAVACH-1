# CAVACH n8n workflows

## ai-cyber-guardian-pipeline.json — user investigation pipeline (fixed)
Webhook (POST, header auth — set the credential in n8n, never in this JSON)
→ Validate + Redact (credential digits → `[REDACTED]`)
→ Dedupe (SHA-256 of redacted text)
→ Check duplicate (Supabase REST, `workflow_runs.content_hash`)
→ IF duplicate → **Respond to Webhook** (duplicate) — branch now responds
→ Detect (full signal table from `backend/engine.py`, not a reduced copy)
→ IF High concern → Save alert (review queue) + Save workflow run → **Respond to Webhook**
→ Else → Save workflow run → **Respond to Webhook**
All HTTP nodes: retry 3×, 5 s apart, 10 s timeout. Supabase URL/keys come from n8n environment variables.

## sentinel-daily.json — Sentinel daily watch
Schedule (07:00 daily) → Collect `intel_items` → Dedupe by hash → Classify (rules only; LLM explanation is added by the Edge Function for user-facing results, never as the sole decision) → Save `sentinel_runs`. A failed source is recorded as a failed run with the source named — never a fake alert. The daily report (email + PDF + in-app admin page) is generated from saved runs by `backend/sentinel.py`.

## Before activating either workflow
1. Set env vars in n8n: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
2. Create the webhook header-auth credential in n8n and attach it to the Webhook node.
3. Apply Supabase migrations 0001–0006 first (the RPC and `content_hash` column are required).

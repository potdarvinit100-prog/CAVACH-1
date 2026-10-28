# CAVACH Sentinel daily report — 2026-10-28T08:45:59.153349+00:00

Generated from real local runs (evaluation, adversarial, RLS status, secret scan).
No fake alerts: sections with no data say so plainly.

- Evaluation (test-set, not real-world): n=153, precision=1.0, recall=0.982
- Held-out: {'n': 20, 'tp': 8, 'fp': 0, 'fn': 2, 'tn': 10, 'precision': 1.0, 'recall': 0.8, 'accuracy': 0.9}
- Adversarial evasion rate: 0.0 (n=9)
- RLS test: not_run — no project credentials (SUPABASE_URL / USER_A_JWT / USER_B_JWT / SUPABASE_ANON_KEY)
- Secret scan hits: none

## Could not check
- Supabase live project (no project configured in this workspace) — RLS test recorded as not_run.
- LLM provider (no key configured) — explanations fall back to the deterministic template.
- Safe Browsing / VirusTotal (no keys configured) — enrichment reports not_checked.
- n8n instance (not connected) — workflows are importable JSON, not live runs.
- Licensed public intel feeds (none configured) — no campaign clusters are claimed.

## Review queue
Empty (no live investigations in this workspace).

## Recommended actions
- Run supabase/rls_test.py against a real project with two accounts before presenting RLS as verified.
- Configure one reputation key (Safe Browsing) and one LLM key to turn not_checked/fallback states into live ones.
- Re-tune the two held-out misses (job registration fee wording, 'connection will be cut') only against a FRESH held-out set, not this one.

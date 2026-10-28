# CAVACH feature status table

See README.md for the same table in brief. This file is the detailed record.

Implemented: branding, routing, auth screen, component split, UUID + RPC transactional save, full-table persistence, graph rehydration, parent-ownership RLS, profile trigger, user_roles/is_admin, hardened Edge Functions (JWT/CORS/payload cap/rate limit/verified findings), enrich-url, generate-embeddings (real loop), fixed n8n (Respond/auth/retries/dedupe/review), pipeline raw-text fix (hash-only runs + redaction), Marathi/Hindi/Hinglish/Roman-Marathi detection, punycode/homoglyph, genuine-OTP guard, relative/new-number combination signals, reward/KYC/APK signals, suspicious-TLD signal, OCR/QR interfaces (unavailable without optional deps), React Flow graph, Recharts dashboard, i18n en/mr/hi, Marathi-first large-text + read-aloud, labelled scenario button, Evaluation page, Sentinel admin page + daily report generator, evidence-pack, incident workspace, CyberWatch opt-in, pre-payment check, Family Guard summary, counterfactual panel, DPDP privacy page, CI workflow, 153-case evaluation with held-out split, adversarial harness, FastAPI service.

Partial: RAG (local TF-IDF 7 docs, threshold 0.02 everywhere; pgvector/multilingual embeddings = deployment step), VoiceShield (upload validation + private bucket when configured; authenticity unavailable), threat intel (Safe Browsing via Edge Function when configured + consented; else not_checked), RLS verification (scripted, not run live), Edge Function live testing (not run — no project).

Simulated (labelled): presentation-scenario button only.

Planned: trained Indian-language classifier + calibration + model card, adversarial LLM-variant harness expansion, Share-to-CAVACH, browser extension, analyst review queue, privacy-safe campaign intelligence (min group size), screenshot-understanding signals (layout/logo-mismatch as signals only), on-device ONNX/WASM mode, synthetic-voice detector (only with cross-dataset EER evidence), graph DB (only if volume justifies), bank/telecom SDK spec (planned label), k6 load test, ZAP baseline against the deployed app (own app only), accessibility audit, backup/restore test, incident runbook for CAVACH itself.

## Self-check scores (2026-10-28, with evidence — not 9s by default)

- Detection quality: **8** — 153-case precision 1.000 / recall 0.982; held-out 0.900. Not 9: held-out recall is 0.80 (2 misses) and there is no real-world validation data.
- Real AI use: **6** — LLM explanation + embeddings are implemented (hardened Edge Functions, real embedding loop), but no live model ran in this workspace (no keys/project); RAG is local TF-IDF. Not 9 until a live LLM + pgvector run is recorded.
- Workflow reliability: **7** — n8n fixed (Respond nodes, header auth, retries, dedupe, review branch), pipeline 18/18. Not 9: n8n was not live-run against an instance.
- Threat graph: **8** — React Flow graph with evidence-bearing edges, cross-investigation linking, five-questions panel. Not 9: cloud rehydration of the graph is not live-tested.
- Security: **7** — parent-ownership RLS, profile trigger, hardened Edge Functions, secret scan clean, hash-only run files. Not 9: RLS test is scripted but not run live; Edge Functions not live-tested; ZAP baseline not run (no deployed URL — cut item, own app only).
- UI/UX: **8** — routed, i18n en/mr/hi, Marathi-first large-text + read-aloud, real data only, meaningful empty/error states. Not 9: 853 KB bundle (code-splitting not done), accessibility audit not run.
- Engineering quality: **8** — component split, CI workflow, TS/Python parity tests on audit cases, single-source migrations, FastAPI service. Not 9: parity is proven on audit cases, not on the full 153-case set.
- Evaluation rigour: **8** — 153 cases, held-out split, per-language, adversarial harness, RAG refusal checks. Not 9: all cases are synthetic templates; no real-world or trained-model comparison.
- Honesty: **9** — every number comes from a runnable script; held-out misses, RLS not_run, and not_checked states are all stated in the product and docs; the only simulated element is the labelled scenario button.

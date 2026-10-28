# CAVACH — One Shield. Every Threat.

> **2026-10-28 update — Supabase REMOVED by owner decision.** This build runs on **device storage only**: no Supabase URL, anon key, or cloud account is required, and no cloud save is attempted. Sign-in, cloud sync, storage-bucket upload, and Edge Functions are unavailable in this build — the UI says so honestly instead of faking them. The SQL files under `supabase/` (including `schema-fixed.sql`, the rerunnable version) are kept for a future re-connection only; they are **not** used by this build.

AI-powered cybersecurity, threat-intelligence and fraud-prevention platform for India (English, Marathi, Hindi, Hinglish, Roman Marathi). Modular shields (Message, Web, Payment, Voice-context, CyberWatch) with **cross-channel threat intelligence** as the differentiator: evidence is linked only on real shared indicators (confirmed / possible / unknown), never on a guess.

**Honesty first:** every number in this repo comes from a script you can run. Evaluation figures are always labelled *test-set result, not real-world accuracy*. Integrations that are not configured say *not checked* / *fallback* — never *live*.

## What actually runs today (verified 2026-10-28)

| Check | Result |
|---|---|
| Frontend production build | ✅ Pass (`npm run build`, Vite 6) |
| Frontend tests (Vitest, Python parity) | ✅ 7/7 (`npm test`) |
| Python audit scenarios | ✅ 18/18 exact band (`backend/evaluate.py`) |
| Python pipeline | ✅ 18/18 (`backend/pipeline.py --check`) |
| Labelled evaluation set | ✅ 153 cases, precision 1.000, recall 0.982, accuracy 0.987 — held-out 0.90 (`backend/eval_dataset.py`) |
| Adversarial harness | ✅ 9/9 robust, evasion 0.0 (`backend/adversarial.py`) |
| Sentinel daily report | ✅ Generated from real runs (`backend/sentinel.py` → `docs/sentinel-report.md`) |
| Secret scan (repo + built bundle) | ✅ No hits |
| RLS isolation (two accounts) | ⚠️ Scripted, **not yet run** — no live project in this workspace (`supabase/rls_test.py` → `supabase/rls_test_results.json` says `not_run`) |
| Safe Browsing / LLM / n8n live | ⚠️ Not configured → labelled `not_checked` / deterministic fallback / importable JSON |

## Quick start (Windows, one PowerShell window)

```powershell
cd frontend
npm install
npm run dev
# success line: Local: http://localhost:5173/
# hard refresh: Ctrl+Shift+R. Stop with Ctrl+C before restarting.
python backend\engine.py --check   # from the project root, if engine.py has a --check path; otherwise use evaluate.py
```

Python checks (from project root):
```bash
python3 backend/evaluate.py
python3 backend/pipeline.py --check
python3 backend/eval_dataset.py
python3 backend/adversarial.py
python3 backend/sentinel.py
```

## Architecture

Browser (React/TS + Vite + Tailwind, react-router, React Flow graph, Recharts dashboard, i18n en/mr/hi, Web Speech read-aloud)
→ Supabase (FUTURE re-connection only — inactive in this build; see banner above) (Auth, Postgres + RLS, Storage, pgvector) — single transactional RPC `create_investigation`
→ Edge Functions (LLM explanation — JWT, restricted CORS, 10 KB cap, 10/min rate limit, findings verified server-side; enrich-url — Safe Browsing, consent-checked, query-stripped; generate-embeddings — real loop, no fabricated vectors)
→ Python FastAPI service (`backend/api.py`) — the engine source of truth; the TS port is CI-proven against the same audit cases
→ n8n (importable JSON: user pipeline with Respond nodes, header auth, retries, dedupe, review branch; Sentinel daily workflow)

## The four audit misses — fixed and proven

1. **Marathi relative-payment + lookalike HDFC link** (`आई… ५००० रुपये पाठव… कोणाला सांगू नकोस https://pay-hdfc-secure.xyz`) — was 0, now **High concern (80)**.
2. **Hindi relative + new number** (`माँ, मेरा नया नंबर है… 2000 रुपये भेजो…`) — now **High concern (90)**.
3. **Genuine OTP notice** (`Your OTP is 482913. Do not share it… -HDFC Bank`) — was Suspicious, now **Low concern** (protective-language guard, incl. Hindi/Marathi).
4. **Punycode PayPal** (`xn--pypal-4ve.com`) — was 0, now **Suspicious (40: punycode + homoglyph lookalike)**; real paypal.com stays Low.

## Feature status (implemented / partial / simulated / planned)

- **Implemented:** CAVACH branding everywhere (name, logo SVG, favicon, title, package name, Safe Browsing clientId); routing + auth screen + component split; UUIDs + transactional RPC save + full-table persistence + graph rehydration; parent-ownership RLS + profile trigger + `user_roles`/`is_admin()`; hardened Edge Functions; fixed n8n workflows; Marathi/Hindi/Hinglish/Roman-Marathi detection; punycode/homoglyph; genuine-OTP guard; OCR/QR interfaces (optional deps, `unavailable` when missing); React Flow threat graph with evidence edges + cross-investigation linking; Recharts dashboard from real data; i18n + Marathi-first large-text mode + read-aloud; labelled presentation-scenario button; Evaluation + Sentinel admin pages; evidence-pack (print-to-PDF); incident workspace + checklist; CyberWatch (opt-in, own submissions only); pre-payment check; Family Guard summary; counterfactual / could-not-check panel; DPDP privacy page; CI workflow.
- **Partial:** RAG — local TF-IDF over 7 curated docs (incl. 2 Marathi), threshold 0.02 everywhere, cited grounded answers + refusal set; pgvector + multilingual embeddings are a deployment step (`generate-embeddings` is a real loop, not a stub, but needs an embedding API key and a live project). VoiceShield — upload with magic-byte/extension/size validation to a private bucket when configured; audio authenticity **unavailable** (no validated model). Threat intel — Safe Browsing via Edge Function when configured + consented; otherwise `not_checked`.
- **Simulated (labelled as such):** the presentation-scenario button only. No other simulated data exists in the product; earlier demo data was removed.
- **Planned (not built):** trained MuRIL/IndicBERT classifier + calibration, Share-to-CAVACH PWA/Telegram bot, browser extension, analyst review queue, on-device ONNX mode, synthetic-voice detector (ASVspoof/WaveFake evaluation required before any claim), graph DB, bank/telecom SDK (spec only). See `docs/status-table.md`.

## Known limitations (do not hide these in a demo)

- Held-out evaluation is 0.90: two low-signal English cases still miss (job-registration-fee wording; “connection will be cut”). They were **not** tuned away, to keep the held-out set independent.
- RLS isolation is scripted, not yet verified against a live project. Run `supabase/rls_test.py` with two accounts before claiming it.
- Edge Functions are written, not live-tested (no Deno/Supabase project in this workspace).
- No live reputation, LLM, or n8n instance is connected in this build — those features report their real state instead of pretending.
- A clean result never means safe. A flag never means a person is a criminal. Never promise fund recovery. No Maharashtra Cyber/Police endorsement is claimed.

## Setup (database + security)

See `docs/setup-guide.md` for: applying migrations 0001–0006 in order, creating the `artifacts` bucket, setting Edge Function secrets, running the two-account RLS test, and importing the n8n workflows. `supabase/schema.sql` is **generated** from the migrations — edit migrations, then regenerate.

## Origin (inspiration only)

A Maharashtra Cyber awareness message (28 Oct 2026: report financial fraud via 1930 / cybercrime.gov.in) and a notice about a cyberattack affecting The Developers Arena website (27 Oct 2026). No method, impact or detail of either incident is known or claimed here.

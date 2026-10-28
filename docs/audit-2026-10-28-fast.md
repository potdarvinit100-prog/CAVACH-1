# Fast audit — 2026-10-28 (Prasad brief, Phase 0, fast slice only)

Scope of this pass: re-run what exists, sweep for dead buttons and secrets,
and report honestly. No engine, UI, or schema code was rebuilt. One README
line was clarified (see Defects). This audit does NOT re-read every module
line by line; it verifies the runnable claims.

## Inventory (verified state, device-storage build)

- Detection engine: Python `backend/engine.py` + TypeScript port
  `frontend/src/engine.ts` — message / URL / payment / voice-context
  signals, fusion bands, Marathi / Hindi / Hinglish / Roman Marathi.
- ThreatFusion: confirmed / possible / unknown edges on shared indicators,
  evidence-bearing graph (React Flow), five-questions panel.
- Assistant: local TF-IDF retrieval over 7 curated docs (incl. 2 Marathi),
  cited answers, refusal set, injection-style query test in UI.
- CyberWatch: opt-in only, shows the user's own submissions; no external
  monitoring, no call recording, no private-conversation access.
- Incident workspace, evidence pack (print to PDF), pre-payment check,
  Family Guard summary, DPDP privacy page, Evaluation + Sentinel pages.
- n8n: importable JSON workflows (`n8n/`) + local pipeline fallback
  (`backend/pipeline.py`). Not live-run against an n8n instance.
- Supabase: REMOVED by owner decision — UI saves to device storage only.
  SQL under `supabase/` (incl. `schema-fixed.sql`) is kept for a future
  re-connection only and is not used by this build.

## Baseline results (all re-run 2026-10-28, this pass)

| Check | Result |
|---|---|
| Python audit scenarios (`backend/evaluate.py`) | 18/18 exact band; FP=0, FN=0 (test-set only) |
| Python pipeline (`backend/pipeline.py --check`) | 18/18 |
| Labelled evaluation set (`backend/eval_dataset.py`) | n=153, precision 1.000, recall 0.982, accuracy 0.987, FP=0, FN=2 |
| Held-out split (20 cases) | accuracy 0.90, recall 0.80 — 2 English misses, left untuned on purpose |
| Adversarial harness (`backend/adversarial.py`) | 9/9 robust, evasion 0.0 (synthetic variants only) |
| Frontend tests (`npm test`, Vitest) | 7/7 |
| Frontend production build (`npm run build`) | Pass, 8.01s, single-file 873 KB (gzip 268 KB) |
| Button sweep (13 buttons, App/pages/components) | All have real onClick actions — no dead buttons found |
| Secret sweep (key/token/JWT patterns, excl. scanner regex itself) | No hits; no `.env` file, only `.env.example` |
| Placeholder sweep (TODO/FIXME/coming soon/not implemented) | None; `placeholder=` hits are input hints only |

Test-set numbers are synthetic-template results, never real-world accuracy.

## Defects

1. (Known, kept) Held-out misses `eval-held-002`, `eval-held-009` — both
   low-signal English cases. Not tuned away, to keep the held-out set
   independent.
2. (Fixed this pass, docs only) README "Architecture" paragraph still
   described Supabase / Edge Functions as the live path. Clarified: it is
   the future re-connection path, inactive in this build.
3. (Accepted) 873 KB single-file bundle. Code-splitting is incompatible
   with `vite-plugin-singlefile`, which the build uses deliberately.

## Gap analysis vs the brief (what is NOT done, and why it is not fast)

- Supabase auth / persistence / RLS live test: OUT OF SCOPE — owner
  removed Supabase from this build. RLS script exists but is moot until
  a future re-connection; it must be run with two accounts before any
  cloud claim is made.
- Live LLM explanations: not configured, no key in this workspace.
  Deterministic fallback is labelled in the UI; never presented as a
  live model.
- Live RAG (pgvector + multilingual embeddings): deployment step only;
  current retrieval is local TF-IDF with a similarity threshold.
- Live reputation (Safe Browsing / VirusTotal): not configured →
  product reports `not_checked`, never `safe`.
- Live n8n run: importable JSON only; local pipeline is the working path.
- Voice authenticity: unavailable; VoiceShield is context assessment
  only and says so. No synthetic-voice claim is made.
- TS/Python parity: proven on audit cases only, not on the full
  153-case set. Fastest next step (not done here): export the 153 cases
  to a shared JSON dataset and run the TS engine against it.

## Implemented vs experimental (truthful list)

Implemented and re-verified this pass: deterministic detection + fusion,
evaluation + adversarial harnesses, pipeline, local RAG with citations,
device-storage investigations, graph, incident workspace, evidence pack,
importable n8n workflows, i18n (en/mr/hi), labelled scenario button.
Partial / fallback-labelled: LLM explanation, pgvector RAG, threat intel,
VoiceShield upload validation, cloud persistence (removed).
Simulated (labelled): the presentation-scenario button only.
Not built: trained classifier, browser extension, Share-to-CAVACH,
analyst queue, on-device ONNX mode, synthetic-voice detector, graph DB.

## Decisions (fast-only scope)

- Nothing was rebuilt: the existing engine already contains the brief's
  fast wins (boundary-aware matching, punycode/homoglyph, genuine-OTP
  guard, tiered correlation, labelled fallbacks).
- No Supabase, LLM key, reputation key, or n8n instance was introduced:
  each needs credentials or a server and is therefore not a fast feature.
- No claim in this document exceeds what the scripts above printed.

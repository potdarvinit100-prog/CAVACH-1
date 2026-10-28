# Implementation checklist — inspected from the uploaded ZIP (identical to the workspace project)

Inspection date: 2026-10-28. ZIP contents verified identical to
`workspace/hackathons/ai-cyber-guardian/` except build artefacts
(`__pycache__`, `tsconfig.tsbuildinfo`). Tests and build both passed before
any change: Python evaluation 8/8 on exact band (test-set only), frontend
production build passed.

## Genuinely implemented
- Deterministic Python engine (`backend/engine.py`) + TypeScript port
  (`frontend/src/engine.ts`): message/URL/payment/voice-context signals, fusion
  bands, Marathi + English next steps.
- React + TS + Vite + Tailwind UI: landing, overview, investigate, graph,
  CyberWatch, assistant, incident, settings. Real actions for investigation,
  graph, checklist, consent toggles, local delete.
- Supabase schema + RLS (`supabase/schema.sql`), `.env.example` files, video
  analysis, README architecture docs.

## Partially implemented
- Supabase: schema + client + sign-up/sign-in code path exist, but
  investigations are stored on device only. Cloud persistence, ownership
  checks in code, and RLS isolation tests were not runnable without a project.
- Assistant: keyword-mapped canned answers with sources, not retrieval.
- CyberWatch: timeline shows submitted investigations only; no event
  ingestion from supported sources, no persistent alert store in cloud.
- VoiceShield: context assessment only; no file upload, validation, or
  metadata handling at all.
- ThreatFusion: bands + confirmed/possible/unknown edges, but findings lack
  id / method / severity / confidence / timestamp / provenance, and the
  "possible" edge fires on any authority+payment pair, however unrelated.

## UI-only / missing
- LLM explanation, RAG retrieval + embeddings, n8n workflow, threat-intel
  enrichment, YARA/ClamAV, admin/system-health view, file-upload restrictions,
  loading + error states on investigation submission.

## Bugs and weaknesses found (fixed in this upgrade unless noted)
1. Substring matching: `fir` matches "first", `pin` matches "shipping",
   bare `pin`/`password` over-flag. Fix: token-boundary regex + phrase-level
   credential patterns.
2. URL handling: no credential-in-URL detection, no punycode decoding, no
   query-token redaction in evidence. Fix: normalisation + redaction.
3. Score inflation: the same signal counted once per artifact (digital-arrest
   case scored 210). Fix: unique-signal scoring + combination bonus, capped
   by band thresholds, never presented as a probability.
4. Duplicated logic: Python and TypeScript engines can drift. Fix: shared
   finding schema + same signal table + same test cases in both; TS tests
   still to be added by the team (noted as remaining work).
5. Credential paste risk: no guard against a user pasting an OTP/PIN.
   Fix: submission guard that refuses and redacts credential-like input.
6. No secret scan was run. Fix: scan in QA below; no real secrets were found
   (only `.env.example` placeholders).

## What this upgrade adds (in priority order)
1. Engine v2: token boundaries, URL normalisation, extraction separated
   from classification, structured findings, confirmed/probable/weak/unknown
   correlation, adversarial + benign test cases.
2. Supabase versioned migrations + store abstraction (cloud when signed in
   and configured, explicit offline device mode otherwise) + RLS test guide.
3. LLM Edge Function with JSON-schema validation, timeout, rejection of
   unsupported claims, and a deterministic fallback that is labelled as such.
4. RAG: curated documents, chunking, local TF-IDF retrieval with threshold,
   source attribution, prompt-injection guard; pgvector + embedding provider
   as the configured path (see `supabase/functions/generate-embeddings/`).
5. n8n importable workflow + local pipeline fallback (`backend/pipeline.py`)
   that mirrors the same steps.
6. Threat-intel clients (Safe Browsing, VirusTotal) — server-side only,
   consent-gated, timeouts, query stripping, `not_checked` when unconfigured.
7. VoiceShield upload validation + metadata (WAV via stdlib) + context
   assessment; audio authenticity explicitly unavailable, never fabricated.
8. UI: loading/error/empty states, credential-paste guard, SVG threat graph,
   system-health section, auth screen with explicit offline mode.
9. QA report + new ZIP.

## Remaining work that still needs external credentials (honest list)
- A Supabase project (URL + anon key; service-role key server-side only) to
  run cloud persistence and RLS isolation tests end to end.
- An LLM provider key + model name for live explanations and embeddings.
- Safe Browsing and/or VirusTotal keys for live reputation enrichment.
- An n8n instance to import and run the workflow (local pipeline works
  without it).

## Reconciliation note on "demo" wording
Vinit's earlier instruction was: no demo, reliable platform only. This master
prompt now asks for a clearly labelled fallback when credentials are missing
and a labelled presentation scenario. Latest instruction governs, applied
narrowly: the product default is real user data; any fallback (deterministic
explanation, local retrieval, local pipeline, offline mode) is labelled as a
fallback in the UI and in code, and is never presented as a live model,
live reputation result, or real victim report.

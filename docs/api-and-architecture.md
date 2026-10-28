# AI Cyber Guardian — API and architecture documentation

## Architecture (updated)

```
User submission (message / URL / call note / audio file metadata)
  → Frontend guard: credential-paste rejection, file type/size validation
  → Deterministic engine v2 (frontend port + Python original, same schema)
      extraction → classification → fusion (unique-signal scoring)
  → Optional: LLM explanation via Supabase Edge Function `analyze-explanation`
      (JSON-schema validation, unsafe-claim rejection, 20s timeout,
       deterministic fallback labelled as such)
  → Optional: RAG retrieval
      local TF-IDF over curated chunks (frontend + backend), threshold 0.02
      pgvector + embeddings when configured (Edge Function generate-embeddings)
  → Optional: threat-intel enrichment (backend clients, server-side only,
      consent-gated, query-stripped, 10s timeout, not_checked without keys)
  → Persistence: Supabase (cloud, RLS) when signed in + configured,
      otherwise explicit offline device storage
  → UI: investigation, SVG threat graph, CyberWatch, assistant, incident pack
  → Automation: n8n workflow (importable) OR local pipeline fallback
      (backend/pipeline.py) — same steps, same validation
```

## Finding schema (every module, Python and TypeScript)

| Field | Meaning |
|---|---|
| id | `f-001`, … per investigation (fusion combo: `f-combo`) |
| artifact_id | The submitted artifact this finding came from (`fusion` for combos) |
| method | `rule:keyword`, `rule:domain`, `rule:combination` |
| signal | e.g. `authority_impersonation`, `lookalike_domain`, `url_with_credentials` |
| weight | Signal weight used in the unique-signal score |
| evidence | Redacted evidence (domains only for URLs; UPI suffix only; no query tokens) |
| indicator_type | `narrative`, `domain`, `url`, `upi_suffix`, `amount` |
| severity | `low`, `medium`, `high`, `critical` |
| confidence | `low`, `medium`, `high` (rule confidence, not a probability) |
| timestamp | ISO-8601 UTC when the finding was produced |
| provenance | `deterministic rule (no external check)` unless an enrichment result says otherwise |

## Correlation tiers

- **confirmed**: exact normalised domain shared by two or more artifacts.
- **probable**: shared lookalike brand + impersonation/payment narrative.
- **weak**: token Jaccard similarity ≥ 0.35 between message texts.
- **unknown**: no tier met its threshold. Generic wording alone never upgrades a band.

## API surface (what exists, what does not)

- No public REST API is exposed by this repo. The frontend talks to
  Supabase (Auth, PostgREST, Edge Functions) with the anon key + user JWT.
- Edge Function `analyze-explanation`: POST `{ findings, band, language? }`
  → `{ summary, relationship_explanation, next_steps, uncertainty,
  missing_evidence, source }`. Returns the deterministic fallback with an
  `error` field when unconfigured, timed out, or validation-failed.
- Edge Function `generate-embeddings`: deployment step, not a user API.
  See its file header for the required steps.
- n8n webhook `acg-submit`: POST `{ message?, url?, voice_note?,
  consent_enrichment?, owner_id? }`. Must be protected (header auth /
  allow-list) before activation. See `n8n/README.md`.
- Local pipeline: `python3 backend/pipeline.py --message "..." --url "..."`.
  Writes a result JSON per submission hash to `backend/runs/`.

## Security notes

- Service-role key: server-side only (n8n credential, Edge Function env).
  Never in frontend code, never in the repo, never in a ZIP.
- OTP/PIN/password values: refused at submission (frontend guard +
  backend pipeline + n8n validation). They are never stored.
- Private files/URLs: never uploaded to VirusTotal / Safe Browsing without
  explicit enrichment consent, and URLs are cleaned of query/fragment first.
- Retrieved documents: treated as data, never as instructions. Chunks
  containing instruction-override phrases are excluded from RAG results.
- OWASP references used for design: ASVS (authentication, session,
  input validation, storage) and Top 10 (broken access control → RLS,
  sensitive data exposure → no secrets in client, injection → parameterised
  Supabase queries, no string-built SQL in app code).

# CAVACH — frontend

> This README is the frontend note. The full project README is at the project root (`../README.md`).

Real React + TypeScript + Vite + Tailwind app. Investigations a user submits are
real user data, analysed by the deterministic engine in `src/engine.ts` (a port of
`../backend/engine.py`) and stored on the device until Supabase is connected.
No sample investigations, no invented events, no invented results anywhere in
the UI.

## Run it

Confirm the folder you are in contains `package.json` before running anything.
If it does not, move into the frontend folder first.

```bash
cd cavach/frontend
npm install
npm run dev
```

Success line to look for: `Local: http://localhost:5173/` — open that address,
not a different port. To stop the server, press Ctrl+C in that same window.

Production build (also type-checks the app):

```bash
npm run build
```

## Supabase (real accounts + cloud storage)

1. Create a project at supabase.com.
2. In Supabase SQL Editor, run `../supabase/schema.sql` (tables + row-level
   security). Verify isolation with two separate accounts before relying on it.
3. Copy `.env.example` to `.env` and fill in your project URL and anon key.
   The anon key is the publishable client key; the service-role key must never
   go in this folder or in frontend code.
4. Rebuild. `src/supabase.ts` exports a client only when both variables are
   present; otherwise it exports null and the UI keeps working on device
   storage without pretending cloud sync happened.

`.env.example`:

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## What is real in this build, and what is not yet

Real: message/URL/call-note analysis, evidence graph from shared indicators,
investigation list, CyberWatch timeline from submitted investigations only,
incident checklist, curated assistant answers with sources, device storage,
account sign-up/sign-in code path (requires Supabase, see above).

Not yet: Supabase persistence until a project is connected, LLM explanations,
RAG over pgvector, Safe Browsing / VirusTotal enrichment, n8n workflow. Each of
those is labelled "not configured" in the product when absent — never faked.

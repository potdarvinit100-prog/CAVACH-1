# UI + one AI model — fast update, 2026-10-28

## One AI model added: Pollinations (keyless public endpoint, open model)

- File: `frontend/src/ai.ts` — `explainWithFreeModel()`.
- Why this one: it is the fastest real model that needs no API key, so
  there is no secret to leak from the browser bundle. Verified reachable
  (test call returned OK) before wiring it in.
- Privacy gate: off by default. The user must tick "I agree to send
  redacted signals" before anything is sent. The payload is only the
  band, the internal ranking score, and signal names with
  severity/confidence — never the raw message, link, phone number,
  amount, or any credential.
- Authority: model text is display-only and labelled "not verified".
  The engine band, score, findings, and next step never change.
- Failure: 20s timeout, HTTP errors, and empty answers all fall back
  to the deterministic explanation with a visible reason. If the
  endpoint ever blocks browser requests (CORS), the same fallback
  applies — nothing is faked.
- Honest limits: no SLA, no data-handling guarantee from the free
  endpoint — which is exactly why it is opt-in and redacted-only.

## UI made professional (no logic changed)

- `index.css` rewritten as a design system: sticky blurred topbar,
  active-page nav pills, "Device only · No sign-in" mode pill, wider
  1080px page, card hover lift, tinted warning/error boxes, result
  panels with an accent edge, flex dashboard rows, AI box styling,
  focus rings, mobile layout (rows stack under 720px).
- `App.tsx`: nav uses NavLink so the current page is highlighted.
- `pages.tsx`: dashboard empty state now has a "Run your first
  investigation" button (the old screen dead-ended); dashboard rows
  use a real card layout instead of a floated button; form fields,
  result, answer, and pre-payment panels use classes instead of
  scattered inline styles. All handlers, engine calls, and storage
  behaviour are unchanged.
- Checkbox width bug fixed: checkboxes no longer stretch full-width.

## Verified

- `npm test`: 7/7. `npm run build`: passes (single-file 878 KB).
- Python engine checks were already re-verified earlier today
  (18/18 audit, 18/18 pipeline, 153-case set) and are untouched by
  this change — no backend file was modified.

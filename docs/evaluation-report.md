# CAVACH — evaluation report (test-set only)

Date: 2026-10-28. Engine: deterministic v2 (Python + TypeScript port, same
signal table). These numbers describe labelled test sets below. They are
NOT real-world detection rates and must never be quoted as such.

## Audit scenarios (18 cases, backend/scenarios.json)
Run: `python3 backend/evaluate.py` and `python3 backend/pipeline.py --check`.
- Exact-band accuracy: 18/18 (1.00); binary precision 1.00, recall 1.00 (TP 8, FP 0, TN 10, FN 0).
- Includes the four reproduced audit misses, now fixed: Marathi relative-payment (High),
  Hindi relative + new number (High), genuine OTP notice (Low), punycode PayPal (Suspicious).

## Labelled evaluation set (153 cases, backend/eval_dataset.py)
Template-generated labelled cases (synthetic, not real victim messages) in
en/mr/hi/Hinglish/Roman-Marathi: malicious, benign, tricky-benign.
- Overall: n=153, precision 1.000, recall 0.982, accuracy 0.987.
- Base (tuned templates + surface variants): n=133, precision 1.000, recall 1.000.
- Held-out (written after the rules were frozen for this run, NOT used for tuning):
  n=20, precision 1.000, recall 0.800, accuracy 0.900.
  Errors (reported, not tuned away): job-registration-fee wording and
  "connection will be cut" — both low-signal English cases. Fixing them
  against this same held-out set would destroy its independence; they are
  the next tuning round's targets, against a fresh held-out set.
- Per language: en 0.972, hi 1.000, hinglish 1.000, mr 1.000, roman-marathi 1.000 accuracy.
- Full machine-readable report: `backend/evaluation_report.json` (also copied to `frontend/src/` for the in-app Evaluation page).

## Adversarial harness (backend/adversarial.py)
Spacing / homoglyph / case variants of 3 scam templates (synthetic):
n=9, robust 9, evasion rate 0.0. The homoglyph narrative gap found in the
first run was fixed by matching against a homoglyph-normalised copy.

## RAG retrieval
Local TF-IDF over 7 curated docs, threshold 0.02 (one value everywhere).
Marathi query "फसवणूक झाल्यास काय करावे" retrieves the Marathi reporting
guidance (score 0.115). Injection-style queries return no passage or a
refusal. No "must refuse" hit-rate table is claimed beyond these checks;
a full RAG question set is a next step (see docs/status-table.md).

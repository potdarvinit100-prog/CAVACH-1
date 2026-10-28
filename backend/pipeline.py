"""Local pipeline fallback — mirrors the n8n workflow steps in code.

Steps: validate -> normalise -> detect (engine v2) -> enrichment
(consent-gated, not_checked without keys) -> fuse -> RAG retrieval ->
deterministic explanation -> save result JSON -> log.
Run: python3 backend/pipeline.py --message "..." --url "https://..."
     python3 backend/pipeline.py --check   (runs the test scenarios)
Duplicate protection: the SHA-256 of the normalised artifacts is stored
with each run; a repeat submission with the same hash is flagged as a
duplicate instead of creating a second investigation silently.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import fuse, extract_indicators  # noqa: E402
from rag_ingest import retrieve, THRESHOLD  # noqa: E402
from threat_intel import check_safe_browsing, check_virustotal  # noqa: E402

BASE = Path(__file__).resolve().parent
RUNS = BASE / "runs"
RUNS.mkdir(exist_ok=True)


def _hash(artifacts: list[dict]) -> str:
    norm = json.dumps(artifacts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(norm.encode()).hexdigest()


def run_pipeline(artifacts: list[dict], consent_enrichment: bool = False) -> dict:
    # 1. Validate: empty submissions are rejected. Credential-looking
    # values are NOT stored raw and do NOT block analysis: the digit
    # values are redacted before any storage, and the assessment runs on
    # the submitted text (so a genuine "do not share" OTP notice can be
    # correctly recognised as protective instead of being rejected).
    # Raw digits never reach the saved run file (see step 5: only a hash
    # of the redacted artifacts is saved, never the text itself).
    from engine import redact_for_storage
    redacted_artifacts = []
    credential_redacted = False
    for a in artifacts:
        redacted, was = redact_for_storage(a.get("text", ""))
        credential_redacted = credential_redacted or was
        redacted_artifacts.append({**a, "text": redacted})
    if not artifacts or not any(a.get("text", "").strip() for a in artifacts):
        return {"status": "rejected", "reason": "No artifact text supplied."}
    # 2. Normalise + detect + fuse (on the original text for correct
    # genuine-notice handling; storage uses the redacted copy only).
    assessment = fuse(artifacts)
    # 3. Enrichment (consent-gated).
    enrichment = []
    for a in artifacts:
        for url in extract_indicators(a.get("text", ""))["urls"]:
            enrichment.append({"url_domain": url.split("/")[2] if "://" in url else url,
                               "safe_browsing": check_safe_browsing(url, consent_enrichment),
                               "virustotal": check_virustotal(url, consent_enrichment)})
    # 4. RAG retrieval over the curated base.
    chunks_path = BASE / "knowledge_chunks.json"
    chunks = json.loads(chunks_path.read_text(encoding="utf-8")) if chunks_path.exists() else []
    query = " ".join(a.get("text", "") for a in artifacts)
    rag = retrieve(query, chunks) if chunks else {"results": [], "method": "local-tfidf", "threshold": THRESHOLD}
    # 5. Duplicate protection.
    digest = _hash(redacted_artifacts)
    duplicate = any((RUNS / f"{digest}.json").exists() for _ in [0])
    result = {"status": "succeeded", "duplicate_of_previous_run": duplicate,
              "credential_digits_redacted": credential_redacted,
              "note": "Saved run contains no raw artifact text, only a hash of the redacted artifacts." ,
              "hash": digest, "assessment": assessment,
              "enrichment": enrichment, "rag": rag,
              "pipeline": "local-fallback (mirrors n8n/ai-cyber-guardian-pipeline.json)"}
    (RUNS / f"{digest}.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--voice-note", default="")
    ap.add_argument("--consent-enrichment", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        scenarios = json.loads((BASE / "scenarios.json").read_text(encoding="utf-8"))
        ok = 0
        for sc in scenarios:
            r = run_pipeline(sc["artifacts"])
            got = r["assessment"]["band"] if r["status"] == "succeeded" else r["status"]
            passed = got == sc["expected_band"]
            ok += passed
            print(f"{'PASS' if passed else 'FAIL'} {sc['id']} expected={sc['expected_band']} got={got}")
        print(f"Pipeline check: {ok}/{len(scenarios)}")
        return 0 if ok == len(scenarios) else 1
    arts = []
    if args.message:
        arts.append({"id": "msg-1", "type": "message", "text": args.message})
    if args.url:
        arts.append({"id": "link-1", "type": "url", "text": args.url})
    if args.voice_note:
        arts.append({"id": "voice-1", "type": "voice_context", "text": args.voice_note})
    print(json.dumps(run_pipeline(arts, args.consent_enrichment), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

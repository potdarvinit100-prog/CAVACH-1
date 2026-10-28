"""CAVACH detection API (FastAPI) — the single engine source of truth.

Run:  uvicorn api:app --port 8000   (from backend/)
The frontend uses its TypeScript port only for offline use; CI parity
tests (frontend/src/engine.test.ts vs backend/scenarios.json) prove the
port matches Python on the audit cases. For a deployed product, point
the frontend at this API instead of the local port.
No raw user text is logged: only a SHA-256 of the redacted text.
Requires: pip install fastapi uvicorn pydantic
"""
from __future__ import annotations
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import fuse, extract_indicators, redact_for_storage  # noqa: E402

try:
    from fastapi import FastAPI, HTTPException  # type: ignore
    from pydantic import BaseModel, Field  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install: pip install fastapi uvicorn pydantic") from exc

app = FastAPI(title="CAVACH detection API", version="2.0.0")

class ArtifactIn(BaseModel):
    id: str
    type: str = "message"
    text: str = Field(..., max_length=10000)

class AnalyzeIn(BaseModel):
    artifacts: list[ArtifactIn] = Field(..., max_length=20)

@app.get("/health")
def health():
    return {"status": "ok", "service": "cavach-detection", "engine": "python-v2"}

@app.post("/analyze")
def analyze(payload: AnalyzeIn):
    arts = []
    for a in payload.artifacts:
        redacted, _ = redact_for_storage(a.text)
        arts.append({"id": a.id, "type": a.type, "text": a.text})
        # Log only a hash of the redacted text, never the text itself.
        _hash = hashlib.sha256(redacted.encode()).hexdigest()
        print(f"[analyze] artifact={a.id} type={a.type} hash={_hash[:16]}")
    result = fuse(arts)
    # Do not echo raw text back in the response body either.
    for a in result.get("artifacts", []):
        a.pop("text", None)
    return result

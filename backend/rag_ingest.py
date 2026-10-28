"""RAG ingestion + retrieval for AI Cyber Guardian.

Ingestion: read knowledge/*.md, normalise, chunk (800 chars, 100 overlap),
write backend/knowledge_chunks.json and frontend/src/knowledge_chunks.json.
Embeddings: when LLM_API_KEY is configured, the generate-embeddings Edge
Function fills Supabase pgvector. Without it, retrieval below uses TF-IDF
over the same chunks — real retrieval, labelled as local, never a fake
embedding score.

Retrieval guard: retrieved text is DATA, never instructions. Any chunk
containing an instruction-override phrase is excluded and flagged.
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CHUNK_SIZE = 800
OVERLAP = 100
# Calibrated on the 5-document curated base: TF-IDF scores for a good
# match land around 0.06–0.09, so 0.15 returned nothing. Threshold is a
# property of this small corpus, not a universal relevance law.
THRESHOLD = 0.02
STOPWORDS = {"how", "do", "does", "did", "i", "you", "to", "on", "in", "a", "an", "the", "is", "are", "what", "why", "should", "can", "me", "my"}
INJECTION_PATTERNS = [
    "ignore previous instructions", "ignore all previous instructions",
    "disregard your instructions", "you are now", "system prompt",
    "send money to", "share your otp",
]


def chunk_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE].strip())
        if start + CHUNK_SIZE >= len(text):
            break
        start += CHUNK_SIZE - OVERLAP
    return [c for c in chunks if c]


def ingest() -> list[dict]:
    out = []
    for path in sorted((BASE / "knowledge").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        lines = raw.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else path.stem
        source = next((l.replace("Source:", "").strip() for l in lines if l.startswith("Source:")), "Curated guidance")
        body = "\n".join(l for l in lines if not l.startswith("# ") and not l.startswith("Source:") and not l.startswith("Applies to:")).strip()
        for i, chunk in enumerate(chunk_text(body)):
            out.append({"id": f"{path.stem}-{i}", "title": title, "source": source,
                        "file": path.name, "chunk_index": i, "text": chunk})
    return out


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w\u0900-\u097f]+", text.lower())


def retrieve(query: str, chunks: list[dict], top_k: int = 3) -> dict:
    """TF-IDF retrieval with a relevance threshold. Returns passages + scores."""
    if not query.strip():
        return {"results": [], "method": "local-tfidf", "threshold": THRESHOLD}
    docs = [_tokens(c["text"]) for c in chunks]
    df = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    n = max(len(docs), 1)
    q = [t for t in _tokens(query) if t not in STOPWORDS]
    if not q:
        return {"results": [], "method": "local-tfidf", "threshold": THRESHOLD}
    scored = []
    for chunk, doc in zip(chunks, docs):
        tf = Counter(doc)
        score = 0.0
        for t in q:
            if tf[t]:
                score += (tf[t] / len(doc)) * math.log((n + 1) / (df[t] + 1))
        # Small bonus for title/source match.
        if any(t in chunk["title"].lower() for t in q):
            score += 0.05
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, chunk in scored[:top_k]:
        if score < THRESHOLD:
            continue
        flagged = any(p in chunk["text"].lower() for p in INJECTION_PATTERNS)
        if flagged:
            continue
        results.append({"id": chunk["id"], "title": chunk["title"], "source": chunk["source"],
                        "text": chunk["text"], "score": round(score, 4)})
    return {"results": results, "method": "local-tfidf", "threshold": THRESHOLD}


def main() -> int:
    if "--retrieve" in sys.argv:
        query = " ".join(sys.argv[sys.argv.index("--retrieve") + 1:])
        chunks = json.loads((BASE / "backend/knowledge_chunks.json").read_text(encoding="utf-8"))
        print(json.dumps(retrieve(query, chunks), indent=2, ensure_ascii=False))
        return 0
    chunks = ingest()
    payload = json.dumps(chunks, indent=2, ensure_ascii=False)
    (BASE / "backend/knowledge_chunks.json").write_text(payload, encoding="utf-8")
    (BASE / "frontend/src/knowledge_chunks.json").write_text(payload, encoding="utf-8")
    print(f"Ingested {len(chunks)} chunks from {(BASE / 'knowledge').__str__()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

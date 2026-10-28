// Local RAG retrieval over the curated chunks (same corpus as backend).
// Local RAG retrieval over the curated chunks (same corpus as backend).
// TF-IDF, threshold 0.02 — ONE value everywhere (frontend, backend
// rag_ingest.py, pipeline fallback). When pgvector + embeddings are
// configured, the server path replaces this; until then the method is
// labelled local-tfidf, never 'AI answer'.
import chunks from './knowledge_chunks.json'

interface Chunk { id: string; title: string; source: string; text: string }

const STOPWORDS = new Set(['how', 'do', 'does', 'did', 'i', 'you', 'to', 'on', 'in', 'a', 'an', 'the', 'is', 'are', 'what', 'why', 'should', 'can', 'me', 'my'])

function tokens(text: string): string[] {
  return (text.toLowerCase().match(/[\w\u0900-\u097f]+/g) ?? [])
}

export function retrieve(query: string, topK = 3): Array<Chunk & { score: number }> {
  const q = tokens(query).filter((t) => !STOPWORDS.has(t))
  if (q.length === 0) return []
  const docs = (chunks as Chunk[]).map((c) => tokens(c.text))
  const df = new Map<string, number>()
  for (const d of docs) for (const t of new Set(d)) df.set(t, (df.get(t) ?? 0) + 1)
  const n = Math.max(docs.length, 1)
  const scored = (chunks as Chunk[]).map((chunk, i) => {
    const doc = docs[i]
    const tf = new Map<string, number>()
    for (const t of doc) tf.set(t, (tf.get(t) ?? 0) + 1)
    let score = 0
    for (const t of q) {
      if (tf.has(t)) score += (tf.get(t)! / doc.length) * Math.log((n + 1) / ((df.get(t) ?? 0) + 1))
    }
    if (q.some((t) => chunk.title.toLowerCase().includes(t))) score += 0.05
    return { ...chunk, score }
  })
  return scored.filter((s) => s.score >= 0.02).sort((a, b) => b.score - a.score).slice(0, topK)
}

export function composeAnswer(query: string): { answer: string; sources: Array<Chunk & { score: number }>; method: string } {
  const results = retrieve(query, 3);
  if (!results.length) return { answer: "No reliable source found in the curated guidance for this question. I will not guess. For a suspected fraud, call 1930 or report at cybercrime.gov.in.", sources: [], method: "local-tfidf (no answer)" };
  const parts = results.map((c, i) => `[${i + 1}] ${c.text} (Source: ${c.source})`);
  return { answer: `Based on the retrieved guidance:\n\n${parts.join("\n\n")}`, sources: results, method: "local-tfidf (grounded in retrieved passages only)" };
}
// Prompt-injection guard: chunks containing override phrases are never used.
export function safeRetrieve(query: string) {
  const OVERRIDE = ["ignore previous", "disregard instructions", "you are now"];
  return retrieve(query).filter((c) => !OVERRIDE.some((p) => c.text.toLowerCase().includes(p)));
}

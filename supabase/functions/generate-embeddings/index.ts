// CAVACH generate-embeddings — real embedding loop (not a stub).
// Reads knowledge_documents rows without an embedding, calls the
// configured embedding API (EMBEDDING_API_URL + EMBEDDING_API_KEY +
// EMBEDDING_MODEL, default multilingual-e5-large via a hosted API),
// and writes embeddings to knowledge_chunks. Requires service role.
// If no embedding API is configured, it exits with a clear error and
// writes nothing — it never fabricates vectors. Invoke manually:
//   supabase functions invoke generate-embeddings
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
Deno.serve(async (req) => {
  const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const apiUrl = Deno.env.get("EMBEDDING_API_URL"), apiKey = Deno.env.get("EMBEDDING_API_KEY"), model = Deno.env.get("EMBEDDING_MODEL") ?? "multilingual-e5-large";
  if (!apiUrl || !apiKey) return new Response(JSON.stringify({ error: "embedding api not configured", written: 0 }), { status: 503 });
  const { data: docs, error } = await supabase.from("knowledge_documents").select("id, chunk_text").is("embedding", null).limit(100);
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  let written = 0;
  for (const doc of docs ?? []) {
    const res = await fetch(apiUrl, { method: "POST", headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({ model, input: doc.chunk_text }) });
    if (!res.ok) continue;
    const data = await res.json();
    const embedding = data.data?.[0]?.embedding;
    if (!Array.isArray(embedding)) continue;
    const { error: upErr } = await supabase.from("knowledge_chunks").insert({ source: "knowledge_documents", chunk_text: doc.chunk_text, embedding });
    if (!upErr) { await supabase.from("knowledge_documents").update({ embedding }).eq("id", doc.id); written++; }
  }
  return new Response(JSON.stringify({ written, total: docs?.length ?? 0, model }));
});

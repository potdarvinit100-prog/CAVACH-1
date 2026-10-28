-- CAVACH 0005: pgvector for RAG embeddings (deployment step, not a stub claim).
-- Requires pgvector extension in the Supabase project. Embedding dimension
-- must match the embedding model configured in generate-embeddings
-- (default below assumes 1536; change both together if you switch models).
create extension if not exists vector;
create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  source text not null, chunk_text text not null,
  embedding vector(1536), created_at timestamptz not null default now()
);
create index if not exists knowledge_chunks_embedding_idx
  on public.knowledge_chunks using hnsw (embedding vector_cosine_ops);
alter table public.knowledge_chunks enable row level security;
create policy "public read chunks" on public.knowledge_chunks for select using (true);

// LLM explanation client.
// Calls the Supabase Edge Function `analyze-explanation` when Supabase is
// configured. Otherwise returns null and the caller uses the deterministic
// explanation from the engine, labelled as such. The model never runs in
// the browser and no key is ever present in this file.
import { supabase } from './supabase'
import type { Finding } from './engine'

export interface LlmExplanation {
  summary: string
  relationship_explanation: string
  next_steps: string[]
  uncertainty: string
  missing_evidence: string[]
  source: string
  error?: string
}

export async function explainWithLlm(findings: Finding[], band: string, textLength = 0): Promise<LlmExplanation | null> {
  if (!supabase) return null
  // The hardened Edge Function verifies every signal + weight and that
  // the band matches the recomputed score — so weights must be sent.
  const { data, error } = await supabase.functions.invoke('analyze-explanation', {
    body: { findings: findings.map((f) => ({ signal: f.signal, weight: f.weight, evidence: f.evidence, severity: f.severity })), band, text_length: textLength },
  })
  if (error) return null
  const d = data as { band: string; score: number; explanation: string; source: string }
  if (typeof d?.explanation !== 'string') return null
  return { summary: d.explanation, relationship_explanation: '', next_steps: [], uncertainty: 'Bands are triage labels, not probabilities.', missing_evidence: [], source: d.source }
}

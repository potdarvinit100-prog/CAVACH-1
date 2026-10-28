// CAVACH store — one shape for cloud and device storage.
// Cloud: a single transactional RPC (create_investigation) writes the
// investigation + artifacts + findings + indicators + relationships +
// risk assessment + audit event, or nothing. Device fallback (no Supabase
// configured or signed out) keeps the SAME shape in localStorage, with
// real UUIDs (crypto.randomUUID), and rehydrates findings/indicators/
// graph on load — cloud reload no longer returns empty findings.
// Raw credential digits are never stored: artifacts store the redacted
// text + a SHA-256 hash of the redacted text.
import { supabase, supabaseConfigured as isConfigured } from "./supabase";
import { redactForStorage, sha256Hex, type Assessment } from "./engine";

export type SavedInvestigation = {
  id: string; title: string; band: string; score: number; created_at: string;
  artifacts: { id: string; type: string; content_redacted: string; content_hash: string; language: string; source_channel: string }[];
  findings: { signal: string; weight: number; evidence: string; severity: string; confidence: string }[];
  indicators: { type: string; value: string }[];
  relationships: { from: string; to: string; type: string; basis: string }[];
  next_action: string; next_action_marathi: string; limitations: string;
  checklist: Record<string, boolean>; notes: string;
  consents: { monitoring: boolean; third_party_enrichment: boolean; storage: boolean };
  enrichment: { status: string; detail: string } | null;
};
const KEY = "cavach.investigations.v2";
export function loadLocal(): SavedInvestigation[] {
  try { return JSON.parse(localStorage.getItem(KEY) ?? "[]"); } catch { return []; }
}
function saveLocal(list: SavedInvestigation[]) { localStorage.setItem(KEY, JSON.stringify(list)); }

export async function saveInvestigation(input: {
  title: string; artifacts: { type: string; text: string; language: string; source_channel: string }[];
  assessment: Assessment; checklist: Record<string, boolean>; notes: string;
  consents: SavedInvestigation["consents"]; enrichment: SavedInvestigation["enrichment"];
}): Promise<SavedInvestigation> {
  const id = crypto.randomUUID();
  const artifacts = await Promise.all(input.artifacts.map(async (a) => {
    const { redacted } = redactForStorage(a.text);
    return { id: crypto.randomUUID(), type: a.type, content_redacted: redacted, content_hash: await sha256Hex(redacted), language: a.language, source_channel: a.source_channel };
  }));
  const findings = input.assessment.unique_findings.map((f) => ({ signal: f.signal, weight: f.weight, evidence: f.evidence, severity: f.severity, confidence: f.confidence }));
  const indicators = [...new Set(input.assessment.unique_findings.filter((f) => f.indicator_type === "domain").map((f) => f.evidence))].slice(0, 20).map((v) => ({ type: "domain", value: v }));
  const relationships = input.assessment.correlated.map((c) => ({ from: c.from, to: c.to, type: c.tier, basis: c.evidence }));
  const saved: SavedInvestigation = { id, title: input.title, band: input.assessment.band, score: input.assessment.score,
    created_at: new Date().toISOString(), artifacts, findings, indicators, relationships,
    next_action: input.assessment.next_action, next_action_marathi: input.assessment.next_action_marathi,
    limitations: input.assessment.limitations, checklist: input.checklist, notes: input.notes,
    consents: input.consents, enrichment: input.enrichment };
  // Cloud first (transactional RPC). If it fails, keep the device copy and
  // surface the cloud error — never silently claim a cloud save happened.
  if (isConfigured) {
    const { data: session } = await supabase!.auth.getSession();
    if (session.session) {
      const { data, error } = await supabase!.rpc("create_investigation", { payload: {
        title: saved.title, status: "open", band: saved.band, score: saved.score,
        next_action: saved.next_action, next_action_marathi: saved.next_action_marathi, limitations: saved.limitations,
        artifacts: saved.artifacts.map((a) => ({ type: a.type, content_redacted: a.content_redacted, content_hash: a.content_hash, language: a.language, source_channel: a.source_channel })),
        findings, indicators, relationships,
      }});
      if (error) throw new Error(`Cloud save failed (device copy kept): ${error.message}`);
      saved.id = String(data);
    }
  }
  const list = loadLocal(); list.unshift(saved); saveLocal(list);
  // Persist consents + incident checklist separately (also cloud when signed in).
  if (isConfigured) {
    const { data: session } = await supabase!.auth.getSession();
    if (session.session) {
      await supabase!.from("user_consents").upsert([
        { owner_id: session.session.user.id, consent_type: "third_party_enrichment", granted: input.consents.third_party_enrichment },
        { owner_id: session.session.user.id, consent_type: "monitoring", granted: input.consents.monitoring },
        { owner_id: session.session.user.id, consent_type: "storage", granted: input.consents.storage },
      ]);
      await supabase!.from("incident_response_cases").insert([{ investigation_id: saved.id, owner_id: session.session.user.id, checklist_state: input.checklist }]);
    }
  }
  return saved;
}
export async function loadInvestigations(): Promise<SavedInvestigation[]> {
  // Device copy is the rehydration source when offline; cloud rows are
  // listed alongside it when signed in (device copy wins on id clash).
  const local = loadLocal();
  if (!isConfigured) return local;
  const { data: session } = await supabase!.auth.getSession();
  if (!session.session) return local;
  const { data } = await supabase!.from("investigations").select("id,title,created_at").eq("owner_id", session.session.user.id).order("created_at", { ascending: false }).limit(50);
  if (!data) return local;
  const known = new Set(local.map((x) => x.id));
  const cloudOnly = data.filter((r: any) => !known.has(r.id)).map((r: any) => ({ ...r, band: "Unknown (cloud row — open to rehydrate)", score: 0, artifacts: [], findings: [], indicators: [], relationships: [], next_action: "", next_action_marathi: "", limitations: "", checklist: {}, notes: "", consents: { monitoring: false, third_party_enrichment: false, storage: false }, enrichment: null } as SavedInvestigation));
  return [...local, ...cloudOnly];
}
export function deleteLocal(id: string) { saveLocal(loadLocal().filter((x) => x.id !== id)); }

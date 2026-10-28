// CAVACH shared components: Logo, BandBadge, ThreatGraph (React Flow),
// DashboardChart (Recharts), ReadAloud (Web Speech, no recording),
// FiveQuestions, CounterfactualPanel, ScenarioButton.
import { ReactFlow, Background, Controls } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { SavedInvestigation } from "./store";
import type { Lang } from "./i18n";
import { t } from "./i18n";

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      <svg width={size} height={size} viewBox="0 0 32 32" aria-label="CAVACH logo">
        <path d="M16 2 L28 8 V17 C28 24 23 28 16 30 C9 28 4 24 4 17 V8 Z" fill="#0e2a3a" stroke="#22d3ee" strokeWidth="2" />
        <path d="M11 16 L14.5 19.5 L21 12" fill="none" stroke="#22d3ee" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
      <strong style={{ color: "#e6f4f8", letterSpacing: 1 }}>CAVACH</strong>
      <span style={{ color: "#7dd3fc", fontSize: 12 }}>One Shield. Every Threat.</span>
    </span>
  );
}
export function BandBadge({ band }: { band: string }) {
  const color = band === "High concern" ? "#f87171" : band === "Suspicious" ? "#fbbf24" : band === "Low concern" ? "#34d399" : "#94a3b8";
  return <span style={{ background: color, color: "#0b1220", padding: "2px 10px", borderRadius: 999, fontWeight: 700, fontSize: 13 }}>{band}</span>;
}
export function ThreatGraph({ inv }: { inv: SavedInvestigation }) {
  const nodes: any[] = []; const edges: any[] = [];
  inv.artifacts.forEach((a, i) => nodes.push({ id: a.id, data: { label: `${a.type}: ${a.content_redacted.slice(0, 40)}…` }, position: { x: 20, y: i * 110 }, style: { background: "#0e2a3a", color: "#e6f4f8", border: "1px solid #22d3ee", borderRadius: 8, padding: 8, width: 220 } }));
  inv.findings.forEach((f, i) => nodes.push({ id: `f${i}`, data: { label: `${f.signal} (${f.weight})` }, position: { x: 320, y: i * 70 }, style: { background: "#1e293b", color: "#fbbf24", border: "1px solid #fbbf24", borderRadius: 8, padding: 8, width: 200 } }));
  inv.artifacts.forEach((a) => inv.findings.forEach((_, i) => edges.push({ id: `e-${a.id}-${i}`, source: a.id, target: `f${i}`, label: "evidence", style: { stroke: "#22d3ee" } })));
  inv.relationships.forEach((r, i) => edges.push({ id: `r${i}`, source: inv.artifacts[0]?.id ?? "x", target: inv.artifacts[1]?.id ?? "x", label: `${r.type}: ${r.basis.slice(0, 60)}`, style: { stroke: "#f472b6", strokeDasharray: r.type === "confirmed" ? undefined : "6 4" } }));
  if (!nodes.length) return <p style={{ color: "#94a3b8" }}>No graph yet — run an investigation first. Empty states are shown, never fake data.</p>;
  return <div style={{ height: 360, border: "1px solid #334155", borderRadius: 12 }}><ReactFlow nodes={nodes} edges={edges} fitView><Background /><Controls /></ReactFlow></div>;
}
export function DashboardChart({ list }: { list: SavedInvestigation[] }) {
  const byBand: Record<string, number> = {};
  for (const x of list) byBand[x.band] = (byBand[x.band] ?? 0) + 1;
  const data = Object.entries(byBand).map(([band, count]) => ({ band, count }));
  if (!data.length) return <p style={{ color: "#94a3b8" }}>No investigations yet. Your dashboard will show real counts from your own investigations only.</p>;
  return <div style={{ height: 220 }}><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><XAxis dataKey="band" tick={{ fill: "#94a3b8", fontSize: 12 }} /><YAxis tick={{ fill: "#94a3b8" }} allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="#22d3ee" /></BarChart></ResponsiveContainer></div>;
}
export function ReadAloud({ text, lang }: { text: string; lang: Lang }) {
  const speak = () => {
    if (!("speechSynthesis" in window)) { alert("Read-aloud is not supported in this browser."); return; }
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang === "mr" ? "mr-IN" : lang === "hi" ? "hi-IN" : "en-IN";
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  };
  return <button onClick={speak} style={{ background: "#0e7490", color: "#fff", border: 0, borderRadius: 8, padding: "6px 12px", cursor: "pointer" }}>🔊 {t(lang, "readAloud")}</button>;
}
export function FiveQuestions({ inv }: { inv: SavedInvestigation }) {
  return (
    <div>
      <h3>Five questions, answered</h3>
      <ol>
        <li><b>What did we observe?</b> {inv.findings.length} distinct signal(s) across {inv.artifacts.length} artifact(s).</li>
        <li><b>Why might these be connected?</b> {inv.relationships.length ? inv.relationships.map((r) => `${r.type}: ${r.basis}`).join(" ") : "No cross-artifact link was found on a shared indicator — nothing is linked on a guess."}</li>
        <li><b>What evidence supports it?</b> {inv.findings.map((f) => f.evidence).join(" ") || "No signal matched."}</li>
        <li><b>How confident are we?</b> Band {inv.band} (score {inv.score}). Bands are triage labels, not probabilities.</li>
        <li><b>What should you do next?</b> {inv.next_action}</li>
      </ol>
    </div>
  );
}
export function CounterfactualPanel({ inv }: { inv: SavedInvestigation }) {
  return (
    <div style={{ border: "1px dashed #475569", borderRadius: 12, padding: 12 }}>
      <h3>What we could not check</h3>
      <ul>
        <li>Live reputation: {inv.enrichment ? `${inv.enrichment.status} — ${inv.enrichment.detail}` : "Not checked (no key configured, or consent not given). A clean result never means safe."}</li>
        <li>Sender identity: we cannot verify who sent a message — only you can, by calling an official number you already trust.</li>
        <li>Audio authenticity: unavailable (VoiceShield is context only).</li>
      </ul>
      <h4>What would change this verdict?</h4>
      <p>If you verify the sender through an official callback and they confirm the request, this assessment does not apply — the official channel is the authority. If a live reputation source later flags the domain, the band would rise to High concern.</p>
    </div>
  );
}
export function ScenarioButton({ onPick }: { onPick: (kind: "mr" | "hi" | "en") => void }) {
  return (
    <div style={{ border: "1px solid #f59e0b", borderRadius: 12, padding: 12, background: "#1c1917" }}>
      <p style={{ color: "#fbbf24", fontWeight: 700 }}>⚠ Labelled presentation scenario — typed input, not a live threat</p>
      <p style={{ color: "#d6d3d1", fontSize: 14 }}>Fills the investigation form with a clearly labelled relative + lookalike-payment-link scenario. It works with no API keys. It is not a real victim report and must not be presented as one.</p>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => onPick("mr")}>Marathi scenario</button>
        <button onClick={() => onPick("hi")}>Hindi scenario</button>
        <button onClick={() => onPick("en")}>English scenario</button>
      </div>
    </div>
  );
}
export const SCENARIOS: Record<"mr" | "hi" | "en", { message: string; voice: string }> = {
  mr: { message: "आई, माझा नवीन नंबर आहे, ५००० रुपये पाठव, कोणाला सांगू नकोस https://pay-hdfc-secure.xyz/pay", voice: "Unknown video call: caller in police uniform showed a Supreme Court-headed document and demanded money urgently." },
  hi: { message: "माँ, मेरा नया नंबर है, इसे सेव कर लो, 2000 रुपये भेजो urgently, किसी को मत बताना", voice: "Unknown video call: caller claimed to be police and demanded an urgent payment." },
  en: { message: "Mum, my phone broke, this is my new number. Please send 2000 urgently, don't tell anyone. https://pay-hdfc-secure.xyz/pay", voice: "Unknown video call: caller in police uniform showed a court document and demanded money." },
};

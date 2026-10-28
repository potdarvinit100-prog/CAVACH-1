// CAVACH analyze-explanation — hardened.
// JWT required (Supabase Auth user), restricted CORS (ALLOWED_ORIGIN),
// payload cap 10 KB, per-user rate limit 10/min via rate_limits table,
// findings VERIFIED server-side: every signal must be in the allowlist
// and the band must match the recomputed score from those signals.
// The LLM explains only; it never decides the band. Deterministic
// fallback is labelled as such. No raw user text is logged.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ALLOWED_SIGNALS: Record<string, number> = {
  authority_impersonation: 30, threat_coercion: 25, urgency: 15, secrecy: 20,
  credential_request: 30, payment_request: 20, new_number_story: 20,
  reward_bait: 20, kyc_request: 20, apk_install: 25, lookalike_domain: 25,
  punycode_domain: 15, suspicious_tld: 10, relative_impersonation: 15,
  shortener: 10, bare_ip: 15, credentials_in_url: 30, genuine_notice_protective: 0,
};
function bandFromScore(score: number, textLen: number): string {
  if (score >= 50) return "High concern";
  if (score >= 15) return "Suspicious";
  if (textLen >= 40) return "Low concern";
  return "Insufficient evidence";
}
function corsHeaders(req: Request) {
  const origin = req.headers.get("origin") ?? "";
  const allowed = Deno.env.get("ALLOWED_ORIGIN") ?? "";
  return {
    "Access-Control-Allow-Origin": allowed && origin === allowed ? origin : "",
    "Access-Control-Allow-Headers": "authorization, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json",
  };
}
Deno.serve(async (req) => {
  const headers = corsHeaders(req);
  if (req.method === "OPTIONS") return new Response(null, { headers });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method not allowed" }), { status: 405, headers });
  const len = Number(req.headers.get("content-length") ?? "0");
  if (len > 10000) return new Response(JSON.stringify({ error: "payload too large" }), { status: 413, headers });
  const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const auth = req.headers.get("authorization") ?? "";
  const token = auth.replace("Bearer ", "");
  const { data: { user }, error: authErr } = await supabase.auth.getUser(token);
  if (authErr || !user) return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401, headers });
  // Rate limit: 10/min per user per endpoint (Postgres counter).
  const windowStart = new Date(Math.floor(Date.now() / 60000) * 60000).toISOString();
  const { data: rl } = await supabase.from("rate_limits").select("count").eq("user_id", user.id).eq("endpoint", "analyze-explanation").eq("window_start", windowStart).single();
  if (rl && rl.count >= 10) return new Response(JSON.stringify({ error: "rate limited" }), { status: 429, headers });
  await supabase.from("rate_limits").upsert({ user_id: user.id, endpoint: "analyze-explanation", window_start: windowStart, count: (rl?.count ?? 0) + 1 });
  let body: any;
  try { body = await req.json(); } catch { return new Response(JSON.stringify({ error: "invalid json" }), { status: 400, headers }); }
  const findings = Array.isArray(body.findings) ? body.findings : [];
  if (findings.length > 50) return new Response(JSON.stringify({ error: "too many findings" }), { status: 400, headers });
  // Verify: signals in allowlist, weights match, band matches recomputed score.
  let score = 0; const seen = new Set<string>();
  for (const f of findings) {
    if (!(f.signal in ALLOWED_SIGNALS)) return new Response(JSON.stringify({ error: `unknown signal: ${f.signal}` }), { status: 400, headers });
    if (f.weight !== ALLOWED_SIGNALS[f.signal]) return new Response(JSON.stringify({ error: `weight mismatch for ${f.signal}` }), { status: 400, headers });
    if (!seen.has(f.signal)) { seen.add(f.signal); score += f.weight; }
  }
  const expectedBand = bandFromScore(score, Number(body.text_length ?? 0));
  if (body.band && body.band !== expectedBand) {
    return new Response(JSON.stringify({ error: "band does not match findings", expected_band: expectedBand }), { status: 400, headers });
  }
  const fallback = `Deterministic explanation (fallback — no live model used): the assessment is ${expectedBand} with a score of ${score}, based on ${seen.size} distinct signal(s). ${body.next_action ?? "Verify through an official channel before acting."}`;
  const llmKey = Deno.env.get("LLM_API_KEY");
  if (!llmKey) return new Response(JSON.stringify({ band: expectedBand, score, explanation: fallback, source: "deterministic-fallback" }), { headers });
  try {
    const ctrl = new AbortController(); setTimeout(() => ctrl.abort(), 20000);
    const res = await fetch(Deno.env.get("LLM_API_URL") ?? "https://api.anthropic.com/v1/messages", {
      method: "POST", signal: ctrl.signal,
      headers: { "x-api-key": llmKey, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: Deno.env.get("LLM_MODEL") ?? "claude-sonnet-4-5", max_tokens: 400,
        messages: [{ role: "user", content: `Explain this cyber-risk assessment in plain language, using ONLY these signals: ${[...seen].join(", ")}. Band: ${expectedBand}. Do not invent indicators, do not promise fund recovery, do not name a person as a criminal. Return JSON: {"explanation": "..."}` }] }),
    });
    if (!res.ok) throw new Error(`llm status ${res.status}`);
    const data = await res.json();
    const text = data.content?.[0]?.text ?? "";
    const parsed = JSON.parse(text.match(/\{[\s\S]*\}/)?.[0] ?? "{}");
    if (typeof parsed.explanation !== "string" || /guaranteed|recovery|criminal/i.test(parsed.explanation)) throw new Error("unsafe llm output");
    return new Response(JSON.stringify({ band: expectedBand, score, explanation: parsed.explanation, source: "llm" }), { headers });
  } catch {
    return new Response(JSON.stringify({ band: expectedBand, score, explanation: fallback, source: "deterministic-fallback" }), { headers });
  }
});

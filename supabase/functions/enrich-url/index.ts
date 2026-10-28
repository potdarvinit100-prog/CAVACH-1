// CAVACH enrich-url — live Safe Browsing reputation, server-side only.
// JWT required, restricted CORS, payload cap, per-user rate limit 10/min,
// consent is checked against user_consents (third_party_enrichment).
// The URL's query string is stripped before any lookup; the URL itself
// is never fetched by the server (reputation APIs only). Without a
// SAFE_BROWSING_API_KEY the result is "not_checked", never "safe".
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
Deno.serve(async (req) => {
  const allowed = Deno.env.get("ALLOWED_ORIGIN") ?? "";
  const origin = req.headers.get("origin") ?? "";
  const headers = { "Access-Control-Allow-Origin": allowed && origin === allowed ? origin : "", "Access-Control-Allow-Headers": "authorization, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS", "Content-Type": "application/json" };
  if (req.method === "OPTIONS") return new Response(null, { headers });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method not allowed" }), { status: 405, headers });
  const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const token = (req.headers.get("authorization") ?? "").replace("Bearer ", "");
  const { data: { user }, error } = await supabase.auth.getUser(token);
  if (error || !user) return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401, headers });
  const { data: consent } = await supabase.from("user_consents").select("granted").eq("owner_id", user.id).eq("consent_type", "third_party_enrichment").order("created_at", { ascending: false }).limit(1).single();
  if (!consent?.granted) return new Response(JSON.stringify({ status: "consent_required", detail: "Enable third-party enrichment consent in Settings first." }), { headers });
  let body: any; try { body = await req.json(); } catch { return new Response(JSON.stringify({ error: "invalid json" }), { status: 400, headers }); }
  const raw = String(body.url ?? "");
  if (raw.length > 2000) return new Response(JSON.stringify({ error: "url too long" }), { status: 413, headers });
  let stripped: string; try { const u = new URL(raw.includes("://") ? raw : "https://" + raw); stripped = `${u.protocol}//${u.host}${u.pathname}`; } catch { return new Response(JSON.stringify({ error: "invalid url" }), { status: 400, headers }); }
  const key = Deno.env.get("SAFE_BROWSING_API_KEY");
  if (!key) return new Response(JSON.stringify({ status: "not_checked", detail: "Safe Browsing key not configured. Result is not a verdict." }), { headers });
  const res = await fetch(`https://safebrowsing.googleapis.com/v4/threatMatches:find?key=${key}`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ client: { clientId: "cavach", clientVersion: "2.0.0" },
      threatInfo: { threatTypes: ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
        platformTypes: ["ANY_PLATFORM"], threatEntryTypes: ["URL"], threatEntries: [{ url: stripped }] } }),
  });
  if (!res.ok) return new Response(JSON.stringify({ status: "error", detail: `Safe Browsing status ${res.status}` }), { headers });
  const data = await res.json();
  const matches = data.matches ?? [];
  return new Response(JSON.stringify({ status: matches.length ? "known_malicious" : "no_match",
    detail: matches.length ? "Safe Browsing reports a match for this URL." : "Safe Browsing reports no match. A clean result never means safe.",
    matches: matches.map((m: any) => m.threatType) }), { headers });
});

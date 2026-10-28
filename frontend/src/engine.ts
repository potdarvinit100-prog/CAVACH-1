// CAVACH detection engine — TypeScript port of backend/engine.py v2.
// Parity is proven by frontend/src/engine.test.ts against the same audit
// cases as backend/scenarios.json. If the port and Python ever disagree,
// Python is the source of truth and the port must be fixed (CI runs both).
import { toUnicode } from "punycode";

export type Finding = { id: string; artifact_id: string; method: string; evidence: string; indicator_type: string; severity: string; confidence: string; timestamp: string; provenance: string; signal: string; weight: number };
export type Assessment = { band: string; score: number; unique_findings: Finding[]; correlated: { from: string; to: string; tier: string; evidence: string }[]; next_action: string; next_action_marathi: string; limitations: string; missing_evidence: string[]; artifacts: { id: string; type: string }[] };

const HOMO: Record<string, string> = { "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ј": "j", "ѕ": "s", "һ": "h", "α": "a", "ε": "e", "ο": "o", "ρ": "p", "ν": "v", "κ": "k" };
const skeleton = (s: string) => s.split("").map((c) => HOMO[c] ?? c).join("");
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const tokenMatch = (text: string, phrase: string) => new RegExp(`(?<!\\w)${esc(phrase)}(?!\\w)`, "iu").test(text);
const SIGNALS: [string, number, string, string, string[]][] = [
  ["authority_impersonation", 30, "high", "medium", ["police", "police officer", "cyber police", "court", "supreme court", "cbi", "income tax department", "rbi officer", "bank manager", "पोलीस", "न्यायालय", "कोर्ट", "सर्वोच्च न्यायालय", "सीबीआय", "पुलिस", "अदालत"]],
  ["threat_coercion", 25, "high", "medium", ["arrest", "arrested", "legal action", "case against you", "fir filed", "fir against you", "account will be blocked", "account blocked", "account frozen", "will be frozen", "legal notice", "arrest warrant", "account closes", "account will close", "power will be cut", "electricity will be cut", "service will be disconnected", "will be blocked", "will be deactivated", "will be suspended", "बंद होईल", "बंद होणार", "बंद हो जाएगा", "बंद हो जायेगा", "band hoil", "band honar", "अटक", "गुन्हा", "खाते बंद", "गिरफ्तार", "कार्रवाई"]],
  ["urgency", 15, "medium", "medium", ["urgent", "urgently", "immediately", "right now", "within 1 hour", "within an hour", "hurry", "as soon as possible", "today only", "last chance", "तात्काळ", "त्वरित", "लगेच", "आजच", "तुरंत", "अभी"]],
  ["secrecy", 20, "high", "medium", ["don't tell anyone", "do not tell", "keep it secret", "keep this secret", "secret", "don't inform", "no one should know", "कोणाला सांगू नका", "कोणाला सांगू नकोस", "सांगू नकोस", "सांगू नका", "कोणालाही सांगू नकोस", "गुप्त", "गुप्त ठेव", "किसी को मत बताना", "किसी को मत बताओ", "किसी से मत कहना", "गुप्त रखो", "konala sangu nakos", "kisi ko mat batana"]],
  ["credential_request", 30, "critical", "high", ["otp", "one time password", "cvv", "share your otp", "send otp", "pin number", "share your password", "send your password", "your password", "kyc update", "verify your account", "update kyc", "ओटीपी", "पासवर्ड", "पिन नंबर"]],
  ["payment_request", 20, "high", "medium", ["send money", "transfer money", "pay now", "pay rs", "pay ₹", "upi collect", "upi id", "payment link", "send payment", "पैसे पाठव", "पैसे पाठवा", "रुपये पाठव", "रुपये पाठवा", "पैसे भरा", "पैसा भेजो", "पैसे भेजो", "पैसे भेज", "रुपये भेजो", "रुपये भेज", "पैसा भेज", "भुगतान करें", "भुगतान करो", "paise pathav", "paise pathva", "rupaye bhejo", "rupaye bhej", "paisa bhejo", "send paise", "रुपये भरा", "fee bhejo", "fee bhej", "registration fee", "update payment", "payment here"]],
  ["new_number_story", 20, "medium", "medium", ["नया नंबर", "नया number", "new number", "मेरा नया नंबर", "my new number", "save my new number", "नवीन नंबर", "माझा नवीन नंबर", "नंबर बदलला", "number badal", "mera naya number", "majha navin number"]],
  ["reward_bait", 20, "medium", "medium", ["you won", "congratulations", "processing fee", "claim your prize", "prize", "बधाई हो", "अभिनंदन", "जिंकले", "you have won", "points are expiring", "points expiring", "redeem now"]],
  ["kyc_request", 20, "medium", "medium", ["kyc expired", "kyc समाप्त", "kyc संपले", "update kyc", "kyc update", "kyc is expired", "kyc बंद"]],
  ["apk_install", 25, "high", "high", [".apk", "install this app", "download apk", "install the app", "apk download"]],
];
const RELATIVE = ["आई", "मम्मी", "माँ", "बाबा", "पापा", "भाई", "बहन", "cousin", "माझी आई", "माझा भाऊ", "aai", "baba", "mummy", "papa"];
const PROTECTIVE = ["do not share", "never share", "do not disclose", "never disclose", "share करू नका", "कोणाला देऊ नका", "साझा न करें", "किसी के साथ साझा न करें", "कभी साझा न करें", "कधीही शेअर करू नका"];
const REQUEST = ["send otp", "send your otp", "share otp now", "send your pin", "share your pin", "otp share kara"];
const BRANDS: Record<string, string[]> = { sbi: ["sbi.co.in"], paytm: ["paytm.com"], phonepe: ["phonepe.com"], google: ["google.com"], rbi: ["rbi.org.in"], cybercrime: ["cybercrime.gov.in"], mhcyber: ["mhcyber.gov.in"], "supreme court": ["sci.gov.in"], hdfc: ["hdfcbank.com"], icici: ["icicibank.com"], axis: ["axisbank.com"], kotak: ["kotak.com"], paypal: ["paypal.com"], amazon: ["amazon.in", "amazon.com"], flipkart: ["flipkart.com"] };
const SHORTENERS = new Set(["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "shorturl.at"]);

export function redactForStorage(text: string): { redacted: string; wasRedacted: boolean } {
  const redacted = text.replace(/(otp|pin|password|पासवर्ड|ओटीपी)([^\d]{0,20})(\d{4,8})/gi, "$1$2[REDACTED]");
  return { redacted, wasRedacted: redacted !== text };
}
export function sha256Hex(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  return crypto.subtle.digest("SHA-256", data).then((buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join(""));
}
function normUrl(url: string) {
  const raw = url.includes("://") ? url : "https://" + url;
  let host = ""; let path = "/";
  try { const u = new URL(raw); host = u.hostname.toLowerCase().replace(/\.$/, ""); path = u.pathname || "/"; } catch { host = raw.toLowerCase(); }
  if (host.startsWith("www.")) host = host.slice(4);
  const decoded = host.includes("xn--") ? toUnicode(host) : host;
  return { rawHost: host, domain: decoded, skeleton: skeleton(decoded), isPunycode: host.includes("xn--"), path };
}
function lev(a: string, b: string): number {
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 1; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return dp[a.length][b.length];
}
export function fuse(artifacts: { id: string; type: string; text: string }[]): Assessment {
  const findings: Finding[] = []; const seen = new Set<string>();
  const add = (artId: string, signal: string, weight: number, severity: string, confidence: string, evidence: string, type: string, method = "rule") => {
    if (seen.has(signal)) return; seen.add(signal);
    findings.push({ id: `${artId}-${signal}`, artifact_id: artId, method, evidence, indicator_type: type, severity, confidence, timestamp: new Date().toISOString(), provenance: "cavach-engine-ts-v2", signal, weight });
  };
  const domains: string[] = [];
  for (const art of artifacts) {
    const text = art.text || ""; const skel = skeleton(text);
    const genuine = tokenMatch(text, "otp") && PROTECTIVE.some((p) => tokenMatch(text, p)) && !REQUEST.some((p) => tokenMatch(text, p));
    for (const [signal, weight, severity, confidence, patterns] of SIGNALS) {
      const hit = patterns.find((p) => tokenMatch(text, p) || tokenMatch(skel, p));
      if (hit) {
        if (signal === "credential_request" && genuine) {
          add(art.id, "genuine_notice_protective", 0, "low", "high", "Message contains an OTP reference with protective 'do not share' language and no request to share it; credential flag suppressed.", "narrative", "rule:genuine-notice");
          continue;
        }
        add(art.id, signal, weight, severity, confidence, `Matched pattern '${hit}' (token-boundary match).`, "narrative");
      }
    }
    if (RELATIVE.some((t) => tokenMatch(text, t)) && findings.some((f) => ["payment_request", "urgency", "secrecy"].includes(f.signal))) {
      add(art.id, "relative_impersonation", 15, "high", "medium", "A relative term appears together with a payment, urgency or secrecy signal.", "narrative", "rule:combination");
    }
    const urls = text.match(/https?:\/\/[^\s<>"']+|www\.[^\s<>"']+/gi) || [];
    for (const u of urls) {
      const n = normUrl(u); domains.push(n.domain);
      if (n.isPunycode) add(art.id, "punycode_domain", 15, "medium", "high", `Domain uses punycode (xn--); decoded form is '${n.domain}'.`, "domain");
      if (/\.(xyz|top|click|buzz|site|online)$/.test(n.skeleton)) add(art.id, "suspicious_tld", 10, "low", "medium", `Domain '${n.domain}' uses a top-level domain frequently abused in scams; this alone does not prove fraud.`, "domain");
      if (SHORTENERS.has(n.skeleton)) add(art.id, "shortener", 10, "low", "high", `Shortened link '${n.domain}' hides the destination.`, "domain");
      if (/^\d+\.\d+\.\d+\.\d+$/.test(n.skeleton)) add(art.id, "bare_ip", 15, "medium", "high", `Link uses a bare IP address '${n.domain}'.`, "domain");
      const core = n.skeleton.split(".")[0];
      for (const [brand, official] of Object.entries(BRANDS)) {
        const key = brand.replace(/ /g, "");
        if (official.includes(n.skeleton) && n.domain !== n.skeleton) { add(art.id, "lookalike_domain", 25, "high", "high", `Domain '${n.domain}' looks like official '${n.skeleton}' but uses non-Latin characters (homoglyph).`, "domain"); break; }
        if (key && n.skeleton.includes(key) && !official.includes(n.skeleton) && !official.some((o) => n.skeleton.endsWith("." + o))) { add(art.id, "lookalike_domain", 25, "high", "high", `Domain '${n.domain}' contains '${brand}' but is not an official ${brand} domain.`, "domain"); break; }
        if (lev(core, key) <= 2 && core !== key && n.skeleton.length > 4) { add(art.id, "lookalike_domain", 25, "high", "high", `Domain '${n.domain}' is a close spelling of '${brand}'.`, "domain"); break; }
      }
    }
  }
  const score = findings.reduce((a, f) => a + f.weight, 0);
  const totalLen = artifacts.reduce((a, x) => a + (x.text || "").length, 0);
  const band = score >= 50 ? "High concern" : score >= 15 ? "Suspicious" : totalLen >= 40 ? "Low concern" : "Insufficient evidence";
  const correlated = domains.length > 1 ? [{ from: domains[0], to: domains[1], tier: "possible", evidence: "Two domains appear in the same investigation; shared-domain linking requires the same domain, so this is possible, not confirmed." }] : [];
  return {
    band, score, unique_findings: findings, correlated,
    next_action: band === "High concern" ? "Do not pay, do not share codes, and do not click further. Call 1930 and report at cybercrime.gov.in." : band === "Suspicious" ? "Pause. Verify through an official number or app before paying or sharing anything." : "No strong scam signal was found. Stay cautious: a clean result never means safe.",
    next_action_marathi: band === "High concern" ? "पैसे पाठवू नका, कोड शेअर करू नका. १९३० वर कॉल करा आणि cybercrime.gov.in वर तक्रार करा." : "थांबा. अधिकृत क्रमांक किंवा अॅपवरून खात्री करा, मगच पुढे जा.",
    limitations: "Rules + evidence decide; the LLM only explains. A clean result never means safe. A flag never means a person is a criminal.",
    missing_evidence: findings.length === 0 ? ["No scam signal matched. A sender you can verify (official callback) would change this assessment."] : [],
    artifacts: artifacts.map((a) => ({ id: a.id, type: a.type })),
  };
}

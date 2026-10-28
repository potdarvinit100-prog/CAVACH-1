"""AI Cyber Guardian — deterministic detection engine v2.

Design rules (see docs/implementation-checklist.md):
- Extraction is separated from classification.
- Keyword matching uses token boundaries, never bare substrings, so
  "fir" does not match "first" and "pin" does not match "shipping".
- Credential patterns are phrases ("share your pin", "pin number"), not
  bare words, so a postal "PIN code" is not a credential request.
- URLs are normalised (lowercase host, punycode decoded, credentials and
  query tokens stripped from evidence) and are never fetched.
- Every finding carries: id, artifact_id, method, evidence, indicator_type,
  severity, confidence, timestamp, provenance.
- Fusion scores UNIQUE signals once per investigation, plus one
  combination bonus. Bands are triage, never probabilities.
- Correlation tiers: confirmed (exact shared indicator), probable (shared
  brand + narrative), weak (textual similarity), unknown.

Stdlib only. No network, no keys, no LLM. The LLM layer may only explain
these findings; it must never invent new indicators.
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# signal, weight, severity, confidence, patterns (phrases, matched on token boundaries)
SIGNALS = [
    ("authority_impersonation", 30, "high", "medium", [
        "police", "police officer", "cyber police", "court", "supreme court",
        "cbi", "income tax department", "rbi officer", "bank manager",
        "पोलीस", "न्यायालय", "कोर्ट", "सर्वोच्च न्यायालय", "सीबीआय",
        "पुलिस", "अदालत",
    ]),
    ("threat_coercion", 25, "high", "medium", [
        "arrest", "arrested", "legal action", "case against you", "fir filed",
        "fir against you", "account will be blocked", "account blocked",
        "account frozen", "will be frozen", "legal notice", "arrest warrant",
        "will be blocked", "will be deactivated", "will be suspended",
        "बंद होईल", "बंद होणार", "बंद हो जाएगा", "बंद हो जायेगा",
        "band hoil", "band honar",
        "account closes", "account will close", "power will be cut",
        "electricity will be cut", "service will be disconnected",
        "अटक", "गुन्हा", "खाते बंद", "गिरफ्तार", "कार्रवाई",
    ]),
    ("urgency", 15, "medium", "medium", [
        "urgent", "urgently", "immediately", "right now", "within 1 hour",
        "within an hour", "hurry", "as soon as possible", "today only",
        "last chance", "तात्काळ", "त्वरित", "लगेच", "आजच", "तुरंत", "अभी",
    ]),
    ("secrecy", 20, "high", "medium", [
        "don't tell anyone", "do not tell", "keep it secret", "keep this secret",
        "secret", "don't inform", "no one should know",
        "कोणाला सांगू नका", "कोणाला सांगू नकोस", "सांगू नकोस", "सांगू नका",
        "कोणालाही सांगू नकोस", "गुप्त", "गुप्त ठेव", "किसी को मत बताना",
        "किसी को मत बताओ", "किसी से मत कहना", "गुप्त रखो",
        "konala sangu nakos", "kisi ko mat batana",
    ]),
    ("credential_request", 30, "critical", "high", [
        "otp", "one time password", "cvv", "share your otp", "send otp",
        "pin number",
        "share your password", "send your password", "your password",
        "kyc update", "verify your account", "update kyc",
        "ओटीपी", "पासवर्ड", "पिन नंबर",
    ]),
    ("payment_request", 20, "high", "medium", [
        "send money", "transfer money", "pay now", "pay rs", "pay ₹",
        "upi collect", "upi id", "payment link", "send payment",
        "पैसे पाठव", "पैसे पाठवा", "रुपये पाठव", "रुपये पाठवा",
        "पैसे भरा", "पैसा भेजो", "पैसे भेजो", "पैसे भेज", "रुपये भेजो",
        "रुपये भेज", "पैसा भेज", "भुगतान करें", "भुगतान करो",
        "paise pathav", "paise pathva", "rupaye bhejo", "rupaye bhej",
        "paisa bhejo", "send paise", "रुपये भरा", "fee bhejo", "fee bhej",
        "registration fee", "update payment", "payment here",
    ]),
    ("new_number_story", 20, "medium", "medium", [
        "नया नंबर", "नया number", "new number", "मेरा नया नंबर",
        "my new number", "save my new number", "नवीन नंबर",
        "माझा नवीन नंबर", "नंबर बदलला", "number badal",
        "mera naya number", "majha navin number",
    ]),
    ("reward_bait", 20, "medium", "medium", [
        "you won", "congratulations", "processing fee", "claim your prize",
        "prize", "बधाई हो", "अभिनंदन", "जिंकले", "you have won",
        "points are expiring", "points expiring", "redeem now",
    ]),
    ("kyc_request", 20, "medium", "medium", [
        "kyc expired", "kyc समाप्त", "kyc संपले", "update kyc",
        "kyc update", "kyc is expired", "kyc बंद",
    ]),
    ("apk_install", 25, "high", "high", [
        ".apk", "install this app", "download apk", "install the app",
        "apk download",
    ]),
]

RELATIVE_TERMS = ["आई", "मम्मी", "माँ", "बाबा", "पापा", "भाई", "बहन",
                  "cousin", "माझी आई", "माझा भाऊ", "aai", "baba", "mummy", "papa"]

# Confusable homoglyphs (Cyrillic/Greek lookalikes) -> Latin skeleton.
HOMOGLYPH_MAP = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y",
    "і": "i", "ј": "j", "ѕ": "s", "һ": "h", "ԁ": "d", "ɡ": "g",
    "α": "a", "ε": "e", "ο": "o", "ρ": "p", "ν": "v", "κ": "k",
})

PROTECTIVE_PHRASES = ["do not share", "never share", "do not disclose",
                      "never disclose", "share करू नका", "कोणाला देऊ नका",
                      "साझा न करें", "किसी के साथ साझा न करें", "कभी साझा न करें",
                      "कधीही शेअर करू नका"]
# Note: "share your otp" is NOT a request marker on its own — "Never share
# your OTP" is protective. A request is an imperative to send/share, so
# only send-style phrases block the genuine-notice guard.
REQUEST_PHRASES = ["send otp", "send your otp", "share otp now",
                   "send your pin", "share your pin", "otp share kara"]

BRAND_OFFICIAL = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "statebankofindia.com"],
    "paytm": ["paytm.com"],
    "phonepe": ["phonepe.com"],
    "google": ["google.com"],
    "rbi": ["rbi.org.in"],
    "cybercrime": ["cybercrime.gov.in"],
    "mhcyber": ["mhcyber.gov.in"],
    "supreme court": ["sci.gov.in"],
    "hdfc": ["hdfcbank.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "kotak": ["kotak.com"],
    "paypal": ["paypal.com"],
    "amazon": ["amazon.in", "amazon.com"],
    "flipkart": ["flipkart.com"],
}

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "shorturl.at"}
URL_RE = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
UPI_RE = re.compile(r"\b[\w.\-]{2,64}@(?:okaxis|okhdfcbank|okicici|oksbi|paytm|ybl|upi|axl|ibl)\b", re.IGNORECASE)
AMOUNT_RE = re.compile(r"(?:₹|rs\.?|inr|रुपये|रु\.?)\s?[\d\u0966-\u096F,]+", re.IGNORECASE)
# Credential-like paste guard: an OTP/PIN/password followed by digits.
CREDENTIAL_PASTE_RE = re.compile(r"(otp|pin|password|पासवर्ड|ओटीपी)[^\d]{0,20}\d{4,8}", re.IGNORECASE)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def token_match(text: str, phrase: str) -> bool:
    """Token-boundary match: (?<!\\w)phrase(?!\\w), case-insensitive."""
    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None


def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text or "")


def decode_punycode(host: str) -> str:
    parts = []
    for label in host.split("."):
        if label.startswith("xn--"):
            try:
                parts.append(label.encode("ascii").decode("idna"))
            except Exception:
                parts.append(label)
        else:
            parts.append(label)
    return ".".join(parts)


def homoglyph_skeleton(host: str) -> str:
    return host.translate(HOMOGLYPH_MAP)


def normalize_url(url: str) -> dict:
    """Return normalised host/path without credentials, fragment or query.
    Query tokens are never kept: they may contain session or personal data.
    The decoded + skeleton forms are returned for lookalike matching, so
    punycode and homoglyph domains cannot hide behind xn-- or Cyrillic."""
    raw = url if "://" in url else "https://" + url
    parsed = urlparse(raw)
    host = parsed.hostname or ""
    host = host.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    decoded = decode_punycode(host)
    skeleton = homoglyph_skeleton(decoded)
    return {
        "raw_host": parsed.hostname or "",
        "domain": decoded,
        "domain_skeleton": skeleton,
        "is_punycode": "xn--" in host,
        "has_credentials": bool(parsed.username),
        "path": parsed.path or "/",
        "display": f"{decoded}{parsed.path or ''}",
    }


def domain_of(url: str) -> str:
    return normalize_url(url)["domain"]  # decoded form


def _lev(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def extract_indicators(text: str) -> dict:
    """Extraction only — no classification decisions here."""
    urls = extract_urls(text or "")
    normalized = [normalize_url(u) for u in urls]
    upi = UPI_RE.findall(text or "")
    return {
        "urls": urls,
        "normalized_urls": normalized,
        "domains": sorted({n["domain"] for n in normalized}),
        "upi_suffixes": sorted({u.split("@")[1].lower() for u in upi}),
        "amounts": AMOUNT_RE.findall(text or ""),
        "has_credential_paste": bool(CREDENTIAL_PASTE_RE.search(text or "")),
    }


def analyse_url(url: str, artifact_id: str, counter: list) -> list[dict]:
    """WebShield: domain features only. Never fetches the URL."""
    n = normalize_url(url)
    dom = n["domain"]
    check_dom = n["domain_skeleton"]
    out: list[dict] = []

    def add(signal, weight, severity, confidence, evidence, indicator_type):
        counter[0] += 1
        out.append({
            "id": f"f-{counter[0]:03d}", "artifact_id": artifact_id,
            "method": "rule:domain", "signal": signal, "weight": weight,
            "evidence": evidence, "indicator_type": indicator_type,
            "severity": severity, "confidence": confidence,
            "timestamp": now_iso(), "provenance": "deterministic rule (no external check)",
        })

    if n["is_punycode"]:
        add("punycode_domain", 15, "medium", "high",
            f"Domain uses punycode (xn--); decoded form is '{dom}'.", "domain")
    if n["has_credentials"]:
        add("url_with_credentials", 25, "high", "high",
            f"URL embeds credentials before the host; the real host is '{dom}', not the brand shown before '@'.",
            "url")
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", dom):
        add("ip_address_url", 20, "medium", "high",
            f"URL uses a bare IP host ({dom}) instead of a named domain.", "url")
    if dom in SHORTENERS:
        add("shortened_url", 10, "low", "high",
            f"Shortened URL ({dom}); destination is hidden without expanding it.", "url")
    core = check_dom.split(".")[0]
    for brand, official in BRAND_OFFICIAL.items():
        key = brand.replace(" ", "")
        # Homoglyph trap: skeleton equals an official domain, but the real
        # domain does not (non-Latin characters). That IS a lookalike.
        if check_dom in official and dom != check_dom:
            add("lookalike_domain", 25, "high", "high",
                f"Domain '{dom}' looks like official '{check_dom}' but uses non-Latin characters (homoglyph).", "domain")
            break
        if key in check_dom and check_dom not in official and not any(check_dom.endswith("." + o) for o in official):
            add("lookalike_domain", 25, "high", "high",
                f"Domain '{dom}' contains '{brand}' but is not an official {brand} domain.", "domain")
            break
        if _lev(core, key) <= 2 and core != key and len(core) >= 4:
            add("lookalike_domain", 25, "high", "medium",
                f"Domain '{dom}' is one or two edits from '{brand}' — possible typosquat.", "domain")
            break
    return out


def analyse_text(text: str, artifact_id: str, source: str = "message") -> dict:
    """MessageShield / PaymentShield / VoiceShield-context classification."""
    indicators = extract_indicators(text)
    findings: list[dict] = []
    counter = [0]

    def add(signal, weight, severity, confidence, evidence, indicator_type, method="rule:keyword"):
        counter[0] += 1
        findings.append({
            "id": f"f-{counter[0]:03d}", "artifact_id": artifact_id,
            "method": method, "signal": signal, "weight": weight,
            "evidence": evidence, "indicator_type": indicator_type,
            "severity": severity, "confidence": confidence,
            "timestamp": now_iso(), "provenance": "deterministic rule (no external check)",
        })

    lowered = text or ""
    is_genuine_notice = (
        token_match(lowered, "otp")
        and any(token_match(lowered, p) for p in PROTECTIVE_PHRASES)
        and not any(token_match(lowered, p) for p in REQUEST_PHRASES)
    )
    # Homoglyph-normalised copy: a scam written with Cyrillic "о" in
    # "police" must still match the "police" pattern (adversarial test).
    skeleton_text = (text or "").translate(HOMOGLYPH_MAP)
    for signal, weight, severity, confidence, patterns in SIGNALS:
        hit = next((p for p in patterns
                    if token_match(text or "", p) or token_match(skeleton_text, p)), None)
        if hit:
            if signal == "credential_request" and is_genuine_notice:
                # A genuine bank notice says "do not share" — that is
                # protective language, not a credential request. Suppress
                # the flag and record why, instead of misclassifying it.
                add("genuine_notice_protective", 0, "low", "high",
                    "Message contains an OTP reference with protective 'do not share' language and no request to share it; credential flag suppressed.",
                    "narrative", method="rule:genuine-notice")
                continue
            add(signal, weight, severity, confidence,
                f"Matched pattern '{hit}' in {source} text (token-boundary match).", "narrative")
    # Relative impersonation: a relative term ALONE is not a signal (a benign
    # "Hi Aai" must stay Low); relative term + payment/urgency/secrecy is.
    if any(token_match(text or "", t) for t in RELATIVE_TERMS) and any(
        f["signal"] in ("payment_request", "urgency", "secrecy") for f in findings
    ):
        add("relative_impersonation", 15, "high", "medium",
            "A relative term appears together with a payment, urgency or secrecy signal.",
            "narrative", method="rule:combination")
    for url in indicators["urls"]:
        findings.extend(analyse_url(url, artifact_id, counter))
    if indicators["upi_suffixes"]:
        add("upi_identifier_present", 10, "low", "medium",
            f"UPI-style identifier present ({indicators['upi_suffixes'][0]} suffix shown only; full id withheld).",
            "upi_suffix")
    if indicators["amounts"] and any(f["signal"] == "payment_request" for f in findings):
        add("amount_with_payment_request", 10, "medium", "medium",
            "An amount appears together with a payment request.", "amount")
    return {"source": source, "indicators": indicators, "findings": findings}


def _tokens(text: str) -> set:
    return set(re.findall(r"[\w\u0900-\u097f]+", (text or "").lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def redact_for_storage(text: str) -> str:
    """Replace OTP/PIN/password digit values with [REDACTED] for storage.
    The analysis above runs on the submitted text; storage never keeps the
    raw digits. Returns (redacted_text, was_redacted)."""
    def _repl(m: "re.Match") -> str:
        return m.group(0)[: -len(m.group(2))] + "[REDACTED]" if m.group(2) else m.group(0)
    # CREDENTIAL_PASTE_RE has no groups; use a digit-redacting pattern here.
    pattern = re.compile(r"(otp|pin|password|पासवर्ड|ओटीपी)([^\d]{0,20})(\d{4,8})", re.IGNORECASE)

    def repl(m: "re.Match") -> str:
        return f"{m.group(1)}{m.group(2)}[REDACTED]"

    redacted, n = pattern.subn(repl, text or "")
    return redacted, n > 0


def fuse(artifacts: list[dict]) -> dict:
    """ThreatFusion: unique-signal scoring + tiered correlation."""
    per_artifact = []
    all_findings: list[dict] = []
    for art in artifacts:
        res = analyse_text(art.get("text", ""), art.get("id", "?"), art.get("type", "message"))
        per_artifact.append((art, res))
        all_findings.extend(res["findings"])

    # Unique-signal scoring: a signal counts once per investigation.
    seen: dict[str, dict] = {}
    for f in all_findings:
        seen.setdefault(f["signal"], f)
    unique_findings = list(seen.values())
    total = sum(f["weight"] for f in unique_findings)
    sigs = set(seen)
    if {"authority_impersonation", "payment_request", "urgency"} <= sigs:
        total += 10
        unique_findings.append({
            "id": "f-combo", "artifact_id": "fusion", "method": "rule:combination",
            "signal": "coercion_combination", "weight": 10,
            "evidence": "Authority claim + payment request + urgency appear together.",
            "indicator_type": "narrative", "severity": "high", "confidence": "medium",
            "timestamp": now_iso(), "provenance": "deterministic combination rule",
        })
    combined = " ".join(a.get("text", "") for a in artifacts)
    weak_only = bool(sigs) and sigs <= {"shortened_url", "upi_identifier_present"}
    if total >= 60:
        band = "High concern"
    elif total >= 30:
        band = "Suspicious"
    elif total == 0 and len(combined.strip()) < 40:
        band = "Insufficient evidence"
    elif weak_only and len(combined.strip()) < 60:
        band = "Insufficient evidence"
    elif total == 0:
        band = "Low concern"
    else:
        band = "Suspicious" if total >= 15 else "Low concern"

    # --- Correlation tiers ---
    edges: list[dict] = []
    # Confirmed: exact shared normalised domain.
    by_domain: dict[str, list[str]] = {}
    for art, res in per_artifact:
        for d in res["indicators"]["domains"]:
            by_domain.setdefault(d, []).append(art.get("id", "?"))
    for dom, ids in by_domain.items():
        if len(set(ids)) > 1:
            edges.append({"type": "confirmed", "via": f"shared domain {dom}",
                          "artifacts": sorted(set(ids)), "confidence": "confirmed",
                          "basis": "exact normalised domain match"})
    # Probable: shared lookalike brand + shared narrative across artifacts.
    brands = set()
    for f in all_findings:
        if f["signal"] == "lookalike_domain":
            m = re.search(r"contains '([^']+)'", f["evidence"]) or re.search(r"from '([^']+)'", f["evidence"])
            if m:
                brands.add(m.group(1))
    if brands and {"authority_impersonation", "payment_request"} <= sigs and len(artifacts) > 1:
        edges.append({"type": "probable", "via": f"shared lookalike brand ({', '.join(sorted(brands))}) + impersonation/payment narrative",
                      "artifacts": [a.get("id", "?") for a in artifacts], "confidence": "probable",
                      "basis": "brand match plus narrative overlap; not an exact identifier match"})
    # Weak: textual similarity between message artifacts.
    texts = [(a.get("id", "?"), a.get("text", "")) for a in artifacts if a.get("type") in ("message", "voice_context")]
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = _jaccard(_tokens(texts[i][1]), _tokens(texts[j][1]))
            if sim >= 0.35:
                edges.append({"type": "weak", "via": f"textual similarity {sim:.2f} (shared wording, not proof of a common source)",
                              "artifacts": [texts[i][0], texts[j][0]], "confidence": "weak",
                              "basis": "token Jaccard similarity"})
    if not edges:
        edges.append({"type": "unknown", "via": "no shared indicator found",
                      "artifacts": [], "confidence": "unknown",
                      "basis": "no confirmed, probable or weak link met its threshold"})

    domains = sorted({d for _, res in per_artifact for d in res["indicators"]["domains"]})
    if band == "High concern":
        action = ("Do not pay, do not share OTP/PIN, and do not stay on the call. "
                  "Hang up, then call back only on a number you already trust — "
                  "never the number shown on screen. Preserve the message, link and "
                  "call details, and if money was lost call 1930 and report at "
                  "cybercrime.gov.in immediately. Recovery is not guaranteed.")
        action_mr = ("पैसे पाठवू नका, OTP/PIN देऊ नका. फोन ठेवा आणि तुम्हाला आधीपासून "
                     "माहीत असलेल्या नंबरवर परत कॉल करा. पुरावे जतन करा; पैसे गेल्यास "
                     "तात्काळ १९३० वर संपर्क साधा.")
    elif band == "Suspicious":
        action = ("Pause before clicking, paying or replying. Verify the sender "
                  "through an independent channel you already trust, and preserve "
                  "the evidence before deleting anything.")
        action_mr = "थांबा. स्वतंत्र मार्गाने तपासा, पुरावे जतन करा, मगच पुढील पाऊल उचला."
    elif band == "Insufficient evidence":
        action = ("Not enough evidence to judge. Do not open shortened or unknown "
                  "links to find out, and do not pay on the basis of this alone.")
        action_mr = "पुरेसा पुरावा नाही. अज्ञात लिंक उघडून तपासू नका."
    else:
        action = ("No suspicious indicators found in the submitted text. That is "
                  "not proof of safety — stay cautious with any follow-up request.")
        action_mr = "सादर केलेल्या मजकुरात संशयास्पद संकेत आढळले नाहीत. तरीही सावध राहा."

    return {
        "band": band, "score": total,
        "findings": all_findings, "unique_findings": unique_findings,
        "domains": domains, "edges": edges,
        "next_action": action, "next_action_marathi": action_mr,
        "limitations": ("Deterministic rules only; no external reputation check ran "
                         "in this mode. A clean result never proves safety, and a "
                         "flag never proves a person is a criminal."),
        "engine": "deterministic-v2",
    }


def main() -> int:
    base = Path(__file__).resolve().parent
    scenarios = json.loads((base / "scenarios.json").read_text(encoding="utf-8"))
    if "--check" in sys.argv:
        for sc in scenarios:
            result = fuse(sc["artifacts"])
            print(f"\n== {sc['id']} — expected: {sc['expected_band']} | got: {result['band']} (score {result['score']})")
            for f in result["unique_findings"]:
                print(f"   + {f['signal']} ({f['weight']}, {f['severity']}/{f['confidence']}): {f['evidence']}")
            for e in result["edges"]:
                print(f"   link [{e['confidence']}]: {e['via']}")
            print(f"   -> {result['next_action']}")
        return 0
    print("Usage: python3 backend/engine.py --check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

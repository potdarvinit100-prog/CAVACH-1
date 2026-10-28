"""Threat-intelligence clients — server-side only, consent-gated.

Rules enforced here:
- Never called without explicit user consent (the caller must pass
  consent=True, which the UI only sets from the Settings toggle).
- URLs are stripped of query, fragment and credentials before sending.
  Private files are NEVER uploaded.
- Timeouts (10s), clear not_checked / error results, no faked verdicts.
- VirusTotal free-tier limits are respected by the caller (4 req/min,
  500/day, no commercial use); this client does not retry aggressively.
"""
from __future__ import annotations

import base64
import os
import urllib.request
import urllib.error
import json
from urllib.parse import urlparse

TIMEOUT = 10


def _clean_url(url: str) -> str:
    raw = url if "://" in url else "https://" + url
    p = urlparse(raw)
    host = (p.hostname or "").lower()
    return f"{p.scheme or 'https'}://{host}{p.path or '/'}"


def _get(url: str, headers: dict) -> tuple[int, dict | str]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:500]
    except Exception as e:  # timeout, DNS, network — reported, not hidden
        return 0, str(e)


def check_safe_browsing(url: str, consent: bool) -> dict:
    if not consent:
        return {"provider": "google_safe_browsing", "verdict": "not_checked",
                "reason": "enrichment consent not granted"}
    key = os.environ.get("GOOGLE_SAFE_BROWSING_API_KEY")
    if not key:
        return {"provider": "google_safe_browsing", "verdict": "not_checked",
                "reason": "API key not configured"}
    clean = _clean_url(url)
    payload = json.dumps({
        "client": {"clientId": "ai-cyber-guardian", "clientVersion": "1.0"},
        "threatInfo": {"threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                       "platformTypes": ["ANY_PLATFORM"], "threatEntryTypes": ["URL"],
                       "threatEntries": [{"url": clean}]},
    }).encode()
    req = urllib.request.Request(
        f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}",
        data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", "ignore"))
    except Exception as e:
        return {"provider": "google_safe_browsing", "verdict": "error", "reason": str(e)}
    if data.get("matches"):
        return {"provider": "google_safe_browsing", "verdict": "malicious",
                "reason": f"{len(data['matches'])} Safe Browsing match(es) for the cleaned URL (query stripped)."}
    return {"provider": "google_safe_browsing", "verdict": "clean",
            "reason": "No Safe Browsing match. A clean result does not prove safety, especially for new domains."}


def check_virustotal(url: str, consent: bool) -> dict:
    if not consent:
        return {"provider": "virustotal", "verdict": "not_checked",
                "reason": "enrichment consent not granted"}
    key = os.environ.get("VIRUSTOTAL_API_KEY")
    if not key:
        return {"provider": "virustotal", "verdict": "not_checked",
                "reason": "API key not configured"}
    clean = _clean_url(url)
    url_id = base64.urlsafe_b64encode(clean.encode()).decode().rstrip("=")
    status, data = _get(f"https://www.virustotal.com/api/v3/urls/{url_id}",
                        {"x-apikey": key})
    if status != 200 or not isinstance(data, dict):
        return {"provider": "virustotal", "verdict": "error",
                "reason": f"VirusTotal lookup failed (status {status})."}
    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    malicious = stats.get("malicious", 0) or 0
    if malicious > 0:
        return {"provider": "virustotal", "verdict": "malicious",
                "reason": f"{malicious} engine(s) flagged this URL; {stats.get('harmless', 0)} harmless."}
    return {"provider": "virustotal", "verdict": "clean",
            "reason": "No engine flagged this URL in the last analysis. A clean result does not prove safety."}

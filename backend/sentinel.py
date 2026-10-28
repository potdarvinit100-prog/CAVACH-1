"""CAVACH Sentinel daily report — generated from real local runs only.

Reads: evaluation_report.json, adversarial_report.json,
rls_test_results.json. Runs: a secret scan over the repo (excluding
node_modules/dist) for obvious secret patterns. Writes:
backend/sentinel_report.json + docs/sentinel-report.md.
Sections: new threats (none — no licensed feed is configured, stated
plainly), self-scan findings, service failures / could-not-check,
review queue (empty — no live investigations), recommended actions.
No fake alerts are ever generated.
Run: python3 backend/sentinel.py
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")

def load(name):
    p = BASE / name
    return json.loads(p.read_text()) if p.exists() else None

def secret_scan():
    hits = []
    for p in ROOT.rglob("*"):
        if any(part in ("node_modules", "dist", ".git", "runs") for part in p.parts):
            continue
        if p.is_file() and p.suffix in (".ts", ".tsx", ".py", ".json", ".md", ".sql"):
            try:
                text = p.read_text(errors="ignore")
            except Exception:
                continue
            if SECRET_RE.search(text):
                hits.append(str(p.relative_to(ROOT)))
    return hits

def main():
    ev, adv, rls = load("evaluation_report.json"), load("adversarial_report.json"), ROOT / "supabase/rls_test_results.json"
    rls_data = json.loads(rls.read_text()) if rls.exists() else {"status": "not_run"}
    secrets = secret_scan()
    report = {
        "date": datetime.now(timezone.utc).isoformat(),
        "evaluation": ev["overall"] if ev else None,
        "heldout": ev["heldout"] if ev else None,
        "adversarial": {"n": adv["n"], "evasion_rate": adv["evasion_rate"]} if adv else None,
        "rls_test": rls_data,
        "secret_scan_hits": secrets,
        "could_not_check": [
            "Supabase live project (no project configured in this workspace) — RLS test recorded as not_run.",
            "LLM provider (no key configured) — explanations fall back to the deterministic template.",
            "Safe Browsing / VirusTotal (no keys configured) — enrichment reports not_checked.",
            "n8n instance (not connected) — workflows are importable JSON, not live runs.",
            "Licensed public intel feeds (none configured) — no campaign clusters are claimed.",
        ],
        "review_queue": [],
        "recommended_actions": [
            "Run supabase/rls_test.py against a real project with two accounts before presenting RLS as verified.",
            "Configure one reputation key (Safe Browsing) and one LLM key to turn not_checked/fallback states into live ones.",
            "Re-tune the two held-out misses (job registration fee wording, 'connection will be cut') only against a FRESH held-out set, not this one.",
        ],
    }
    (BASE / "sentinel_report.json").write_text(json.dumps(report, indent=2))
    md = f"""# CAVACH Sentinel daily report — {report['date']}

Generated from real local runs (evaluation, adversarial, RLS status, secret scan).
No fake alerts: sections with no data say so plainly.

- Evaluation (test-set, not real-world): n={report['evaluation']['n'] if report['evaluation'] else 'n/a'}, precision={report['evaluation']['precision'] if report['evaluation'] else 'n/a'}, recall={report['evaluation']['recall'] if report['evaluation'] else 'n/a'}
- Held-out: {report['heldout']}
- Adversarial evasion rate: {report['adversarial']['evasion_rate'] if report['adversarial'] else 'n/a'} (n={report['adversarial']['n'] if report['adversarial'] else 'n/a'})
- RLS test: {rls_data.get('status')} — {rls_data.get('reason', '')}
- Secret scan hits: {secrets if secrets else 'none'}

## Could not check
{chr(10).join('- ' + x for x in report['could_not_check'])}

## Review queue
Empty (no live investigations in this workspace).

## Recommended actions
{chr(10).join('- ' + x for x in report['recommended_actions'])}
"""
    (ROOT / "docs/sentinel-report.md").write_text(md)
    print(md)
    return report

if __name__ == "__main__":
    main()

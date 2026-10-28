"""Lightweight file/text indicator matching (YARA-style rules, stdlib only).

This is deliberately NOT presented as YARA or ClamAV: those tools need
their engines installed and, for ClamAV, a daemon/scan binary. This module
applies the curated text rules in rules/rules.json to submitted text
content and reports which rules fired, with the rule id as provenance.
A real deployment should add yara-python (compiled .yar rules, sandboxed
scanning) and clamscan (if available) behind the same consent gate, and
must never scan a third-party system or upload a private file without
explicit authorisation.
"""
from __future__ import annotations

import json
from pathlib import Path

RULES = json.loads((Path(__file__).resolve().parent / "rules/rules.json").read_text(encoding="utf-8"))["rules"]


def scan_text(text: str) -> list[dict]:
    lowered = (text or "").lower()
    fired = []
    for rule in RULES:
        hits = [p for p in rule["patterns"] if p.lower() in lowered]
        if hits:
            fired.append({"rule_id": rule["id"], "matched_patterns": hits, "note": rule["note"]})
    return fired

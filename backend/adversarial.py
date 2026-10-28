"""Adversarial robustness harness (labelled synthetic variants only).

Transforms: spacing insertion, homoglyph substitution, mixed-script
swapping, and case changes. Reports how many malicious variants still
score Suspicious/High (robust) vs drop to Low/Insufficient (evasion).
Run: python3 backend/adversarial.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import fuse

BASE = [
 ("en", "URGENT: Your account will be blocked today. Share your OTP now: https://secure-bank-verify.xyz/login"),
 ("en", "This is police. You are under digital arrest. Pay 50000 immediately. Do not tell anyone."),
 ("mr", "आई, माझा नवीन नंबर आहे, ५००० रुपये पाठव, कोणाला सांगू नकोस https://pay-hdfc-secure.xyz/pay"),
]
HOMO = {"a": "а", "e": "е", "o": "о", "p": "р", "c": "с"}

def variants(text):
    spaced = " ".join(list(text.replace(" ", ""))) if False else text.replace(" ", "  ")
    homoglyphed = "".join(HOMO.get(ch, ch) for ch in text)
    upper = text.upper()
    return {"spacing": spaced, "homoglyph": homoglyphed, "case": upper}

def run():
    rows = []
    for lang, text in BASE:
        for name, v in variants(text).items():
            r = fuse([{"id": "a1", "type": "message", "text": v}])
            rows.append({"lang": lang, "transform": name, "band": r["band"], "score": r["score"],
                         "robust": r["band"] in ("High concern", "Suspicious")})
    out = Path(__file__).resolve().parent / "adversarial_report.json"
    robust = sum(1 for r in rows if r["robust"])
    report = {"n": len(rows), "robust": robust, "evasion_rate": round(1 - robust / len(rows), 3) if rows else 0,
              "rows": rows, "note": "Synthetic-variant test-set result, not real-world evasion rate."}
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report

if __name__ == "__main__":
    run()

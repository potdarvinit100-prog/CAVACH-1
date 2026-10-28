"""Evaluate the deterministic engine on the labelled scenario set ONLY.

This reports test-set accuracy / precision / recall / FP / FN. It is NOT a
real-world detection rate, and must never be quoted as one.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import fuse  # noqa: E402

base = Path(__file__).resolve().parent
scenarios = json.loads((base / "scenarios.json").read_text(encoding="utf-8"))

POSITIVE = {"High concern", "Suspicious"}
tp = fp = tn = fn = 0
rows = []
for sc in scenarios:
    got = fuse(sc["artifacts"])["band"]
    exp, ok = sc["expected_band"], got == sc["expected_band"]
    rows.append((sc["id"], exp, got, ok))
    if exp in POSITIVE and got in POSITIVE:
        tp += 1
    elif exp in POSITIVE:
        fn += 1
    elif got in POSITIVE:
        fp += 1
    else:
        tn += 1

for r in rows:
    print(f"{'PASS' if r[3] else 'FAIL'}  {r[0]:28s} expected={r[1]:22s} got={r[2]}")
prec = tp / (tp + fp) if tp + fp else 0
rec = tp / (tp + fn) if tp + fn else 0
band_acc = sum(1 for r in rows if r[3]) / len(rows)
print(f"\nTest-set only (n={len(scenarios)}): exact-band accuracy={band_acc:.2f} "
      f"binary precision={prec:.2f} recall={rec:.2f} TP={tp} FP={fp} TN={tn} FN={fn}")
print("Do not quote these numbers as real-world performance.")

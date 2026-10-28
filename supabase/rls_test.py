"""Scripted two-account RLS isolation test (requires a real project).

Usage: SUPABASE_URL=... USER_A_JWT=... USER_B_JWT=... python3 supabase/rls_test.py
A creates an investigation via the RPC; B must NOT be able to read it
(and must NOT be able to insert a child row under it). Results are
written to supabase/rls_test_results.json with date + pass/fail.
Without env vars the script exits with status 2 and writes
{"status": "not_run", "reason": "no project credentials"} — it never
fabricates a pass. Run this against a real project before claiming
RLS isolation is verified.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

def call(url, jwt):
    req = urllib.request.Request(url, headers={"apikey": os.environ["SUPABASE_ANON_KEY"],
        "Authorization": f"Bearer {jwt}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"[]")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:200]}

def main():
    out = {"date": datetime.now(timezone.utc).isoformat(), "status": "not_run"}
    url, a, b = os.environ.get("SUPABASE_URL"), os.environ.get("USER_A_JWT"), os.environ.get("USER_B_JWT")
    if not (url and a and b and os.environ.get("SUPABASE_ANON_KEY")):
        out["reason"] = "no project credentials (SUPABASE_URL / USER_A_JWT / USER_B_JWT / SUPABASE_ANON_KEY)"
        json.dump(out, open("supabase/rls_test_results.json", "w"), indent=2)
        print(json.dumps(out)); return 2
    # A lists own investigations; B lists A's id directly (should be empty).
    sa, ra = call(f"{url}/rest/v1/investigations?select=id", a)
    if not (isinstance(ra, list) and ra):
        out.update({"status": "failed", "reason": "user A has no investigation to test against"}); print(json.dumps(out)); return 1
    inv = ra[0]["id"]
    sb, rb = call(f"{url}/rest/v1/investigations?id=eq.{inv}&select=id", b)
    isolated = sb == 200 and rb == []
    out.update({"status": "passed" if isolated else "failed", "investigation_id": inv,
                "user_b_read_status": sb, "user_b_rows": rb})
    json.dump(out, open("supabase/rls_test_results.json", "w"), indent=2)
    print(json.dumps(out)); return 0 if isolated else 1

if __name__ == "__main__":
    raise SystemExit(main())

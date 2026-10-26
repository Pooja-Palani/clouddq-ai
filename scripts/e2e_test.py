"""End-to-end test of the live CloudDQ AI platform.

Creates 20 new data assets, re-analyses each one 4 times along a quality
trajectory (improving / declining / stable / volatile / recovering) so the
trend score can be checked, then exercises every other API feature.

Usage:  CLOUDDQ_PASSWORD=... python3 scripts/e2e_test.py
Output: report/test_results/e2e_results.json and e2e_results.md
"""
from __future__ import annotations

import csv
import io
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

REGION = "us-east-1"
API = "https://fdro0463k8.execute-api.us-east-1.amazonaws.com/prod"
CLIENT_ID = "7hhl4r28t393ujpgif37vsv07m"
DATA_USER = "datauser@clouddq.com"
BUSINESS_USER = "businessuser@clouddq.com"
PASSWORD = os.environ["CLOUDDQ_PASSWORD"]
OUT = Path(__file__).resolve().parent.parent / "report" / "test_results"
RUN_TAG = time.strftime("%m%d-%H%M")

# defect rate per version (fraction of rows touched by each defect type)
TRAJECTORIES = {
    "improving": [0.55, 0.35, 0.18, 0.02],
    "declining": [0.02, 0.18, 0.35, 0.55],
    "stable": [0.06, 0.06, 0.06, 0.06],
    "volatile": [0.02, 0.50, 0.03, 0.45],
    "recovering": [0.05, 0.50, 0.25, 0.03],
}

FIRST = ["Aarav", "Diya", "Kavin", "Meera", "Rohan", "Sara", "Arjun", "Nila", "Vikram", "Anika", "Lathika", "Dewlyn"]
LAST = ["Sharma", "Iyer", "Nair", "Reddy", "Patel", "Das", "Menon", "Rao", "Gupta", "Shree"]
CITIES = ["Chennai", "Mumbai", "Delhi", "Bengaluru", "Kochi", "Pune", "Hyderabad"]


def _name(r):
    return f"{r.choice(FIRST)} {r.choice(LAST)}"


def _email(r, name):
    return f"{name.lower().replace(' ', '.')}{r.randint(1, 99)}@example.com"


def _phone(r):
    return f"+91 9{r.randint(100000000, 999999999)}"


def _day(r, back=30):
    return (date.today() - timedelta(days=r.randint(0, back))).isoformat()


# 20 asset definitions: name -> (id prefix, column builders)
ASSETS = [
    ("Retail Orders", "ORD", {"customer": _name, "city": lambda r: r.choice(CITIES), "amount": lambda r: round(r.uniform(100, 9000), 2), "order_date": _day}),
    ("Patient Admissions", "PAT", {"patient_name": _name, "age": lambda r: r.randint(1, 95), "ward": lambda r: r.choice(["ICU", "General", "Pediatric"]), "admit_date": _day}),
    ("Bank Transactions", "TXN", {"account_holder": _name, "amount": lambda r: round(r.uniform(-50, 50000), 2), "channel": lambda r: r.choice(["UPI", "NEFT", "Card"]), "txn_date": _day}),
    ("Student Enrollment", "STU", {"student_name": _name, "email": "email", "course": lambda r: r.choice(["CSE", "ECE", "IT", "MECH"]), "enrolled_on": _day}),
    ("Supplier Registry", "SUP", {"supplier": lambda r: r.choice(["Acme", "Globex", "Initech", "Umbrella"]) + " Ltd", "contact_email": "email", "phone": _phone, "city": lambda r: r.choice(CITIES)}),
    ("Inventory Stock", "SKU", {"product": lambda r: r.choice(["Laptop", "Mouse", "Monitor", "Keyboard"]), "quantity": lambda r: r.randint(0, 500), "price": lambda r: round(r.uniform(5, 1500), 2), "restocked_on": _day}),
    ("Insurance Claims", "CLM", {"claimant": _name, "claim_amount": lambda r: round(r.uniform(1000, 200000), 2), "status": lambda r: r.choice(["Open", "Approved", "Rejected"]), "filed_on": _day}),
    ("HR Payroll", "EMP", {"employee": _name, "email": "email", "salary_amount": lambda r: round(r.uniform(20000, 250000), 2), "pay_date": _day}),
    ("Marketing Leads", "LEAD", {"lead_name": _name, "email": "email", "phone": _phone, "source": lambda r: r.choice(["Web", "Event", "Referral"])}),
    ("Flight Bookings", "PNR", {"passenger": _name, "route": lambda r: r.choice(["MAA-DEL", "BOM-BLR", "COK-HYD"]), "fare_amount": lambda r: round(r.uniform(2500, 22000), 2), "travel_date": _day}),
    ("Hotel Reservations", "RES", {"guest": _name, "email": "email", "nights": lambda r: r.randint(1, 10), "checkin_date": _day}),
    ("IoT Sensor Readings", "DEV", {"site": lambda r: r.choice(CITIES), "temperature": lambda r: round(r.uniform(18, 42), 1), "humidity": lambda r: round(r.uniform(20, 95), 1), "reading_date": lambda r: _day(r, 5)}),
    ("Vendor Invoices", "INV", {"vendor": lambda r: r.choice(["Acme", "Globex", "Initech"]), "invoice_amount": lambda r: round(r.uniform(500, 90000), 2), "currency": lambda r: r.choice(["INR", "USD"]), "invoice_date": _day}),
    ("Customer Support Tickets", "TKT", {"customer": _name, "email": "email", "priority": lambda r: r.choice(["Low", "Medium", "High"]), "opened_on": _day}),
    ("Loan Applications", "LOAN", {"applicant": _name, "age": lambda r: r.randint(21, 70), "loan_amount": lambda r: round(r.uniform(50000, 5000000), 2), "applied_on": _day}),
    ("E-commerce Returns", "RET", {"customer": _name, "reason": lambda r: r.choice(["Damaged", "Wrong size", "Late"]), "refund_amount": lambda r: round(r.uniform(100, 8000), 2), "returned_on": _day}),
    ("Fleet Maintenance", "VEH", {"vehicle": lambda r: r.choice(["Truck", "Van", "Bike"]), "odometer": lambda r: r.randint(1000, 300000), "service_cost_amount": lambda r: round(r.uniform(500, 40000), 2), "serviced_on": _day}),
    ("Event Registrations", "REG", {"attendee": _name, "email": "email", "phone": _phone, "event": lambda r: r.choice(["AWS Summit", "DevFest", "PyCon"])}),
    ("Energy Meter Readings", "MTR", {"city": lambda r: r.choice(CITIES), "kwh": lambda r: round(r.uniform(50, 900), 2), "tariff": lambda r: r.choice(["Domestic", "Commercial"]), "read_on": lambda r: _day(r, 10)}),
    ("Clinical Lab Results", "LAB", {"patient_name": _name, "age": lambda r: r.randint(1, 95), "test": lambda r: r.choice(["CBC", "Lipid", "HbA1c"]), "result_date": _day}),
]
PATTERNS = list(TRAJECTORIES)


def build_csv(index: int, version: int, defect: float, rows: int = 120) -> str:
    name, prefix, cols = ASSETS[index]
    r = random.Random(index * 1000 + round(defect * 100))
    out = io.StringIO()
    header = ["record_id", *cols]
    writer = csv.DictWriter(out, fieldnames=header)
    writer.writeheader()
    for i in range(rows):
        row = {"record_id": f"{prefix}-{i:05d}"}
        person = None
        for col, gen in cols.items():
            if gen == "email":
                person = person or _name(r)
                row[col] = _email(r, person)
            else:
                val = gen(r)
                if gen is _name:
                    person = val
                row[col] = val
        if r.random() < defect:  # missing values
            row[r.choice(list(cols))] = ""
        if r.random() < defect:  # duplicate key
            row["record_id"] = f"{prefix}-{max(0, i - 1):05d}"
        if r.random() < defect:  # inconsistent casing / bad formats / out of range
            col = r.choice(list(cols))
            v = row[col]
            if "email" in col and v:
                row[col] = str(v).replace("@", "_at_")
            elif "date" in col or col.endswith("_on"):
                row[col] = (date.today() + timedelta(days=r.randint(30, 400))).isoformat()
            elif col == "age":
                row[col] = r.randint(130, 200)
            elif "amount" in col or col == "price":
                row[col] = -abs(float(v or 1))
            elif isinstance(v, str):
                row[col] = v.upper()
        writer.writerow(row)
    return out.getvalue()


# ---------------------------------------------------------------- HTTP helpers
def login(username: str) -> str:
    req = urllib.request.Request(
        f"https://cognito-idp.{REGION}.amazonaws.com/",
        data=json.dumps({"AuthFlow": "USER_PASSWORD_AUTH", "ClientId": CLIENT_ID,
                         "AuthParameters": {"USERNAME": username, "PASSWORD": PASSWORD}}).encode(),
        headers={"Content-Type": "application/x-amz-json-1.1",
                 "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["AuthenticationResult"]["IdToken"]


def call(token: str | None, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            raw = e.read()
            if e.code in (429, 502, 503, 504) and attempt < 2:
                time.sleep(2 + attempt * 3)
                continue
            try:
                return e.code, json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return e.code, {"raw": raw.decode(errors="replace")}
    raise RuntimeError("unreachable")


def put_s3(url: str, text: str) -> int:
    req = urllib.request.Request(url, data=text.encode(), method="PUT", headers={"Content-Type": "text/csv"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status


# ---------------------------------------------------------------- test runner
class Results:
    def __init__(self):
        self.checks: list[dict] = []

    def check(self, area: str, name: str, ok: bool, detail: str = ""):
        self.checks.append({"area": area, "name": name, "pass": bool(ok), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {area}: {name}" + (f" — {detail}" if detail else ""), flush=True)


def upload_version(token: str, index: int, version: int, defect: float, filename: str) -> dict:
    status, up = call(token, "POST", "/datasets/upload-url", {"filename": filename, "contentType": "text/csv"})
    if status != 200:
        raise RuntimeError(f"upload-url {status} {up}")
    put_s3(up["uploadUrl"], build_csv(index, version, defect))
    return up


def create_asset(token: str, index: int) -> dict:
    name, prefix, _ = ASSETS[index]
    pattern = PATTERNS[index % len(PATTERNS)]
    levels = TRAJECTORIES[pattern]
    filename = f"{prefix.lower()}_{RUN_TAG}.csv"
    up = upload_version(token, index, 0, levels[0], filename)
    status, ds = call(token, "POST", "/datasets", {"datasetId": up["datasetId"], "s3Key": up["s3Key"],
                                                   "name": f"{name} ({RUN_TAG})", "filename": filename})
    if status != 201:
        raise RuntimeError(f"register {status} {ds}")
    dataset_id = ds["datasetId"]
    runs = []
    for v, defect in enumerate(levels):
        body = {}
        if v > 0:
            body = {"s3Key": upload_version(token, index, v, defect, filename)["s3Key"]}
        status, res = call(token, "POST", f"/datasets/{dataset_id}/analyze", body)
        if status != 200:
            raise RuntimeError(f"analyze v{v + 1} {status} {res}")
        runs.append(res["run"])
    final = res["dataset"]
    return {
        "index": index, "datasetId": dataset_id, "name": final["name"], "pattern": pattern,
        "defect_levels": levels, "scores": [r["dq_score"] for r in runs],
        "health": final["latestHealth"], "trend": final.get("trend"),
        "pii_hints": runs[-1].get("pii_hints") or [], "anomalies": [a["type"] for a in runs[-1].get("anomalies") or []],
        "issues": runs[-1]["severity"]["total"],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    res = Results()
    started = time.time()

    # Auth
    status, body = call(None, "GET", "/datasets")
    res.check("Security", "API rejects requests without a Cognito token", status == 401, f"HTTP {status}")
    data_tok = login(DATA_USER)
    biz_tok = login(BUSINESS_USER)
    res.check("Auth", "Cognito login — DataUser and BusinessUser", bool(data_tok and biz_tok))
    status, body = call(data_tok, "GET", "/health")
    res.check("API", "Health endpoint", status == 200 and body.get("status") == "ok", json.dumps(body))

    # 20 new data assets × 4 runs
    t0 = time.time()
    assets, errors = [], []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(create_asset, data_tok, i) for i in range(len(ASSETS))]
        for f in futures:
            try:
                assets.append(f.result())
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))
    assets.sort(key=lambda a: a["index"])
    res.check("Upload & analysis", "20 new data assets uploaded to S3, registered and analysed 4× each",
              len(assets) == 20 and not errors,
              f"{len(assets)} assets, {sum(len(a['scores']) for a in assets)} runs in {time.time() - t0:.0f}s"
              + (f"; errors: {errors[:3]}" if errors else ""))

    # Trend analysis
    expected = {"improving": "Improving", "declining": "Declining", "stable": "Stable", "recovering": None, "volatile": None}
    trend_ok = 0
    for a in assets:
        t = a["trend"] or {}
        ok = t.get("runs") == 4 and t.get("trend_score") is not None and 0 <= t["trend_score"] <= 100
        want = expected[a["pattern"]]
        if want:
            ok = ok and t.get("direction") == want
        trend_ok += ok
    res.check("Trend analysis", "Trend score computed for every asset (0–100) with correct direction",
              trend_ok == len(assets), f"{trend_ok}/{len(assets)} correct")
    vol = [a["trend"]["volatility"] for a in assets if a["pattern"] == "volatile"]
    stab = [a["trend"]["volatility"] for a in assets if a["pattern"] == "stable"]
    res.check("Trend analysis", "Volatile assets show higher volatility than stable assets",
              min(vol) > max(stab), f"volatile σ={vol}, stable σ={stab}")

    status, port = call(biz_tok, "GET", "/trends")
    ours = {a["datasetId"] for a in assets}
    port_ids = {d["datasetId"] for d in port.get("datasets", [])}
    res.check("Trend analysis", "Portfolio trend endpoint (GET /trends) aggregates all assets",
              status == 200 and ours <= port_ids,
              f"avg trend score {port.get('average_trend_score')}, counts {port.get('counts')}")

    # Anomaly detection
    declining_anoms = [a for a in assets if a["pattern"] == "declining" and a["anomalies"]]
    res.check("Anomaly detection", "Run-over-run anomalies raised on declining assets",
              len(declining_anoms) > 0, f"{len(declining_anoms)} declining assets flagged: "
              + ", ".join(sorted({x for a in declining_anoms for x in a["anomalies"]})))

    # Comprehend PII
    pii = [a for a in assets if any(h.get("source") == "comprehend" for h in a["pii_hints"])]
    res.check("Amazon Comprehend", "PII columns detected by Comprehend", len(pii) >= 5,
              f"{len(pii)} assets with Comprehend PII hints, e.g. "
              + "; ".join(f"{a['name'].split(' (')[0]}: " + ", ".join(h["column"] for h in a["pii_hints"]) for a in pii[:3]))

    # Registry / RBAC visibility
    status, mine = call(data_tok, "GET", "/datasets")
    res.check("Repository", "DataUser lists own datasets (includes all 20)",
              status == 200 and ours <= {d["datasetId"] for d in mine["datasets"]}, f"{len(mine.get('datasets', []))} datasets")
    status, allds = call(biz_tok, "GET", "/datasets")
    res.check("Repository", "BusinessUser sees the portfolio (includes all 20)",
              status == 200 and ours <= {d["datasetId"] for d in allds["datasets"]}, f"{len(allds.get('datasets', []))} datasets")

    sample = next(a for a in assets if a["pattern"] == "improving")
    sid = sample["datasetId"]
    status, runs = call(data_tok, "GET", f"/datasets/{sid}/runs")
    res.check("Run history", "GET /runs returns all 4 runs in order", status == 200 and len(runs["runs"]) == 4,
              " → ".join(str(r["dq_score"]) for r in runs.get("runs", [])))
    status, rep = call(biz_tok, "GET", f"/datasets/{sid}/report")
    res.check("Reports", "Quality report (6 dimensions, heatmap, issues)",
              status == 200 and len(rep["run"]["dimensions"]) == 6 and rep["run"]["heatmap"], json.dumps(rep["run"]["dimensions"]))
    status, exp = call(biz_tok, "GET", f"/datasets/{sid}/export")
    res.check("Reports", "CSV export includes trend score", status == 200 and "Trend score" in exp.get("content", ""),
              exp.get("filename", ""))

    # Issue lifecycle on a declining asset (has open issues)
    bad = min(assets, key=lambda a: a["scores"][-1])
    bid = bad["datasetId"]
    status, iss = call(data_tok, "GET", f"/datasets/{bid}/issues")
    issues = iss.get("issues", [])
    res.check("Issues", "Rule breaches generate issues", status == 200 and len(issues) > 0, f"{len(issues)} issues on {bad['name']}")
    if issues:
        first = issues[0]["issue_id"]
        s1, a1 = call(data_tok, "POST", f"/issues/{first}/assign", {"datasetId": bid})
        s2, a2 = call(data_tok, "POST", f"/issues/{first}/acknowledge", {"datasetId": bid})
        res.check("Issues", "Assign → acknowledge lifecycle", s1 == 200 and s2 == 200 and a2["status"] == "IN_PROGRESS",
                  f"{a1.get('status')} → {a2.get('status')}")
        _, bad_meta = call(data_tok, "GET", f"/datasets/{bid}")
        bad_dims = bad_meta.get("latestDimensions") or {}
        failing = next((i for i in issues if bad_dims.get(i.get("dimension"), 100) < i.get("threshold", 0)), issues[0])
        s3, a3 = call(data_tok, "POST", f"/issues/{failing['issue_id']}/resolve", {"datasetId": bid})
        res.check("Issues", "Resolve is blocked when re-validation still fails", s3 == 400, a3.get("error", a3.get("message", ""))[:120])
        s4, a4 = call(data_tok, "POST", f"/issues/{first}/reopen", {"datasetId": bid})
        res.check("Issues", "Reopen issue", s4 == 200 and a4["status"] == "OPEN")

    # Resolve succeeds once data improved: improving asset's old issues now pass re-validation
    status, iss = call(data_tok, "GET", f"/datasets/{sid}/issues")
    status_dims = rep["run"]["dimensions"]
    passing = [i for i in iss.get("issues", []) if status_dims.get(i.get("dimension"), 0) >= i.get("threshold", 101)]
    if passing:
        s5, a5 = call(data_tok, "POST", f"/issues/{passing[0]['issue_id']}/resolve", {"datasetId": sid})
        res.check("Issues", "Resolve succeeds after data was corrected and re-analysed", s5 == 200 and a5["status"] == "RESOLVED",
                  f"{passing[0]['rule_name']} on {sample['name']}")

    # Alerts + SNS
    s, alert = call(biz_tok, "POST", "/alerts", {"datasetId": bid, "note": "E2E test: quality dropped, please fix."})
    res.check("Alerts & SNS", "BusinessUser raises alert on unhealthy asset; SNS publish succeeds",
              s == 201 and alert.get("notified") is True, f"alert {alert.get('alertId')}, notified={alert.get('notified')}")
    healthy = max(assets, key=lambda a: a["scores"][-1])
    s, gated = call(biz_tok, "POST", "/alerts", {"datasetId": healthy["datasetId"], "note": "should be gated"})
    res.check("Alerts & SNS", "Alert gate blocks alerts on healthy assets (no force)", s == 400, f"{healthy['name']} score {healthy['scores'][-1]}")
    s, inbox = call(data_tok, "GET", "/alerts")
    res.check("Alerts & SNS", "DataUser inbox receives the alert",
              s == 200 and any(x["alertId"] == alert.get("alertId") for x in inbox["alerts"]), f"{len(inbox.get('alerts', []))} alerts")
    s, one = call(data_tok, "GET", f"/alerts/{alert.get('alertId')}")
    res.check("Alerts & SNS", "Alert detail", s == 200 and one.get("status") == "OPEN")
    if issues:
        call(data_tok, "POST", f"/issues/{issues[0]['issue_id']}/acknowledge", {"datasetId": bid})
        s, d = call(data_tok, "GET", f"/datasets/{bid}")
        res.check("Workflow", "Acknowledging moves alerted dataset to InCorrection", d.get("workflowStatus") == "InCorrection",
                  d.get("workflowStatus", ""))

    s, d = call(data_tok, "POST", f"/datasets/{sid}/correction", {"note": "E2E correction flow"})
    res.check("Workflow", "Move to correction", s == 200 and d.get("workflowStatus") == "InCorrection")

    # AI summary
    s, summ = call(biz_tok, "POST", f"/datasets/{sid}/summary")
    model = summ.get("model")
    res.check("AI summary", "Summary endpoint returns an executive summary + recommendations",
              s == 200 and summ.get("executive_summary") and summ.get("recommendations"),
              f"model={model} ({'Bedrock still blocked — offline template used' if summ.get('offline') else 'Amazon Bedrock'})")

    # RBAC + validation
    s, _ = call(biz_tok, "POST", f"/datasets/{sid}/analyze", {})
    res.check("Security", "BusinessUser cannot run analysis (403)", s == 403, f"HTTP {s}")
    s, _ = call(data_tok, "POST", "/alerts", {"datasetId": bid})
    res.check("Security", "DataUser cannot raise alerts (403)", s == 403, f"HTTP {s}")
    s, _ = call(biz_tok, "POST", "/datasets/upload-url", {"filename": "x.csv"})
    res.check("Security", "BusinessUser cannot upload (403)", s == 403, f"HTTP {s}")
    s, b = call(data_tok, "POST", "/datasets/upload-url", {"filename": "notes.txt"})
    res.check("Validation", "Non-CSV upload rejected (400)", s == 400, b.get("error", ""))
    s, _ = call(data_tok, "POST", "/datasets", {"name": "no key"})
    res.check("Validation", "Register without s3Key rejected (400)", s == 400, f"HTTP {s}")
    s, _ = call(data_tok, "GET", "/datasets/does-not-exist")
    res.check("Validation", "Unknown dataset returns 404", s == 404, f"HTTP {s}")

    elapsed = round(time.time() - started)
    passed = sum(c["pass"] for c in res.checks)
    summary = {"run_tag": RUN_TAG, "elapsed_s": elapsed, "passed": passed, "total": len(res.checks),
               "checks": res.checks, "assets": assets, "portfolio": port}
    (OUT / "e2e_results.json").write_text(json.dumps(summary, indent=2))
    write_markdown(summary)
    print(f"\n{passed}/{len(res.checks)} checks passed in {elapsed}s")
    return 0 if passed == len(res.checks) else 1


def write_markdown(s: dict) -> None:
    lines = [f"# CloudDQ AI — end-to-end test ({s['run_tag']})", "",
             f"**{s['passed']}/{s['total']} checks passed** in {s['elapsed_s']} s against the live AWS stack.", "",
             "## Checks", "", "| Area | Check | Result | Detail |", "|---|---|---|---|"]
    for c in s["checks"]:
        lines.append(f"| {c['area']} | {c['name']} | {'PASS' if c['pass'] else 'FAIL'} | {c['detail'].replace('|', '/')} |")
    lines += ["", "## Trend analysis — 20 new data assets (4 runs each)", "",
              "| # | Asset | Planned path | DQ scores (run 1→4) | Direction | Trend score | Slope pp/run | Volatility | Forecast next |",
              "|---|---|---|---|---|---|---|---|---|"]
    for a in s["assets"]:
        t = a["trend"] or {}
        lines.append(f"| {a['index'] + 1} | {a['name']} | {a['pattern']} | {' → '.join(f'{x:.1f}' for x in a['scores'])} | "
                     f"{t.get('direction')} | {t.get('trend_score')} | {t.get('slope_per_run')} | {t.get('volatility')} | {t.get('forecast_next')} |")
    p = s["portfolio"]
    lines += ["", f"Portfolio average trend score: **{p.get('average_trend_score')}** · direction counts: {p.get('counts')}", "",
              "Trend score = 0.7 × momentum + 0.3 × stability, where momentum = 50 + 5 × slope (pp per run) "
              "and stability = 100 − 4 × std-dev of scores, each clamped to 0–100. 50 means flat."]
    (OUT / "e2e_results.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())

# CloudDQ AI — end-to-end test (1026-0708)

**32/32 checks passed** in 87 s against the live AWS stack.

## Checks

| Area | Check | Result | Detail |
|---|---|---|---|
| Security | API rejects requests without a Cognito token | PASS | HTTP 401 |
| Auth | Cognito login — DataUser and BusinessUser | PASS |  |
| API | Health endpoint | PASS | {"service": "CloudDQ AI", "status": "ok"} |
| Upload & analysis | 20 new data assets uploaded to S3, registered and analysed 4× each | PASS | 20 assets, 80 runs in 53s |
| Trend analysis | Trend score computed for every asset (0–100) with correct direction | PASS | 20/20 correct |
| Trend analysis | Volatile assets show higher volatility than stable assets | PASS | volatile σ=[4.86, 4.56, 5.04, 10.43], stable σ=[0, 0, 0, 0] |
| Trend analysis | Portfolio trend endpoint (GET /trends) aggregates all assets | PASS | avg trend score 58.8, counts {'Declining': 8, 'Stable': 7, 'Improving': 6, 'Baseline': 1} |
| Anomaly detection | Run-over-run anomalies raised on declining assets | PASS | 2 declining assets flagged: dimension_score_drop |
| Amazon Comprehend | PII columns detected by Comprehend | PASS | 17 assets with Comprehend PII hints, e.g. Retail Orders: customer, city; Patient Admissions: patient_name; Bank Transactions: account_holder |
| Repository | DataUser lists own datasets (includes all 20) | PASS | 22 datasets |
| Repository | BusinessUser sees the portfolio (includes all 20) | PASS | 22 datasets |
| Run history | GET /runs returns all 4 runs in order | PASS | 87.44 → 91.19 → 93.62 → 99.62 |
| Reports | Quality report (6 dimensions, heatmap, issues) | PASS | {"accuracy": 100, "completeness": 100, "consistency": 100, "timeliness": 100, "uniqueness": 97.5, "validity": 100} |
| Reports | CSV export includes trend score | PASS | Retail Orders (1026-0708)_dq_report.csv |
| Issues | Rule breaches generate issues | PASS | 11 issues on Fleet Maintenance (1026-0708) |
| Issues | Assign → acknowledge lifecycle | PASS | ASSIGNED → IN_PROGRESS |
| Issues | Resolve is blocked when re-validation still fails | PASS | Re-validation failed: completeness is 89.83% (threshold 95%). Re-run analysis after fixing data. |
| Issues | Reopen issue | PASS |  |
| Issues | Resolve succeeds after data was corrected and re-analysed | PASS | Overall Completeness on Retail Orders (1026-0708) |
| Alerts & SNS | BusinessUser raises alert on unhealthy asset; SNS publish succeeds | PASS | alert a492d1aa-deda-4310-8cf3-d87ac103e536, notified=True |
| Alerts & SNS | Alert gate blocks alerts on healthy assets (no force) | PASS | Hotel Reservations (1026-0708) score 99.65 |
| Alerts & SNS | DataUser inbox receives the alert | PASS | 2 alerts |
| Alerts & SNS | Alert detail | PASS |  |
| Workflow | Acknowledging moves alerted dataset to InCorrection | PASS | InCorrection |
| Workflow | Move to correction | PASS |  |
| AI summary | Summary endpoint returns an executive summary + recommendations | PASS | model=offline-template (Bedrock still blocked — offline template used) |
| Security | BusinessUser cannot run analysis (403) | PASS | HTTP 403 |
| Security | DataUser cannot raise alerts (403) | PASS | HTTP 403 |
| Security | BusinessUser cannot upload (403) | PASS | HTTP 403 |
| Validation | Non-CSV upload rejected (400) | PASS | Only CSV files are supported |
| Validation | Register without s3Key rejected (400) | PASS | HTTP 400 |
| Validation | Unknown dataset returns 404 | PASS | HTTP 404 |

## Trend analysis — 20 new data assets (4 runs each)

| # | Asset | Planned path | DQ scores (run 1→4) | Direction | Trend score | Slope pp/run | Volatility | Forecast next |
|---|---|---|---|---|---|---|---|---|
| 1 | Retail Orders (1026-0708) | improving | 87.4 → 91.2 → 93.6 → 99.6 | Improving | 73.3 | 3.9 | 4.43 | 100 |
| 2 | Patient Admissions (1026-0708) | declining | 99.5 → 94.9 → 91.2 → 89.7 | Declining | 48.9 | -3.31 | 3.78 | 85.57 |
| 3 | Bank Transactions (1026-0708) | stable | 94.5 → 94.5 → 94.5 → 94.5 | Stable | 65 | 0 | 0 | 94.48 |
| 4 | Student Enrollment (1026-0708) | volatile | 99.7 → 88.7 → 99.2 → 91.0 | Declining | 53.6 | -1.58 | 4.86 | 90.68 |
| 5 | Supplier Registry (1026-0708) | recovering | 92.0 → 76.6 → 85.2 → 95.1 | Improving | 62.7 | 1.78 | 7.12 | 91.68 |
| 6 | Inventory Stock (1026-0708) | improving | 76.5 → 79.0 → 81.3 → 99.2 | Improving | 78.9 | 7.04 | 8.96 | 100 |
| 7 | Insurance Claims (1026-0708) | declining | 99.3 → 94.5 → 91.2 → 89.0 | Declining | 48.4 | -3.42 | 3.88 | 84.98 |
| 8 | HR Payroll (1026-0708) | stable | 98.5 → 98.5 → 98.5 → 98.5 | Stable | 65 | 0 | 0 | 98.54 |
| 9 | Marketing Leads (1026-0708) | volatile | 98.3 → 88.5 → 97.7 → 89.2 | Declining | 53.3 | -1.79 | 4.56 | 88.94 |
| 10 | Flight Bookings (1026-0708) | recovering | 99.0 → 90.3 → 93.7 → 99.0 | Stable | 61.7 | 0.32 | 3.67 | 96.31 |
| 11 | Hotel Reservations (1026-0708) | improving | 89.1 → 92.2 → 96.0 → 99.7 | Improving | 72.7 | 3.55 | 3.97 | 100 |
| 12 | IoT Sensor Readings (1026-0708) | declining | 99.1 → 91.0 → 84.3 → 79.3 | Declining | 32.9 | -6.63 | 7.45 | 71.83 |
| 13 | Vendor Invoices (1026-0708) | stable | 92.0 → 92.0 → 92.0 → 92.0 | Stable | 65 | 0 | 0 | 92.04 |
| 14 | Customer Support Tickets (1026-0708) | volatile | 99.1 → 88.4 → 99.0 → 89.7 | Declining | 52.7 | -1.78 | 5.04 | 89.59 |
| 15 | Loan Applications (1026-0708) | recovering | 98.7 → 90.5 → 93.9 → 99.5 | Improving | 62.6 | 0.57 | 3.63 | 97.07 |
| 16 | E-commerce Returns (1026-0708) | improving | 88.4 → 91.7 → 94.8 → 99.5 | Improving | 72.8 | 3.62 | 4.07 | 100 |
| 17 | Fleet Maintenance (1026-0708) | declining | 94.8 → 81.1 → 79.3 → 77.3 | Declining | 37.7 | -5.43 | 6.88 | 69.56 |
| 18 | Event Registrations (1026-0708) | stable | 97.1 → 97.1 → 97.1 → 97.1 | Stable | 65 | 0 | 0 | 97.14 |
| 19 | Energy Meter Readings (1026-0708) | volatile | 99.8 → 78.1 → 98.1 → 78.1 | Declining | 36.7 | -4.5 | 10.43 | 77.27 |
| 20 | Clinical Lab Results (1026-0708) | recovering | 98.7 → 89.7 → 93.5 → 98.7 | Stable | 61.8 | 0.4 | 3.79 | 96.15 |

Portfolio average trend score: **58.8** · direction counts: {'Declining': 8, 'Stable': 7, 'Improving': 6, 'Baseline': 1}

Trend score = 0.7 × momentum + 0.3 × stability, where momentum = 50 + 5 × slope (pp per run) and stability = 100 − 4 × std-dev of scores, each clamped to 0–100. 50 means flat.

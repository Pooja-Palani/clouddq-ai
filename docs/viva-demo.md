# CloudDQ AI — Viva demo script (≈5 minutes)

## One-liner

> CloudDQ AI is a serverless AWS SaaS that evaluates CSV data quality with an explainable six-dimension rule engine, visualizes results, generates Bedrock executive summaries from metrics only, and supports Business→Data User alerts with soft correction.

## Demo steps

1. **Login as Data User** (`data@example.com` locally, or seeded Cognito user).
2. **Upload** `samples/customers_dirty.csv` → auto-analyze.
3. Show **DQ score**, **health / fit-for-use**, **six dimension chart**, **column heatmap**, **issues**.
4. Click **AI executive summary** — emphasize Bedrock sees metrics JSON, not raw rows.
5. **Sign out → Business User** (`business@example.com`).
6. Open same dataset → **Send quality alert**.
7. **Sign back in as Data User** → Alerts inbox → Acknowledge → re-upload fixed CSV → Resolve (re-validation).

## Architecture talking points

- Exactly **8 AWS services** (Amplify, Cognito, API Gateway, Lambda, S3, DynamoDB, CloudWatch, Bedrock).
- **Single Lambda** router + Python DQ engine.
- **Presigned S3** uploads — no AWS keys in the browser.
- Monitoring extensions reuse dataset `runHistory` — **no new table**.
- Anomalies = plain Python deltas, **not ML**.

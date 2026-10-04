# CloudDQ AI — Architecture notes

## End-to-end flow

```text
Login (Cognito) → Upload CSV (presigned S3) → Lambda DQ Engine
  → Profile → Rules → 6 dimensions → Score / Health / Issues / Anomalies
  → DynamoDB (META + RUN + ISSUE)
  → Dashboard / Export
  → Metrics JSON → Bedrock → Executive summary + Top 3
  → Business alert → Data User correction → Re-upload → Re-analyze → Resolve
```

## DynamoDB single-table keys

| Entity | PK | SK |
|--------|----|----|
| Dataset | `DATASET#{id}` | `META` |
| Run | `DATASET#{id}` | `RUN#{iso}` |
| Issue | `DATASET#{id}` | `ISSUE#{id}` |
| Alert | `ALERT#{id}` | `META` |

GSI1: `GSI1PK=USER#{sub}` for a user's datasets (`DATASET#…`) and inbox alerts (`ALERT#…`).

Dataset `META.runHistory` stores the last N scores for trend charts — **no extra table**.

## Deterministic DQ vs generative AI

- **DQ engine** answers: What is wrong? How severe? What is the score?
- **Bedrock** answers: How should a business stakeholder understand this? What are the top fixes?

## Anomaly detection

Plain Python comparison vs previous run:

- Null-rate spike
- Record/volume drop
- Freshness delay increase
- Dimension score drop

No ML model.

## Soft correction statuses

Dataset workflow: `Completed → AlertRaised → InCorrection → Analyzing → Completed / Resolved`

Issue lifecycle: `OPEN → ASSIGNED → IN_PROGRESS → RESOLVED` (+ reopen)

Resolve requires re-validation: latest dimension score ≥ rule threshold.

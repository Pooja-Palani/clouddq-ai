# CloudDQ AI

AI-powered serverless **Data Quality Assessment and Monitoring** platform on AWS.

> CloudDQ AI securely accepts CSV datasets, evaluates them with an explainable six-dimension rule-based engine, visualizes quality metrics, uses Amazon Bedrock for executive insights from aggregated metrics only, and provides role-based alerts with a lightweight correction / re-validation workflow.

## Architecture (8 AWS services only)

| Service | Role |
|---------|------|
| **AWS Amplify** | React SPA hosting + CI |
| **Amazon Cognito** | Auth + groups `DataUser` / `BusinessUser` |
| **API Gateway** | REST + JWT authorizer |
| **AWS Lambda** | Single Python 3.12 API + DQ engine + alerts + Bedrock bridge |
| **Amazon S3** | Private CSV storage (presigned uploads) |
| **Amazon DynamoDB** | Single-table app data (datasets, runs, issues, alerts) |
| **Amazon CloudWatch** | Lambda logs |
| **Amazon Bedrock** | Executive summary + top-3 recommendations (metrics JSON only) |

```text
User → Amplify (React) → Cognito JWT → API Gateway → Lambda
                              ↓                ↓
                             S3 CSV      DynamoDB metadata
                                              ↓
                                         Bedrock (metrics)
```

## Modules

| ID | Module |
|----|--------|
| M1 | Authentication & dual roles |
| M2 | Frontend SaaS (React + TS + Tailwind + Recharts) |
| M3 | Dataset upload & repository |
| M4 | Data quality engine (6 dimensions) |
| M5 | Dashboard, reports & analytics |
| M6 | AI executive summary |
| M7 | Alert & soft correction workflow |
| M8 | API, data store & cloud deployment |

## DQ score

```text
DQ = 0.25×Completeness + 0.20×Validity + 0.15×Uniqueness
   + 0.15×Consistency + 0.15×Accuracy + 0.10×Timeliness
```

Health: **80–100 Healthy** · **60–79 Warning** · **&lt;60 Critical**

## Repository layout

```text
frontend/     React + TypeScript SPA (Amplify)
backend/      SAM template + Python Lambda + local_server.py
samples/      Dirty/clean demo CSVs
scripts/      Cognito seed helper
docs/         Architecture & API notes
```

## Local development (no AWS required)

### 1. API

```bash
cd backend
python3 local_server.py
# → http://127.0.0.1:3000
```

### 2. Frontend

```bash
cd frontend
cp .env.development .env.local   # already has VITE_DEV_AUTH=1
npm install
npm run dev
# → http://127.0.0.1:5173
```

**Dev login:** any password. Email containing `business` → BusinessUser; otherwise DataUser.

Demo path:

1. Sign in as `data@example.com`
2. Upload `samples/customers_dirty.csv`
3. View dimensions, heatmap, issues
4. Generate AI summary
5. Sign out → sign in as `business@example.com`
6. Open dataset → send alert
7. Sign back in as Data User → acknowledge → re-upload corrected CSV → resolve issues

## AWS deployment

### Prerequisites

- AWS CLI configured
- SAM CLI (`sam`)
- Node.js 20+
- Bedrock model access enabled in the target region (default `amazon.nova-lite-v1:0`)

### Backend

```bash
cd backend
sam build
sam deploy --guided
# Note outputs: ApiUrl, UserPoolId, UserPoolClientId, BucketName
```

Seed demo users:

```bash
export USER_POOL_ID=...   # from stack output
export REGION=us-east-1
chmod +x ../scripts/seed_cognito_users.sh
../scripts/seed_cognito_users.sh
```

### Frontend (Amplify Hosting)

1. Push repo to GitHub
2. Amplify Console → New app → connect repo → app root `frontend`
3. Set environment variables:

```text
VITE_AWS_REGION=
VITE_COGNITO_USER_POOL_ID=
VITE_COGNITO_CLIENT_ID=
VITE_API_BASE_URL=          # ApiUrl output
VITE_DEV_AUTH=0
```

`amplify.yml` is already in `frontend/`.

## Security principles

- Cognito groups for RBAC
- JWT on every API call
- Private S3; short-lived presigned PUT URLs
- Browser never holds AWS access keys
- Bedrock receives **aggregated metrics JSON only** — raw CSV stays in S3

## API (JWT-protected)

| Method | Path | Role |
|--------|------|------|
| POST | `/datasets/upload-url` | DataUser |
| POST | `/datasets` | DataUser |
| GET | `/datasets` | Both |
| GET | `/datasets/{id}` | Both |
| POST | `/datasets/{id}/analyze` | DataUser |
| GET | `/datasets/{id}/runs` | Both |
| GET | `/datasets/{id}/report` | Both |
| GET | `/datasets/{id}/export` | Both |
| POST | `/datasets/{id}/summary` | Both |
| POST | `/datasets/{id}/correction` | DataUser |
| GET | `/datasets/{id}/issues` | Both |
| POST | `/alerts` | BusinessUser |
| GET | `/alerts` | Both |
| POST | `/issues/{id}/assign\|acknowledge\|resolve\|reopen` | mostly DataUser |

## License

Educational / project use.

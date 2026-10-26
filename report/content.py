"""Shared content for the review PPT and the PDF report.

Edit TEAM below, then run:  python build_report.py
"""

TITLE = "CloudDQ AI"
SUBTITLE = "Serverless, AI-Assisted Data Quality Assessment and Monitoring Platform on AWS"
TEAM_NAME = "[Team name]"
TEAM = [
    {"name": "Pooja Palani", "reg": "[Reg. No.]", "role": "Backend & API — Lambda, API Gateway, DynamoDB, Bedrock invoke"},
    {"name": "Dewlyn Mary", "reg": "[Reg. No.]", "role": "Frontend & Identity — Amplify, Cognito, S3"},
    {"name": "Lathika Shree", "reg": "[Reg. No.]", "role": "Operations & Governance — CloudWatch, IAM, config, Bedrock access"},
]
LIVE_URL = "https://main.d3ffgcfvtof2u.amplifyapp.com/"
REPO = "github.com/Pooja-Palani/clouddq-ai"

OBJECTIVE = (
    "Organisations make decisions on data they rarely measure. CloudDQ AI lets a Data User upload a CSV "
    "dataset, scores it across six standard data-quality dimensions with an explainable rule engine, shows "
    "the result as a dashboard, writes a plain-language executive summary with Amazon Bedrock, and lets a "
    "Business User raise an alert that the Data User corrects and re-validates. The whole platform is "
    "serverless on AWS, keeps raw data private, and sends only aggregated metrics to the AI model."
)

OBJECTIVE_POINTS = [
    "Measure dataset quality with a transparent, weighted six-dimension score (0–100).",
    "Classify health as Healthy (80–100), Warning (60–79) or Critical (<60) and decide fitness for analytics.",
    "Visualise dimensions, column quality, score trend, severity and issues for each dataset.",
    "Detect personal data (names, emails, phone numbers) in uploaded columns with Amazon Comprehend.",
    "Generate an executive summary and top-3 fixes with Amazon Bedrock from metrics only, never raw rows.",
    "Support two roles: Data Users run quality checks; Business Users review results and raise alerts.",
    "Close the loop with a correction workflow: alert (emailed through Amazon SNS) → acknowledge → re-upload → re-analyse → resolve.",
    "Run fully serverless on AWS with no stored AWS keys in the browser.",
]

MODULES = [
    {
        "id": "M1", "name": "Authentication & Role-Based Access",
        "aws": "Cognito, API Gateway authorizer",
        "summary": "Email sign-in and two user roles enforced in both the UI and the API.",
        "details": [
            "Amazon Cognito user pool with email sign-in and a strong password policy (upper, lower, number, symbol).",
            "Public SPA app client (no secret) using SRP authentication through amazon-cognito-identity-js.",
            "Two Cognito groups, DataUser and BusinessUser; the group claim in the ID token decides the role.",
            "Every API call carries the ID token as Authorization: Bearer; API Gateway's Cognito authorizer rejects missing or invalid tokens with 401.",
            "Lambda re-checks the role for each action (e.g. only DataUser can upload; only BusinessUser can raise alerts) and returns 403 otherwise.",
        ],
    },
    {
        "id": "M2", "name": "Frontend SaaS Application",
        "aws": "Amplify Hosting",
        "summary": "React + TypeScript single-page app with role-aware navigation.",
        "details": [
            "React 19, TypeScript, Vite and Tailwind CSS; charts with Recharts; routing with React Router.",
            "Pages: Landing, Login, Home (role workspace), Datasets repository, Upload, Dataset detail, Alerts.",
            "Protected routes redirect signed-out users to login; the Upload route is visible only to Data Users.",
            "Built and hosted by AWS Amplify from the GitHub main branch; configuration is injected at build time through VITE_ environment variables.",
        ],
    },
    {
        "id": "M3", "name": "Dataset Upload & Repository",
        "aws": "S3, Lambda, DynamoDB",
        "summary": "Secure CSV upload with presigned URLs and a per-user dataset catalogue.",
        "details": [
            "The browser asks the API for a short-lived presigned S3 PUT URL (15 minutes), then uploads the CSV directly to the private bucket.",
            "The dataset is registered in DynamoDB (DATASET#id / META) with owner, file, S3 key, status and a status timeline.",
            "Uploads are keyed datasets/<user>/<dataset>/<file>.csv; the bucket blocks all public access and is encrypted (SSE-S3).",
            "The repository page lists the user's datasets through the GSI1 index (USER#sub) with score and health badges.",
        ],
    },
    {
        "id": "M4", "name": "Data Quality Engine (Six Dimensions)",
        "aws": "Lambda, Comprehend",
        "summary": "Explainable profiling, scoring, rules, anomaly detection and PII detection.",
        "details": [
            "Profiler infers each column's type (id, email, phone, date, numeric, categorical, string) and null rate.",
            "Dimension scores: Completeness (null cells), Validity (format checks), Uniqueness (duplicate keys), Consistency (case/format variants), Accuracy (range checks), Timeliness (future and stale dates).",
            "DQ score = 0.25·Completeness + 0.20·Validity + 0.15·Uniqueness + 0.15·Consistency + 0.15·Accuracy + 0.10·Timeliness.",
            "Rules with thresholds and severities (e.g. Uniqueness ≥ 98 HIGH, Validity ≥ 90 MEDIUM) turn failures into issues.",
            "Anomaly detection compares with the previous run: null-rate spike, volume drop, freshness delay and dimension score drop. No ML model is needed.",
            "Amazon Comprehend DetectPiiEntities scans up to five sample values per column and flags columns holding personal data (NAME, EMAIL, PHONE, ADDRESS…) with a confidence score; generic types such as dates are ignored.",
        ],
    },
    {
        "id": "M5", "name": "Dashboard, Reports & Analytics",
        "aws": "Lambda, DynamoDB, Amplify",
        "summary": "Visual quality report per dataset with export and print.",
        "details": [
            "Score card with health and fit-for-analytics flag; status timeline (Uploaded → Processing → Analyzed → ReportGenerated → Completed).",
            "Six-dimension bar chart, DQ score trend across runs, column quality heatmap, severity and rule coverage.",
            "Issue list with severity filter (High / Medium / Low) and audit history.",
            "Export the report as CSV and print it; the run history is kept on the dataset item for trend charts.",
        ],
    },
    {
        "id": "M6", "name": "AI Executive Summary",
        "aws": "Bedrock, Lambda",
        "summary": "Business-friendly explanation and top-3 recommendations from aggregated metrics.",
        "details": [
            "Lambda builds a metrics JSON (score, health, dimensions, issue counts, anomalies, top issue messages) — no raw CSV rows.",
            "Calls the Amazon Bedrock Converse API (Amazon Nova Lite, inference profile us.amazon.nova-lite-v1:0) and asks for JSON with an executive summary and exactly three recommendations.",
            "The summary is cached on the dataset per analysis run, and the UI shows exactly which metrics the model received.",
            "If Bedrock is unavailable, a deterministic summary is built from the same metrics so the feature degrades gracefully.",
        ],
    },
    {
        "id": "M7", "name": "Alerts & Soft Correction Workflow",
        "aws": "Lambda, DynamoDB, SNS",
        "summary": "Business → Data User collaboration with email notification and re-validation.",
        "details": [
            "A Business User sends a quality alert with a note; the dataset workflow moves to AlertRaised and the Data User sees it in the inbox.",
            "Lambda publishes the alert to the Amazon SNS topic clouddq-alerts, which emails subscribers with the score, health, note and a link to the dataset.",
            "The Data User acknowledges, moves the dataset to correction, re-uploads a fixed CSV and re-runs the analysis.",
            "Issue lifecycle OPEN → ASSIGNED → IN_PROGRESS → RESOLVED, with reopen and a full audit history.",
            "An issue can only be resolved when the latest dimension score meets the rule threshold (re-validation).",
        ],
    },
    {
        "id": "M8", "name": "API, Data Store & Cloud Deployment",
        "aws": "API Gateway, Lambda, DynamoDB, CloudWatch, SNS, IAM",
        "summary": "One REST API, one Lambda, one table — monitored and least-privilege.",
        "details": [
            "API Gateway REST API (stage prod) with / and /{proxy+} ANY methods routed to one Python 3.12 Lambda by Lambda proxy integration.",
            "DynamoDB single-table design: PK/SK plus GSI1 for a user's datasets and alerts; on-demand capacity.",
            "Lambda logs to CloudWatch (/aws/lambda/clouddq-api); alarm clouddq-api-errors fires on any error in 5 minutes and notifies the SNS topic.",
            "Three IAM users (one per team member) with role-scoped policies and an execution role clouddq-lambda-role for the function.",
        ],
    },
]

AWS_SERVICES = [
    ("AWS Amplify", "Builds and hosts the React app from GitHub; injects VITE_ configuration at build time.", "clouddq-ai · main branch"),
    ("Amazon Cognito", "User pool for sign-in; DataUser / BusinessUser groups; issues the JWT used by the API.", "us-east-1_DT3M9ZhMz"),
    ("Amazon API Gateway", "REST API with a Cognito authorizer; forwards requests to Lambda (proxy).", "fdro0463k8 · stage prod"),
    ("AWS Lambda", "Python 3.12 backend: routing, DQ engine, alerts, presigned URLs, AI integrations.", "clouddq-api"),
    ("Amazon S3", "Private, encrypted storage for uploaded CSVs; presigned PUT uploads.", "clouddq-datasets-121835991420"),
    ("Amazon DynamoDB", "Single table for datasets, runs, issues, alerts; GSI1 for per-user queries.", "CloudDQ"),
    ("Amazon Comprehend", "AI service: detects personal data (PII) in sample column values during analysis.", "DetectPiiEntities"),
    ("Amazon SNS", "Emails business alerts to the Data User and CloudWatch alarm notifications.", "clouddq-alerts"),
    ("Amazon CloudWatch", "Lambda logs and error alarm for monitoring.", "/aws/lambda/clouddq-api"),
    ("Amazon Bedrock", "Generative AI executive summary from aggregated metrics (Converse API); account access pending with AWS.", "us.amazon.nova-lite-v1:0"),
    ("AWS IAM", "Team IAM users with scoped policies; Lambda execution role.", "clouddq-lambda-role"),
]

CONTRIBUTIONS = [
    {
        "name": "Pooja Palani",
        "focus": "Backend, API and AI integration",
        "modules": "M3, M4, M6, M8",
        "items": [
            "Created the DynamoDB table CloudDQ with the PK/SK keys and GSI1 index.",
            "Created the Lambda execution role and the clouddq-api function (Python 3.12, us-east-1); packaged and deployed the backend code and set environment variables.",
            "Built the REST API in API Gateway: Cognito authorizer, / and /{proxy+} routes, CORS, deployment to the prod stage.",
            "Implemented the Bedrock Converse call and the metrics-only payload for the AI summary.",
            "Integrated Amazon Comprehend PII detection into the analysis and added its IAM permission to the Lambda role.",
            "Ran the first Lambda test so CloudWatch logging started.",
        ],
    },
    {
        "name": "Dewlyn Mary",
        "focus": "Frontend, identity and storage",
        "modules": "M1, M2, M3 (upload), M5",
        "items": [
            "Created the Cognito user pool, public SPA app client, DataUser / BusinessUser groups and demo users.",
            "Created the private, encrypted S3 bucket and its CORS rule for browser uploads.",
            "Set up AWS Amplify Hosting from GitHub, the monorepo build specification and the VITE_ environment variables.",
            "Connected the frontend sign-in (Cognito) and API configuration; added the Amplify URL to Cognito and S3 CORS.",
        ],
    },
    {
        "name": "Lathika Shree",
        "focus": "Operations, monitoring and governance",
        "modules": "M6 (model access), M7 testing, M8 (monitoring, IAM)",
        "items": [
            "Checked Amazon Bedrock model availability (Nova Lite) and the inference profile used by Lambda.",
            "Verified the Amplify environment variables before release.",
            "Confirmed the CloudWatch log group and created the clouddq-api-errors alarm.",
            "Created the Amazon SNS topic clouddq-alerts for alert emails and connected the CloudWatch alarm to it.",
            "Reviewed IAM users and policies for least privilege.",
            "Tested the end-to-end alert and correction workflow with both roles.",
        ],
    },
    {
        "name": "All three",
        "focus": "Shared",
        "modules": "—",
        "items": [
            "Requirement analysis, architecture design, DQ dimension and rule design, testing, documentation and the review presentation.",
        ],
    },
]

TOOLS = [
    ("Languages", "Python 3.12 (backend), TypeScript (frontend)"),
    ("Frontend", "React 19, Vite 8, Tailwind CSS 4, React Router 7, Recharts 3, Axios, amazon-cognito-identity-js"),
    ("Backend", "boto3 / botocore (AWS SDK for Python), Python standard library (csv, re, statistics)"),
    ("AWS tooling", "AWS Management Console, AWS CLI v2, AWS SAM (template.yaml)"),
    ("Dev tools", "Cursor / VS Code, Git and GitHub, Node.js 20+, npm, Postman, Google Chrome DevTools"),
    ("Testing", "Python unittest/pytest for the DQ engine; local API server (backend/local_server.py)"),
    ("Hardware", "Any laptop with 8 GB RAM and internet access; AWS account (region us-east-1)"),
]

AWS_SCREENS = [
    ("iam_users", "AWS IAM", "IAM → Users: Pooja, DewlynMary, LathikaShree"),
    ("iam_role", "AWS IAM", "Roles → clouddq-lambda-role → Permissions"),
    ("cognito_pool", "Amazon Cognito", "User pool us-east-1_DT3M9ZhMz → Overview"),
    ("cognito_groups", "Amazon Cognito", "User pool → Groups: DataUser, BusinessUser"),
    ("cognito_users", "Amazon Cognito", "User pool → Users (demo Data User and Business User)"),
    ("s3_bucket", "Amazon S3", "Bucket clouddq-datasets-121835991420 → Objects"),
    ("s3_cors", "Amazon S3", "Bucket → Permissions: Block all public access On"),
    ("dynamodb_table", "Amazon DynamoDB", "Table CloudDQ → Explore items"),
    ("lambda_function", "AWS Lambda", "Function clouddq-api → overview with API Gateway trigger"),
    ("lambda_env", "AWS Lambda", "Function clouddq-api → Configuration"),
    ("api_gateway", "Amazon API Gateway", "REST API fdro0463k8 → Resources: / and /{proxy+} ANY"),
    ("api_authorizer", "Amazon API Gateway", "REST API → Authorizers: CognitoAuthorizer"),
    ("amplify_app", "AWS Amplify", "App clouddq-ai → Overview (main branch deployed)"),
    ("amplify_env", "AWS Amplify", "App clouddq-ai → Environment variables"),
    ("cloudwatch_logs", "Amazon CloudWatch", "Log group /aws/lambda/clouddq-api"),
    ("cloudwatch_alarm", "Amazon CloudWatch", "Alarm clouddq-api-errors"),
    ("sns_topic", "Amazon SNS", "Topic clouddq-alerts (alert emails and alarm notifications)"),
    ("comprehend", "Amazon Comprehend", "PII detection result inside CloudDQ (Employee Directory dataset)"),
    ("bedrock", "Amazon Bedrock", "Model catalog → Amazon Nova Lite"),
]

WALKTHROUGH_SNS = [
    ("01_signin_lathika", "Sign in as LathikaShree", "IAM user sign-in with account 121835991420 and username LathikaShree."),
    ("02_console_home", "Console home", "Signed in as LathikaShree in US East (N. Virginia)."),
    ("03_sns_topics_empty", "Amazon SNS → Topics", "No topics yet. Choose Create topic."),
    ("04_create_topic_standard_name", "Create topic", "Type Standard, name clouddq-alerts. The red KMS banner only means Lathika can't list encryption keys; this topic uses default encryption, so it can be ignored."),
    ("05_topic_created", "Topic created", "ARN arn:aws:sns:us-east-1:121835991420:clouddq-alerts — the same ARN Lambda uses in ALERT_TOPIC_ARN. Subscriptions are added from this page."),
    ("06_alarm_details", "CloudWatch → Alarms → clouddq-api-errors", "Open the alarm, then Actions → Edit."),
    ("07_alarm_edit_step1_metric", "Edit alarm — step 1", "Metric and condition stay the same (Lambda Errors > 0 in 5 minutes). Choose Next."),
    ("08_alarm_edit_step2_actions", "Edit alarm — step 2", "Configure actions. Choose Add notification."),
    ("09_add_notification_form", "Add notification", "Trigger In alarm, Select an existing SNS topic."),
    ("10_notification_topic_selected", "Choose the topic", "Send a notification to clouddq-alerts. Then Next."),
    ("11_alarm_details_name", "Edit alarm — step 3", "Name stays clouddq-api-errors. Choose Next."),
    ("12_preview_and_update", "Edit alarm — step 4", "Preview the change and choose Update alarm."),
    ("13_alarm_updated", "Alarm updated", "Back on the alarm page."),
    ("14_alarm_actions_tab", "Actions tab", "Notification to clouddq-alerts when the alarm goes In alarm. 'Configuration not verified' disappears once an email subscription is confirmed."),
]

FEATURE_SCREENS = [
    ("landing", "Landing page", "Public landing page describing the platform and the six dimensions."),
    ("login", "Cognito sign-in", "Email and password sign-in against the Amazon Cognito user pool."),
    ("datauser_home", "Data User workspace", "Role-aware home with dataset and alert counts for the Data User."),
    ("upload", "CSV upload", "Upload form; the file goes straight to S3 through a presigned URL."),
    ("datasets_list", "Dataset repository", "All datasets with DQ score, health and workflow status."),
    ("dataset_detail_top", "Quality report", "Score 90.13% Healthy, actions, status timeline, dimensions and trend."),
    ("sec_dimensions", "Six-dimension scores", "Accuracy, completeness, consistency, timeliness, uniqueness, validity."),
    ("sec_heatmap", "Column quality heatmap", "Per-column quality from null rates and type checks."),
    ("sec_severity", "Severity & rule coverage", "Issue counts by severity and how many rules passed."),
    ("sec_pii", "Personal data detection (Amazon Comprehend)", "Comprehend flags Full_Name as NAME and Email as EMAIL with 100% confidence."),
    ("sec_issues", "Issues with lifecycle actions", "Rule failures with severity, acknowledge / resolve and audit history."),
    ("sec_ai_summary", "AI executive summary", "Executive summary and top-3 recommendations from metrics JSON only (simulated preview while Bedrock access is pending)."),
    ("sec_correction", "Soft correction", "Data User re-uploads a corrected CSV to re-validate."),
    ("business_home", "Business User workspace", "Business User view — no upload, read results and raise alerts."),
    ("sec_send_alert", "Send quality alert", "Business User sends an alert with a note to the Data User."),
    ("business_alerts", "Sent alerts", "Alert status OPEN with score and health, plus status history."),
    ("datauser_alerts", "Data User alert inbox", "Data User receives the alert and starts the correction workflow."),
]

RESULTS = [
    "Sample dataset Customer Master (customers_dirty.csv) scored 90.13% — HEALTHY, fit for analytics.",
    "Dimension scores: completeness 95.96, validity 84.21, uniqueness 90.91, consistency 92.86, accuracy 81.25, timeliness 95.45.",
    "Three open issues raised: Key Uniqueness (HIGH), Overall Validity (MEDIUM), Value Accuracy (MEDIUM).",
    "Employee Directory (employees_clean.csv) scored 96.0% — Comprehend flagged Full_Name (NAME) and Email (EMAIL) at 100% confidence.",
    "Business User alert moved the dataset workflow to AlertRaised, appeared in the Data User inbox and was published to SNS.",
    "Requests without a token are rejected by API Gateway with 401, and wrong-role actions by Lambda with 403.",
]

CHALLENGES = [
    ("Bedrock access on a new account",
     "The account returned NOT_AUTHORIZED for Bedrock models with a quota of 0. The Converse integration and IAM are in place; "
     "the app falls back to a deterministic summary from the same metrics until AWS lifts the restriction (support case)."),
    ("Monorepo build on Amplify",
     "The app root is the repository root, so the build spec runs cd frontend and publishes frontend/dist."),
    ("Greedy proxy resource in API Gateway",
     "The /{proxy+} resource needs the greedy path parameter and the authorizer on ANY only, never on the OPTIONS preflight."),
    ("Cognito first sign-in",
     "Admin-created users start in FORCE_CHANGE_PASSWORD; passwords were set as permanent to match the in-app login."),
]

FUTURE = [
    "S3 event notifications → automatic analysis on upload; Step Functions for the analysis workflow.",
    "Per-user SNS subscriptions or Amazon SES templated emails, and Comprehend-driven masking of PII columns.",
    "AWS Glue Data Quality and Athena for very large datasets and SQL exploration.",
    "Bedrock Guardrails and Knowledge Bases for safer, rule-aware explanations.",
    "Infrastructure as code (SAM / CDK) with a CI/CD pipeline and multiple environments.",
]

REFERENCES = [
    "Amazon Web Services, “AWS Amplify Hosting User Guide.” https://docs.aws.amazon.com/amplify/latest/userguide/",
    "Amazon Web Services, “Amazon Cognito Developer Guide — User pools.” https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools.html",
    "Amazon Web Services, “Use Amazon Cognito user pools as authorizer for a REST API.” https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html",
    "Amazon Web Services, “Lambda proxy integrations in API Gateway.” https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html",
    "Amazon Web Services, “AWS Lambda Developer Guide — Building with Python.” https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html",
    "Amazon Web Services, “Uploading objects with presigned URLs.” https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html",
    "Amazon Web Services, “Best practices for DynamoDB — single-table design.” https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html",
    "Amazon Web Services, “Amazon Bedrock — Converse API.” https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html",
    "Amazon Web Services, “Amazon Nova User Guide.” https://docs.aws.amazon.com/nova/latest/userguide/",
    "Amazon Web Services, “Amazon Comprehend — Detecting PII entities.” https://docs.aws.amazon.com/comprehend/latest/dg/how-pii.html",
    "Amazon Web Services, “Amazon SNS Developer Guide — Email notifications.” https://docs.aws.amazon.com/sns/latest/dg/sns-email-notifications.html",
    "Amazon Web Services, “Using Amazon CloudWatch alarms.” https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html",
    "Amazon Web Services, “Security best practices in IAM.” https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
    "DAMA International, DAMA-DMBOK: Data Management Body of Knowledge, 2nd ed. Technics Publications, 2017.",
    "ISO/IEC 25012:2008, Software engineering — Software product Quality Requirements and Evaluation (SQuaRE) — Data quality model.",
    "R. Y. Wang and D. M. Strong, “Beyond accuracy: What data quality means to data consumers,” Journal of Management Information Systems, 12(4), 5–33, 1996.",
    "React documentation. https://react.dev/ · Vite documentation. https://vite.dev/ · Recharts. https://recharts.org/",
]

CODE_GROUPS = [
    ("M1 — Authentication & Role-Based Access", [
        "backend/src/auth/__init__.py",
        "frontend/src/lib/cognito.ts",
        "frontend/src/auth/AuthContext.tsx",
        "frontend/src/pages/LoginPage.tsx",
    ]),
    ("M2 — Frontend SaaS Application", [
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/config.ts",
        "frontend/src/types.ts",
        "frontend/src/components/AppShell.tsx",
        "frontend/src/components/Badges.tsx",
        "frontend/src/pages/LandingPage.tsx",
        "frontend/src/pages/HomePage.tsx",
        "frontend/src/index.css",
        "frontend/index.html",
        "frontend/vite.config.ts",
        "frontend/package.json",
    ]),
    ("M3 — Dataset Upload & Repository", [
        "backend/src/datasets/__init__.py",
        "backend/src/datasets/service.py",
        "backend/src/store/__init__.py",
        "backend/src/store/s3.py",
        "frontend/src/lib/api.ts",
        "frontend/src/pages/UploadPage.tsx",
        "frontend/src/pages/DatasetsPage.tsx",
    ]),
    ("M4 — Data Quality Engine", [
        "backend/src/dq_engine/__init__.py",
        "backend/src/dq_engine/profiler.py",
        "backend/src/dq_engine/dimensions.py",
        "backend/src/dq_engine/rules.py",
        "backend/src/dq_engine/anomalies.py",
        "backend/src/dq_engine/engine.py",
        "backend/src/ai/comprehend.py",
        "backend/tests/test_dq_engine.py",
    ]),
    ("M5 — Dashboard, Reports & Analytics", [
        "frontend/src/pages/DatasetDetailPage.tsx",
    ]),
    ("M6 — AI Executive Summary (Amazon Bedrock)", [
        "backend/src/ai/__init__.py",
        "backend/src/ai/bedrock.py",
    ]),
    ("M7 — Alerts & Soft Correction Workflow", [
        "backend/src/alerts/__init__.py",
        "backend/src/alerts/service.py",
        "backend/src/store/sns.py",
        "frontend/src/pages/AlertsPage.tsx",
    ]),
    ("M8 — API, Data Store & Cloud Deployment", [
        "backend/src/handler.py",
        "backend/src/http_util.py",
        "backend/src/__init__.py",
        "backend/src/store/dynamo.py",
        "backend/src/requirements.txt",
        "backend/template.yaml",
        "backend/local_server.py",
        "frontend/amplify.yml",
    ]),
]

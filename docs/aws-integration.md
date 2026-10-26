# CloudDQ AI — AWS integration steps

One AWS account (`121835991420`) in **US East (N. Virginia)**. Every service below is in that account and region. The browser never receives AWS keys. It signs in with Cognito and sends the ID token to API Gateway.

| Person | IAM user | Owns |
|---|---|---|
| Pooja | `Pooja` | DynamoDB, Lambda, API Gateway, Cognito authorizer, Bedrock invoke, Comprehend |
| Dewlyn Mary | `DewlynMary` | Cognito user pool and app client, S3 and CORS, Amplify hosting |
| Lathika Shree | `LathikaShree` | Amplify and Lambda config check, CloudWatch, SNS, IAM review, Bedrock model access |

Sign-in URL for all three IAM users: `https://121835991420.signin.aws.amazon.com/console`

Do the steps in this order. A later step uses an ID copied from an earlier step.

## 1. Create the three IAM users

**Who:** Pooja, signed in once as the account root. After the users exist, everyone including Pooja uses an IAM user. Root is not used again.

1. Open **IAM → Users → Create user**.
2. Create `Pooja`, `DewlynMary`, and `LathikaShree` with console access.
3. On **Set permissions**, choose **Add user to group** and create one group per person.

| Group | User | Policies |
|---|---|---|
| `CloudDQ-Backend` | `Pooja` | `AWSCloudFormationFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `AmazonDynamoDBFullAccess`, `AmazonCognitoPowerUser`, `AmazonBedrockFullAccess`, `IAMFullAccess` |
| `CloudDQ-Frontend` | `DewlynMary` | `AdministratorAccess-Amplify`, `AmazonS3FullAccess`, `AmazonCognitoPowerUser` |
| `CloudDQ-Ops` | `LathikaShree` | `CloudWatchFullAccess`, `AmazonSNSFullAccess`, `IAMReadOnlyAccess`, `AmazonBedrockFullAccess`, `AdministratorAccess-Amplify` |

`IAMFullAccess` stays only on Pooja’s group, because a Lambda role has to be created. If the API Gateway console later reports that `ec2:DescribeVpcEndpoints` is missing, add that one action to `Pooja`. The API itself is Regional and does not use a VPC endpoint. The console only looks endpoints up while the create page loads.

## 2. Create the Cognito user pool and app client

**Who:** Dewlyn

Cognito is the user directory. The React app and API Gateway both have to point at this same pool.

1. Open **Amazon Cognito → User pools → Create user pool**.
2. Application type: **Single-page application (SPA)**. Name: `CloudDQ`.
3. Sign-in identifier: **Email** only. Leave Username and Phone number unchecked.
4. Leave **Enable self-registration** checked. Leave required attributes empty. Clear any half-typed return URL.
5. Create the pool. Copy the **User pool ID** and the **App client ID**.

Values from this project:

```text
User pool ID:    us-east-1_DT3M9ZhMz
App client ID:   7hhl4r28t393ujpgif37vsv07m
```

6. Open the app client. Confirm it has **no client secret**.
7. Turn on **ALLOW_USER_SRP_AUTH**, **ALLOW_USER_PASSWORD_AUTH**, and **ALLOW_REFRESH_TOKEN_AUTH**. The React page signs in with email and password inside the app. It does not use the Cognito hosted login redirect.
8. Create two groups named exactly `DataUser` and `BusinessUser`. The console may draw a space in the list. The stored name has no space. The app checks those exact strings.
9. Create the two demo users, assign the groups, and set each password as **permanent**. A temporary password makes the app stop with “New password required.” The pool also requires an uppercase letter, a lowercase letter, a number, and a symbol.

| Email | Group |
|---|---|
| `datauser@clouddq.com` | `DataUser` |
| `businessuser@clouddq.com` | `BusinessUser` |

Send the pool ID and client ID to Pooja and Lathika.

## 3. Create the private CSV bucket

**Who:** Dewlyn

The browser uploads a CSV with a short-lived presigned URL. It never gets an S3 access key.

1. Open **S3 → Create bucket**.
2. Name: `clouddq-datasets-121835991420`.
3. Keep **Block all public access** on. Enable default encryption (SSE-S3).
4. After the bucket exists, open **Permissions → CORS** and save:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedOrigins": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

`AllowedOrigins` is tightened to the Amplify URL in step 10, after that URL exists. Send the bucket name to Pooja.

## 4. Create the DynamoDB table

**Who:** Pooja

One table holds datasets, analysis runs, issues, and alerts.

1. Open **DynamoDB → Create table**.
2. Table name: `CloudDQ`.
3. Partition key: `PK` (String). Sort key: `SK` (String). Capacity: on-demand.
4. After the table is active, open **Indexes → Create index**.
5. Index name: `GSI1`. Partition key: `GSI1PK` (String). Sort key: `GSI1SK` (String).

Lambda reads and writes this table using the `TABLE_NAME` environment variable. If the table is missing, dataset registration returns `ResourceNotFoundException`.

## 5. Create the Lambda execution role and function

**Who:** Pooja

1. Open **IAM → Roles → Create role**.
2. Trusted entity: **AWS service → Lambda**. Use case: **Lambda**. Do not choose `AWSServiceRoleForLambda`.
3. Attach `AmazonDynamoDBFullAccess`, `AmazonS3FullAccess`, `AmazonBedrockFullAccess`, and `AWSLambdaBasicExecutionRole`.
4. Name the role `clouddq-lambda-role`.

Create the function in **US East (N. Virginia)** only. A function created in another region cannot see this table, bucket, or user pool.

1. Open **Lambda → Create function → Author from scratch**.
2. Name: `clouddq-api`. Runtime: **Python 3.12**. Leave ARM64 off.
3. Open **Additional settings**, turn on **Custom execution role**, and choose `clouddq-lambda-role`.
4. On your laptop, zip the *contents* of `backend/src` so `handler.py` is at the top of the zip:

```bash
cd backend/src
zip -r ../clouddq-api.zip .
```

5. In the function, open **Update → .zip file** and upload `backend/clouddq-api.zip`. The file list must show `handler.py`, not the sample `lambda_function.py`.
6. Set the handler to `handler.lambda_handler`.
7. **Configuration → General configuration:** timeout **2 min**, memory **1024 MB**.
8. **Configuration → Environment variables:**

```text
TABLE_NAME=CloudDQ
BUCKET_NAME=clouddq-datasets-121835991420
BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0
USER_POOL_ID=us-east-1_DT3M9ZhMz
LOG_LEVEL=INFO
```

`BUCKET_NAME` and `USER_POOL_ID` come from Dewlyn’s steps. `BEDROCK_MODEL_ID` is the US inference profile, not the base model id `amazon.nova-lite-v1:0`. The base id returns `Operation not allowed` in this region.

## 6. Check Bedrock model access

**Who:** Lathika

1. Open **Amazon Bedrock** in **US East (N. Virginia)**.
2. The old **Model access** page is retired. Serverless models are supposed to turn on at first use.
3. Open **Model catalog → Nova Lite** only to read the base id `amazon.nova-lite-v1:0`. Do not run the playground on that base model.
4. Open **Infer → Inference profiles → US Nova Lite** (`us.amazon.nova-lite-v1:0`) and run one prompt.

On this account both ids return `ValidationException: Operation not allowed`. `get-foundation-model-availability` reports `authorizationStatus: NOT_AUTHORIZED`, and the on-demand Nova Lite quota is 0 requests per minute. That is an account hold set by AWS. IAM policies and the Lambda environment variable cannot clear it. The function catches the error and writes an offline summary from the same metrics JSON. A live model response needs an AWS Support case under Account and billing that quotes the `NOT_AUTHORIZED` status.

## 7. Create the REST API and Cognito authorizer

**Who:** Pooja

API Gateway checks the Cognito token before Lambda runs.

1. Open **API Gateway → Create API → REST API** (not HTTP API).
2. Choose **New API**. Name: `clouddq-api`. Endpoint type: **Regional**. Security policy: TLS 1.2. Ignore the `ec2:DescribeVpcEndpoints` banner.
3. **Authorizers → Create authorizer.**
   - Name: `CognitoAuthorizer`
   - Type: **Cognito**
   - Region: `us-east-1`
   - User pool: the CloudDQ pool `us-east-1_DT3M9ZhMz`
   - Token source: `Authorization` only. The console adds `method.request.header.` itself.
   - Leave token validation empty.
4. **Create resource.** Turn **Proxy resource** on. Leave the parent path as `/`. Set the resource name to `{proxy+}`. Check **CORS**. The tree must show `/{proxy+}`.
5. On `/{proxy+}` **ANY**, choose **Edit integration**. Integration type: **Lambda function**. Turn on **Lambda proxy integration**. Function: `clouddq-api` in `us-east-1`.
6. Open **Method request** for that **ANY** method and set **Authorization** to `CognitoAuthorizer`.
7. On the existing `/` resource, create an **ANY** method with the same Lambda proxy integration and the same authorizer.
8. Leave **OPTIONS** without the Cognito authorizer. The browser preflight has no token.
9. **Deploy API.** Stage name: `prod`.

Invoke URL from this project:

```text
https://fdro0463k8.execute-api.us-east-1.amazonaws.com/prod
```

A call with no token returns **401**. That is the authorizer working. Send this URL to Dewlyn and Lathika.

## 8. Host the React app on Amplify

**Who:** Dewlyn creates the app. Lathika checks the variables before the build is treated as final.

1. Dewlyn opens **AWS Amplify → Create new app**.
2. Connect GitHub repository `Pooja-Palani/clouddq-ai`, branch `main`.
3. App name: `clouddq-ai`.
4. The console’s auto-detected build command is empty and the output directory is `/`. Replace the build spec with:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

5. Open **Advanced settings** and add the environment variables. Vite reads them at build time, so they must be present before the first deploy. Lathika then opens **Hosting → Environment variables** and confirms the same five values. `VITE_DEV_AUTH` must be the digit `0`. Any other value makes the app skip Cognito.

```text
VITE_AWS_REGION=us-east-1
VITE_COGNITO_USER_POOL_ID=us-east-1_DT3M9ZhMz
VITE_COGNITO_CLIENT_ID=7hhl4r28t393ujpgif37vsv07m
VITE_API_BASE_URL=https://fdro0463k8.execute-api.us-east-1.amazonaws.com/prod
VITE_DEV_AUTH=0
```

6. Deploy. Site URL from this project:

```text
https://main.d3ffgcfvtof2u.amplifyapp.com/
```

If Lathika changes a variable after the first deploy, she redeploys the app. A rebuild is required because the values are compiled into the JavaScript bundle.

## 9. Point Cognito and S3 at the Amplify URL

**Who:** Dewlyn

1. In the Cognito app client, add `https://main.d3ffgcfvtof2u.amplifyapp.com/` as an allowed callback URL and sign-out URL.
2. In the S3 bucket CORS rule, replace `"*"` in `AllowedOrigins` with that same URL.

The password form does not redirect through Cognito, but the app client still needs the site URL if hosted login is used later. S3 CORS must allow the site origin or the browser blocks the CSV upload.

## 10. Create the CloudWatch log group and alarm

**Who:** Pooja runs the function once. Lathika reads the logs and creates the alarm.

The log group does not exist until Lambda runs. Lathika cannot open Lambda. Her user is denied `lambda:ListFunctions` on purpose.

1. Pooja opens **Lambda → clouddq-api → Test**.
2. Use a synchronous private test event named `health` with this JSON:

```json
{
  "httpMethod": "GET",
  "path": "/health",
  "headers": {},
  "requestContext": {}
}
```

3. Run the test. A successful body says the service is ok. The run creates `/aws/lambda/clouddq-api`.
4. Lathika opens **CloudWatch → Log groups** in **US East (N. Virginia)** and refreshes. She does not click **Create log group**.
5. Lathika opens **Alarms → Create alarm**.
   - Data source: **Metrics**. Type: **Classic**.
   - Metric path: **Lambda → By Function Name → clouddq-api → Errors**.
   - Condition: **Greater** than `0`, period **5 minutes**.
   - Leave notifications empty for now; step 11 connects the alarm to SNS. Name the alarm `clouddq-api-errors`.

## 11. Add Amazon SNS alert emails

**Who:** Lathika creates the topic and connects the alarm. Pooja gives Lambda permission to publish and sets the topic ARN.

Screenshots of every click, recorded from the `LathikaShree` user, are in `report/screens/walkthrough_sns/` (steps 01–14).

1. Lathika opens **Amazon SNS → Topics → Create topic**. Type: **Standard**. Name: `clouddq-alerts`. Copy the ARN: `arn:aws:sns:us-east-1:121835991420:clouddq-alerts`. A red "Couldn't retrieve KMS keys" banner may appear; it only affects the optional custom-encryption list and can be ignored.
2. To receive emails, open the topic, choose **Create subscription**, set protocol **Email**, and enter a real inbox. AWS sends a confirmation email; click **Confirm subscription** in it.
3. Lathika opens **CloudWatch → Alarms → clouddq-api-errors → Actions → Edit**, adds a notification **In alarm → clouddq-alerts**, and saves.
4. Pooja opens **IAM → Roles → clouddq-lambda-role → Add permissions → Create inline policy**, and adds `sns:Publish` on the topic ARN.
5. Pooja adds two Lambda environment variables:

```text
ALERT_TOPIC_ARN=arn:aws:sns:us-east-1:121835991420:clouddq-alerts
APP_URL=https://main.d3ffgcfvtof2u.amplifyapp.com
```

When a Business User chooses **Alert Data User**, Lambda saves the alert in DynamoDB and publishes it to the topic. Subscribers get an email with the dataset name, score, health, note and a link to the dataset. If no one is subscribed, the alert still works in the app.

## 12. Add Amazon Comprehend PII detection

**Who:** Pooja

Comprehend has no resource to create. Lambda calls its `DetectPiiEntities` API directly during each analysis.

1. On the same inline policy of `clouddq-lambda-role`, add `comprehend:DetectPiiEntities` (resource `*`). The policy is saved as `clouddq-comprehend-sns`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "comprehend:DetectPiiEntities", "Resource": "*"},
    {"Effect": "Allow", "Action": "sns:Publish", "Resource": "arn:aws:sns:us-east-1:121835991420:clouddq-alerts"}
  ]
}
```

2. Upload the new Lambda zip that contains `ai/comprehend.py`.
3. Run an analysis. For each column, Lambda sends the column name and up to five sample values to Comprehend. Columns where Comprehend finds a name, email, phone number, address or similar with at least 80% confidence appear under **PII hints** on the dataset page. Dates and ages are ignored, because on their own they don't identify a person.

Uploading `samples/employees_clean.csv` as **Employee Directory** shows `Full_Name (NAME · Amazon Comprehend 100%)` and `Email (EMAIL · Amazon Comprehend 100%)`.

## 13. Review IAM

**Who:** Lathika

Open **IAM → Users** and confirm only these three users exist, with the policies from step 1. `LathikaShree` has IAM read-only and does not have `IAMFullAccess`.

## 14. Prove the services are connected

**Who:** Pooja drives the data-user path. Dewlyn’s pool and bucket are what that path uses. Lathika confirms the log group receives the invocation.

1. Open `https://main.d3ffgcfvtof2u.amplifyapp.com/` and sign in as `datauser@clouddq.com`.
2. Upload `samples/customers_dirty.csv`. The page asks Lambda for a presigned URL, the browser uploads the file to S3, Lambda writes the dataset to DynamoDB, and Lambda runs the six-dimension engine.
3. The dataset **Customer Master** should show score **90.13%**, health **Healthy**, and three open issues.
4. Sign out. Sign in as `businessuser@clouddq.com`. The Upload link is hidden. Open the dataset and choose **Alert Data User**.
5. The dataset workflow becomes **AlertRaised**, the alert appears under **Sent alerts**, and subscribers of `clouddq-alerts` receive the email.
6. Upload `samples/employees_clean.csv` as the Data User and show the Comprehend PII hints on the dataset page.
7. Lathika refreshes `/aws/lambda/clouddq-api` and shows the new log stream.

## How each ID connects

```text
Amplify bundle
  pool us-east-1_DT3M9ZhMz
  client 7hhl4r28t393ujpgif37vsv07m
  API https://fdro0463k8.execute-api.us-east-1.amazonaws.com/prod
        |
        |  Authorization: Bearer <Cognito ID token>
        v
API Gateway authorizer  -->  same user pool
        |
        v
Lambda clouddq-api
  USER_POOL_ID  = us-east-1_DT3M9ZhMz
  BUCKET_NAME   = clouddq-datasets-121835991420
  TABLE_NAME    = CloudDQ
  BEDROCK_MODEL_ID = us.amazon.nova-lite-v1:0
  ALERT_TOPIC_ARN  = arn:aws:sns:us-east-1:121835991420:clouddq-alerts
        |
        +--> S3 presigned PUT for the CSV
        +--> DynamoDB PK/SK and GSI1
        +--> Comprehend DetectPiiEntities on sample column values
        +--> Bedrock Converse, or the offline metrics summary
        +--> SNS topic clouddq-alerts (alert emails; also the CloudWatch alarm action)
        +--> CloudWatch log group /aws/lambda/clouddq-api
```

The group claim inside the token is what Lambda uses for the role. `DataUser` can upload and analyze. `BusinessUser` can read results and send an alert.

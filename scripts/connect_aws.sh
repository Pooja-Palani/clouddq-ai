#!/usr/bin/env bash
# Deploy CloudDQ AI to AWS and point the local frontend at the live stack.
# Prerequisite: `aws configure` (do not paste keys into chat).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REGION="${AWS_REGION:-${REGION:-us-east-1}}"
STACK_NAME="${STACK_NAME:-clouddq-ai}"

echo "Checking AWS credentials..."
aws sts get-caller-identity --region "$REGION" >/dev/null

echo "Building backend..."
cd "$ROOT/backend"
sam build

echo "Deploying stack $STACK_NAME in $REGION..."
sam deploy \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --no-confirm-changeset \
  --parameter-overrides "BedrockModelId=amazon.nova-lite-v1:0 CorsOrigin=* ExistingUserPoolId=us-east-1_9lWN4OKAr ExistingUserPoolClientId=1m549v3r066u5t2armb5n8tr2t"

echo "Reading stack outputs..."
outputs="$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output json)"

api_url="$(python3 -c "import json,sys; o=json.loads(sys.argv[1]); print(next(i['OutputValue'] for i in o if i['OutputKey']=='ApiUrl'))" "$outputs")"
pool_id="$(python3 -c "import json,sys; o=json.loads(sys.argv[1]); print(next(i['OutputValue'] for i in o if i['OutputKey']=='UserPoolId'))" "$outputs")"
client_id="$(python3 -c "import json,sys; o=json.loads(sys.argv[1]); print(next(i['OutputValue'] for i in o if i['OutputKey']=='UserPoolClientId'))" "$outputs")"

ENV_FILE="$ROOT/frontend/.env.development.local"
cat > "$ENV_FILE" <<EOF
VITE_DEV_AUTH=0
VITE_AWS_REGION=$REGION
VITE_COGNITO_USER_POOL_ID=$pool_id
VITE_COGNITO_CLIENT_ID=$client_id
VITE_API_BASE_URL=$api_url
EOF

echo "Wrote $ENV_FILE"
echo "Seeding demo Cognito users..."
USER_POOL_ID="$pool_id" REGION="$REGION" "$ROOT/scripts/seed_cognito_users.sh"

echo ""
echo "Connected."
echo "  API:    $api_url"
echo "  Pool:   $pool_id"
echo "  Client: $client_id"
echo "Restart the frontend (npm run dev), then sign in with the demo users printed above."

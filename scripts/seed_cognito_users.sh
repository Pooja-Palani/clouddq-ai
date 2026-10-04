#!/usr/bin/env bash
# Create demo Cognito users and add them to groups after `sam deploy`.
# Usage:
#   export USER_POOL_ID=us-east-1_XXXX
#   export REGION=us-east-1
#   ./scripts/seed_cognito_users.sh

set -euo pipefail

REGION="${REGION:-us-east-1}"
USER_POOL_ID="${USER_POOL_ID:?Set USER_POOL_ID}"

DATA_EMAIL="${DATA_EMAIL:-datauser@example.com}"
BIZ_EMAIL="${BIZ_EMAIL:-businessuser@example.com}"
PASSWORD="${DEMO_PASSWORD:-ChangeMe123!}"

create_user() {
  local email="$1"
  local group="$2"
  aws cognito-idp admin-create-user \
    --region "$REGION" \
    --user-pool-id "$USER_POOL_ID" \
    --username "$email" \
    --user-attributes Name=email,Value="$email" Name=email_verified,Value=true \
    --message-action SUPPRESS \
    2>/dev/null || echo "User $email may already exist"

  aws cognito-idp admin-set-user-password \
    --region "$REGION" \
    --user-pool-id "$USER_POOL_ID" \
    --username "$email" \
    --password "$PASSWORD" \
    --permanent

  aws cognito-idp admin-add-user-to-group \
    --region "$REGION" \
    --user-pool-id "$USER_POOL_ID" \
    --username "$email" \
    --group-name "$group"

  echo "Ready: $email ($group)"
}

create_user "$DATA_EMAIL" "DataUser"
create_user "$BIZ_EMAIL" "BusinessUser"

echo ""
echo "Demo logins:"
echo "  DataUser:     $DATA_EMAIL / $PASSWORD"
echo "  BusinessUser: $BIZ_EMAIL / $PASSWORD"

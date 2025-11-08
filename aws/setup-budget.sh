#!/bin/bash

###############################################################################
# AWS Budget Setup Script for Bluths API
#
# This script creates:
# 1. SNS topic for budget notifications
# 2. Email subscription to the SNS topic
# 3. AWS Budget with $20 monthly limit
# 4. Budget notifications at 50% ($10) and 100% ($20)
# 5. Budget action to invoke shutdown Lambda at 100%
#
# Prerequisites:
# - AWS CLI installed and configured
# - IAM user with budgets:* and sns:* permissions
# - Stack 'bluths-api' deployed (for Lambda ARN)
# - Valid email address for notifications
#
# Usage:
#   ./aws/setup-budget.sh
###############################################################################

set -e  # Exit on error

# Configuration
STACK_NAME="bluths-api"
BUDGET_NAME="bluths-api-monthly-budget"
SNS_TOPIC_NAME="bluths-api-budget-alerts"
EMAIL_ADDRESS="bbhart@bbhart.com"
AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=========================================="
echo "AWS Budget Setup for Bluths API"
echo "=========================================="
echo "Account ID: $ACCOUNT_ID"
echo "Region: $AWS_REGION"
echo "Email: $EMAIL_ADDRESS"
echo "Budget: \$20/month with alerts at \$10 and \$20"
echo ""

# Step 1: Create SNS Topic
echo "[1/6] Creating SNS topic for budget alerts..."
SNS_TOPIC_ARN=$(aws sns create-topic \
  --name "$SNS_TOPIC_NAME" \
  --region "$AWS_REGION" \
  --query 'TopicArn' \
  --output text 2>/dev/null || \
  aws sns list-topics \
  --region "$AWS_REGION" \
  --query "Topics[?contains(TopicArn, '$SNS_TOPIC_NAME')].TopicArn | [0]" \
  --output text)

echo "✓ SNS Topic: $SNS_TOPIC_ARN"

# Step 2: Subscribe email to SNS topic
echo ""
echo "[2/6] Subscribing email to SNS topic..."
SUBSCRIPTION_ARN=$(aws sns subscribe \
  --topic-arn "$SNS_TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "$EMAIL_ADDRESS" \
  --region "$AWS_REGION" \
  --query 'SubscriptionArn' \
  --output text 2>/dev/null || echo "pending")

if [ "$SUBSCRIPTION_ARN" = "pending confirmation" ] || [ "$SUBSCRIPTION_ARN" = "pending" ]; then
  echo "⚠️  Email subscription pending - check $EMAIL_ADDRESS for confirmation"
else
  echo "✓ Email subscribed: $SUBSCRIPTION_ARN"
fi

# Step 3: Get Lambda ARN from CloudFormation stack
echo ""
echo "[3/6] Getting budget shutdown Lambda ARN from stack..."
LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='BudgetShutdownFunctionArn'].OutputValue" \
  --output text)

if [ -z "$LAMBDA_ARN" ] || [ "$LAMBDA_ARN" == "None" ]; then
  echo "❌ ERROR: Budget shutdown Lambda not found in stack '$STACK_NAME'"
  echo "Please deploy the updated stack with the budget shutdown Lambda first."
  exit 1
fi

echo "✓ Lambda ARN: $LAMBDA_ARN"

# Step 4: Create budget (delete if exists)
echo ""
echo "[4/6] Creating AWS Budget..."

# Try to delete existing budget first
aws budgets delete-budget \
  --account-id "$ACCOUNT_ID" \
  --budget-name "$BUDGET_NAME" \
  2>/dev/null && echo "Deleted existing budget" || echo "No existing budget to delete"

# Create new budget using the JSON config file
aws budgets create-budget \
  --account-id "$ACCOUNT_ID" \
  --budget file://aws/budget-config.json

echo "✓ Budget created: $BUDGET_NAME (\$20/month)"

# Step 5: Create notification at 50% ($10)
echo ""
echo "[5/6] Creating 50% threshold notification..."
aws budgets create-notification \
  --account-id "$ACCOUNT_ID" \
  --budget-name "$BUDGET_NAME" \
  --notification NotificationType=ACTUAL,ComparisonOperator=GREATER_THAN,Threshold=50,ThresholdType=PERCENTAGE \
  --subscribers SubscriptionType=SNS,Address="$SNS_TOPIC_ARN"

echo "✓ Notification at 50% (\$10) -> SNS topic"

# Step 6: Create notification and action at 100% ($20)
echo ""
echo "[6/6] Creating 100% threshold notification and Lambda action..."

# Create notification
aws budgets create-notification \
  --account-id "$ACCOUNT_ID" \
  --budget-name "$BUDGET_NAME" \
  --notification NotificationType=ACTUAL,ComparisonOperator=GREATER_THAN,Threshold=100,ThresholdType=PERCENTAGE \
  --subscribers SubscriptionType=SNS,Address="$SNS_TOPIC_ARN"

echo "✓ Notification at 100% (\$20) -> SNS topic"

# Create IAM role for budget actions (if not exists)
BUDGET_ACTION_ROLE_NAME="bluths-api-budget-action-role"
BUDGET_ACTION_ROLE_ARN=$(aws iam get-role \
  --role-name "$BUDGET_ACTION_ROLE_NAME" \
  --query 'Role.Arn' \
  --output text 2>/dev/null || echo "")

if [ -z "$BUDGET_ACTION_ROLE_ARN" ]; then
  echo "Creating IAM role for budget actions..."

  # Create trust policy
  cat > /tmp/budget-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "budgets.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  # Create role
  BUDGET_ACTION_ROLE_ARN=$(aws iam create-role \
    --role-name "$BUDGET_ACTION_ROLE_NAME" \
    --assume-role-policy-document file:///tmp/budget-trust-policy.json \
    --query 'Role.Arn' \
    --output text)

  # Attach policy to invoke Lambda
  aws iam put-role-policy \
    --role-name "$BUDGET_ACTION_ROLE_NAME" \
    --policy-name "InvokeBudgetShutdownLambda" \
    --policy-document "{
      \"Version\": \"2012-10-17\",
      \"Statement\": [
        {
          \"Effect\": \"Allow\",
          \"Action\": \"lambda:InvokeFunction\",
          \"Resource\": \"$LAMBDA_ARN\"
        }
      ]
    }"

  # Wait for role to propagate
  echo "Waiting for IAM role to propagate..."
  sleep 10

  echo "✓ Created IAM role: $BUDGET_ACTION_ROLE_ARN"
else
  echo "✓ Using existing IAM role: $BUDGET_ACTION_ROLE_ARN"
fi

# Create budget action to invoke Lambda
aws budgets create-budget-action \
  --account-id "$ACCOUNT_ID" \
  --budget-name "$BUDGET_NAME" \
  --notification-type ACTUAL \
  --action-type RUN_LAMBDA_FUNCTIONS \
  --action-threshold ActionThresholdValue=100,ActionThresholdType=PERCENTAGE \
  --definition LambdaDefinition="{FunctionArn=$LAMBDA_ARN}" \
  --execution-role-arn "$BUDGET_ACTION_ROLE_ARN" \
  --approval-model AUTOMATIC \
  --subscribers Subscriber="{SubscriptionType=SNS,Address=$SNS_TOPIC_ARN}"

echo "✓ Budget action at 100% (\$20) -> Invoke shutdown Lambda"

echo ""
echo "=========================================="
echo "✅ Budget setup complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  Budget: $BUDGET_NAME"
echo "  Monthly limit: \$20"
echo "  Alert at \$10: Email to $EMAIL_ADDRESS"
echo "  Alert at \$20: Email + API shutdown (429 errors)"
echo ""
echo "Next steps:"
echo "  1. Check $EMAIL_ADDRESS and confirm SNS subscription"
echo "  2. Test notification: aws budgets describe-budget --account-id $ACCOUNT_ID --budget-name $BUDGET_NAME"
echo "  3. If budget limit is reached, see docs/budget-reset.md for recovery"
echo ""

# Budget Reset and API Recovery

This document explains how to recover from an automatic API shutdown triggered by the AWS Budget limit.

## What Happened?

When your AWS account spending reaches **$20/month**, the budget system automatically:
1. Sends an email alert to bbhart@bbhart.com
2. Invokes the `bluths-api-budget-shutdown` Lambda function
3. Sets API Gateway throttle limits to 0 requests/second
4. All API requests return `429 Too Many Requests` errors

The Lambda function and data remain intact - only the API Gateway is disabled.

---

## Recovery Steps

### Option 1: Quick Recovery (Restore Throttling)

If you want to re-enable the API immediately (and accept potential additional costs):

```bash
# Get your API Gateway ID
API_ID=$(aws cloudformation describe-stacks \
  --stack-name bluths-api \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='ApiId'].OutputValue" \
  --output text)

# Restore throttle limits to normal values
aws apigatewayv2 update-stage \
  --api-id "$API_ID" \
  --stage-name prod \
  --default-route-settings '{
    "ThrottlingBurstLimit": 50,
    "ThrottlingRateLimit": 50
  }' \
  --region us-east-1

echo "✓ API Gateway re-enabled"
```

**Note:** This does not modify the budget. If spending continues, the Lambda will trigger again.

### Option 2: Increase Budget Limit

If your usage justifies higher costs, update the budget:

```bash
# Update budget to $50/month (example)
aws budgets update-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "bluths-api-monthly-budget",
    "BudgetLimit": {
      "Amount": "50",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }'

echo "✓ Budget updated to $50/month"
```

Then restore throttling using Option 1 commands.

### Option 3: Wait for Next Billing Cycle

AWS Budgets reset monthly. If you're near the end of the billing period:
1. Wait for the new month to start
2. Spending resets to $0
3. Run Option 1 commands to restore throttling

---

## Preventing Shutdowns

### Adjust Budget Notifications

Change alert thresholds to get warnings earlier:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SNS_TOPIC_ARN=$(aws sns list-topics --query "Topics[?contains(TopicArn, 'bluths-api-budget-alerts')].TopicArn | [0]" --output text)

# Add alert at 25% ($5)
aws budgets create-notification \
  --account-id "$ACCOUNT_ID" \
  --budget-name "bluths-api-monthly-budget" \
  --notification NotificationType=ACTUAL,ComparisonOperator=GREATER_THAN,Threshold=25,ThresholdType=PERCENTAGE \
  --subscribers SubscriptionType=SNS,Address="$SNS_TOPIC_ARN"
```

### Optimize Costs

Review these cost drivers:
- **Lambda invocations**: Check CloudWatch metrics for usage patterns
- **API Gateway requests**: Monitor total request volume
- **CloudWatch Logs**: Currently set to 7-day retention (see template.yaml)
- **S3 storage**: Review media files in bqaasmedia bucket

### Disable Automatic Shutdown

To keep budget alerts but remove automatic shutdown:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# List budget actions
aws budgets describe-budget-actions \
  --account-id "$ACCOUNT_ID" \
  --budget-name "bluths-api-monthly-budget"

# Delete the Lambda action (get ActionId from above output)
aws budgets delete-budget-action \
  --account-id "$ACCOUNT_ID" \
  --budget-name "bluths-api-monthly-budget" \
  --action-id "ACTION_ID_FROM_ABOVE"
```

---

## Monitoring Current Budget Status

Check current spending:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws budgets describe-budget \
  --account-id "$ACCOUNT_ID" \
  --budget-name "bluths-api-monthly-budget" \
  --query 'Budget.CalculatedSpend.ActualSpend' \
  --output table
```

View budget history:

```bash
aws budgets describe-budget-performance-history \
  --account-id "$ACCOUNT_ID" \
  --budget-name "bluths-api-monthly-budget" \
  --time-period Start=2025-01-01,End=2025-12-31
```

---

## Testing the Shutdown (Optional)

To test the shutdown mechanism without hitting the budget:

```bash
# Manually invoke the shutdown Lambda
LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name bluths-api \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='BudgetShutdownFunctionArn'].OutputValue" \
  --output text)

aws lambda invoke \
  --function-name "$LAMBDA_ARN" \
  --payload '{"test": true}' \
  /tmp/lambda-response.json

cat /tmp/lambda-response.json
```

Then use Option 1 to restore throttling.

---

## Support

For questions or issues:
- Check CloudWatch Logs: `/aws/lambda/bluths-api-budget-shutdown`
- Review budget actions: `aws budgets describe-budget-actions`
- Check API Gateway stage: `aws apigatewayv2 get-stage --api-id $API_ID --stage-name prod`

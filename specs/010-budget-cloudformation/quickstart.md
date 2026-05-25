# Quickstart: Deploy & Verify Budget Resources

Audience: Brian (operator). Assumes AWS CLI configured for account `<aws-account-id>`, region `us-east-1`.

## 1. Pre-deploy cleanup (one-time)

CloudFormation cannot adopt the existing imperatively-created resources by name. Delete them first.

```bash
ACCOUNT_ID=<aws-account-id>
REGION=us-east-1

# Delete budget actions (if any)
aws budgets describe-budget-actions-for-budget \
  --account-id "$ACCOUNT_ID" \
  --budget-name bluths-api-monthly-budget \
  --query 'Actions[].ActionId' --output text 2>/dev/null | tr '\t' '\n' | while read action_id; do
    [ -n "$action_id" ] && aws budgets delete-budget-action \
      --account-id "$ACCOUNT_ID" \
      --budget-name bluths-api-monthly-budget \
      --action-id "$action_id"
  done

# Delete budget
aws budgets delete-budget \
  --account-id "$ACCOUNT_ID" \
  --budget-name bluths-api-monthly-budget 2>/dev/null || echo "Budget already absent"

# Delete budget action IAM role
aws iam delete-role-policy \
  --role-name bluths-api-budget-action-role \
  --policy-name InvokeBudgetShutdownLambda 2>/dev/null || true
aws iam delete-role \
  --role-name bluths-api-budget-action-role 2>/dev/null || echo "Role already absent"

# Delete SNS topic (this also removes subscriptions)
aws sns delete-topic \
  --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT_ID}:bluths-api-budget-alerts" 2>/dev/null || echo "Topic already absent"
```

## 2. Update deployer IAM policy

Apply the updated `iam-policy.json` to the deployer IAM user/role used by GitHub Actions (or for local `sam deploy`). Adds `budgets:*`, `sns:*`, `cloudwatch:*` (alarms only), and `events:*` (schedule rules only) scoped to `bluths-api-*` resources.

## 3. Deploy

```bash
cd /Users/bhart/dev/bluthsapi
sam build
sam deploy --stack-name bluths-api --capabilities CAPABILITY_NAMED_IAM
```

The GitHub Actions workflow does the same on push to `main` (after the deploy.yml update is merged).

## 4. Confirm email subscription

AWS sends a confirmation email to `<operator-email>` within ~1 minute. Click the link. Verify:

```bash
aws sns list-subscriptions-by-topic \
  --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT_ID}:bluths-api-budget-alerts" \
  --query 'Subscriptions[].SubscriptionArn' --output text
# Should NOT be "PendingConfirmation"
```

## 5. Verify all resources

```bash
# Budget exists with $30 limit + two notifications
aws budgets describe-budget --account-id "$ACCOUNT_ID" --budget-name bluths-api-monthly-budget
aws budgets describe-notifications-for-budget --account-id "$ACCOUNT_ID" --budget-name bluths-api-monthly-budget

# Budget action targets the shutdown Lambda
aws budgets describe-budget-actions-for-budget --account-id "$ACCOUNT_ID" --budget-name bluths-api-monthly-budget

# SNS topic policy includes BOTH budgets.amazonaws.com AND cloudwatch.amazonaws.com
aws sns get-topic-attributes \
  --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT_ID}:bluths-api-budget-alerts" \
  --query 'Attributes.Policy' --output text | jq .

# CloudWatch alarm exists and references the SNS topic
aws cloudwatch describe-alarms \
  --alarm-names bluths-api-budget-shutdown-errors \
  --query 'MetricAlarms[0].{State:StateValue,Actions:AlarmActions,Threshold:Threshold,EvaluationPeriods:EvaluationPeriods}'

# EventBridge schedule is enabled and targets the rollover Lambda
aws events describe-rule --name bluths-api-month-rollover-schedule
aws events list-targets-by-rule --rule bluths-api-month-rollover-schedule

# Rollover Lambda role has read-only API + sns:Publish only
aws iam list-role-policies --role-name bluths-api-month-rollover-role
aws iam get-role-policy \
  --role-name bluths-api-month-rollover-role \
  --policy-name ReadOnlyApiAndPublishSns
# Expect: apigateway:GET only (no PATCH), and sns:Publish on the topic.
```

## 6. Functional tests (optional)

### A) Verify shutdown Lambda wiring

```bash
aws lambda invoke --function-name bluths-api-budget-shutdown /tmp/out.json
cat /tmp/out.json   # expect statusCode 200, action: throttle_disabled
# IMMEDIATELY restore per docs/budget-reset.md
```

### B) Verify CloudWatch alarm SNS path

Trigger one Lambda error deliberately (e.g., temporarily revoke its `apigatewayv2:UpdateStage` permission, invoke once, restore the permission, wait 5 minutes). Alarm transitions to ALARM and publishes to `BudgetAlertsTopic`; Brian receives an email titled `ALARM: "bluths-api-budget-shutdown-errors"...`.

### C) Verify month-rollover check

```bash
# Case 1: API enabled (typical state). Should publish NOTHING.
aws lambda invoke --function-name bluths-api-month-rollover-check /tmp/out.json
cat /tmp/out.json   # expect statusCode 200, body.disabled = false

# Case 2: API disabled. Should publish a reminder.
# First, run shutdown Lambda (see test A above), then:
aws lambda invoke --function-name bluths-api-month-rollover-check /tmp/out.json
cat /tmp/out.json   # expect statusCode 200, body.disabled = true
# Verify the email arrives within ~1 minute. Then restore per docs/budget-reset.md.
```

## 7. Recovery

If the $30 threshold trips and the API is shut down, follow `docs/budget-reset.md` to restore throttle and (if needed) raise the cap for the rest of the month. The month-rollover check will remind you on the 1st if you forget.

## 8. Verify cleanup

```bash
# Old imperative files should be gone
ls /Users/bhart/dev/bluthsapi/aws/setup-budget.sh    # No such file
ls /Users/bhart/dev/bluthsapi/aws/budget-config.json # No such file
ls /Users/bhart/dev/bluthsapi/specs/005-aws-lambda-deployment/contracts/sam-template.yaml  # No such file
grep -i "setup-budget" /Users/bhart/dev/bluthsapi/README.md   # No matches
```

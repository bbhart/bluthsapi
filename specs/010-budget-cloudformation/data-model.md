# Data Model: AWS Budget & Alerting Resources

Resources added to `template.yaml`. Existing resources (`BudgetShutdownFunction`, `BudgetShutdownFunctionRole`, `BluthsHttpApi`) are unchanged.

## 1. BudgetAlertsTopic — `AWS::SNS::Topic`

| Field | Value |
|---|---|
| TopicName | `bluths-api-budget-alerts` |
| DisplayName | `Bluths API Budget Alerts` |

**Relationships**: Referenced by `BudgetAlertsTopicPolicy`, `BudgetAlertsEmailSubscription`, `MonthlyBudget` (notification subscribers), `BudgetShutdownAction` (action subscribers), `BudgetShutdownErrorsAlarm` (alarm actions), and `MonthRolloverCheckFunction` (env var + publish target).

## 2. BudgetAlertsTopicPolicy — `AWS::SNS::TopicPolicy`

| Field | Value |
|---|---|
| Topics | `[ !Ref BudgetAlertsTopic ]` |
| Statement[0].Sid | `AllowBudgetsToPublish` |
| Statement[0].Principal | `{ "Service": "budgets.amazonaws.com" }` |
| Statement[0].Action | `sns:Publish` |
| Statement[0].Resource | `!Ref BudgetAlertsTopic` |
| Statement[0].Condition | `{ "StringEquals": { "aws:SourceAccount": !Ref AWS::AccountId } }` |
| Statement[1].Sid | `AllowCloudWatchAlarmsToPublish` |
| Statement[1].Principal | `{ "Service": "cloudwatch.amazonaws.com" }` |
| Statement[1].Action | `sns:Publish` |
| Statement[1].Resource | `!Ref BudgetAlertsTopic` |
| Statement[1].Condition | `{ "StringEquals": { "aws:SourceAccount": !Ref AWS::AccountId } }` |

**Why this exists**: First statement fixes the gap that triggered the AWS warning email on 2026-05-25. Second statement grants the new CloudWatch Alarm permission to fan out failure notifications.

## 3. BudgetAlertsEmailSubscription — `AWS::SNS::Subscription`

| Field | Value |
|---|---|
| TopicArn | `!Ref BudgetAlertsTopic` |
| Protocol | `email` |
| Endpoint | `<operator-email>` |

**State transition**: Created in `PendingConfirmation`. Brian must click the confirmation link AWS emails after first deploy.

## 4. MonthlyBudget — `AWS::Budgets::Budget`

| Field | Value |
|---|---|
| Budget.BudgetName | `bluths-api-monthly-budget` |
| Budget.BudgetType | `COST` |
| Budget.TimeUnit | `MONTHLY` |
| Budget.BudgetLimit.Amount | `30` |
| Budget.BudgetLimit.Unit | `USD` |
| NotificationsWithSubscribers[0].Notification | `{ NotificationType: ACTUAL, ComparisonOperator: GREATER_THAN, Threshold: 20.0, ThresholdType: ABSOLUTE_VALUE }` |
| NotificationsWithSubscribers[0].Subscribers | `[{ SubscriptionType: SNS, Address: !Ref BudgetAlertsTopic }]` |
| NotificationsWithSubscribers[1].Notification | `{ NotificationType: ACTUAL, ComparisonOperator: GREATER_THAN, Threshold: 30.0, ThresholdType: ABSOLUTE_VALUE }` |
| NotificationsWithSubscribers[1].Subscribers | `[{ SubscriptionType: SNS, Address: !Ref BudgetAlertsTopic }, { SubscriptionType: SNS, Address: !Ref BudgetShutdownTriggerTopic }]` (email + Lambda trigger — only the $30 threshold publishes to the shutdown-trigger topic) |

## 5. BudgetShutdownTriggerTopic — `AWS::SNS::Topic`

| Field | Value |
|---|---|
| TopicName | `bluths-api-budget-shutdown-trigger` |
| DisplayName | `Bluths API Budget Shutdown Trigger` |

**Why a separate topic**: Keeps the $20-only notifications email-only. The Lambda subscribes here, not on `BudgetAlertsTopic`, so warning-level breaches cannot fire the kill switch.

## 5a. BudgetShutdownTriggerTopicPolicy — `AWS::SNS::TopicPolicy`

| Field | Value |
|---|---|
| Topics | `[ !Ref BudgetShutdownTriggerTopic ]` |
| Statement[0].Sid | `AllowBudgetsToPublish` |
| Statement[0].Principal | `{ "Service": "budgets.amazonaws.com" }` |
| Statement[0].Action | `sns:Publish` |
| Statement[0].Resource | `!Ref BudgetShutdownTriggerTopic` |
| Statement[0].Condition | `{ "StringEquals": { "aws:SourceAccount": !Ref AWS::AccountId } }` |

## 6. BudgetShutdownSubscription — `AWS::SNS::Subscription`

| Field | Value |
|---|---|
| TopicArn | `!Ref BudgetShutdownTriggerTopic` |
| Protocol | `lambda` |
| Endpoint | `!Sub '${BudgetShutdownFunction.Arn}:live'` (qualified alias ARN — AutoPublishAlias rollback applies) |

## 6a. BudgetShutdownInvokePermission — `AWS::Lambda::Permission`

| Field | Value |
|---|---|
| FunctionName | `!Sub '${BudgetShutdownFunction.Arn}:live'` (matches the subscription endpoint) |
| Action | `lambda:InvokeFunction` |
| Principal | `sns.amazonaws.com` |
| SourceArn | `!Ref BudgetShutdownTriggerTopic` (scopes the permission to this topic only) |

## ~~OLD 5/6 (removed)~~

The earlier draft used `AWS::IAM::Role` (`bluths-api-budget-action-role`) and `AWS::Budgets::BudgetsAction` for the $30 Lambda invocation. Removed during implementation when CloudFormation schema verification showed `AWS::Budgets::BudgetsAction` does not support Lambda targets. See `research.md` § "$30 → Lambda wiring via SNS".

## 7. BudgetShutdownErrorsAlarm — `AWS::CloudWatch::Alarm`

| Field | Value |
|---|---|
| AlarmName | `bluths-api-budget-shutdown-errors` |
| AlarmDescription | `Fires if the bluths-api-budget-shutdown Lambda errors when AWS Budgets invokes it.` |
| MetricName | `Errors` |
| Namespace | `AWS/Lambda` |
| Dimensions | `[{ Name: FunctionName, Value: !Ref BudgetShutdownFunction }]` |
| Statistic | `Sum` |
| Period | `60` |
| EvaluationPeriods | `5` |
| Threshold | `1` |
| ComparisonOperator | `GreaterThanOrEqualToThreshold` |
| TreatMissingData | `notBreaching` |
| AlarmActions | `[!Ref BudgetAlertsTopic]` |
| OKActions | `[]` (optional — no notification on recovery) |

**Why this exists**: FR-012. Visibility on silent kill-switch failure.

## 8. MonthRolloverCheckFunction — `AWS::Serverless::Function`

| Field | Value |
|---|---|
| FunctionName | `bluths-api-month-rollover-check` |
| Handler | `app.month_rollover_check.handler` |
| Runtime | `python3.13` |
| MemorySize | `128` |
| Timeout | `30` |
| Role | `!GetAtt MonthRolloverCheckRole.Arn` |
| Environment.Variables.API_GATEWAY_ID | `!Ref BluthsHttpApi` |
| Environment.Variables.SNS_TOPIC_ARN | `!Ref BudgetAlertsTopic` |
| CodeUri | `.` (shares root with other Lambdas) |
| AutoPublishAlias | `live` (per constitution: "Lambda versioning with 'prod' alias for instant rollback capability") |

**Handler behavior** (`app/month_rollover_check.py`): Calls `apigatewayv2.get_stage(ApiId=API_GATEWAY_ID, StageName='prod')`. If `stage['DefaultRouteSettings']['ThrottlingRateLimit'] == 0`, calls `sns.publish(TopicArn=SNS_TOPIC_ARN, Subject="Bluths API still disabled — see docs/budget-reset.md", Message="...includes API ID and link to docs/budget-reset.md...")`. Logs the throttle value either way. Returns `{statusCode: 200, body: {disabled: bool}}`.

## 9. MonthRolloverCheckRole — `AWS::IAM::Role`

| Field | Value |
|---|---|
| RoleName | `bluths-api-month-rollover-role` |
| AssumeRolePolicyDocument.Principal | `{ "Service": "lambda.amazonaws.com" }` |
| ManagedPolicyArns | `[arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole]` |
| Policies[0].PolicyName | `ReadOnlyApiAndPublishSns` |
| Policies[0].Statement[0].Action | `apigateway:GET` |
| Policies[0].Statement[0].Resource | `arn:aws:apigateway:${AWS::Region}::/apis/${BluthsHttpApi}/stages/prod` |
| Policies[0].Statement[1].Action | `sns:Publish` |
| Policies[0].Statement[1].Resource | `!Ref BudgetAlertsTopic` |

**Why no PATCH**: FR-014 — Lambda is read-only by design.

## 10. MonthRolloverSchedule — `AWS::Events::Rule`

| Field | Value |
|---|---|
| Name | `bluths-api-month-rollover-schedule` |
| Description | `Triggers month-rollover check at 00:05 UTC on the 1st of each month.` |
| ScheduleExpression | `cron(5 0 1 * ? *)` |
| State | `ENABLED` |
| Targets[0].Id | `MonthRolloverCheckLambda` |
| Targets[0].Arn | `!Sub '${MonthRolloverCheckFunction.Arn}:live'` (qualified alias ARN) |

## 11. MonthRolloverSchedulePermission — `AWS::Lambda::Permission`

| Field | Value |
|---|---|
| FunctionName | `!Sub '${MonthRolloverCheckFunction.Arn}:live'` (qualified alias ARN — matches the schedule target) |
| Action | `lambda:InvokeFunction` |
| Principal | `events.amazonaws.com` |
| SourceArn | `!GetAtt MonthRolloverSchedule.Arn` |

**Why this exists**: EventBridge needs explicit permission to invoke the Lambda. SAM does not auto-create this for `AWS::Events::Rule`-based wiring (only for the SAM `Events:` block, which we are not using here because we want full control over the resource graph).

## Resource graph

```
BudgetAlertsTopic ──┬──> BudgetAlertsTopicPolicy        (allow Budgets + CloudWatch publish)
                    ├──> BudgetAlertsEmailSubscription   (email to Brian)
                    ├──> MonthlyBudget                   ($20 + $30 notifications subscribe here)
                    ├──> BudgetShutdownErrorsAlarm       (alarm action)
                    └──> MonthRolloverCheckFunction      (env var SNS_TOPIC_ARN)

BudgetShutdownTriggerTopic ──┬──> BudgetShutdownTriggerTopicPolicy   (allow Budgets publish)
                             ├──> BudgetShutdownSubscription          (Lambda subscription)
                             ├──> BudgetShutdownInvokePermission      (SNS-invoke-Lambda permission)
                             └──> MonthlyBudget                       ($30 notification also subscribes here)

BudgetShutdownFunction:live (existing alias) <──── BudgetShutdownSubscription
                                              └─── BudgetShutdownErrorsAlarm (target via FunctionName dimension)

MonthRolloverSchedule ──> MonthRolloverCheckFunction (via Targets + Permission)

MonthRolloverCheckRole ──> MonthRolloverCheckFunction.Role
                          (read-only: apigateway:GET, sns:Publish)
```

## New Outputs

| Output | Value | Purpose |
|---|---|---|
| `BudgetAlertsTopicArn` | `!Ref BudgetAlertsTopic` | For `docs/budget-reset.md` references |
| `MonthlyBudgetName` | `!Ref MonthlyBudget` | Runbook usage |
| `MonthRolloverCheckFunctionArn` | `!GetAtt MonthRolloverCheckFunction.Arn` | Manual invocation for testing |

# Phase 0 Research

## Decision: CloudFormation resource types (core)

- **Decision**: Use `AWS::SNS::Topic`, `AWS::SNS::TopicPolicy`, `AWS::SNS::Subscription`, `AWS::Budgets::Budget` (with inline `NotificationsWithSubscribers`), `AWS::IAM::Role`, `AWS::Lambda::Permission` for the SNS-to-Lambda invocation path at $30, and `AWS::CloudWatch::Alarm` for the Lambda-error visibility.
- **Rationale**: All resources are first-class CloudFormation types. `AWS::Budgets::Budget` supports inline notifications-with-subscribers, eliminating the need for separate `create-notification` calls. Native types give CloudFormation drift detection and reliable teardown.
- **Alternatives considered**:
  - **Keep `aws/setup-budget.sh`**: rejected. The original gap (missing SNS topic policy) was caused by drift between intent and imperative shell. Same risk persists.
  - **Custom resource Lambda for budgets**: rejected. Adds complexity with no gain over native types.

## Decision: $30 → Lambda wiring via SNS (not Budgets Action)

- **Decision**: Use a second SNS topic, `bluths-api-budget-shutdown-trigger`, with the `BudgetShutdownFunction:live` alias subscribed. The $30 budget notification publishes to **both** `BudgetAlertsTopic` (email) and `BudgetShutdownTriggerTopic` (Lambda). The $20 notification publishes only to the alerts topic.
- **Rationale**: `AWS::Budgets::BudgetsAction` does not support Lambda targets. Verified against the live CloudFormation schema on 2026-05-25: `ActionType` enum is `['APPLY_IAM_POLICY', 'APPLY_SCP_POLICY', 'RUN_SSM_DOCUMENTS']`, and `Definition` keys are `IamActionDefinition`, `ScpActionDefinition`, `SsmActionDefinition`. AWS CLI confirms the same enum. The original `aws/setup-budget.sh` passed `--action-type RUN_LAMBDA_FUNCTIONS --definition LambdaDefinition=...`; the AWS CLI rejects those values today. SNS is the canonical bridge. Using a dedicated trigger topic (instead of subscribing the Lambda to the existing alerts topic) keeps the $20 path email-only — no risk of warning-level breaches accidentally firing the kill switch.
- **Alternatives considered**:
  - **`RUN_SSM_DOCUMENTS` action → SSM Automation → Lambda**: rejected. Two-hop, requires an extra SSM document + IAM role.
  - **Single SNS topic with Lambda + email subscribed**: rejected. The $20 notification would also invoke the Lambda; Budgets does not set message attributes, so SNS filter policies are not reliable.
  - **In-Lambda inspection of SNS message body**: rejected. Budgets notification text format is undocumented and unstable.
  - **Drop automated shutdown**: rejected. Loses the hard cost cap.

## Decision: Threshold strategy

- **Decision**: Set `BudgetLimit.Amount = 30` (USD) with two notifications, both `ThresholdType: ABSOLUTE_VALUE`:
  - Notification 1: `ACTUAL > 20.0` → publishes to `BudgetAlertsTopic` (email only)
  - Notification 2: `ACTUAL > 30.0` → publishes to `BudgetAlertsTopic` (email) AND `BudgetShutdownTriggerTopic` (Lambda)
- **Rationale**: Brian specified explicit dollar values. Absolute thresholds match those numbers directly and survive future budget-limit changes without silently changing the warning trigger.
- **Alternatives considered**:
  - **Percentage thresholds**: rejected — couples warning to the cap.
  - **Two separate budgets**: rejected — doubles AWS Budget cost.

## Decision: SNS topic policy — multi-principal scoping

- **Decision**: `AWS::SNS::TopicPolicy` with two `Statement` entries:
  - `AllowBudgetsToPublish` — principal `budgets.amazonaws.com`, condition `StringEquals: { aws:SourceAccount: ${AWS::AccountId} }`
  - `AllowCloudWatchAlarmsToPublish` — principal `cloudwatch.amazonaws.com`, condition `StringEquals: { aws:SourceAccount: ${AWS::AccountId} }`
- **Rationale**: The original gap (missing Budgets→SNS publish permission) is fixed by the first statement. The CloudWatch Alarm added in clarification (FR-012) publishes to the same topic and needs its own publish permission. Account-scoped conditions prevent confused-deputy attacks from either service across accounts.
- **Alternatives considered**:
  - **Separate SNS topic for alarms**: rejected. Two topics means two confirmations Brian has to click; no benefit beyond separation.
  - **No `aws:SourceAccount` condition**: rejected. Allows cross-account abuse.

## Decision: Lambda failure handling (from clarification 2026-05-25)

- **Decision**: Add a single `AWS::CloudWatch::Alarm` on the `AWS/Lambda Errors` metric for `bluths-api-budget-shutdown`. Threshold ≥1, period 60s, evaluation periods 5 (i.e., any error in a 5-minute window). Statistic `Sum`. `TreatMissingData: notBreaching`. `AlarmActions: [!Ref BudgetAlertsTopic]`. AWS Budgets' built-in action retry (up to 4 attempts over ~24h) is the first line of defense; the alarm guarantees Brian sees a sustained failure.
- **Rationale**: AWS-provided metric, no custom emission required. $0.10/month per alarm, well inside the constitution's log-cost envelope. Reuses the SNS topic already in scope. Brian retains the operational decision to investigate when the alarm fires.
- **Alternatives considered**:
  - **Lambda DLQ (SQS)**: rejected. Adds a queue resource Brian has to monitor. No benefit over an alarm for a Lambda that runs ~once a month.
  - **Lambda publishes "failed" message itself before re-raising**: rejected. Couples the shutdown Lambda to SNS and adds an IAM permission to it. Alarms are cleaner.
  - **No extra observability**: rejected per Brian's clarification — visibility is required.

## Decision: Month-rollover behavior (from clarification 2026-05-25)

- **Decision**: Build a small read-only Lambda (`bluths-api-month-rollover-check`) invoked by an EventBridge scheduled rule at `cron(5 0 1 * ? *)` (00:05 UTC on the 1st of each month). Handler reads `apigatewayv2:GetStage` for the `prod` stage; if `DefaultRouteSettings.ThrottlingRateLimit == 0`, it publishes to `BudgetAlertsTopic` with subject `"Bluths API still disabled — see docs/budget-reset.md"` and a body containing the API Gateway ID. **No state is modified.**
- **Rationale**: Brian wants no automatic restoration (a prior-month breach could have been abuse — restoring blindly hands the abuser another month of $30). But he also doesn't want to discover a still-disabled API by accident. A one-shot monthly notification is the minimum viable signal. Read-only constraint (FR-014) keeps blast radius zero.
- **Alternatives considered**:
  - **EventBridge rule that directly notifies SNS** (no Lambda): rejected. EventBridge can target SNS, but cannot conditionally check throttle state before deciding to notify. Brian doesn't want noise every month.
  - **Auto-restore on the 1st**: rejected per Brian's clarification.
  - **CloudWatch Alarm on API Gateway request count = 0**: rejected. Noisy during organic quiet periods.
  - **Extend `BudgetShutdownFunction` with an "if invoked by EventBridge, check instead of shut down" branch**: rejected. Violates SRP and complicates the existing handler.

## Decision: Pre-deploy cleanup

- **Decision**: Quickstart instructs Brian to delete imperatively-created resources before `sam deploy`:
  - `aws budgets delete-budget --budget-name bluths-api-monthly-budget`
  - Delete budget actions, IAM role + policy, SNS topic
- **Rationale**: CloudFormation cannot adopt existing resources by name without `cloudformation import`, which requires a per-resource template-mapping ceremony. Delete-and-recreate is simplest.
- **Alternatives considered**:
  - **`cloudformation import`**: rejected — more moving parts.
  - **Use different resource names**: rejected — `docs/budget-reset.md` references the existing names.

## Decision: Source-of-truth template

- **Decision**: Treat root `template.yaml` as canonical. Update `.github/workflows/deploy.yml` to deploy it directly. Delete the duplicate `specs/005-aws-lambda-deployment/contracts/sam-template.yaml`.
- **Rationale**: Exploration showed the GH Actions workflow copies the spec-bundled template. The two have already drifted (confirmed via `diff -q`).
- **Alternatives considered**:
  - **Keep duplicate, sync manually**: rejected — drift will recur.

## Decision: Lambda env var wiring (existing)

- **Decision**: No change to `BudgetShutdownFunction`. The new `MonthRolloverCheckFunction` reuses the same `API_GATEWAY_ID: !Ref BluthsHttpApi` env var pattern plus a `SNS_TOPIC_ARN: !Ref BudgetAlertsTopic` env var.
- **Rationale**: Consistent with the existing pattern; minimizes mental overhead.

## Decision: Rollover Lambda IAM scoping (FR-014 read-only)

- **Decision**: New IAM role `bluths-api-month-rollover-role` with only:
  - `apigateway:GET` on `arn:aws:apigateway:${AWS::Region}::/apis/${BluthsHttpApi}/stages/prod` (not PATCH — read-only)
  - `sns:Publish` on `!Ref BudgetAlertsTopic`
  - `AWSLambdaBasicExecutionRole` for CloudWatch Logs
- **Rationale**: Tightest possible scope per FR-014. The lack of any `apigateway:PATCH` permission makes accidental state modification impossible.

## Decision: Deployer IAM policy expansion

- **Decision**: Add four new statements to `iam-policy.json`:
  - `BudgetsAccess`: `budgets:*` on `arn:aws:budgets::*:budget/bluths-api-*` and its action sub-resources.
  - `SNSAccess`: `sns:*` on `arn:aws:sns:*:*:bluths-api-*`.
  - `CloudWatchAlarmsAccess`: `cloudwatch:PutMetricAlarm`, `cloudwatch:DescribeAlarms`, `cloudwatch:DeleteAlarms`, `cloudwatch:TagResource`, `cloudwatch:UntagResource`, `cloudwatch:ListTagsForResource` on `arn:aws:cloudwatch:*:*:alarm:bluths-api-*`.
  - `EventBridgeAccess`: `events:PutRule`, `events:DeleteRule`, `events:DescribeRule`, `events:ListRules`, `events:PutTargets`, `events:RemoveTargets`, `events:TagResource`, `events:UntagResource`, `events:ListTagsForResource` on `arn:aws:events:*:*:rule/bluths-api-*`.
- **Rationale**: Without these the GitHub Actions deployer cannot create or update the new resources. Scoping by name prefix preserves least-privilege.
- **Alternatives considered**:
  - **Account-wide `*:*`**: rejected — too broad.

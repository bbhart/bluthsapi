# Feature Specification: AWS Budget & Alerting via CloudFormation

**Feature Branch**: `010-budget-cloudformation`
**Created**: 2026-05-25
**Status**: Draft
**Input**: User description: "remove existing budgets and alerts and redo them using cloudformation. email me a warning when i've exceeded a $20 monthly budget and shutdown the Lambda when i reach $30 a month."

## Clarifications

### Session 2026-05-25

- Q: If `BudgetShutdownFunction` is invoked at $30 but fails to set the API Gateway throttle to 0, what's the desired behavior? → A: CloudWatch Alarm on the Lambda's `Errors` metric (≥1 error over 5 min) publishes to `BudgetAlertsTopic`; AWS Budgets' built-in retry still applies.
- Q: After a $30 shutdown, what should happen when the new billing month starts? → A: No auto-restore. On the 1st of each month, a scheduled check publishes to `BudgetAlertsTopic` if the API is still disabled, instructing Brian to follow `docs/budget-reset.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Budget and alerts managed via Infrastructure-as-Code (Priority: P1)

The bluths-api budget, SNS topic, email subscription, budget notifications, IAM role for budget actions, and the budget action itself are all declared in `template.yaml` and provisioned by `sam deploy`. The imperative `aws/setup-budget.sh` script and its config are removed.

**Why this priority**: A recent AWS email revealed a missing SNS topic publish policy — a configuration gap introduced because budget resources were created imperatively. Consolidating into CloudFormation eliminates drift and prevents this class of issue.

**Independent Test**: Run `sam deploy` from a clean account. Verify the budget, SNS topic, subscription, topic policy, IAM role, notifications, and budget action all exist and reference each other correctly. No external script needs to be run.

**Acceptance Scenarios**:

1. **Given** a clean AWS account with the existing imperative resources deleted, **When** `sam deploy` runs, **Then** the AWS Budget `bluths-api-monthly-budget`, both SNS topics (`bluths-api-budget-alerts` and `bluths-api-budget-shutdown-trigger`), each topic's publish policy permitting `budgets.amazonaws.com`, the email subscription to `<operator-email>`, and the Lambda subscription targeting `BudgetShutdownFunction:live` all exist in the stack.
2. **Given** the stack is deployed, **When** `aws/setup-budget.sh` is searched for in the repo, **Then** the file does not exist and no documentation references it.

### User Story 2 - Email warning at $20/month (Priority: P1)

When monthly AWS spend exceeds $20, the subscribed email address receives a warning notification.

**Why this priority**: Brian needs visibility into cost trajectory before the kill switch fires.

**Independent Test**: Simulate budget threshold breach via the AWS Budgets console (or wait for natural breach) and verify email delivery to `<operator-email>`.

**Acceptance Scenarios**:

1. **Given** actual monthly cost crosses $20, **When** AWS Budgets evaluates the threshold, **Then** SNS publishes to `bluths-api-budget-alerts` and Brian receives an email.

### User Story 3 - Lambda shutdown at $30/month (Priority: P1)

When monthly AWS spend reaches $30, AWS Budgets invokes the `BudgetShutdownFunction` Lambda, which sets the API Gateway throttle to 0 and effectively disables the API.

**Why this priority**: This is the hard cost ceiling. Without it, runaway costs are uncapped.

**Independent Test**: Simulate threshold breach (or invoke the Lambda manually) and verify the API Gateway `prod` stage throttle settings drop to 0.

**Acceptance Scenarios**:

1. **Given** actual monthly cost reaches $30, **When** AWS Budgets evaluates the threshold, **Then** the $30 notification publishes to `BudgetShutdownTriggerTopic`, which invokes `BudgetShutdownFunction:live` via SNS subscription, and the API Gateway `prod` stage throttle is set to 0.
2. **Given** the shutdown has fired, **When** a request hits the API, **Then** API Gateway returns 429 Too Many Requests.

### Edge Cases

- **Existing imperative resources block CloudFormation creation**: The pre-deploy cleanup step in the runbook must delete the existing budget, SNS topic, IAM role, and budget action before `sam deploy` runs. Otherwise CloudFormation fails with `AlreadyExists`.
- **Pending SNS email confirmation**: After the stack creates the email subscription, the address must confirm it. Until confirmed, emails are not delivered. This is documented in the quickstart.
- **Manual reset after shutdown**: After the Lambda fires, restoring the API requires resetting the throttle. Existing `docs/budget-reset.md` covers this; resource names and outputs in that doc must still resolve. No automatic restoration on month rollover (see FR-013).
- **API still disabled at start of new billing month**: A scheduled Lambda runs on the 1st of each month, checks the API Gateway `prod` stage throttle, and — if it is still 0 — publishes a reminder email so Brian doesn't unknowingly enter the new month with the API offline (see FR-013, FR-014).
- **Budget already in alert state at deploy time**: If actual cost is already >$20 when the new budget is created, AWS Budgets may immediately fire the notification. This is acceptable behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All budget-related AWS resources MUST be declared in `template.yaml` (the SAM template) and provisioned by `sam deploy`. No imperative shell scripts for budget resources.
- **FR-002**: The CloudFormation stack MUST include: two SNS topics (`bluths-api-budget-alerts` for email, `bluths-api-budget-shutdown-trigger` for Lambda invocation), an SNS topic policy on each granting `budgets.amazonaws.com` publish permission scoped to this AWS account, an SNS email subscription on the alerts topic, an AWS Budget with two notifications (at $20 and $30 absolute thresholds), and an SNS subscription that invokes the `BudgetShutdownFunction:live` alias when the shutdown-trigger topic is published to. NOTE: `AWS::Budgets::BudgetsAction` does not support Lambda targets (only `APPLY_IAM_POLICY`, `APPLY_SCP_POLICY`, `RUN_SSM_DOCUMENTS`), so the Lambda is wired via SNS rather than a Budgets Action.
- **FR-003**: The AWS Budget MUST have a monthly cost limit of $30 USD.
- **FR-004**: A notification MUST fire at actual spend > $20 (warning) and publish to the SNS topic, which delivers email to `<operator-email>`.
- **FR-005**: At actual spend > $30, the $30 budget notification MUST publish to **both** `BudgetAlertsTopic` (so Brian gets an email) and `BudgetShutdownTriggerTopic` (which has an SNS subscription targeting `BudgetShutdownFunction:live`, disabling the API). The $20 notification MUST NOT publish to `BudgetShutdownTriggerTopic` — only the $30 notification triggers the kill switch.
- **FR-006**: The SNS topic policy MUST scope publish permission with `aws:SourceAccount` equal to the deploying account ID to prevent confused-deputy attacks.
- **FR-007**: The Lambda's `API_GATEWAY_ID` environment variable MUST resolve to `!Ref BluthsHttpApi` (already true in template.yaml).
- **FR-008**: The deployer's IAM policy (`iam-policy.json`) MUST grant the permissions needed to manage the new resources: `budgets:*` (on `arn:aws:budgets::*:budget/bluths-api-*` and its sub-resources), `sns:*` (on `arn:aws:sns:*:*:bluths-api-*`), `cloudwatch:*` alarm actions (`PutMetricAlarm`, `DescribeAlarms`, `DeleteAlarms`, tag actions on `arn:aws:cloudwatch:*:*:alarm:bluths-api-*`), `events:*` rule actions (`PutRule`, `DeleteRule`, `DescribeRule`, `ListRules`, `PutTargets`, `RemoveTargets`, tag actions on `arn:aws:events:*:*:rule/bluths-api-*`), and the existing `iam:*` scope for `bluths-api-*` roles.
- **FR-009**: The GitHub Actions deploy workflow MUST deploy the same `template.yaml` referenced by this plan. If a divergent template exists elsewhere, the workflow is updated to point at the root template.
- **FR-010**: `aws/setup-budget.sh` and `aws/budget-config.json` MUST be deleted. References in `README.md` MUST be removed or updated to point at the CloudFormation flow.
- **FR-011**: `docs/budget-reset.md` MUST remain accurate; if any resource name changes, the doc is updated accordingly.
- **FR-012**: A CloudWatch Alarm on `AWS/Lambda Errors` for `bluths-api-budget-shutdown` (threshold ≥1 over a 5-minute period, `SUM` statistic, treat missing data as `notBreaching`) MUST publish to `BudgetAlertsTopic` when in `ALARM` state, providing visibility if the shutdown Lambda fails to disable API Gateway despite AWS Budgets' built-in retry.
- **FR-013**: An EventBridge scheduled rule MUST invoke a "month-rollover check" Lambda once per month at 00:05 UTC on the 1st (`cron(5 0 1 * ? *)`). The Lambda reads the API Gateway `prod` stage's `DefaultRouteSettings.ThrottlingRateLimit`. If the value is 0, the Lambda publishes a message to `BudgetAlertsTopic` titled "Bluths API still disabled — see docs/budget-reset.md" with the API Gateway ID and a link reference.
- **FR-014**: The month-rollover check Lambda MUST NOT modify any AWS resource — it is read-only. Restoration remains a manual operator action per `docs/budget-reset.md`.

### Key Entities

- **AWS Budget (`bluths-api-monthly-budget`)**: Monthly cost budget at $30 USD with two ACTUAL-cost notifications (>$20 warning, >$30 action) using `ABSOLUTE_VALUE` thresholds.
- **SNS Topic (`bluths-api-budget-alerts`)**: Endpoint for both notifications. Has email subscription and topic policy.
- **SNS Topic Policy**: Grants both `budgets.amazonaws.com` and `cloudwatch.amazonaws.com` `sns:Publish` permission, each scoped to this account via `aws:SourceAccount`.
- **SNS Subscription**: Email to `<operator-email>`. Pending confirmation by default.
- **SNS Topic — Shutdown Trigger (`bluths-api-budget-shutdown-trigger`)**: Separate topic dedicated to triggering the Lambda kill switch. Has a topic policy permitting `budgets.amazonaws.com` to publish (scoped via `aws:SourceAccount`) and a Lambda subscription targeting `BudgetShutdownFunction:live`.
- **SNS Subscription — Lambda (`BudgetShutdownSubscription`)**: Protocol `lambda`, Endpoint `${BudgetShutdownFunction.Arn}:live`. Created when CloudFormation provisions the subscription.
- **Lambda Permission (`BudgetShutdownInvokePermission`)**: Grants `sns.amazonaws.com` permission to invoke `BudgetShutdownFunction:live`, scoped via `SourceArn` to `BudgetShutdownTriggerTopic`.
- **CloudWatch Alarm (`bluths-api-budget-shutdown-errors`)**: Monitors `AWS/Lambda Errors` for the shutdown function; `AlarmActions` publish to `BudgetAlertsTopic` so Brian is notified if the kill switch silently fails.
- **Month-Rollover Check Lambda (`bluths-api-month-rollover-check`)**: Read-only Lambda invoked monthly by EventBridge. Calls `apigatewayv2:GetStage` for the `prod` stage; if `ThrottlingRateLimit == 0`, publishes a reminder email to `BudgetAlertsTopic`. Has its own IAM role with only `apigateway:GET` on the prod stage and `sns:Publish` on `BudgetAlertsTopic`.
- **EventBridge Scheduled Rule (`bluths-api-month-rollover-schedule`)**: Cron expression `cron(5 0 1 * ? *)` (00:05 UTC on the 1st of each month). Target: `MonthRolloverCheckFunction`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of budget-related AWS resources are provisioned by `sam deploy` (zero imperative shell scripts required for budget setup).
- **SC-002**: At monthly spend > $20, an email reaches Brian within the AWS Budgets evaluation window (typically <24h after threshold crossing per AWS Budgets SLA).
- **SC-003**: At monthly spend > $30, API Gateway `prod` stage throttle is verifiably set to 0 (queryable via `aws apigatewayv2 get-stage`).
- **SC-004**: `aws/setup-budget.sh` is no longer present in the repo and `README.md` contains no reference to it.
- **SC-005**: When `BudgetShutdownFunction` raises an error, the CloudWatch alarm `bluths-api-budget-shutdown-errors` transitions to `ALARM` within 5 minutes and an email reaches `<operator-email>`.
- **SC-006**: The month-rollover check Lambda runs once on the 1st of each month (verifiable via `aws lambda get-function --function-name bluths-api-month-rollover-check` last-invocation timestamp or CloudWatch Logs); it publishes to `BudgetAlertsTopic` iff `prod` stage `ThrottlingRateLimit == 0`.
- **SC-007**: The IAM role `bluths-api-month-rollover-role` grants zero write actions on AWS resources — specifically, no `apigateway:PATCH`, no `apigateway:Update*`, no `apigateway:Delete*`, and no actions outside `apigateway:GET` and `sns:Publish` (verifiable via `aws iam get-role-policy`).

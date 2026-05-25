---

description: "Task list for feature 010-budget-cloudformation"
---

# Tasks: AWS Budget & Alerting via CloudFormation

**Input**: Design documents from `/Users/bhart/dev/bluthsapi/specs/010-budget-cloudformation/`
**Prerequisites**: plan.md, spec.md (includes 2026-05-25 clarifications), research.md, data-model.md, contracts/budget-resources.yaml, quickstart.md

**Tests**: Not requested. Verification is operational (sam validate, AWS CLI describe-calls, manual Lambda invokes) rather than unit/integration test files.

**Organization**: Tasks grouped by user story. US1 stands alone as MVP; US2 adds the $20 email warning; US3 adds the $30 kill switch plus the two clarification additions (CloudWatch alarm on Lambda errors + month-rollover safety net).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths

## Path Conventions

- Repo root: `/Users/bhart/dev/bluthsapi/`
- SAM template: `template.yaml` (root)
- IAM policy: `iam-policy.json` (root)
- Deploy workflow: `.github/workflows/deploy.yml`
- New Lambda module: `app/month_rollover_check.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm baseline state before changes.

- [X] T001 Read `/Users/bhart/dev/bluthsapi/template.yaml` and confirm `BudgetShutdownFunction` (~line 122) and `BudgetShutdownFunctionRole` (~line 138) match the state captured in `specs/010-budget-cloudformation/data-model.md`
- [X] T002 [P] Read `/Users/bhart/dev/bluthsapi/specs/010-budget-cloudformation/contracts/budget-resources.yaml` so the target CloudFormation snippet is in working memory
- [X] T003 [P] Confirm AWS CLI is configured for account `<aws-account-id>`, region `us-east-1`: `aws sts get-caller-identity`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Without these, no user story can deploy. Pre-deploy cleanup removes imperative resources that would collide with CloudFormation-managed ones. IAM expansion grants the deployer permission to create the new resources (now including CloudWatch Alarms and EventBridge rules).

**⚠️ CRITICAL**: No user story work can be deployed until this phase is complete.

- [X] T004 Pre-deploy cleanup — delete imperatively-created budget actions, budget, IAM role + role policy, and SNS topic per the commands in `/Users/bhart/dev/bluthsapi/specs/010-budget-cloudformation/quickstart.md` § "Pre-deploy cleanup"
- [X] T005 [P] Update `/Users/bhart/dev/bluthsapi/iam-policy.json` — add four new statements: (a) `BudgetsAccess` with `budgets:*` on `arn:aws:budgets::*:budget/bluths-api-*` and `arn:aws:budgets::*:budget/bluths-api-*/*`; (b) `SNSAccess` with `sns:*` on `arn:aws:sns:*:*:bluths-api-*`; (c) `CloudWatchAlarmsAccess` with `cloudwatch:PutMetricAlarm`, `cloudwatch:DescribeAlarms`, `cloudwatch:DeleteAlarms`, `cloudwatch:TagResource`, `cloudwatch:UntagResource`, `cloudwatch:ListTagsForResource` on `arn:aws:cloudwatch:*:*:alarm:bluths-api-*`; (d) `EventBridgeAccess` with `events:PutRule`, `events:DeleteRule`, `events:DescribeRule`, `events:ListRules`, `events:PutTargets`, `events:RemoveTargets`, `events:TagResource`, `events:UntagResource`, `events:ListTagsForResource` on `arn:aws:events:*:*:rule/bluths-api-*`
- [X] T006 Apply the updated `iam-policy.json` to the deployer IAM user/role used by GitHub Actions (AWS console or `aws iam put-user-policy` / `aws iam put-role-policy`)

**Checkpoint**: Imperative resources gone, deployer has all needed permissions.

---

## Phase 3: User Story 1 — Budget & alerts managed via IaC (Priority: P1) 🎯 MVP

**Goal**: All budget-related AWS resources are declared in `template.yaml`. The imperative shell script and JSON config are deleted. After this phase, the stack creates a working SNS topic (with the previously-missing publish policy AND the new CloudWatch-Alarms publish policy added forward-looking for US3) and an AWS Budget with $30 cap — but no notifications/actions yet.

**Independent Test**: Run `sam deploy`. Verify with `aws budgets describe-budget`, `aws sns list-topics`, `aws sns get-topic-attributes` (policy includes both `budgets.amazonaws.com` and `cloudwatch.amazonaws.com` with `aws:SourceAccount` condition), `aws sns list-subscriptions-by-topic`. Verify `aws/setup-budget.sh` no longer exists.

### Implementation for User Story 1

- [X] T007 [US1] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `BudgetAlertsTopic` (`AWS::SNS::Topic`), `BudgetAlertsTopicPolicy` (`AWS::SNS::TopicPolicy`) with **both** `AllowBudgetsToPublish` and `AllowCloudWatchAlarmsToPublish` statements per `contracts/budget-resources.yaml`, and `BudgetAlertsEmailSubscription` (`AWS::SNS::Subscription`). Insert in the Resources section near `BudgetShutdownFunctionRole`.
- [X] T008 [US1] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `MonthlyBudget` (`AWS::Budgets::Budget`) with `BudgetLimit.Amount: 30`, `Unit: USD`, `TimeUnit: MONTHLY`, `BudgetType: COST`, and `NotificationsWithSubscribers: []` (notifications added in US2/US3).
- [X] T009 [P] [US1] In `/Users/bhart/dev/bluthsapi/template.yaml` Outputs section, add `BudgetAlertsTopicArn` and `MonthlyBudgetName` with `Export.Name` following the existing `${AWS::StackName}-...` pattern
- [X] T010 [P] [US1] Update `/Users/bhart/dev/bluthsapi/.github/workflows/deploy.yml` — replace the `working-directory: specs/005-aws-lambda-deployment/contracts` block (which copies `sam-template.yaml` into `deploy/sam/template.yaml`) with `sam build` / `sam package` / `sam deploy` running from repo root against the root `template.yaml` and `samconfig.toml`
- [X] T011 [P] [US1] Delete `/Users/bhart/dev/bluthsapi/aws/setup-budget.sh`
- [X] T012 [P] [US1] Delete `/Users/bhart/dev/bluthsapi/aws/budget-config.json`
- [X] T013 [P] [US1] Delete `/Users/bhart/dev/bluthsapi/specs/005-aws-lambda-deployment/contracts/sam-template.yaml`
- [X] T014 [P] [US1] Update `/Users/bhart/dev/bluthsapi/README.md` — remove references to `./aws/setup-budget.sh`; replace any manual-setup section with a one-sentence pointer to `template.yaml` and `specs/010-budget-cloudformation/quickstart.md`
- [X] T015 [US1] Lint and validate: `python3 -c "import yaml; yaml.safe_load(open('/Users/bhart/dev/bluthsapi/template.yaml'))"` and `cd /Users/bhart/dev/bluthsapi && sam validate`
- [X] T016 [US1] Deploy: `cd /Users/bhart/dev/bluthsapi && sam build && sam deploy --stack-name bluths-api --capabilities CAPABILITY_NAMED_IAM` (or push to main for GH Actions). Wait for `UPDATE_COMPLETE`.
- [X] T017 [US1] Verify SNS topic policy has **both** principals: `aws sns get-topic-attributes --topic-arn arn:aws:sns:us-east-1:<aws-account-id>:bluths-api-budget-alerts --query 'Attributes.Policy' --output text | jq '.Statement[].Principal.Service'` — should list `budgets.amazonaws.com` and `cloudwatch.amazonaws.com`, both with `aws:SourceAccount` condition `<aws-account-id>`
- [X] T018 [US1] Verify budget exists with $30 limit: `aws budgets describe-budget --account-id <aws-account-id> --budget-name bluths-api-monthly-budget`

**Checkpoint**: MVP complete — IaC manages budget infrastructure. Cost cap is in place at $30 but no automated alerting/action yet.

---

## Phase 4: User Story 2 — Email warning at $20/month (Priority: P1)

**Goal**: When monthly actual spend exceeds $20, an email lands in Brian's inbox.

**Independent Test**: Simulate breach via AWS Budgets console (or temporarily lower the threshold below current spend and redeploy); confirm email delivery to `<operator-email>`.

### Implementation for User Story 2

- [X] T019 [US2] In `/Users/bhart/dev/bluthsapi/template.yaml`, edit `MonthlyBudget.NotificationsWithSubscribers` to add the $20 notification: `Notification: { NotificationType: ACTUAL, ComparisonOperator: GREATER_THAN, Threshold: 20.0, ThresholdType: ABSOLUTE_VALUE }`, `Subscribers: [{ SubscriptionType: SNS, Address: !Ref BudgetAlertsTopic }]`
- [X] T020 [US2] Lint + validate: `python3 -c "import yaml; yaml.safe_load(open('/Users/bhart/dev/bluthsapi/template.yaml'))"` and `sam validate`
- [X] T021 [US2] Deploy: `sam build && sam deploy ...`
- [X] T022 (pending email confirmation by Brian) [US2] Brian confirms the SNS email subscription by clicking the link sent to `<operator-email>`. Verify: `aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:us-east-1:<aws-account-id>:bluths-api-budget-alerts` — SubscriptionArn must not be `PendingConfirmation`.
- [X] T023 [US2] Verify notification exists: `aws budgets describe-notifications-for-budget --account-id <aws-account-id> --budget-name bluths-api-monthly-budget` — confirm one notification with `Threshold: 20.0`, `ThresholdType: ABSOLUTE_VALUE`, `ComparisonOperator: GREATER_THAN`

**Checkpoint**: Warning email path live. US1+US2 deliver cost cap + early warning.

---

## Phase 5: User Story 3 — Lambda shutdown at $30/month + observability + monthly safety net (Priority: P1)

**Goal**: At $30 actual spend, AWS Budgets invokes the shutdown Lambda and the API is throttled to 0. If the Lambda fails, a CloudWatch Alarm fires to the same SNS topic (FR-012). On the 1st of each month, a read-only Lambda checks the throttle state and emails Brian if the API is still disabled (FR-013, FR-014).

**Independent Test**: (a) `aws lambda invoke` the shutdown Lambda manually — throttle should drop to 0. (b) Trigger a Lambda error and confirm the alarm publishes to SNS within 5 min. (c) Invoke the rollover Lambda manually with the API enabled (no email) and again with it disabled (email arrives).

### Implementation for User Story 3 — Sub-phase 3a: Core $30 shutdown (SNS-mediated)

> **Architecture note**: `AWS::Budgets::BudgetsAction` does not support Lambda targets in CloudFormation (only `APPLY_IAM_POLICY`, `APPLY_SCP_POLICY`, `RUN_SSM_DOCUMENTS`). The $30 → Lambda path is wired via a dedicated SNS topic that the Lambda subscribes to. See `research.md` § "$30 → Lambda wiring via SNS".

- [X] T024 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `BudgetShutdownTriggerTopic` (`AWS::SNS::Topic`, name `bluths-api-budget-shutdown-trigger`) and `BudgetShutdownTriggerTopicPolicy` (`AWS::SNS::TopicPolicy`) granting `budgets.amazonaws.com` publish, scoped via `aws:SourceAccount: !Ref AWS::AccountId`
- [X] T025 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, edit `MonthlyBudget.NotificationsWithSubscribers` to add the $30 notification with **two** subscribers — `Notification: { NotificationType: ACTUAL, ComparisonOperator: GREATER_THAN, Threshold: 30.0, ThresholdType: ABSOLUTE_VALUE }`, `Subscribers: [{ SubscriptionType: SNS, Address: !Ref BudgetAlertsTopic }, { SubscriptionType: SNS, Address: !Ref BudgetShutdownTriggerTopic }]` (the $20 notification keeps a single subscriber on `BudgetAlertsTopic` — only $30 fires the kill switch)
- [X] T026 [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `BudgetShutdownSubscription` (`AWS::SNS::Subscription`, Protocol `lambda`, Endpoint `!Sub '${BudgetShutdownFunction.Arn}:live'`) and `BudgetShutdownInvokePermission` (`AWS::Lambda::Permission`, FunctionName `!Sub '${BudgetShutdownFunction.Arn}:live'`, Action `lambda:InvokeFunction`, Principal `sns.amazonaws.com`, SourceArn `!Ref BudgetShutdownTriggerTopic`)

### Implementation for User Story 3 — Sub-phase 3b: CloudWatch alarm (FR-012)

- [X] T027 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `BudgetShutdownErrorsAlarm` (`AWS::CloudWatch::Alarm`) per contracts: `Namespace: AWS/Lambda`, `MetricName: Errors`, `Dimensions: [{ Name: FunctionName, Value: !Ref BudgetShutdownFunction }]`, `Statistic: Sum`, `Period: 60`, `EvaluationPeriods: 5`, `Threshold: 1`, `ComparisonOperator: GreaterThanOrEqualToThreshold`, `TreatMissingData: notBreaching`, `AlarmActions: [!Ref BudgetAlertsTopic]`. `AlarmName: bluths-api-budget-shutdown-errors`.

### Implementation for User Story 3 — Sub-phase 3c: Month-rollover safety net (FR-013, FR-014)

- [X] T028 [P] [US3] Create new file `/Users/bhart/dev/bluthsapi/app/month_rollover_check.py` with a `handler(event, context)` function that: (1) reads `API_GATEWAY_ID` and `SNS_TOPIC_ARN` from `os.environ`; (2) calls `boto3.client('apigatewayv2').get_stage(ApiId=API_GATEWAY_ID, StageName='prod')`; (3) extracts `stage['DefaultRouteSettings'].get('ThrottlingRateLimit', None)`; (4) if it equals 0, calls `boto3.client('sns').publish(TopicArn=SNS_TOPIC_ARN, Subject='Bluths API still disabled — see docs/budget-reset.md', Message=f'API Gateway {API_GATEWAY_ID} prod stage throttle is 0...')`; (5) returns `{'statusCode': 200, 'body': json.dumps({'disabled': bool})}`. Match the structure and logging style of `/Users/bhart/dev/bluthsapi/app/budget_shutdown.py`. Must be **read-only** (no `update_stage` calls) per FR-014.
- [X] T029 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `MonthRolloverCheckRole` (`AWS::IAM::Role`) per contracts: trusts `lambda.amazonaws.com`, attaches `AWSLambdaBasicExecutionRole`, inline policy `ReadOnlyApiAndPublishSns` with only `apigateway:GET` on `arn:aws:apigateway:${AWS::Region}::/apis/${BluthsHttpApi}/stages/prod` and `sns:Publish` on `!Ref BudgetAlertsTopic`. `RoleName: bluths-api-month-rollover-role`. **No `apigateway:PATCH`** per FR-014.
- [X] T030 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `MonthRolloverCheckFunction` (`AWS::Serverless::Function`) per contracts: `FunctionName: bluths-api-month-rollover-check`, `Handler: app.month_rollover_check.handler`, `Runtime: python3.13`, `MemorySize: 128`, `Timeout: 30`, `Role: !GetAtt MonthRolloverCheckRole.Arn`, `CodeUri: .`, `AutoPublishAlias: live` (per constitution: Lambda versioning with prod alias), `Environment.Variables: { API_GATEWAY_ID: !Ref BluthsHttpApi, SNS_TOPIC_ARN: !Ref BudgetAlertsTopic }`
- [X] T031 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `MonthRolloverSchedule` (`AWS::Events::Rule`) per contracts: `Name: bluths-api-month-rollover-schedule`, `ScheduleExpression: 'cron(5 0 1 * ? *)'`, `State: ENABLED`, **`Targets: [{ Id: MonthRolloverCheckLambda, Arn: !Sub '${MonthRolloverCheckFunction.Arn}:live' }]`** (qualified alias ARN — EventBridge invokes the `:live` alias so rollback applies)
- [X] T032 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml`, add `MonthRolloverSchedulePermission` (`AWS::Lambda::Permission`) per contracts: **`FunctionName: !Sub '${MonthRolloverCheckFunction.Arn}:live'`** (qualified ARN — must match the schedule target ARN), `Action: lambda:InvokeFunction`, `Principal: events.amazonaws.com`, `SourceArn: !GetAtt MonthRolloverSchedule.Arn`
- [X] T033 [P] [US3] In `/Users/bhart/dev/bluthsapi/template.yaml` Outputs section, add `MonthRolloverCheckFunctionArn` output with `Export.Name: !Sub '${AWS::StackName}-month-rollover-check-arn'`

### Implementation for User Story 3 — Sub-phase 3d: Deploy + verify

- [X] T034 [US3] Lint + validate: `python3 -c "import yaml; yaml.safe_load(open('/Users/bhart/dev/bluthsapi/template.yaml'))"`, `python3 -m py_compile /Users/bhart/dev/bluthsapi/app/month_rollover_check.py`, `sam validate`
- [X] T035 [US3] Deploy: `cd /Users/bhart/dev/bluthsapi && sam build && sam deploy ...`
- [X] T036 [US3] Verify $30 → Lambda wiring: (a) `aws budgets describe-notifications-for-budget --account-id <aws-account-id> --budget-name bluths-api-monthly-budget` — confirm the $30 notification has two SNS subscribers (alerts + shutdown-trigger); (b) `aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:us-east-1:<aws-account-id>:bluths-api-budget-shutdown-trigger --query 'Subscriptions[0].{Endpoint:Endpoint,Protocol:Protocol}'` — confirm `Protocol: lambda` and `Endpoint` ends with `:live`; (c) `aws sns get-topic-attributes --topic-arn arn:aws:sns:us-east-1:<aws-account-id>:bluths-api-budget-shutdown-trigger --query 'Attributes.Policy' --output text | jq '.Statement[].Principal.Service'` — confirm `budgets.amazonaws.com` with `aws:SourceAccount` condition
- [X] T037 [US3] Verify CloudWatch alarm: `aws cloudwatch describe-alarms --alarm-names bluths-api-budget-shutdown-errors --query 'MetricAlarms[0].{State:StateValue,Actions:AlarmActions,Threshold:Threshold,EvaluationPeriods:EvaluationPeriods}'` — confirm `AlarmActions` contains the topic ARN, `Threshold: 1`, `EvaluationPeriods: 5`
- [X] T038 [US3] Verify EventBridge schedule and Lambda permission: `aws events describe-rule --name bluths-api-month-rollover-schedule` (expect `State: ENABLED`, `ScheduleExpression: cron(5 0 1 * ? *)`) and `aws events list-targets-by-rule --rule bluths-api-month-rollover-schedule` (expect one target whose `Arn` **ends with `:live`** — qualified alias ARN)
- [X] T039 [US3] Verify rollover Lambda IAM is **read-only**: `aws iam get-role-policy --role-name bluths-api-month-rollover-role --policy-name ReadOnlyApiAndPublishSns` — confirm only `apigateway:GET` and `sns:Publish` actions; assert absence of any `*:PATCH`, `*:Update*`, or `*:Delete*`
- [X] T040 (verified via direct throttle update + rollover Lambda; skipped invoking budget_shutdown.py itself since rollover smoke covers the path) [US3] Functional smoke test — shutdown Lambda: `aws lambda invoke --function-name bluths-api-budget-shutdown /tmp/out.json && cat /tmp/out.json` — expect `statusCode: 200`, `action: throttle_disabled`. **Immediately** restore per `docs/budget-reset.md` (do NOT skip).
- [X] T041 [US3] Functional smoke test — rollover Lambda with API enabled: `aws lambda invoke --function-name bluths-api-month-rollover-check /tmp/out.json && cat /tmp/out.json` — expect `body.disabled: false`, no email sent
- [X] T042 [US3] Functional smoke test — rollover Lambda with API disabled: re-run T040 shutdown, then immediately `aws lambda invoke --function-name bluths-api-month-rollover-check /tmp/out.json` — expect `body.disabled: true`, email arrives within ~1 min. Then restore per `docs/budget-reset.md`.
- [ ] T043 (skipped — CloudWatch alarm wiring verified structurally; not deliberately triggering Lambda errors) [US3] (Optional) Functional smoke test — CloudWatch alarm path: deliberately cause one shutdown-Lambda error (e.g., temporarily revoke its `apigatewayv2:UpdateStage` permission, invoke once, restore the permission), wait ~5 minutes for the alarm to transition to ALARM, verify an email arrives titled `ALARM: "bluths-api-budget-shutdown-errors"...`

**Checkpoint**: Full kill switch live with observability + monthly safety net. All three user stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T044 [P] Verify `/Users/bhart/dev/bluthsapi/docs/budget-reset.md` — confirm all referenced resource names (`bluths-api-budget-alerts`, `bluths-api-monthly-budget`, `bluths-api-budget-shutdown`, output keys `ApiId` and `BudgetShutdownFunctionArn`) still resolve. Optionally add a brief note pointing at `bluths-api-month-rollover-check` as a manual diagnostic.
- [X] T045 [P] Final repo cleanliness check: `grep -rn "setup-budget\|budget-config.json" /Users/bhart/dev/bluthsapi --include="*.md" --include="*.yml" --include="*.yaml" --include="*.sh" --include="*.py"` returns no results outside `specs/010-budget-cloudformation/`
- [X] T046 Run `/Users/bhart/dev/bluthsapi/specs/010-budget-cloudformation/quickstart.md` § 4–7 end-to-end and confirm all assertions pass
- [X] T047 (aws/ removed entirely) [P] Confirm `aws/` directory state: either empty (then remove the directory) or contains only non-budget artifacts
- [X] T048 [P] Python lint on the new module: `cd /Users/bhart/dev/bluthsapi && python3 -m py_compile app/month_rollover_check.py` and (if project linter is configured) `ruff check app/month_rollover_check.py` or equivalent

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks all user stories** because (a) deployer needs new IAM permissions for `budgets`, `sns`, `cloudwatch`, `events`; (b) imperative resources must be deleted before CloudFormation can create same-named ones.
- **User Story 1 (Phase 3)**: Depends on Foundational. MVP — deliverable on its own.
- **User Story 2 (Phase 4)**: Depends on US1 (needs `MonthlyBudget` and `BudgetAlertsTopic`).
- **User Story 3 (Phase 5)**: Depends on US1 (needs `MonthlyBudget`, `BudgetAlertsTopic`, `BudgetShutdownFunction`, `BluthsHttpApi`). Independent of US2.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- US1 must complete before US2 or US3 (both edit `MonthlyBudget.NotificationsWithSubscribers`; both reference `BudgetAlertsTopic`).
- US2 and US3 can be implemented in either order, but each requires its own deploy + verify cycle.

### Within US3

- T024, T025, T027–T033 (the [P] tasks adding new YAML/Python files) can be done in parallel.
- T026 depends on T024 (BudgetActionRole must exist for BudgetShutdownAction's `ExecutionRoleArn`).
- T030 depends on T029 (Function's `Role` field needs the Role to exist).
- T030 depends on T028 (Function's `Handler` references the Python module).
- T031 + T032 depend on T030 (Schedule target + Permission both reference the Function).
- T034 (lint/validate) depends on all template additions being saved.
- T035 (deploy) depends on T034 (validate first).
- T036–T043 (verify + smoke tests) depend on T035 (need the deploy to land first).

### Parallel Opportunities

- **Phase 1**: T002, T003 parallel.
- **Phase 2**: T004 ⟂ T005 (different surfaces — AWS API vs file edit).
- **US1**: T009–T014 (Outputs, workflow, three deletes, README) all touch different files and run in parallel after T007/T008 land.
- **US3 sub-phase 3c**: T028 (new .py file), T029, T030, T031, T032, T033 are all in different YAML resources or files; parallelizable as a group, subject to the in-template reference order above.

---

## Parallel Example: User Story 3 sub-phase 3c (month-rollover)

```bash
# After T024–T027 land, the rollover work can be tackled in parallel:
Task T028: Create app/month_rollover_check.py
Task T029: Add MonthRolloverCheckRole to template.yaml
# Then T030 references T029 + T028:
Task T030: Add MonthRolloverCheckFunction to template.yaml
# Then T031, T032, T033 reference T030:
Task T031: Add MonthRolloverSchedule to template.yaml
Task T032: Add MonthRolloverSchedulePermission to template.yaml
Task T033: Add MonthRolloverCheckFunctionArn output
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup (T001–T003).
2. Phase 2 Foundational (T004–T006). **Critical** — blocks deploy.
3. Phase 3 US1 (T007–T018). Deploy and verify.
4. **STOP and VALIDATE**: Stack manages all infra in IaC. Cost cap at $30 is enforced administratively but no automated alerting/action yet.

### Incremental Delivery

1. Setup + Foundational → ready to deploy.
2. US1 → IaC migration complete (MVP).
3. US2 → $20 warning email live.
4. US3 sub-phase 3a → $30 Lambda kill switch live.
5. US3 sub-phase 3b → silent-failure observability (alarm).
6. US3 sub-phase 3c → monthly safety net.
7. Polish → docs reconciled, repo grep clean.

Each US3 sub-phase can be deployed separately if Brian prefers smaller increments. Recommended order: 3a → 3b → 3c.

### Single-Developer Strategy

Sequential through phases. Each phase ends with a deploy + verify, so the stack is always in a working state.

---

## Notes

- [P] tasks = different files, no in-flight dependencies on other [P] tasks.
- [Story] label maps task to specific user story.
- Each user story produces a deployable, verifiable increment.
- Pre-deploy cleanup (T004) is irreversible from the AWS side; recreating identical resources is the intent of the next deploy.
- After T022 (email confirmation), keep the confirmation link out of git/screenshots.
- US3 contains 20 tasks (the largest phase) because the clarification additions tripled the resource count for this story. Sub-phasing (3a/3b/3c/3d) keeps it manageable.

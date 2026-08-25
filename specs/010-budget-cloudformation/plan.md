# Implementation Plan: AWS Budget & Alerting via CloudFormation

**Branch**: `010-budget-cloudformation` | **Date**: 2026-05-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-budget-cloudformation/spec.md`

## Summary

Replace the imperative `aws/setup-budget.sh` budget setup with native CloudFormation resources in `template.yaml`. The new stack provisions an SNS topic (with the publish policy that was missing and caused the recent AWS warning email), a monthly AWS Budget with two thresholds, an IAM role for Budget Actions, and a Budget Action that invokes the existing `BudgetShutdownFunction` Lambda. Notification thresholds use absolute USD values: $20 (email warning) and $30 (email + Lambda shutdown).

Two reliability/observability additions from clarification session 2026-05-25:

- **CloudWatch Alarm** on the shutdown Lambda's `Errors` metric — publishes to the same SNS topic so a silent kill-switch failure is visible.
- **Month-rollover check Lambda** invoked on the 1st of each month by EventBridge — read-only; emails the operator if the API is still disabled from a prior-month shutdown, pointing at `docs/budget-reset.md`.

## Technical Context

**Language/Version**: YAML (SAM/CloudFormation), Python 3.11 (existing `app/budget_shutdown.py` unchanged; one new ~40-line handler `app/month_rollover_check.py`)
**Primary Dependencies**: AWS SAM (`AWS::Serverless-2016-10-31`); CloudFormation resource types `AWS::SNS::Topic`, `AWS::SNS::TopicPolicy`, `AWS::SNS::Subscription`, `AWS::Budgets::Budget`, `AWS::IAM::Role`, `AWS::CloudWatch::Alarm`, `AWS::Events::Rule`, `AWS::Lambda::Permission` (used for both SNS→Lambda and EventBridge→Lambda invocation grants); Python `boto3` (already available in Lambda runtime) for the rollover check. NOTE: `AWS::Budgets::BudgetsAction` is NOT used — it does not support Lambda targets in CloudFormation (verified against the live schema). The $30→Lambda path is wired via SNS instead.
**Storage**: N/A (infrastructure only)
**Testing**: `sam validate`; manual `aws budgets describe-budget`, `aws sns get-topic-attributes`, `aws cloudwatch describe-alarms`, `aws events list-rules`; simulated breach via AWS Budgets console; manual `aws lambda invoke` for the rollover check
**Target Platform**: AWS us-east-1, account <ACCOUNT_ID>
**Project Type**: Single (infrastructure + one new small Lambda module)
**Performance Goals**: N/A (the rollover Lambda runs ~12 times/year for <100ms each)
**Constraints**: Monthly cost cap of $30 USD; resource names must remain stable to keep `docs/budget-reset.md` accurate; rollover Lambda MUST be read-only (FR-014)
**Scale/Scope**: Single-account, single-region; ~9 new CloudFormation resources added to existing stack; 1 new Python file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution (`.specify/memory/constitution.md`) reviewed against this plan:

- **I. Read-Only Access / II. Public Access / III. RESTful Design / IV. Quote Data Structure / V. Simple Error Handling**: Not affected. Infrastructure-only.
- **API Standards (Required Endpoints)**: Not affected.
- **Documentation**: README must drop the `aws/setup-budget.sh` reference. In scope (FR-010).
- **Code Quality (linting)**: `template.yaml` MUST validate via `python3 -c "import yaml; yaml.safe_load(open('template.yaml'))"` and `sam validate`. The new `app/month_rollover_check.py` MUST pass the project's Python linter.
- **Deployment Standards (Lambda, rate limiting, observability)**: Reinforced. The kill switch operates by throttling API Gateway, matching the "Global throttling only" principle. Constitution says "No custom CloudWatch metrics, dashboards, or X-Ray tracing (cost optimization)" — we are adding **one** CloudWatch Alarm (on a built-in AWS-provided metric `AWS/Lambda Errors`, no custom metric publishing). At $0.10/alarm/month this is well inside the constitution's $0.50-2/month log-cost envelope.

**Result**: No violations. No complexity-tracking entries needed. The single CloudWatch Alarm is consistent with the constitution's intent (no *custom* metrics; alarms on AWS-provided metrics are not prohibited).

## Project Structure

### Documentation (this feature)

```text
specs/010-budget-cloudformation/
├── plan.md              # This file (/speckit.plan output)
├── spec.md              # Feature specification (includes 2026-05-25 clarifications)
├── research.md          # Phase 0 output — refreshed with alarm + rollover decisions
├── data-model.md        # Phase 1 output — 9-resource inventory
├── quickstart.md        # Phase 1 output — deploy + verify runbook
└── contracts/
    └── budget-resources.yaml  # CloudFormation snippet (advisory)
```

### Source Code (repository root)

```text
# Files modified
template.yaml                        # Add SNS topic + policy + subscription, budget, budget action role, budget action,
                                     # CloudWatch alarm, rollover Lambda + role, EventBridge rule + invoke permission
iam-policy.json                      # Add budgets:*, sns:*, cloudwatch:* (alarms), events:* statements
.github/workflows/deploy.yml         # Deploy root template.yaml directly; remove specs/005 spec-template copy step
README.md                            # Remove aws/setup-budget.sh references
docs/budget-reset.md                 # Verify resource names still resolve

# Files created
app/month_rollover_check.py          # ~40-line handler: read prod stage throttle, publish to SNS if 0

# Files deleted
aws/setup-budget.sh
aws/budget-config.json
specs/005-aws-lambda-deployment/contracts/sam-template.yaml   # Retired — root template canonical
```

**Structure Decision**: Root `template.yaml` is the single source of truth for the SAM stack. `.github/workflows/deploy.yml` is updated to deploy it directly. The drifted duplicate at `specs/005-aws-lambda-deployment/contracts/sam-template.yaml` is removed. The new Python module `app/month_rollover_check.py` sits alongside the existing `app/budget_shutdown.py`, mirroring its structure.

## Complexity Tracking

> *No violations to justify.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (none)    |            |                                      |

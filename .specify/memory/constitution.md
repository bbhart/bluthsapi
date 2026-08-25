# Bluths API Constitution

## Core Principles

### I. Read-Only Access
All endpoints must be GET requests only. No POST, PUT, PATCH, or DELETE operations. API serves data retrieval exclusively.

### II. Public Access
No authentication required. All quote data is publicly accessible without API keys or tokens.

### III. RESTful Design
Resource-based URLs following REST conventions. Proper HTTP status codes. Consistent JSON response structure.

### IV. Quote Data Structure
Every quote includes: quote text. Optional fields: primary speaker, one or more speakers, context, image url.

### V. Simple Error Handling
Use standard HTTP status codes: 200 (success), 404 (not found), 500 (server error). Return descriptive error messages in JSON format.

## API Standards

Do not allow for fetching of all quotes. There should be only one quote per request.

### Required Endpoints
- GET /quotes/random - Get random quote
- GET /quotes/<primary speaker> - Get random quote filtered by the primary speaker
- GET /quotes/meme - Get random quote where there's an image url 

### Response Format
Success: `{ "data": { ... } }` with status 200
Error: `{ "error": "message" }` with appropriate status code

## Documentation

Basic README with endpoint list and example responses required.

## Development Environment Standards
- Development primarily happens on MacOS
- On MacOS python is called using the `python3` command
- Cross-platform compatibility required (MacOS and Windows)
- Avoid symlinks - use file copies or configuration references instead (symlinks break on Windows)

### Code Quality Standards (Mandatory)

**Linting is REQUIRED** - All code must pass linting checks before commit or deployment.

- **Python files** MUST be validated with a Python linter (flake8, pylint, or ruff recommended)
- **YAML files** MUST be validated with YAML parser (`python3 -c "import yaml; yaml.safe_load(...)"` minimum)
- **GitHub Actions workflows** MUST be validated for YAML syntax before committing
- Linting checks MUST be run:
  - Before committing code (developer responsibility)
  - In CI/CD pipeline (automated validation)
  - When reviewing configuration changes
- Fix all linting errors before proceeding - no bypassing for convenience

## Deployment Standards

### AWS Lambda Deployment
- Deploy using AWS Lambda with API Gateway as entry point
- Bundle static data (quotes.json) with deployment package
- Use GitHub Actions for CI/CD (.github/workflows/deploy.yml)
- Automated deployment triggered by commits to main branch
- Lambda versioning with "prod" alias for instant rollback capability
- Deployment validation via /health endpoint (must return HTTP 200)
- Automatic rollback to previous version if validation fails
- AWS credentials stored in GitHub Secrets (remote) or .env file (local development)
- Use Mangum adapter for FastAPI-to-Lambda compatibility

### Rate Limiting
- Global throttling only via API Gateway (50 requests/second in production; see `GlobalRateLimit` in samconfig.toml)
- No per-IP rate limiting (avoids infrastructure complexity and cost)
- Return HTTP 429 with Retry-After header when limits exceeded
- Rate limits must be configurable via API Gateway settings

### Observability
- CloudWatch Logs with structured JSON logging (errors, warnings, deployment events)
- No custom CloudWatch metrics, dashboards, or X-Ray tracing (cost optimization)
- Log cost target: $0.50-2/month at expected traffic volumes

### Health Checks
- Health check endpoint: GET /health (required for all deployment methods)
- Returns HTTP 200 on success
- Used for deployment validation in Lambda

### Package Management
- Use uv for Python dependency management (10-100x faster than pip)
- Lock dependencies for reproducible builds (uv.lock)
- Separate production (requirements.txt) and development (requirements-dev.txt) dependencies

## Governance

This constitution defines minimal viable quote API.
All endpoints must remain read-only and publicly accessible.
Serving costs should be minimized. This is not expected to be a high use API.

### Speckit Workflow Standards (Mandatory)

**Branch and Commit Management** - The following practices are REQUIRED for all speckit workflows to ensure proper review and quality control.

**Commits in Feature Branches**:
- `/speckit.implement` and automated workflows MUST NOT create commits in feature branches
- All commits must be reviewed and created manually by the developer
- Rationale: Commits are critical review points that require human oversight
- Exception: Planning documents (spec.md, plan.md, research.md, tasks.md) may be tracked separately but should not be auto-committed during implementation

**Branch Merging**:
- `/speckit.implement` and automated workflows MUST NOT merge feature branches into main
- All merges to main must be done manually by the developer (direct merge or pull request)
- Rationale: Merging to main is a critical decision point that requires human review
- The developer is responsible for:
  - Reviewing all changes in the feature branch
  - Testing the implementation
  - Deciding when and how to merge (direct merge, squash merge, PR with review, etc.)

**Implementation Workflow**:
- Speckit commands may modify files to implement features
- Speckit commands may stage files (`git add`) to show what changed
- Speckit commands MUST stop before committing or merging
- Final output should indicate: "Changes staged and ready for your review. Run `git status` to see changes, then commit and merge when ready."

**Rationale**:
- Commits create permanent history and should reflect intentional checkpoints
- Merges to main affect production and require careful consideration
- Developer maintains full control over version control operations
- Allows developer to review, test, and adjust before finalizing changes

### Security Principles (Non-Negotiable)

**Least Privilege is MANDATORY** - Under no circumstances should permissions be granted beyond what is strictly required, even for MVPs, prototypes, or testing. Security fundamentals are never compromised for convenience.

- IAM policies MUST scope permissions to specific resources (e.g., `bluths-api-*`)
- IAM policies MUST grant only required actions (no wildcards like `*` or `lambda:*` unless absolutely necessary)
- Never use `*FullAccess` managed policies (e.g., `IAMFullAccess`, `AWSLambda_FullAccess`)
- All AWS resource access follows Least Privilege from day one

### AWS IAM Policy Requirements for SAM Deployment

**Context**: This policy enables GitHub Actions (or local users) to deploy the Bluths API using AWS SAM. It was developed through iterative debugging of permission errors during actual deployments.

**Policy Location**: `iam-policy.json` (project root)

**Attach To**:
- IAM user: `github-actions-deployer` (for CI/CD)
- Local IAM users who need to deploy manually

#### Core Principles

1. **Resource Scoping**: All permissions scoped to `bluths-api-*` resources where possible
2. **Separate Read/Write Permissions**: Mutating operations (create/delete) use resource-scoped ARNs, read operations (describe/list) use `Resource: "*"` when required by AWS API
3. **CloudFormation-Aware**: Includes describe permissions for stack introspection and GetAtt operations
4. **No Wildcards on Actions**: Use explicit action lists, not `service:*`, except for Lambda/API Gateway where SAM requires comprehensive access

#### Required Permission Categories

**1. CloudFormation (Stack Management)**
- Full stack operations on `bluths-api*` stacks
- Change set management
- Serverless transform access
- **Critical Read Permissions**: `DescribeStacks`, `DescribeStackEvents`, `DescribeChangeSet`, `ListStacks` (required for SAM CLI and change set review)

**2. S3 (Artifact Storage)**
- SAM managed buckets: `aws-sam-cli-managed-default-*`
- Custom deployment bucket: `bbh-applications`
- Required actions: create, get, put, delete, list, versioning, policy management

**3. Lambda (Function Deployment)**
- Full access to `bluths-api-*` functions and layers
- Includes versioning, aliases, concurrency, and tagging
- Rationale: SAM requires comprehensive Lambda permissions for AutoPublishAlias and ReservedConcurrentExecutions

**4. API Gateway (HTTP API)**
- Full access to `/apis` and `/restapis` resources
- Tag management
- Rationale: SAM manages API lifecycle including CORS, throttling, and access logging

**5. IAM (Execution Roles)**
- Role operations: `bluths-api-*` roles only
- Policy operations: `bluths-api-*` policies only
- **Critical**: `iam:PassRole` required for CloudFormation to assign roles to Lambda
- **Read-only global**: `iam:ListPolicies` on `Resource: "*"` (AWS API requirement)

**6. CloudWatch Logs (Application Logging)**
- **Resource-scoped**: Create/delete log groups for `/aws/lambda/bluths-api-*` and `/aws/apigateway/bluths-api-*`
- **Global (required)**: `logs:DescribeLogGroups`, `logs:CreateLogDelivery`, `logs:GetLogDelivery`, `logs:UpdateLogDelivery`, `logs:DeleteLogDelivery`, `logs:ListLogDeliveries`
- Rationale:
  - `DescribeLogGroups` required for `!GetAtt LogGroup.Arn` in CloudFormation
  - Log Delivery permissions required for API Gateway access logging feature

#### Lessons Learned (Avoid These Errors)

**Error 1: "Access denied for operation 'logs:DescribeLogGroups'"**
- **Cause**: CloudFormation uses `!GetAtt ApiAccessLogGroup.Arn` which requires describe permission
- **Fix**: Add `logs:DescribeLogGroups` with `Resource: "*"` (cannot be resource-scoped)

**Error 2: "Not authorized to perform logs:CreateLogDelivery"**
- **Cause**: API Gateway access logging creates a log delivery resource, not just a log group
- **Fix**: Add all `logs:*LogDelivery` actions with `Resource: "*"`

**Error 3: "Unable to import module 'app.main': No module named 'app'"**
- **Cause**: Dependencies built for local OS (macOS ARM64) instead of Lambda runtime (Linux x86_64)
- **Fix**: Use `sam build --use-container` or add `use_container = true` to `samconfig.toml`
- **Not an IAM issue** - but critical for deployment success

**Error 4: Template not found in GitHub Actions**
- **Cause**: Workflow copies template to `deploy/sam/` but CodeUri paths become incorrect
- **Fix**: Use `sed` to adjust `CodeUri: ../../../` → `CodeUri: ../../` when copying template

#### SAM Build Configuration

**Local Development** (`samconfig.toml`):
```toml
[default.build.parameters]
use_container = true
```

**GitHub Actions** (`.github/workflows/deploy.yml`):
```bash
sam build --use-container
```

**Rationale**: Ensures dependencies (especially native extensions like `pydantic_core`) are compiled for Lambda's Linux runtime, not the build machine's OS.

#### Policy Maintenance

- Review policy when adding new AWS services to SAM template (DynamoDB, SQS, etc.)
- Keep permissions scoped to `bluths-api-*` resources
- Document any new `Resource: "*"` permissions with AWS API justification
- Test policy changes in dev/staging before production

#### Policy Version History

- **v1.0** (Initial): Basic CloudFormation, Lambda, API Gateway, S3
- **v1.1** (+DescribeLogGroups): Fixed GetAtt errors
- **v1.2** (+LogDelivery): Fixed API Gateway access logging
- **v1.3** (+CloudFormation Describe): Fixed change set review and stack introspection
- **v1.4** (-ECR): Removed unnecessary container registry permissions

**Version**: 1.6.0 | **Ratified**: 2025-10-24 | **Last Amended**: 2025-11-05

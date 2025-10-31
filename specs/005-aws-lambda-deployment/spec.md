# Feature Specification: AWS Lambda Deployment with CI/CD and Rate Limiting

**Feature Branch**: `005-aws-lambda-deployment`
**Created**: 2025-10-28
**Status**: Draft
**Input**: User description: "Deploy to AWS Lambda. The quotes.json file will not change often so it should be packaged with the code. Package should be updated whenever a new commit to main is pushed to this project's github repository. Queries should be limited to 1 query per second per IP address and the overall service should be limited to 10 total queries per second. Provide documentation on how to change the allowed per-IP and total QPS values later. Locally the AWS access key and secret key will be stored in the .env file and remotely should be stored in the appropriate secrets manager."

## Clarifications

### Session 2025-10-31

- Q: Rate Limiting Implementation Strategy - The spec requires per-IP (1 QPS) and global (10 QPS) rate limiting, but AWS Lambda is stateless. What implementation approach should be used? → A: Use API Gateway throttling alone (no per-IP tracking, only global limits) - simplest approach
- Q: Deployment Rollback Strategy - When a deployment fails validation (FR-018), the system must roll back to the previous version. What rollback mechanism should be used? → A: Use Lambda versioning with aliases (prod points to stable version) - AWS native, instant rollback, zero additional cost
- Q: Deployment Validation Criteria - FR-017 and FR-018 require deployment status reporting and rollback on validation failure, but the specific validation checks are not defined. What criteria determine if a deployment succeeds or needs rollback? → A: Health check responds 200
- Q: Observability and Monitoring Scope - The spec mentions "basic CloudWatch logs" but doesn't specify the level of observability needed. What CloudWatch observability should be implemented? → A: CloudWatch Logs with structured JSON logging (errors, warnings, deployment events) - basic debugging, ~$0.50-2/month
- Q: GitHub Actions Workflow Storage - The spec requires GitHub Actions for CI/CD but doesn't specify where the workflow configuration should live. Where should the workflow file be stored? → A: .github/workflows/deploy.yml

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Deployment on Git Push (Priority: P1)

Developers push code changes to the main branch on GitHub, and the application automatically deploys to AWS Lambda without manual intervention. The deployment includes the bundled quotes.json file and updates the live service.

**Why this priority**: This is the core deployment automation requirement. Without it, the application cannot be deployed to production, making it the foundational capability.

**Independent Test**: Can be fully tested by pushing a commit to main branch and verifying the Lambda function updates within 5 minutes, delivering automated deployment.

**Acceptance Scenarios**:

1. **Given** a commit is pushed to the main branch, **When** the CI/CD pipeline executes, **Then** the Lambda function is updated with the new code and bundled quotes.json within 5 minutes
2. **Given** the deployment completes successfully and the /health check returns 200, **When** users access the API, **Then** they receive responses from the newly deployed version via the updated prod alias
3. **Given** the deployment fails or /health check does not return 200, **When** checking the CI/CD logs, **Then** the failure reason is clearly documented and the prod alias still points to the previous stable version

---

### User Story 2 - Global QPS Limit Protection (Priority: P1)

The API enforces a maximum of 10 total queries per second across all users to control AWS Lambda costs and ensure predictable service capacity using API Gateway's built-in throttling.

**Why this priority**: Rate limiting is a critical cost control measure. Global throttling prevents unexpected charges from traffic spikes or DDoS attacks without requiring additional infrastructure for per-IP tracking.

**Independent Test**: Can be fully tested by generating 15 requests per second from any source and verifying only 10 succeed while 5 are rejected with 429 status, delivering cost protection.

**Acceptance Scenarios**:

1. **Given** the service is receiving 10 requests per second, **When** an 11th request arrives in the same second, **Then** it is rejected with HTTP 429 (Too Many Requests)
2. **Given** the rate limit is reached, **When** the next second begins, **Then** the counter resets and requests are accepted again
3. **Given** traffic is below 10 QPS, **When** any valid request arrives, **Then** it is processed normally

---

### User Story 3 - Local Development with AWS Credentials (Priority: P2)

Developers can run deployment scripts locally using AWS credentials stored in a .env file, enabling testing and manual deployments without committing sensitive credentials to version control.

**Why this priority**: Essential for development workflow but not required for end-user functionality. Can be implemented after basic deployment works.

**Independent Test**: Can be fully tested by creating a .env file with AWS credentials, running the deployment script locally, and verifying successful Lambda deployment, delivering local development capability.

**Acceptance Scenarios**:

1. **Given** a developer has AWS credentials, **When** they create a .env file with AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, **Then** they can run deployment commands successfully
2. **Given** the .env file is present, **When** the developer commits to Git, **Then** the .env file is ignored and not committed (via .gitignore)
3. **Given** credentials are missing or invalid, **When** attempting deployment, **Then** a clear error message explains the credential issue

---

### User Story 4 - Secure Remote Credential Storage (Priority: P2)

AWS credentials used by the CI/CD pipeline are stored in GitHub Secrets (or equivalent secrets manager), ensuring sensitive credentials are never exposed in code or logs.

**Why this priority**: Security best practice and explicitly required, but depends on P1 deployment working first.

**Independent Test**: Can be fully tested by verifying credentials are stored in GitHub Secrets, reviewing deployment logs to confirm no credentials are visible, and confirming successful automated deployments, delivering secure credential management.

**Acceptance Scenarios**:

1. **Given** AWS credentials are stored in GitHub Secrets, **When** the CI/CD pipeline runs, **Then** it successfully authenticates with AWS without exposing credentials in logs
2. **Given** a developer views the CI/CD logs, **When** they search for credential values, **Then** no AWS keys or secrets are visible in plain text
3. **Given** credentials are updated in GitHub Secrets, **When** the next deployment runs, **Then** it uses the updated credentials automatically

---

### User Story 5 - Configurable Rate Limit Documentation (Priority: P3)

Operations team members can adjust the global rate limit (currently 10 QPS) by following clear documentation without requiring code changes or deep technical knowledge.

**Why this priority**: Nice to have for operational flexibility but not essential for initial launch. Can be added after core functionality is stable.

**Independent Test**: Can be fully tested by following the documentation to change rate limits, deploying the change, and verifying the new limits are enforced, delivering operational flexibility.

**Acceptance Scenarios**:

1. **Given** the documentation is followed, **When** an operator changes the global limit to 20 QPS and deploys, **Then** the service accepts 20 requests per second before throttling
2. **Given** configuration changes are made, **When** reviewing the documentation, **Then** it clearly explains which API Gateway settings to modify and what values are acceptable
3. **Given** invalid rate limit values are configured, **When** deployment is attempted, **Then** validation fails with a helpful error message before deployment proceeds

---

### Edge Cases

- What happens when the quotes.json file exceeds AWS Lambda's deployment package size limit (250MB uncompressed)?
- How does the system handle partial deployments where the Lambda code updates but API Gateway configuration fails?
- What happens when GitHub Actions experiences an outage during a critical deployment?
- How does the system handle Lambda cold starts affecting response times near the rate limit threshold?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deploy the FastAPI application to AWS Lambda with Mangum adapter
- **FR-002**: System MUST bundle quotes.json file with the Lambda deployment package
- **FR-003**: System MUST trigger automatic deployment when commits are pushed to the main branch on GitHub
- **FR-004**: System MUST enforce a global rate limit of 10 requests per second across all traffic using API Gateway throttling
- **FR-005**: System MUST return HTTP 429 (Too Many Requests) when rate limits are exceeded
- **FR-006**: System MUST include appropriate Retry-After headers in 429 responses
- **FR-007**: System MUST use AWS API Gateway as the entry point for Lambda functions
- **FR-008**: System MUST load AWS credentials from .env file for local deployments
- **FR-009**: System MUST load AWS credentials from GitHub Secrets for CI/CD deployments
- **FR-010**: System MUST prevent AWS credentials from appearing in logs or error messages
- **FR-011**: System MUST provide documentation on how to modify global QPS limits in API Gateway
- **FR-012**: System MUST validate deployment package size before attempting deployment
- **FR-013**: System MUST maintain all existing API endpoints (/health, /api/quotes/random, /api/quotes/meme, /api/quotes/{speaker})
- **FR-014**: System MUST preserve the existing CORS configuration allowing all origins
- **FR-015**: System MUST maintain existing cache control headers (public, max-age=3600)
- **FR-016**: System MUST serve static files from the /public directory at the root path
- **FR-017**: System MUST report deployment status (success/failure) in CI/CD logs
- **FR-018**: System MUST automatically roll back to previous Lambda version using aliases if deployment validation fails (validation = /health endpoint returns HTTP 200)
- **FR-019**: System MUST emit structured JSON logs to CloudWatch Logs for errors, warnings, and deployment events

### Non-Functional Requirements

- **NFR-001**: Lambda cold start time MUST NOT exceed 3 seconds
- **NFR-002**: API response time MUST remain under 500ms for warm Lambda instances
- **NFR-003**: Deployment process MUST complete within 10 minutes
- **NFR-004**: Rate limiting overhead MUST NOT add more than 50ms to request latency
- **NFR-005**: Documentation MUST be maintainable by non-developers

### Key Entities

- **Deployment Package**: Contains the FastAPI application code, dependencies, quotes.json data file, and static assets bundled together for Lambda execution
- **Lambda Version**: Immutable snapshot of Lambda function code and configuration, identified by version number (e.g., $1, $2, $3)
- **Lambda Alias**: Named pointer (e.g., "prod") that references a specific Lambda version, allowing instant traffic switching for rollbacks
- **Rate Limit Rule**: Defines a threshold (requests per time window), scope (global), and action (reject with 429) for controlling traffic via API Gateway
- **AWS Credential**: Includes Access Key ID and Secret Access Key, stored in .env locally or GitHub Secrets remotely, used for AWS authentication
- **CI/CD Pipeline**: GitHub Actions workflow defined in .github/workflows/deploy.yml that is triggered by commits to main, builds, tests, packages, deploys the Lambda function, and validates before updating the prod alias
- **API Gateway Configuration**: Includes route mappings, CORS rules, and rate limiting policies that front the Lambda function via the prod alias

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can push a commit to main and see the live API updated within 10 minutes without manual intervention
- **SC-002**: The service handles up to 10 requests per second across all sources while rejecting excess traffic with 429 responses
- **SC-003**: Operations team members can modify rate limits by following documentation and complete the change within 30 minutes
- **SC-004**: Local deployments work by following a 5-step setup process documented in README
- **SC-005**: Zero AWS credentials are visible in GitHub repository history, CI/CD logs, or error messages
- **SC-006**: The deployed API maintains 99.9% of current response times compared to the pre-Lambda version
- **SC-007**: All existing API endpoints return the same response formats and status codes as before deployment

## Assumptions

- The current quotes.json file is under 50MB and will remain under 100MB for the foreseeable future
- GitHub Actions is the CI/CD platform (not Jenkins, GitLab CI, etc.)
- AWS is the target cloud provider (not Azure, GCP)
- The development team has AWS account admin access to create Lambda functions, API Gateway, and IAM roles
- The GitHub repository is the source of truth for production code
- Rate limiting will use API Gateway's built-in throttling for global limits only (no per-IP tracking)
- Static files in /public directory are small enough to bundle with Lambda (<10MB)
- Lambda execution time will remain under 30 seconds (Lambda's maximum timeout)
- The application will use a single AWS region (not multi-region)
- Standard AWS Lambda pricing applies (~$0.20 per 1M requests after free tier)

## Dependencies

- AWS account with permissions to create Lambda functions, API Gateway, IAM roles, CloudWatch Logs, and Lambda versioning/aliases
- GitHub repository with Actions enabled
- Existing FastAPI application must remain compatible with ASGI (for Mangum adapter)
- quotes.json file must be valid JSON and accessible at build time
- .env file format compatible with Python-dotenv or similar library
- API Gateway must support global throttling rules

## Post-Deployment Manual Steps

### SSL Certificate and Custom Domain Configuration (Manual)

After the initial automated deployment completes, configure SSL certificate and custom domain for `bqaas.lucille2.com`:

**Step 1: Request ACM Certificate** (before DNS configuration)

1. Request certificate in AWS Certificate Manager:
   - Domain name: `bqaas.lucille2.com`
   - Validation method: DNS validation
   - **CRITICAL**: Certificate MUST list `bqaas.lucille2.com` as an allowed name

2. Complete DNS validation:
   - ACM provides a CNAME record for validation
   - Add this validation CNAME to your DNS provider
   - Wait for ACM to validate (typically 5-30 minutes)
   - Certificate status changes to "Issued"

**Step 2: Configure API Gateway Custom Domain**

1. Create API Gateway Custom Domain Name resource (via AWS Console or SAM template update)
2. Point custom domain to the certificate ARN from Step 1
3. API Gateway generates a CloudFront distribution domain (e.g., `d123.cloudfront.net`)

**Step 3: Update DNS**

Create CNAME record in DNS provider:
- Name: `bqaas.lucille2.com`
- Type: `CNAME`
- Value: `<cloudfront-domain-from-step-2>` (e.g., `d123.cloudfront.net`)
- TTL: `300` (5 minutes)

**Step 4: Configure API Mapping**

In API Gateway Custom Domain settings, map:
- Path: `/` (root)
- Target: API Gateway HTTP API (prod stage)

**Result**: API accessible via `https://bqaas.lucille2.com` with valid SSL certificate (no browser warnings)

## Out of Scope

- Multi-region deployment or global load balancing
- Database migration or persistent storage beyond bundled JSON
- CloudWatch dashboards, alarms, or alerting (only structured logs for debugging)
- Custom CloudWatch metrics or X-Ray distributed tracing
- A/B testing or canary deployments
- Authentication or authorization for API endpoints (remains public)
- Media file hosting changes (remains on S3 as currently configured)
- WebSocket support or real-time features
- GraphQL endpoint or alternative API formats
- Per-IP rate limiting or per-endpoint rate limit customization (global throttling only)
- Geolocation-based routing or restrictions

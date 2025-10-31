# Implementation Plan: AWS Lambda Deployment with CI/CD and Rate Limiting

**Branch**: `005-aws-lambda-deployment` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-aws-lambda-deployment/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Deploy the Bluths API (Arrested Development Quotes API) to AWS Lambda with automated CI/CD via GitHub Actions. The deployment will bundle the quotes.json file (~177KB) with the application code and enforce dual rate limiting: 1 request per second per IP address and 10 requests per second globally. AWS credentials will be managed via .env files locally and GitHub Secrets in CI/CD. After initial deployment, a custom domain (bqaas.lucille2.com) will be manually configured via CNAME record pointing to the API Gateway endpoint. The technical approach uses AWS SAM (Serverless Application Model) for infrastructure-as-code, Mangum adapter to bridge FastAPI to Lambda's event model, and API Gateway's native throttling capabilities for rate limiting.

## Technical Context

**Language/Version**: Python 3.11+ (matches existing project - see requirements.txt)
**Primary Dependencies**: FastAPI 0.104.0, Mangum (ASGI-to-Lambda adapter), AWS SAM CLI, python-dotenv (for .env support)
**Storage**: File-based (quotes.json bundled in Lambda package, media files on S3 as currently configured)
**Testing**: pytest (for existing tests), AWS SAM local testing for Lambda functions
**Target Platform**: AWS Lambda (Python 3.11 runtime), AWS API Gateway (HTTP API), single region deployment
**Project Type**: Single project (web API backend only, existing structure in app/ directory)
**Performance Goals**: <500ms API response time (warm Lambda), <3s cold start, 10 QPS throughput
**Constraints**: <10 minute deployment time, <250MB Lambda package (uncompressed), <50ms rate limiting overhead, maintain 99.9% of current response times
**Scale/Scope**: Low-medium traffic API (~177KB data file, 4 endpoints, public read-only access)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Read-Only Access (Article I)
- **Status**: PASS - No changes to API design, all endpoints remain GET-only
- **Evidence**: spec.md FR-015 maintains all existing endpoints unchanged

### ✅ Public Access (Article II)
- **Status**: PASS - No authentication added, API remains publicly accessible
- **Evidence**: Rate limiting uses IP-based throttling, not authentication

### ✅ RESTful Design (Article III)
- **Status**: PASS - Existing REST endpoints preserved, HTTP status codes maintained
- **Evidence**: spec.md FR-015, FR-016, FR-017 preserve current API behavior

### ✅ Quote Data Structure (Article IV)
- **Status**: PASS - No changes to quote schema, quotes.json bundled as-is
- **Evidence**: spec.md FR-002 bundles existing quotes.json without modification

### ✅ Simple Error Handling (Article V)
- **Status**: PASS with ADDITION - Adds HTTP 429 for rate limiting (standard practice)
- **Evidence**: spec.md FR-006, FR-007 add rate limit errors using standard HTTP codes

### ✅ Required Endpoints
- **Status**: PASS - All required endpoints maintained (/quotes/random, /quotes/<speaker>, /quotes/meme)
- **Evidence**: spec.md FR-015 explicitly maintains all existing endpoints
- **Note**: Current implementation uses `/api/quotes/*` paths which satisfy the requirement

### ✅ Response Format
- **Status**: PASS - Existing response format preserved
- **Evidence**: spec.md SC-008 requires "same response formats and status codes"

### ✅ Cost Minimization (Governance)
- **Status**: PASS - Lambda + rate limiting explicitly controls costs
- **Evidence**: spec.md FR-005 caps at 10 QPS, AWS Lambda pricing ~$0.20 per 1M requests

### Post-Design Re-check Required
After Phase 1 design, verify:
- [ ] SAM template doesn't introduce authentication
- [ ] API Gateway throttling implementation preserves RESTful responses
- [ ] Lambda cold start doesn't break health check timing requirements

## Project Structure

### Documentation (this feature)

```text
specs/005-aws-lambda-deployment/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── sam-template.yaml    # AWS SAM infrastructure definition
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Existing structure (preserved)
app/
├── __init__.py
├── main.py              # FastAPI application (add Mangum handler)
├── models.py
├── services.py
├── config.py
└── data/
    └── quotes.json      # 177KB - bundled with Lambda

# New deployment infrastructure
.github/
└── workflows/
    └── deploy-lambda.yml    # GitHub Actions CI/CD workflow

deploy/
├── sam/
│   ├── template.yaml        # AWS SAM infrastructure-as-code
│   ├── samconfig.toml       # SAM CLI configuration
│   └── requirements.txt     # Lambda dependencies (copied from root)
├── scripts/
│   ├── package-lambda.sh    # Build and package Lambda function
│   ├── validate-size.sh     # Check package size before deploy
│   └── local-deploy.sh      # Local deployment script using .env
└── docs/
    └── RATE_LIMITS.md       # Documentation for changing rate limits

# Configuration
.env.example             # Template for local AWS credentials
.gitignore               # Updated to exclude .env

# Existing test structure (preserved)
tests/
├── test_main.py
└── test_services.py

# Existing requirements (preserved)
requirements.txt
requirements-dev.txt
```

**Structure Decision**: Single project deployment infrastructure added to existing FastAPI application. The `deploy/` directory contains all AWS-specific configuration isolated from application code. This follows the principle of separation of concerns: `app/` remains deployment-agnostic, `deploy/` handles AWS Lambda specifics. GitHub Actions workflow coordinates the build and deployment process.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All constitution requirements remain satisfied. The addition of HTTP 429 status codes for rate limiting is a standard REST practice and aligns with Simple Error Handling (Article V).

## Phase 0: Research & Decision Log

### Research Tasks

1. **AWS SAM vs Serverless Framework vs Manual Lambda**
   - Decision needed: Which deployment tool to use
   - Rationale: SAM is AWS-native, Serverless has broader ecosystem, Manual gives most control
   - Research: Compare setup complexity, maintainability, rate limiting support

2. **API Gateway Throttling Implementation**
   - Decision needed: How to implement per-IP rate limiting (1 QPS)
   - Research: API Gateway usage plans, Lambda@Edge, custom middleware
   - Challenge: API Gateway throttling is account-level or per-route, not per-IP by default

3. **Mangum Configuration for FastAPI**
   - Decision needed: Optimal Mangum settings for FastAPI + static files
   - Research: Handler configuration, event format (v1 vs v2), static asset handling
   - Challenge: spec.md FR-018 requires serving /public static files

4. **GitHub Actions AWS Authentication**
   - Decision needed: Long-lived keys vs OIDC provider
   - Research: Security best practices, GitHub Actions AWS authentication methods
   - Consideration: spec.md FR-010 requires GitHub Secrets (suggests long-lived keys)

5. **Lambda Cold Start Optimization**
   - Decision needed: Strategies to meet <3s cold start requirement
   - Research: Provisioned concurrency, SnapStart, dependency optimization
   - Challenge: spec.md NFR-001 requires cold start <3s

6. **Deployment Rollback Strategy**
   - Decision needed: How to implement FR-020 rollback on failure
   - Research: Lambda versions, aliases, SAM deployment options
   - Requirement: spec.md FR-020 requires automatic rollback

## Phase 1: Design Artifacts

### Data Model (data-model.md)

**Entities to document**:
- Deployment Package structure (code + dependencies + quotes.json + static files)
- AWS Credential management (local .env vs GitHub Secrets)
- Rate Limit Configuration (per-IP and global thresholds)
- CI/CD Pipeline stages (build, validate, package, deploy, verify)

### API Contracts (contracts/)

**Files to generate**:
- `sam-template.yaml`: Complete AWS SAM infrastructure definition
  - Lambda function configuration (Python 3.11 runtime, memory, timeout)
  - API Gateway HTTP API configuration
  - Throttling settings (10 QPS burst/rate limits)
  - IAM roles and policies
  - Environment variables
  - Deployment configuration

- `github-actions.yml`: CI/CD workflow schema
  - Trigger conditions (push to main)
  - Build steps (install dependencies, bundle quotes.json)
  - Package validation (size check)
  - SAM deploy step
  - Post-deployment verification
  - Rollback on failure

- `env-template`: Local development environment variables
  - AWS_ACCESS_KEY_ID (placeholder)
  - AWS_SECRET_ACCESS_KEY (placeholder)
  - AWS_REGION (default)
  - AWS_ACCOUNT_ID (placeholder)

### Quickstart Guide (quickstart.md)

**Sections to include**:
1. Prerequisites (AWS account, AWS CLI, SAM CLI, Python 3.11+)
2. Local deployment setup
   - Clone repository
   - Create .env file from template
   - Install dependencies
   - Run local deployment script
3. CI/CD setup
   - Configure GitHub Secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
   - Push to main to trigger deployment
   - Verify deployment in AWS console
4. Changing rate limits (link to RATE_LIMITS.md)
5. Troubleshooting common issues

## Phase 2: Task Generation

*Created by `/speckit.tasks` command (not this command)*

Expected task categories:
1. **Infrastructure Setup** (P1)
   - Create SAM template with Lambda function definition
   - Configure API Gateway with throttling
   - Set up IAM roles and policies

2. **Application Changes** (P1)
   - Add Mangum handler to app/main.py
   - Add mangum to requirements.txt
   - Update .gitignore for .env

3. **CI/CD Pipeline** (P1)
   - Create GitHub Actions workflow
   - Configure GitHub Secrets documentation
   - Implement deployment validation

4. **Local Development** (P2)
   - Create .env.example template
   - Write local deployment script
   - Add python-dotenv support

5. **Documentation** (P3)
   - Write RATE_LIMITS.md guide
   - Update main README with deployment section
   - Create troubleshooting guide
   - Document custom domain setup (bqaas.lucille2.com CNAME configuration)

6. **Testing & Verification** (P1)
   - Test rate limiting enforcement
   - Verify cold start times
   - Validate response time requirements

7. **Post-Deployment Manual Steps** (P3 - Manual)
   - Document: Request ACM certificate for bqaas.lucille2.com (MUST list domain in SAN)
   - Document: Complete DNS validation for ACM certificate
   - Document: Create API Gateway Custom Domain Name resource with ACM certificate
   - Document: Create API mapping (path: `/`, stage: `prod`)
   - Document: Create CNAME record pointing to CloudFront domain (not API Gateway URL)
   - Document: Verify SSL certificate shows bqaas.lucille2.com (no browser warnings)

## Known Challenges & Mitigation

### Challenge 1: Per-IP Rate Limiting in API Gateway

**Problem**: API Gateway's native throttling is per-account or per-route, not per-IP by default.

**Options**:
1. Use Lambda@Edge or CloudFront Functions to inspect IP and reject requests
2. Implement rate limiting middleware in FastAPI (stateless, may not work across Lambda instances)
3. Use DynamoDB to track IP request counts (adds latency and cost)
4. Use AWS WAF rate-based rules (simplest, but costs ~$1/month for the rule)

**Research needed**: Compare latency overhead (<50ms requirement) and cost for each option.

### Challenge 2: Static File Serving from Lambda

**Problem**: Lambda is designed for dynamic responses, not static file serving. spec.md FR-018 requires serving /public directory.

**Options**:
1. Bundle static files in Lambda package (increases size, inefficient)
2. Serve static files from S3 + CloudFront (adds complexity, violates "single Lambda" approach)
3. Use API Gateway's binary response support with Lambda (complex)

**Decision needed**: Verify if /public directory is actually used or can be moved to S3.

### Challenge 3: Lambda Cold Start <3s Requirement

**Problem**: Python Lambda cold starts typically 1-2s, but loading 177KB quotes.json adds overhead.

**Mitigation strategies**:
- Use Provisioned Concurrency (adds cost: ~$0.015/hour = $10.80/month for 1 instance)
- Optimize dependencies (remove unused packages, use slim layers)
- Use Lambda SnapStart (not available for Python yet, only Java)
- Load quotes.json on first request instead of at import time (makes first request slower)

**Research needed**: Measure actual cold start time with current codebase.

### Challenge 4: GitHub Secrets vs OIDC Authentication

**Problem**: spec.md FR-010 suggests GitHub Secrets (long-lived credentials), but AWS best practice is OIDC.

**Trade-off**:
- **GitHub Secrets**: Simpler to set up, matches spec requirement, requires credential rotation
- **OIDC**: More secure (temporary credentials), requires additional IAM configuration

**Decision**: Implement GitHub Secrets to match spec requirement, document OIDC as future improvement.

## Success Validation Checklist

*After implementation, verify these map to spec.md Success Criteria*:

- [ ] SC-001: Push commit to main → Lambda updated in <10 minutes
- [ ] SC-002: 2nd request from same IP within 1s → receives 429
- [ ] SC-003: 11th request per second globally → receives 429
- [ ] SC-004: Change rate limit via docs → works in <30 minutes
- [ ] SC-005: Local deployment → works in 5 steps
- [ ] SC-006: No credentials visible anywhere (git history, logs, errors)
- [ ] SC-007: Response times maintain 99.9% of current performance
- [ ] SC-008: All endpoints return same responses as before

## Next Steps

After this planning phase completes:

1. **Phase 0 Research** (next): Run research agents to resolve all "Decision needed" items above
2. **Phase 1 Design**: Generate data-model.md, contracts/, and quickstart.md based on research
3. **Agent Context Update**: Run `.specify/scripts/bash/update-agent-context.sh claude` to add AWS Lambda, SAM, Mangum to technology list
4. **Task Generation**: Run `/speckit.tasks` to create dependency-ordered implementation tasks
5. **Implementation**: Run `/speckit.implement` to execute tasks

# Data Model: AWS Lambda Deployment

**Feature**: AWS Lambda Deployment with CI/CD and Rate Limiting
**Branch**: 005-aws-lambda-deployment
**Date**: 2025-10-28

## Overview

This document defines the logical entities involved in deploying and operating the Bluths API on AWS Lambda. These entities represent configuration, runtime state, and deployment artifacts - not traditional database records.

## Entity Definitions

### 1. Deployment Package

**Purpose**: The complete artifact deployed to AWS Lambda containing application code, dependencies, data, and static assets.

**Attributes**:
- `function_name`: String - Lambda function name (e.g., "bluths-api-BluthsApiFunction-ABC123")
- `runtime`: String - Python version ("python3.11")
- `handler`: String - Entry point ("app.main.handler")
- `code_size`: Integer - Package size in bytes (limit: 250MB uncompressed, 50MB zipped)
- `memory_size`: Integer - Allocated memory in MB (512MB)
- `timeout`: Integer - Maximum execution time in seconds (30s)
- `environment_variables`: Map - Runtime configuration
  - `S3_BASE_URL`: String - URL for media files (from existing config)
- `layers`: List<String> - Lambda layer ARNs (empty initially)
- `reserved_concurrency`: Integer - Max concurrent executions (3)

**Contents**:
```
deployment-package/
├── app/
│   ├── __init__.py
│   ├── main.py              # Includes Mangum handler
│   ├── models.py
│   ├── services.py
│   ├── config.py
│   └── data/
│       └── quotes.json      # 177KB bundled data
├── public/
│   └── index.html           # 8.5KB static HTML
├── fastapi/
├── mangum/
├── pydantic/
└── ... (other dependencies)
```

**Validation Rules**:
- `code_size` MUST be < 250MB uncompressed (FR-014)
- `code_size` MUST be < 50MB when zipped
- `runtime` MUST be "python3.11"
- `timeout` MUST be ≤ 30s (AWS Lambda limit)
- `reserved_concurrency` MUST be ≥ 1 and ≤ 10

**Lifecycle**:
1. Build: Collect code + dependencies + data files
2. Validate: Check size limits
3. Package: Zip into deployment artifact
4. Upload: S3 upload by SAM CLI
5. Deploy: Lambda function update
6. Version: Automatic versioning by SAM AutoPublishAlias

**Related Entities**: CI/CD Pipeline, Lambda Function Version

### 2. Rate Limit Configuration

**Purpose**: Defines throttling rules to control API request rates and prevent abuse.

**Attributes**:
- `per_ip_limit`: Integer - Requests per second per IP address (1)
- `per_ip_window`: Float - Time window in seconds (1.0)
- `global_limit`: Integer - Total requests per second (10)
- `global_burst`: Integer - Maximum burst capacity (10)
- `retry_after_seconds`: Integer - Value for Retry-After header (1)
- `error_message`: String - Message in 429 response ("Rate limit exceeded")

**Storage Locations**:
- **Per-IP limit**: In-memory dictionary in Lambda (`ip_last_request: Dict[str, float]`)
- **Global limit**: API Gateway throttle settings in SAM template

**Validation Rules**:
- `per_ip_limit` MUST be > 0
- `global_limit` MUST be > 0
- `global_limit` SHOULD be ≥ `per_ip_limit` (otherwise per-IP is meaningless)
- `retry_after_seconds` SHOULD match `per_ip_window` for consistency

**Rate Limiting Algorithm**:
```
Per-IP (in FastAPI middleware):
  IF current_time - last_request_time[ip] < per_ip_window:
    RETURN HTTP 429 with Retry-After: per_ip_window
  ELSE:
    UPDATE last_request_time[ip] = current_time
    CONTINUE to handler

Global (at API Gateway):
  IF requests_in_current_second > global_limit:
    RETURN HTTP 429
  ELSE:
    FORWARD to Lambda
```

**Configuration Files**:
- **SAM template** (`deploy/sam/template.yaml`): API Gateway throttle settings
- **FastAPI middleware** (`app/main.py`): Per-IP rate limiting logic
- **Documentation** (`deploy/docs/RATE_LIMITS.md`): Operator guide for changing values

**State Management**:
- **Per-IP state**: In-memory Python dict, reset on Lambda cold start
- **Global state**: API Gateway built-in counters (AWS-managed, persistent)

**Modification Process** (for operators):
1. Update `per_ip_limit` in `app/main.py` (RATE_LIMIT_PER_IP constant)
2. Update `global_limit` in `deploy/sam/template.yaml` (RateLimit + BurstLimit)
3. Run `sam deploy` to apply changes
4. Verify with test script

**Related Entities**: API Gateway Configuration, FastAPI Middleware

### 3. AWS Credential

**Purpose**: Authentication credentials for AWS API access during deployment and runtime.

**Attributes**:
- `access_key_id`: String - AWS access key (20 characters, starts with "AKIA")
- `secret_access_key`: String - AWS secret key (40 characters)
- `region`: String - AWS region (e.g., "us-east-1")
- `account_id`: String - 12-digit AWS account ID
- `usage_context`: Enum - "local" or "cicd"

**Storage by Context**:

**Local Development**:
- **Location**: `.env` file in repository root (gitignored)
- **Format**:
  ```
  AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
  AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  AWS_REGION=us-east-1
  AWS_ACCOUNT_ID=123456789012
  ```
- **Access**: Loaded by deployment scripts via python-dotenv

**CI/CD (GitHub Actions)**:
- **Location**: GitHub repository secrets (Settings → Secrets and variables → Actions)
- **Secret names**:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`
  - `AWS_ACCOUNT_ID`
- **Access**: Environment variables in GitHub Actions workflow

**Security Requirements** (FR-011):
- MUST NOT appear in git history
- MUST NOT appear in CloudWatch logs
- MUST NOT appear in error messages
- MUST NOT appear in SAM CLI output
- `.env` file MUST be in `.gitignore`

**IAM Permissions** (minimum required):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "apigateway:*",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole",
        "s3:GetObject",
        "s3:PutObject",
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

**Rotation Schedule**:
- Local: 90 days (manual)
- CI/CD: 90 days (manual update in GitHub Secrets)
- Future: Migrate to OIDC (no rotation needed)

**Related Entities**: CI/CD Pipeline, Deployment Package

### 4. CI/CD Pipeline

**Purpose**: Automated workflow that builds, validates, packages, and deploys the Lambda function when code changes are pushed to the main branch.

**Attributes**:
- `trigger_branch`: String - Git branch that triggers deployment ("main")
- `workflow_file`: String - GitHub Actions workflow path (".github/workflows/deploy-lambda.yml")
- `build_timeout`: Integer - Maximum build time in minutes (10)
- `deployment_timeout`: Integer - Maximum deployment time in minutes (10)
- `validation_enabled`: Boolean - Whether to run post-deployment tests (true)
- `rollback_enabled`: Boolean - Whether to rollback on validation failure (true)

**Pipeline Stages**:

**Stage 1: Trigger**
- **Event**: Push to `main` branch or manual workflow_dispatch
- **Inputs**: Git commit SHA, changed files
- **Duration**: <1 second

**Stage 2: Build**
- **Actions**:
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies (`pip install -r requirements.txt`)
  4. Copy `app/data/quotes.json` to deployment directory
  5. Copy `public/` directory to deployment directory
- **Outputs**: Build artifacts in `deploy/sam/.aws-sam/`
- **Duration**: 2-3 minutes

**Stage 3: Validate**
- **Actions**:
  1. Check deployment package size (<50MB zipped)
  2. Verify quotes.json is valid JSON
  3. Run pytest on unit tests
- **Outputs**: Validation report
- **Duration**: 30 seconds
- **Failure action**: Stop pipeline, do not deploy

**Stage 4: Package**
- **Actions**:
  1. Run `sam build`
  2. Run `sam package` (uploads to S3)
  3. Store previous Lambda version for rollback
- **Outputs**: CloudFormation template with S3 references
- **Duration**: 1-2 minutes

**Stage 5: Deploy**
- **Actions**:
  1. Run `sam deploy --no-fail-on-empty-changeset`
  2. Wait for CloudFormation stack completion
  3. Extract API Gateway endpoint URL
- **Outputs**: Deployed Lambda function, API Gateway URL
- **Duration**: 3-5 minutes
- **Rollback**: Automatic CloudFormation rollback on failure

**Stage 6: Verify**
- **Actions**:
  1. Wait 10 seconds for API Gateway propagation
  2. Call `/health` endpoint
  3. Call `/api/quotes/random` endpoint
  4. Test rate limiting (make 2 requests within 1 second, expect 429)
- **Outputs**: Verification results in workflow logs
- **Duration**: 30 seconds
- **Failure action**: Trigger Stage 7 (Rollback)

**Stage 7: Rollback** (if Stage 6 fails)
- **Actions**:
  1. Update Lambda alias to previous version
  2. Log failure reason in GitHub Actions
  3. Mark workflow as failed
- **Outputs**: Restored previous version
- **Duration**: 30 seconds

**Success Criteria**:
- Total pipeline duration < 10 minutes (NFR-003)
- Deployment status clearly logged (FR-019)
- Failed deployments revert to previous version (FR-020)

**Monitoring**:
- GitHub Actions logs (preserved for 90 days)
- CloudFormation stack events
- CloudWatch Logs for Lambda function

**Related Entities**: Deployment Package, AWS Credential, Lambda Function Version

### 5. API Gateway Configuration

**Purpose**: HTTP API frontend that routes requests to Lambda function and enforces rate limiting.

**Attributes**:
- `api_type`: String - API Gateway type ("HTTP API")
- `api_name`: String - Display name ("BluthsAPI")
- `stage_name`: String - Deployment stage ("prod")
- `endpoint_url`: String - Public API URL (e.g., "https://abc123.execute-api.us-east-1.amazonaws.com/prod")
- `custom_domain`: String - Custom domain name ("bqaas.lucille2.com") - configured manually via CNAME
- `custom_domain_type`: Enum - "CNAME" (simple DNS pointer, no ACM certificate)
- `cors_enabled`: Boolean - Whether CORS is enabled (true)
- `cors_origins`: List<String> - Allowed origins (["*"])
- `cors_methods`: List<String> - Allowed methods (["GET", "OPTIONS"])
- `throttle_rate_limit`: Integer - Steady-state requests per second (10)
- `throttle_burst_limit`: Integer - Burst capacity (10)
- `default_route`: String - Catch-all route ("/{proxy+}")

**Routes**:
- `GET /health` → Lambda function
- `GET /api/quotes/random` → Lambda function
- `GET /api/quotes/meme` → Lambda function
- `GET /api/quotes/{speaker}` → Lambda function
- `GET /` → Lambda function (serves static HTML)
- `/{proxy+}` → Lambda function (catch-all)

**CORS Configuration** (FR-016):
```yaml
CorsConfiguration:
  AllowOrigins:
    - "*"
  AllowMethods:
    - GET
    - OPTIONS
  AllowHeaders:
    - "*"
  AllowCredentials: false
```

**Throttling Configuration** (FR-005):
```yaml
ThrottleSettings:
  RateLimit: 10     # Requests per second
  BurstLimit: 10    # Token bucket capacity
```

**Integration**:
- **Type**: AWS_PROXY (Lambda proxy integration)
- **Payload format**: Version 2.0 (HTTP API default)
- **Timeout**: 30 seconds (matches Lambda timeout)

**Caching**:
- API Gateway caching: DISABLED (adds cost, low traffic doesn't justify)
- Application-level caching: Enabled via `Cache-Control` headers in responses (FR-017)

**Logging**:
- Access logs: ENABLED → CloudWatch Logs
- Execution logs: ENABLED (for debugging)
- Log format: JSON with `$context` variables

**Related Entities**: Rate Limit Configuration, Lambda Function

### 6. Lambda Function Version

**Purpose**: Immutable snapshot of Lambda function code and configuration, enabling rollback and traffic management.

**Attributes**:
- `function_name`: String - Base Lambda function name
- `version_number`: Integer - Sequential version (1, 2, 3, ...)
- `version_arn`: String - Full ARN with version (e.g., "arn:aws:lambda:us-east-1:123456789012:function:bluths-api:42")
- `code_sha256`: String - SHA256 hash of deployment package
- `published_date`: DateTime - When version was published
- `alias_name`: String - Alias pointing to this version ("live")

**Version Management**:
- **Creation**: Automatic via SAM `AutoPublishAlias: live`
- **Retention**: All versions retained (can be cleaned up manually)
- **Active version**: Tracked by alias "live"

**Alias Configuration**:
```yaml
Alias: live
TargetVersion: $LATEST  # Points to newest version
```

**Rollback Process**:
1. Identify previous version number (e.g., N-1)
2. Update alias to point to previous version:
   ```bash
   aws lambda update-alias \
     --function-name bluths-api \
     --name live \
     --function-version N-1
   ```
3. Traffic instantly switches to previous version
4. Current version (N) remains deployed but receives no traffic

**Version Lifecycle**:
```
Deploy → Publish Version N → Update Alias "live" → Version N receives traffic
         ↓
         If validation fails → Update Alias to N-1 → Version N-1 receives traffic
```

**Storage**:
- Versions stored in Lambda service (AWS-managed)
- Each version has own code artifact in S3
- No automatic cleanup (manual deletion if needed)

**Related Entities**: Deployment Package, CI/CD Pipeline

### 7. Custom Domain Configuration

**Purpose**: DNS configuration that provides a branded domain name (bqaas.lucille2.com) instead of the AWS-generated API Gateway URL.

**Attributes**:
- `custom_domain`: String - "bqaas.lucille2.com"
- `record_type`: String - "CNAME"
- `target`: String - CloudFront distribution domain (e.g., "d123abc456.cloudfront.net")
- `ttl`: Integer - DNS TTL in seconds (300)
- `dns_provider`: String - Where DNS is managed (e.g., "Namecheap", "Route53", "Cloudflare")
- `configuration_method`: Enum - "manual" (not automated in CI/CD)
- `certificate_arn`: String - ACM certificate ARN (e.g., "arn:aws:acm:us-east-1:123456789012:certificate/abc-def-123")
- `certificate_domain`: String - "bqaas.lucille2.com" (MUST match custom_domain)
- `certificate_validation`: Enum - "DNS" (uses DNS CNAME for validation)
- `api_gateway_domain_name`: String - CloudFront domain assigned by API Gateway Custom Domain Name resource

**Configuration Process** (manual, post-deployment):

1. **Request ACM Certificate**:
   - Domain: `bqaas.lucille2.com`
   - Validation: DNS (CNAME record)
   - Region: Must match Lambda region (e.g., `us-east-1`)
   - **CRITICAL**: Certificate MUST list `bqaas.lucille2.com` in Subject Alternative Names

2. **Complete DNS Validation**:
   - ACM provides validation CNAME (e.g., `_abc123.bqaas.lucille2.com` → `_xyz789.acm-validations.aws`)
   - Add validation CNAME to DNS provider
   - Wait 5-30 minutes for ACM to issue certificate

3. **Create API Gateway Custom Domain Name**:
   - Domain: `bqaas.lucille2.com`
   - Certificate: Select ACM certificate from step 1
   - API Gateway generates CloudFront domain (e.g., `d123abc456.cloudfront.net`)

4. **Create API Mapping**:
   - Custom domain: `bqaas.lucille2.com`
   - API: HTTP API (bluths-api)
   - Stage: `prod`
   - Path: `/` (root)

5. **Update DNS**:
   - Create CNAME: `bqaas.lucille2.com` → `d123abc456.cloudfront.net` (CloudFront domain from step 3)
   - TTL: `300` seconds
   - Wait 5-15 minutes for propagation

6. **Verify**:
   - DNS: `dig bqaas.lucille2.com` (should resolve to CloudFront domain)
   - SSL: `curl -v https://bqaas.lucille2.com/health` (should show certificate for bqaas.lucille2.com)
   - Browser: No certificate warnings

**DNS Record Structure**:
```
# Validation CNAME (temporary, for ACM)
_abc123def456.bqaas.lucille2.com.  300  IN  CNAME  _xyz789ghi012.acm-validations.aws.

# Custom domain CNAME (permanent)
bqaas.lucille2.com.  300  IN  CNAME  d123abc456.cloudfront.net.
```

**Access Methods**:
- **Default URL**: `https://abc123.execute-api.us-east-1.amazonaws.com/prod` (always works)
- **Custom domain**: `https://bqaas.lucille2.com` (with valid SSL, no warnings)
- Both URLs point to same Lambda function

**SSL/TLS Certificate**:
- **Approach**: AWS Certificate Manager (ACM) public certificate
- **Domain**: `bqaas.lucille2.com` (exact match required)
- **Validation**: DNS validation via CNAME record
- **Result**: Valid SSL certificate trusted by all browsers
- **Cost**: Free (ACM public certificates are free)

**Validation Rules**:
- `custom_domain` MUST be a valid fully-qualified domain name
- `certificate_domain` MUST exactly match `custom_domain`
- `certificate_arn` MUST reference an ACM certificate in the same region as API Gateway
- ACM certificate Subject Alternative Names MUST include `bqaas.lucille2.com`
- `target` (CNAME value) MUST be CloudFront domain, NOT API Gateway default URL
- DNS provider MUST allow CNAME records for the specified domain

**Maintenance**:
- **ACM certificate renewal**: Automatic (AWS renews before expiration)
- **DNS validation CNAME**: Keep in DNS permanently (required for auto-renewal)
- **Custom domain CNAME**: Set once manually, persists indefinitely
- **API Gateway URL changes**: Do NOT affect custom domain (abstracted by Custom Domain Name resource)
- **DNS propagation**: Changes take 5-15 minutes based on TTL

**Cost**:
- ACM certificate: **Free**
- API Gateway Custom Domain Name: **Free**
- CloudFront distribution (behind the scenes): **Free** (included with API Gateway)
- DNS CNAME records: Typically free (depends on DNS provider)

**Related Entities**: API Gateway Configuration, ACM Certificate (external)

## Entity Relationships

```
┌─────────────────────┐
│   CI/CD Pipeline    │
│  (GitHub Actions)   │
└──────────┬──────────┘
           │ triggers
           ▼
┌─────────────────────┐
│ Deployment Package  │◄───────┐
│   (code + data)     │        │ contains
└──────────┬──────────┘        │
           │ deploys to        │
           ▼                   │
┌─────────────────────┐        │
│ Lambda Function     │        │
│    Version N        │────────┘
└──────────┬──────────┘
           │ fronted by
           ▼
┌─────────────────────┐
│  API Gateway        │◄───────────┐
│  (HTTP API)         │            │ CNAME points to
└──────────┬──────────┘            │
           │ enforces         ┌────┴──────────────┐
           ▼                  │ Custom Domain     │
┌─────────────────────┐       │ bqaas.lucille2.com│
│ Rate Limit Config   │       └───────────────────┘
│ (per-IP + global)   │
└─────────────────────┘

┌─────────────────────┐
│  AWS Credential     │
│ (local or GitHub)   │
└──────────┬──────────┘
           │ authenticates
           ▼
┌─────────────────────┐
│   CI/CD Pipeline    │
└─────────────────────┘
```

## State Diagram: Deployment Lifecycle

```
[Code Change Pushed]
        │
        ▼
[Build & Validate]
        │
        ├─ Validation Failed → [Stop, Log Error]
        │
        ▼
[Package & Upload]
        │
        ▼
[Deploy to Lambda]
        │
        ├─ Deploy Failed → [CloudFormation Rollback]
        │
        ▼
[Update Version & Alias]
        │
        ▼
[Run Health Checks]
        │
        ├─ Health Check Failed → [Rollback Alias to N-1]
        │
        ▼
[Deployment Complete]
```

## Configuration Files Reference

| Entity | Configuration File | Location | Format |
|--------|-------------------|----------|--------|
| Deployment Package | `template.yaml` | `deploy/sam/` | YAML (SAM) |
| Rate Limit Config (per-IP) | `main.py` | `app/` | Python |
| Rate Limit Config (global) | `template.yaml` | `deploy/sam/` | YAML (SAM) |
| AWS Credential (local) | `.env` | Repository root | Key=Value |
| AWS Credential (CI/CD) | GitHub Secrets | GitHub repository settings | UI |
| CI/CD Pipeline | `deploy-lambda.yml` | `.github/workflows/` | YAML (Actions) |
| API Gateway | `template.yaml` | `deploy/sam/` | YAML (SAM) |
| Custom Domain | DNS CNAME record | DNS provider (Namecheap/Route53) | DNS Record |

## Open Questions

1. **CloudWatch log retention**: Should we set a retention period (e.g., 7 days) to minimize costs?
   - **Recommendation**: Yes, 7 days for production, 3 days for testing

2. **Lambda memory size**: Start with 512MB or 1024MB?
   - **Recommendation**: 512MB, monitor performance, scale up if needed

3. **API Gateway stage**: Use "prod" or "v1"?
   - **Recommendation**: "prod" for simplicity

4. **Version cleanup**: Should old Lambda versions be automatically deleted?
   - **Recommendation**: No automatic cleanup, manual deletion if storage costs become issue

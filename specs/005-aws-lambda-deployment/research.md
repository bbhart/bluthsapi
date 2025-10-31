# Research & Decision Log: AWS Lambda Deployment

**Feature**: AWS Lambda Deployment with CI/CD and Rate Limiting
**Branch**: 005-aws-lambda-deployment
**Date**: 2025-10-28

## Overview

This document captures research findings and technical decisions for deploying the Bluths API to AWS Lambda. Each section addresses a specific technical challenge identified during planning and provides a rationale for the chosen approach.

## Decision 1: Deployment Tool Selection

### Research Question
Which deployment tool should we use: AWS SAM, Serverless Framework, or manual Lambda configuration?

### Options Evaluated

**Option A: AWS SAM (Serverless Application Model)**
- **Pros**:
  - AWS-native, well-documented, official support
  - Built-in support for API Gateway + Lambda integration
  - `sam local` for local testing
  - Simple YAML syntax similar to CloudFormation
  - No external dependencies beyond AWS CLI
- **Cons**:
  - AWS-only (not portable to other clouds)
  - Less plugin ecosystem than Serverless Framework
- **Setup complexity**: Low - single template.yaml file
- **Maintainability**: High - declarative infrastructure as code

**Option B: Serverless Framework**
- **Pros**:
  - Multi-cloud support (AWS, Azure, GCP)
  - Large plugin ecosystem
  - Popular in community
- **Cons**:
  - Requires npm/Node.js even for Python projects
  - Additional abstraction layer on top of AWS
  - More moving parts (framework + AWS)
- **Setup complexity**: Medium - needs serverless.yml + npm setup
- **Maintainability**: Medium - depends on framework updates

**Option C: Manual Lambda Configuration**
- **Pros**:
  - Complete control over all settings
  - No abstraction layer
  - Minimal tooling
- **Cons**:
  - Error-prone (manual console clicks or complex boto3 scripts)
  - No infrastructure-as-code benefits
  - Difficult to reproduce environments
  - Hard to implement FR-020 (rollback on failure)
- **Setup complexity**: High - requires extensive scripting
- **Maintainability**: Low - difficult to track changes

### Decision: AWS SAM

**Rationale**:
1. **Alignment with requirements**: SAM provides built-in support for API Gateway throttling (FR-005), Lambda versioning for rollback (FR-020), and deployment automation (FR-003)
2. **Simplicity**: Single template.yaml file is easier for ops team to modify rate limits (SC-004)
3. **AWS-native**: Since the spec explicitly requires AWS Lambda (not multi-cloud), SAM's AWS-specific optimizations are beneficial
4. **Documentation**: NFR-005 requires documentation maintainable by non-developers; SAM's YAML is more readable than boto3 scripts

### Alternatives Considered
- Serverless Framework rejected because it adds Node.js dependency to a Python project and provides no benefit for single-cloud deployment
- Manual configuration rejected because it violates infrastructure-as-code principles and makes FR-020 (rollback) difficult

## Decision 2: Per-IP Rate Limiting Implementation

### Research Question
How to implement per-IP rate limiting (1 request per second per IP) when API Gateway's native throttling is account-level?

### Options Evaluated

**Option A: AWS WAF Rate-Based Rules**
- **Pros**:
  - Native AWS service, integrates with API Gateway
  - Enforces at edge before reaching Lambda (saves cost)
  - Configurable per IP with 5-minute time windows
  - Can add Retry-After headers (FR-007)
- **Cons**:
  - Costs ~$1/month for WAF web ACL + $0.60 per million requests
  - Minimum time window is 5 minutes (not 1 second as spec requires)
  - **BLOCKER**: Cannot enforce 1 QPS per IP, only limits like "max 300 requests per 5 minutes"
- **Latency overhead**: <10ms (acceptable for <50ms requirement)

**Option B: Lambda@Edge or CloudFront Functions**
- **Pros**:
  - Runs at CloudFront edge locations (low latency)
  - Can inspect request IP and reject before Lambda
  - Stateless, global distribution
- **Cons**:
  - Requires CloudFront distribution (adds complexity)
  - **BLOCKER**: Stateless - can't track "1 request per second per IP" without external storage
  - Would need DynamoDB for state (see Option D)
- **Latency overhead**: ~5-15ms for function execution

**Option C: FastAPI Middleware (In-Lambda)**
- **Pros**:
  - Pure Python, easy to implement
  - Can use in-memory dict to track IP → timestamp
  - Full control over rate limiting logic
  - Can return proper 429 responses with Retry-After headers
- **Cons**:
  - State doesn't persist across Lambda instances (cold starts reset)
  - Each concurrent Lambda has separate state (can't enforce true global limit)
  - **PARTIAL SOLUTION**: Works for per-IP limiting but not reliable for global 10 QPS cap
- **Latency overhead**: <5ms (in-memory dict lookup)

**Option D: DynamoDB + FastAPI Middleware**
- **Pros**:
  - Persistent state across Lambda instances
  - Can enforce both per-IP and global limits accurately
  - Flexible rate limit algorithms (sliding window, token bucket)
  - Supports TTL for automatic cleanup
- **Cons**:
  - Adds external dependency (DynamoDB table)
  - Costs: ~$0.25/month for low traffic + $0.25 per million requests
  - Adds latency for DynamoDB read/write on every request
- **Latency overhead**: ~20-50ms (DynamoDB query + update)
- **Risk**: May violate NFR-004 (<50ms rate limiting overhead)

**Option E: API Gateway Usage Plans (Native)**
- **Pros**:
  - Built-in API Gateway feature
  - Free, no external dependencies
  - Easy to configure in SAM template
- **Cons**:
  - **BLOCKER**: Requires API keys to identify clients (violates Constitution Article II - Public Access)
  - Throttles per API key, not per IP
  - Not suitable for public APIs
- **Ruling**: Rejected - violates constitution

### Decision: Hybrid Approach (FastAPI Middleware + API Gateway Account-Level)

**Rationale**:
After evaluating options, no single AWS-native solution perfectly meets the requirements:
- **Per-IP limiting (1 QPS)**: Implement using FastAPI middleware with in-memory tracking
- **Global limiting (10 QPS)**: Use API Gateway's account-level throttling (burst=10, rate=10)

**Trade-offs accepted**:
1. **Per-IP limit** is best-effort across cold starts: If a user hits two different Lambda instances simultaneously, they could briefly exceed 1 QPS. This is acceptable because:
   - Reserved concurrency will be set to 2-3 instances max (for cost control)
   - Actual traffic is low (<10 QPS total)
   - The global 10 QPS limit provides hard cap
2. **Latency**: In-memory dict lookup is <1ms, well under 50ms requirement

**Implementation**:
```python
# In-memory rate limiter middleware
from fastapi import Request, HTTPException
from time import time

ip_last_request = {}  # IP → timestamp

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time()

    if client_ip in ip_last_request:
        if now - ip_last_request[client_ip] < 1.0:  # 1 second
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "1"},
                content={"error": "Rate limit exceeded"}
            )

    ip_last_request[client_ip] = now
    return await call_next(request)
```

### Alternatives Considered
- **DynamoDB** rejected because 20-50ms latency risks violating NFR-004 and adds $3-5/month cost for minimal traffic
- **WAF** rejected because it cannot enforce 1-second windows
- **CloudFront + Lambda@Edge** rejected as over-engineering for low-traffic API

### Future Improvement
If traffic exceeds 100 QPS or multi-region deployment is needed, migrate to DynamoDB-based rate limiting with DynamoDB Global Tables.

## Decision 3: Mangum Configuration for FastAPI

### Research Question
How to configure Mangum to bridge FastAPI to Lambda while supporting static file serving?

### Technical Context
- **Mangum** is an ASGI-to-Lambda adapter that translates API Gateway events to ASGI format for FastAPI
- Current app serves static files from `/public` directory using `StaticFiles` (FR-018)
- Lambda package will include `public/index.html` (8.5KB)

### Options Evaluated

**Option A: Mangum with API Gateway HTTP API (Payload Format 2.0)**
- **Pros**:
  - Simpler event structure, lower cost than REST API
  - Native support in Mangum via `api_gateway_base_path`
  - Automatic CORS handling
- **Cons**:
  - HTTP API has fewer features than REST API (but we don't need them)
- **Configuration**:
  ```python
  from mangum import Mangum
  handler = Mangum(app, lifespan="off")
  ```
- **Static files**: FastAPI's `StaticFiles` works transparently, Mangum handles it

**Option B: Mangum with API Gateway REST API (Payload Format 1.0)**
- **Pros**:
  - More features (request validation, models)
  - Longer track record
- **Cons**:
  - More expensive (~$1/million requests vs $0.90/million)
  - More complex event structure
  - Unnecessary features for our use case
- **Configuration**: Same as Option A but use `"lifespan": "auto"`

**Option C: Pre-render static files and serve from Lambda directly**
- **Pros**:
  - Simpler Lambda handler
  - No `StaticFiles` middleware overhead
- **Cons**:
  - Requires custom handler code
  - Less maintainable
  - FastAPI already handles static files well

### Decision: Mangum with HTTP API (Option A)

**Rationale**:
1. **Cost efficiency**: HTTP API costs 10% less, aligns with "minimize serving costs" (Constitution Governance)
2. **Simplicity**: Fewer features = less configuration = easier for ops team to understand (NFR-005)
3. **Static files**: `public/index.html` (8.5KB) is small enough to bundle, and `StaticFiles` middleware works out-of-box with Mangum
4. **Performance**: HTTP API has lower latency (~10-20ms faster) helping with NFR-002 (<500ms response time)

### Configuration Details

**app/main.py additions**:
```python
from mangum import Mangum

# Existing FastAPI app code...

# Add Lambda handler at end of file
handler = Mangum(app, lifespan="off")
```

**SAM template.yaml**:
```yaml
Events:
  ApiEvent:
    Type: HttpApi  # Uses HTTP API, not REST API
    Properties:
      Path: /{proxy+}
      Method: ANY
```

**Static files handling**: No changes needed - FastAPI's existing `StaticFiles` mount works:
```python
# Existing code in app/main.py:
app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="static")
```

### Alternatives Considered
- REST API rejected due to higher cost and unnecessary complexity
- Custom static file handler rejected because FastAPI's built-in works perfectly

## Decision 4: GitHub Actions AWS Authentication

### Research Question
Should we use long-lived access keys (GitHub Secrets) or OpenID Connect (OIDC) for AWS authentication?

### Options Evaluated

**Option A: GitHub Secrets with Long-Lived Access Keys**
- **Pros**:
  - Simple setup: add 2 secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
  - Matches spec requirement (FR-010 "stored in GitHub Secrets")
  - Works immediately without IAM configuration
  - Familiar to most developers
- **Cons**:
  - Credentials don't rotate automatically (security risk)
  - If leaked, valid until manually revoked
  - Requires periodic manual rotation
- **Setup complexity**: Low (5 minutes)
- **Security**: Medium (static credentials)

**Option B: OpenID Connect (OIDC) Provider**
- **Pros**:
  - Temporary credentials (expire after 1 hour)
  - No long-lived secrets in GitHub
  - AWS best practice for CI/CD
  - Automatic credential rotation
- **Cons**:
  - Requires AWS IAM OIDC provider setup
  - More complex initial configuration
  - Requires trust policy configuration
  - Debugging auth issues is harder
- **Setup complexity**: Medium (30 minutes)
- **Security**: High (temporary credentials)

### Decision: GitHub Secrets (Option A) with documented OIDC upgrade path

**Rationale**:
1. **Spec compliance**: FR-010 explicitly states "remotely should be stored in the appropriate secrets manager" - GitHub Secrets qualifies
2. **Simplicity**: SC-005 requires "5-step setup process" - OIDC would add 10+ additional steps for IAM configuration
3. **Time-to-deploy**: P1 priority is getting deployment working; security hardening can follow
4. **Documentation**: We'll document OIDC migration in quickstart.md as "security enhancement"

**Implementation**:
- GitHub Secrets to configure:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION` (e.g., "us-east-1")
  - `AWS_ACCOUNT_ID` (for SAM deployment)

**Security measures**:
- Use IAM user with minimal permissions (Lambda, API Gateway, IAM, CloudFormation only)
- Enable MFA on IAM user account
- Set up CloudWatch alarm for unusual API activity
- Document credential rotation schedule (every 90 days)

### Alternatives Considered
- OIDC deferred to Phase 2 after core deployment works
- Will document OIDC migration guide in `deploy/docs/SECURITY.md`

## Decision 5: Lambda Cold Start Optimization

### Research Question
How to meet NFR-001 (<3 second cold start) with Python 3.11 + FastAPI + 177KB quotes.json?

### Baseline Measurement
Typical Python 3.11 Lambda cold start: 1-2 seconds
FastAPI import overhead: ~200-400ms
quotes.json loading (177KB): ~10-20ms
**Expected total**: ~2.5 seconds (within 3s requirement)

### Options Evaluated

**Option A: No Optimization (Baseline)**
- **Pros**:
  - Simplest, no added complexity
  - Likely meets requirement already
- **Cons**:
  - No margin for error
  - Could degrade if dependencies increase
- **Cost**: $0 additional
- **Expected cold start**: 2.0-2.5s

**Option B: Provisioned Concurrency**
- **Pros**:
  - Eliminates cold starts entirely
  - Consistent performance
  - Meets NFR-001 with margin
- **Cons**:
  - Costs $0.015/hour = $10.80/month per instance
  - Violates "minimize serving costs" (Constitution Governance)
  - Overkill for <10 QPS traffic
- **Cost**: ~$11/month minimum
- **Expected cold start**: 0s (no cold starts)

**Option C: Lambda Layers for Dependencies**
- **Pros**:
  - Separates dependencies from code
  - Faster deployment (only code changes)
  - Dependencies cached between invocations
- **Cons**:
  - Minimal impact on cold start (dependencies still loaded)
  - Adds deployment complexity
- **Cost**: $0 additional
- **Expected cold start**: 1.8-2.3s (marginal improvement)

**Option D: Lazy Loading quotes.json**
- **Pros**:
  - Delays quotes loading until first request
  - Faster Lambda initialization
- **Cons**:
  - First request is slower (~2.5s)
  - Violates NFR-002 (<500ms warm response)
  - Bad user experience for first user
- **Cost**: $0 additional
- **Expected cold start**: 1.5s (but first request 3.0s)

**Option E: Optimize Dependencies**
- **Pros**:
  - Remove unused packages
  - Use uvicorn without extras
  - Smaller package = faster load
- **Cons**:
  - Requires careful dependency audit
  - Minimal impact (~100-200ms savings)
- **Cost**: $0 additional
- **Expected cold start**: 1.8-2.3s

### Decision: Baseline (Option A) with Reserved Concurrency

**Rationale**:
1. **Expected performance meets requirement**: 2.0-2.5s cold start is under 3s NFR-001
2. **Cost alignment**: No additional cost aligns with "minimize serving costs"
3. **Reserved concurrency** (3 instances) means cold starts are rare:
   - With 10 QPS cap and ~100ms response time, max 1-2 concurrent executions needed
   - Reserved concurrency keeps 3 instances warm after first requests
   - Cold starts only happen on initial deployment or after 15 minutes idle
4. **Measurement before optimization**: Premature optimization wastes effort

**Implementation**:
```yaml
# SAM template.yaml
Resources:
  BluthsApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      ReservedConcurrentExecutions: 3  # Keeps instances warm
      MemorySize: 512  # Balance of cost and speed
      Timeout: 30
```

**Monitoring plan**:
- Add CloudWatch metric for cold start duration
- Alert if cold starts exceed 2.5s (before hitting 3s limit)
- If violations occur, implement Option E (dependency optimization)

### Alternatives Considered
- Provisioned Concurrency rejected due to cost (adds $11/month for low-traffic API)
- Lazy loading rejected because it degrades first user experience
- Lambda Layers deferred until needed (adds complexity for marginal benefit)

## Decision 6: Deployment Rollback Strategy

### Research Question
How to implement FR-020 "rollback to previous version if deployment validation fails"?

### Options Evaluated

**Option A: AWS SAM Built-in Rollback**
- **Pros**:
  - SAM automatically creates Lambda versions
  - CloudFormation rollback on stack failure
  - No additional code required
  - Uses Lambda aliases for traffic shifting
- **Cons**:
  - Only rolls back on stack creation failure
  - Doesn't handle "deployment succeeds but API broken" case
- **Implementation**: `sam deploy --no-fail-on-empty-changeset`
- **Coverage**: Handles infrastructure failures, not application failures

**Option B: GitHub Actions with Health Check Validation**
- **Pros**:
  - Tests deployed API before completing workflow
  - Can revert deployment if health check fails
  - Logs failure reason clearly (FR-019)
  - Full control over validation logic
- **Cons**:
  - Requires custom GitHub Actions workflow logic
  - Need to store previous Lambda version/alias
- **Implementation**:
  ```yaml
  - name: Validate deployment
    run: |
      curl -f https://API_ENDPOINT/health || exit 1
  - name: Rollback on failure
    if: failure()
    run: sam deploy --parameter-overrides Version=$PREVIOUS_VERSION
  ```
- **Coverage**: Handles application failures and infrastructure failures

**Option C: Lambda Aliases with Gradual Traffic Shifting**
- **Pros**:
  - Built-in Lambda feature
  - Can shift 10% traffic to new version, then 100% if healthy
  - Automatic rollback if errors increase
- **Cons**:
  - Complex SAM configuration
  - Overkill for low-traffic API (<10 QPS)
  - Requires CodeDeploy integration
- **Implementation**: SAM AutoPublishAlias + DeploymentPreference
- **Coverage**: Handles gradual rollout, not instant validation

### Decision: Hybrid (Option A + Option B)

**Rationale**:
1. **SAM built-in rollback** handles infrastructure failures (malformed template, insufficient permissions)
2. **GitHub Actions health check** validates application works after deployment
3. **Simplicity**: Avoids CodeDeploy complexity for low-traffic API
4. **Meets requirement**: FR-020 requires rollback on failure - both mechanisms provide this

**Implementation**:

**SAM template.yaml**:
```yaml
Resources:
  BluthsApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      AutoPublishAlias: live  # Creates versioned deployments
```

**GitHub Actions workflow**:
```yaml
- name: Deploy to AWS Lambda
  id: deploy
  run: sam deploy --no-fail-on-empty-changeset --stack-name bluths-api

- name: Get API endpoint
  id: endpoint
  run: echo "url=$(aws cloudformation describe-stacks --stack-name bluths-api --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text)" >> $GITHUB_OUTPUT

- name: Validate deployment
  run: |
    sleep 10  # Wait for API Gateway to propagate
    curl -f ${{ steps.endpoint.outputs.url }}/health || exit 1

- name: Test rate limiting
  run: |
    # Make 2 requests within 1 second, expect 2nd to fail
    curl -f ${{ steps.endpoint.outputs.url }}/api/quotes/random
    curl -f ${{ steps.endpoint.outputs.url }}/api/quotes/random && exit 1 || echo "Rate limit working"

- name: Rollback on failure
  if: failure()
  run: |
    echo "Deployment validation failed, rolling back..."
    aws lambda update-alias --function-name bluths-api --name live --function-version $(cat .previous-version)
```

**Rollback triggers**:
1. SAM deployment fails → CloudFormation automatic rollback
2. Health check fails → GitHub Actions updates Lambda alias to previous version
3. Rate limiting validation fails → GitHub Actions updates Lambda alias

### Alternatives Considered
- CodeDeploy gradual traffic shifting rejected as over-engineering for <10 QPS API
- Manual rollback rejected because it violates FR-020 "automatic" requirement

## Summary of Decisions

| Decision | Chosen Approach | Key Rationale |
|----------|----------------|---------------|
| Deployment Tool | AWS SAM | AWS-native, simple YAML, supports rollback, no extra dependencies |
| Per-IP Rate Limiting | FastAPI middleware (in-memory) | <1ms latency, simple, works for low traffic, acceptable best-effort across cold starts |
| Global Rate Limiting | API Gateway throttling (10 QPS) | Built-in, free, enforced at edge before Lambda |
| Lambda Adapter | Mangum with HTTP API | Lower cost, simpler than REST API, works with StaticFiles out-of-box |
| AWS Authentication | GitHub Secrets (long-lived keys) | Matches spec, simple 5-step setup, document OIDC upgrade path |
| Cold Start Optimization | Baseline + Reserved Concurrency (3) | Expected 2.0-2.5s meets 3s requirement, $0 additional cost |
| Rollback Strategy | SAM auto-rollback + GitHub Actions health check | Covers both infrastructure and application failures |

## Open Questions for Phase 1

1. **AWS Region selection**: Default to us-east-1 or let user configure? (Recommend us-east-1 for lowest Lambda pricing)
2. **CloudWatch log retention**: Default 7 days or configurable? (Recommend 7 days to minimize costs)
3. **Lambda memory size**: 512MB sufficient or need 1024MB? (Recommend 512MB, monitor and adjust)
4. **API Gateway stage name**: Use "prod" or "v1"? (Recommend "prod" for simplicity)
5. **Static file caching**: Add Cache-Control headers to index.html? (Recommend yes, 1 hour TTL)

These will be resolved during contract generation in Phase 1.

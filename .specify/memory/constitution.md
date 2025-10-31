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
- Global throttling only via API Gateway (10 requests/second default)
- No per-IP rate limiting (avoids infrastructure complexity and cost)
- Return HTTP 429 with Retry-After header when limits exceeded
- Rate limits must be configurable via API Gateway settings

### Observability
- CloudWatch Logs with structured JSON logging (errors, warnings, deployment events)
- No custom CloudWatch metrics, dashboards, or X-Ray tracing (cost optimization)
- Log cost target: $0.50-2/month at expected traffic volumes

### Docker Requirements (Legacy/Alternative Deployment)
- Multi-stage builds for minimal image size
- Run as non-root user for security
- Health checks must use lightweight tools (curl preferred) - avoid loading language interpreters
- Clean up package manager cache to minimize image size (e.g., `rm -rf /var/lib/apt/lists/*`)

### Health Checks
- Health check endpoint: GET /health (required for all deployment methods)
- Returns HTTP 200 on success
- Used for deployment validation in Lambda
- Docker health check parameters: interval=30s, timeout=3s, start-period=5s, retries=3
- Docker health check command format: `curl -f http://localhost:PORT/health || exit 1`

### Package Management
- Use uv for Python dependency management (10-100x faster than pip)
- Lock dependencies for reproducible builds (uv.lock)
- Separate production (requirements.txt) and development (requirements-dev.txt) dependencies

## Governance

This constitution defines minimal viable quote API.
All endpoints must remain read-only and publicly accessible.
Serving costs should be minimized. This is not expected to be a high use API.

### Security Principles (Non-Negotiable)

**Least Privilege is MANDATORY** - Under no circumstances should permissions be granted beyond what is strictly required, even for MVPs, prototypes, or testing. Security fundamentals are never compromised for convenience.

- IAM policies MUST scope permissions to specific resources (e.g., `bluths-api-*`)
- IAM policies MUST grant only required actions (no wildcards like `*` or `lambda:*` unless absolutely necessary)
- Never use `*FullAccess` managed policies (e.g., `IAMFullAccess`, `AWSLambda_FullAccess`)
- All AWS resource access follows Least Privilege from day one

**Version**: 1.3.0 | **Ratified**: 2025-10-24 | **Last Amended**: 2025-10-31

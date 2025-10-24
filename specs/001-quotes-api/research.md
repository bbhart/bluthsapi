# Research: Arrested Development Quotes API

**Date**: 2025-10-24
**Feature**: 001-quotes-api
**Purpose**: Resolve technical decisions for self-hosted, read-only REST API

## Research Questions

1. What hosting approach should we use?
2. What language/framework should we choose?
3. What dependencies do we need?
4. What testing approach should we use?
5. How should we structure deployment?

---

## Decision 1: Hosting Platform

**Decision**: Self-hosted Docker container

**Rationale**:
- **Full control**: Deploy anywhere (home server, VPS, cloud provider of choice)
- **No vendor lock-in**: Not tied to serverless platform limitations
- **Cost flexibility**: Can use free tier VPS, home server, or any hosting provider
- **Portable**: Docker container runs consistently across environments
- **Scalability**: Easy to replicate or scale if needed (though low traffic expected)
- **Development parity**: Local dev environment identical to production

**Alternatives Considered**:
- **Cloudflare Pages**: Requires JavaScript, user prefers Python
- **Vercel**: Limited free tier (100 requests/day too restrictive)
- **Render**: Cold starts (~30s) unacceptable for API
- **PythonAnywhere**: Too restrictive for simple use case

**Implementation Notes**:
- Single Docker container with Python + FastAPI
- Static HTML served by FastAPI (no separate web server needed for this scale)
- Container can run on any Docker-capable host
- Minimal resource requirements (< 100MB RAM expected)

---

## Decision 2: Language/Framework

**Decision**: Python 3.11+ with FastAPI

**Rationale**:
- **User preference**: Developer more comfortable with Python than JavaScript
- **FastAPI benefits**:
  - High performance (comparable to Node.js)
  - Automatic OpenAPI documentation generation (self-documenting API)
  - Type hints for data validation (Pydantic models)
  - Async/await support for concurrent requests
  - Minimal boilerplate for simple APIs
- **JSON native**: Python's `json` module handles quote data easily
- **Static file serving**: FastAPI can serve `index.html` directly (no nginx needed)
- **Testing ecosystem**: pytest is mature and comprehensive

**Alternatives Considered**:
- **Flask**: Simpler but lacks async support and auto-documentation
- **Django**: Massive overkill for 3 endpoint read-only API
- **JavaScript/Node.js**: User prefers Python

**Version**: Python 3.11 or 3.12 (latest stable)

---

## Decision 3: Package Manager

**Decision**: uv (modern Python package manager)

**Rationale**:
- **Extremely fast**: 10-100x faster than pip, written in Rust
- **Built-in virtual environment**: `uv venv` creates isolated environments
- **Drop-in pip replacement**: `uv pip install` works like pip but faster
- **Lockfile support**: Generates `uv.lock` for reproducible builds
- **pyproject.toml native**: Modern Python packaging standard
- **No separate virtualenv tool**: uv handles both packages and environments

**Commands**:
```bash
uv venv                    # Create virtual environment
uv pip install package     # Install package (fast)
uv pip sync requirements.txt  # Sync exact versions
```

**Alternatives Considered**:
- **pip + venv**: Traditional but slow, no lockfile
- **poetry**: Feature-rich but heavier, slower than uv
- **pipenv**: Lockfile support but slower than uv

---

## Decision 4: Framework/Dependencies

**Decision**: FastAPI with minimal dependencies

**Rationale**:
- **Minimal stack**: FastAPI + Uvicorn (ASGI server) is all that's needed
- **No database**: Static JSON file eliminates SQLAlchemy, ORMs, migrations
- **No caching layer**: Dataset small enough to load into memory
- **Auto OpenAPI**: FastAPI generates `/docs` and `/redoc` endpoints automatically

**Required Dependencies** (managed via uv):
```
fastapi==0.104.0      # Web framework
uvicorn[standard]==0.24.0  # ASGI server
pydantic==2.5.0       # Data validation (included with FastAPI)
pydantic-settings==2.1.0  # Settings management
```

**Development Dependencies** (managed via uv):
```
pytest==7.4.0         # Testing framework
httpx==0.25.0         # Async HTTP client for testing
pytest-asyncio==0.21.0  # Async test support
pytest-cov==4.1.0     # Coverage reporting
```

**Alternatives Considered**:
- **Adding Redis**: Unnecessary for static data that fits in memory
- **Adding PostgreSQL**: Overkill for read-only JSON file
- **Adding nginx**: FastAPI can serve static files directly for low traffic

---

## Decision 5: Testing Framework

**Decision**: pytest with httpx for API testing

**Rationale**:
- **pytest**: Industry standard for Python testing
- **httpx**: Async HTTP client, works seamlessly with FastAPI's TestClient
- **FastAPI TestClient**: Built-in testing support, no server needed
- **Coverage**: pytest-cov for code coverage reports
- **Fast**: Tests run in milliseconds (no database, no external services)

**Test Strategy**:
- **Unit tests**: Test quote filtering logic (case-insensitive, random selection)
- **Integration tests**: Test API endpoints using FastAPI TestClient
- **Contract tests**: Validate response schemas match OpenAPI spec

**Example Test Structure**:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_random_quote():
    response = client.get("/api/quotes/random")
    assert response.status_code == 200
    assert "data" in response.json()
```

**Alternatives Considered**:
- **unittest**: pytest is more modern, better fixtures
- **nose**: Deprecated, pytest replaced it
- **requests library**: httpx is async-native, better for FastAPI

---

## Decision 6: Deployment Strategy

**Decision**: Docker container with multi-stage build

**Rationale**:
- **Reproducible**: Same container in dev, staging, production
- **Isolated**: All dependencies bundled, no system package conflicts
- **Efficient**: Multi-stage build keeps image small (~150MB)
- **Portable**: Runs on any Docker host (local, VPS, cloud)
- **Simple**: Single `docker run` command to start

**Dockerfile Strategy**:
```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
# Install dependencies

FROM python:3.11-slim
# Copy only runtime files
# Run as non-root user
```

**Deployment Options**:
- **Local/Home Server**: `docker run -p 8000:8000 bluthsapi`
- **Any VPS** (DigitalOcean, Linode, Hetzner): Docker pre-installed
- **Cloud providers**: AWS ECS, Google Cloud Run, Azure Container Instances
- **Container platforms**: Railway.app, Fly.io (both have free tiers)

**Alternatives Considered**:
- **Direct Python installation**: Not portable, dependency conflicts
- **Virtual environment only**: Doesn't solve deployment portability
- **Kubernetes**: Massive overkill for single container API

---

## Decision 7: Configuration Management

**Decision**: Environment variables with `.env` file support

**Rationale**:
- **Standard practice**: 12-factor app methodology
- **Docker-friendly**: Pass env vars with `docker run -e` or `--env-file`
- **Development**: Use `.env` file locally (not committed to git)
- **Production**: Set via Docker/host environment
- **FastAPI support**: Built-in with `pydantic-settings`

**Configuration Variables**:
```bash
S3_BASE_URL=https://bucket.s3.amazonaws.com  # Required
HOST=0.0.0.0                                  # Optional (default)
PORT=8000                                     # Optional (default)
```

**Implementation**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    s3_base_url: str
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
```

**Alternatives Considered**:
- **Config file (config.json)**: Less portable, can't override at runtime
- **Hardcoded values**: Inflexible, insecure
- **Secrets manager**: Overkill for single public S3 URL

---

## Decision 8: Project Structure

**Decision**: FastAPI standard layout with domain separation

**Structure**:
```
app/
├── main.py              # FastAPI app, routes registration
├── models.py            # Pydantic models (Quote, QuoteResponse, ErrorResponse)
├── services.py          # Business logic (filtering, random selection)
├── config.py            # Settings/configuration
└── data/
    └── quotes.json      # Static quote data

public/
└── index.html           # Static documentation page

tests/
├── test_services.py     # Unit tests for business logic
├── test_api.py          # Integration tests for endpoints
└── conftest.py          # pytest fixtures

Dockerfile
docker-compose.yml       # Optional: for easy local dev
requirements.txt         # Production dependencies
requirements-dev.txt     # Development dependencies
.env.example             # Template for environment variables
```

**Rationale**:
- **Flat structure**: Simple for small API (only 3 endpoints)
- **Separation of concerns**: Models, services, routes separated
- **Testable**: Services can be unit tested without API client
- **Docker-friendly**: All code in `app/` directory

---

## Summary of Technical Stack

| Component | Decision | Justification |
|-----------|----------|---------------|
| **Hosting** | Self-hosted Docker container | Full control, portable, cost-flexible |
| **Language** | Python 3.11+ | User preference, mature ecosystem |
| **Framework** | FastAPI | High performance, auto-docs, minimal code |
| **Server** | Uvicorn | Standard ASGI server for FastAPI |
| **Testing** | pytest + httpx | Industry standard, async support |
| **Deployment** | Docker multi-stage build | Reproducible, portable, efficient |
| **Config** | Environment variables | 12-factor, Docker-friendly |
| **Data Storage** | Static JSON file in container | Simple, version-controlled |

---

## Updated Technical Context

**Language/Version**: Python 3.11+
**Package Manager**: uv (fast, modern Python package manager)
**Primary Dependencies**: FastAPI, Uvicorn, Pydantic
**Storage**: Static JSON file (in container), images in AWS S3 (base URL via env var)
**Testing**: pytest with httpx for async API testing
**Target Platform**: Docker container (self-hosted on any Docker-capable host)
**Project Type**: Dockerized FastAPI REST API
**Performance Goals**: <1 second response time (in-memory data lookup)
**Constraints**: Minimal resource usage (<100MB RAM), read-only operations
**Scale/Scope**: Low traffic API, single JSON file, 3 endpoints + 1 static HTML page
**Deployment**: `docker build` + `docker run` on any host
**Configuration**: S3_BASE_URL environment variable (via .env or docker -e flag)

---

## Resource Requirements

**Development**:
- Python 3.11+ installed
- uv package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker Desktop (or Docker Engine on Linux)
- 512MB RAM available
- ~500MB disk for Docker image

**Production**:
- Any VPS/server with Docker support
- Minimum: 512MB RAM, 1 vCPU, 5GB disk
- Recommended: 1GB RAM for headroom
- Examples:
  - DigitalOcean $4/month Droplet
  - Linode Nanode $5/month
  - Oracle Cloud free tier (ARM)
  - Home server with Docker

---

## Next Steps

Phase 1 artifacts to update:
1. **quickstart.md**: Docker development workflow and deployment guide
2. **plan.md**: Update Technical Context with Docker + FastAPI
3. **Re-evaluate constitution**: Ensure Docker approach maintains compliance

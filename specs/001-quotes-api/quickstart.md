# Quickstart Guide: Arrested Development Quotes API

**Feature**: 001-quotes-api
**Date**: 2025-10-24
**Audience**: Developers setting up local development or deploying to production

---

## Prerequisites

- **Python**: Version 3.11+ ([download](https://www.python.org/downloads/))
- **uv**: Modern Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
  ```bash
  # Install uv (macOS/Linux)
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Install uv (Windows)
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Docker**: Docker Desktop or Docker Engine ([download](https://docs.docker.com/get-docker/))
- **Git**: For version control

---

## Local Development Setup (without Docker)

### 1. Clone Repository & Setup Virtual Environment

```bash
# Clone repository
git clone https://github.com/yourusername/bluthsapi.git
cd bluthsapi

# Create virtual environment with uv (fast!)
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install production dependencies with uv (10-100x faster than pip)
uv pip install -r requirements.txt

# Install development dependencies (for testing)
uv pip install -r requirements-dev.txt

# Or install all at once
uv pip install -r requirements.txt -r requirements-dev.txt
```

**requirements.txt**:
```
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

**requirements-dev.txt**:
```
pytest==7.4.0
httpx==0.25.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
```

### 3. Create Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**.env**:
```bash
S3_BASE_URL=https://your-bucket.s3.amazonaws.com
HOST=0.0.0.0
PORT=8000
```

### 4. Create Placeholder Data File

Create `app/data/quotes.json`:

```json
{
  "quotes": [
    {
      "id": "quote-001",
      "quote": "There are dozens of us! DOZENS!!!",
      "primarySpeaker": "Tobias"
    }
  ]
}
```

**Note**: This placeholder file with a single Tobias quote will be created as part of this feature implementation. Full quotes dataset will be added in a future feature.

### 5. Start Development Server

```bash
# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Server starts at http://localhost:8000
```

### 6. Test Endpoints

```bash
# Get random quote
curl http://localhost:8000/api/quotes/random

# Get quote by speaker (case-insensitive)
curl http://localhost:8000/api/quotes/gob

# Get meme quote
curl http://localhost:8000/api/quotes/meme

# View auto-generated API docs
open http://localhost:8000/docs

# View alternative docs
open http://localhost:8000/redoc

# View static documentation page
open http://localhost:8000/
```

---

## Local Development Setup (with Docker)

### 1. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies with uv (fast!)
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application code
COPY app/ ./app/
COPY public/ ./public/

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/quotes/random')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create Docker Compose (Optional but Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - S3_BASE_URL=${S3_BASE_URL:-https://example-bucket.s3.amazonaws.com}
      - HOST=0.0.0.0
      - PORT=8000
    env_file:
      - .env
    volumes:
      # Mount code for hot-reload during development
      - ./app:/app/app:ro
      - ./public:/app/public:ro
    restart: unless-stopped
```

### 3. Build and Run with Docker

```bash
# Build image
docker build -t bluthsapi:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e S3_BASE_URL=https://your-bucket.s3.amazonaws.com \
  --name bluthsapi \
  bluthsapi:latest

# Check logs
docker logs -f bluthsapi

# Stop container
docker stop bluthsapi
```

### 4. Or Use Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Running Tests

### Unit Tests (Business Logic)

```bash
# Activate virtual environment first (if not already activated)
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_services.py

# Run with verbose output
pytest -v
```

### Integration Tests (API Endpoints)

```bash
# Tests use FastAPI TestClient (no server needed)
pytest tests/test_api.py -v
```

### Example Test (tests/test_api.py)

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_random_quote():
    response = client.get("/api/quotes/random")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "quote" in data["data"]
    assert "id" in data["data"]

def test_speaker_filter_case_insensitive():
    # Test lowercase
    response = client.get("/api/quotes/gob")
    assert response.status_code == 200

    # Test uppercase
    response = client.get("/api/quotes/GOB")
    assert response.status_code == 200

    # Both should return Gob quotes
    assert response.json()["data"]["primarySpeaker"] == "Gob"

def test_meme_quote():
    response = client.get("/api/quotes/meme")
    assert response.status_code == 200
    data = response.json()
    assert "imageUrl" in data["data"]
    assert data["data"]["imageUrl"].startswith("http")

def test_invalid_speaker():
    response = client.get("/api/quotes/nonexistent")
    assert response.status_code == 404
    assert "error" in response.json()
```

---

## Deployment to Production

### Option 1: Deploy to VPS (DigitalOcean, Linode, etc.)

**Prerequisites**: VPS with Docker installed

```bash
# 1. SSH into your server
ssh user@your-server.com

# 2. Clone repository
git clone https://github.com/yourusername/bluthsapi.git
cd bluthsapi

# 3. Create .env file
nano .env
# Add: S3_BASE_URL=https://your-bucket.s3.amazonaws.com

# 4. Build and run
docker build -t bluthsapi:latest .
docker run -d \
  -p 80:8000 \
  --env-file .env \
  --name bluthsapi \
  --restart unless-stopped \
  bluthsapi:latest

# 5. Verify it's running
curl http://localhost/api/quotes/random
```

### Option 2: Deploy to AWS ECS (Fargate)

```bash
# 1. Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker build -t bluthsapi .
docker tag bluthsapi:latest your-account.dkr.ecr.us-east-1.amazonaws.com/bluthsapi:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/bluthsapi:latest

# 2. Create ECS task definition with:
# - Image: your-account.dkr.ecr.us-east-1.amazonaws.com/bluthsapi:latest
# - Port mappings: 8000:8000
# - Environment: S3_BASE_URL=your-bucket-url

# 3. Create ECS service with Application Load Balancer
```

### Option 3: Deploy to Google Cloud Run

```bash
# 1. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/your-project/bluthsapi

# 2. Deploy to Cloud Run
gcloud run deploy bluthsapi \
  --image gcr.io/your-project/bluthsapi \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars S3_BASE_URL=https://your-bucket.s3.amazonaws.com
```

### Option 4: Deploy to Railway.app (Free Tier Available)

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Dockerfile
5. Add environment variable: `S3_BASE_URL`
6. Deploy automatically

### Option 5: Deploy to Fly.io (Free Tier Available)

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch app (creates fly.toml)
flyctl launch

# 4. Set environment variable
flyctl secrets set S3_BASE_URL=https://your-bucket.s3.amazonaws.com

# 5. Deploy
flyctl deploy
```

---

## Verifying Deployment

### Health Check

```bash
# Test health (should return quote JSON)
curl https://your-domain.com/api/quotes/random

# Expected response:
{
  "data": {
    "id": "quote-001",
    "quote": "I've made a huge mistake.",
    "primarySpeaker": "Gob"
  }
}
```

### Load Testing

```bash
# Install apache bench
# On macOS: brew install httpd
# On Ubuntu: apt-get install apache2-utils

# Test 1000 requests with 10 concurrent
ab -n 1000 -c 10 https://your-domain.com/api/quotes/random
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution**: Ensure you're running from project root and `app/` directory exists:
```bash
python -c "import app.main"  # Should not error
uvicorn app.main:app
```

### Issue: "Port 8000 already in use"

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

### Issue: Docker container immediately exits

**Solution**: Check logs for errors:
```bash
docker logs bluthsapi

# Common issue: quotes.json missing or malformed
# Verify JSON is valid:
python -m json.tool app/data/quotes.json
```

### Issue: "S3_BASE_URL not set" error

**Solution**:
```bash
# For local dev: create .env file
echo "S3_BASE_URL=https://bucket.s3.amazonaws.com" > .env

# For Docker: pass environment variable
docker run -e S3_BASE_URL=https://bucket.s3.amazonaws.com ...
```

### Issue: Case-insensitive matching not working

**Solution**: Verify `services.py` uses `.lower()` comparison:
```python
def filter_by_speaker(quotes, speaker):
    speaker_lower = speaker.lower()
    return [q for q in quotes if q.get("primarySpeaker", "").lower() == speaker_lower]
```

---

## Development Workflow

### Making Changes

1. **Create feature branch**:
   ```bash
   git checkout -b add-new-endpoints
   ```

2. **Make changes** to `app/` files

3. **Test locally**:
   ```bash
   pytest
   uvicorn app.main:app --reload
   ```

4. **Test in Docker** (production parity):
   ```bash
   docker build -t bluthsapi:test .
   docker run -p 8000:8000 -e S3_BASE_URL=test bluthsapi:test
   ```

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add new endpoint for character search"
   git push origin add-new-endpoints
   ```

6. **Deploy to production**: Pull latest on server and rebuild
   ```bash
   git pull origin main
   docker build -t bluthsapi:latest .
   docker stop bluthsapi && docker rm bluthsapi
   docker run -d -p 80:8000 --env-file .env --name bluthsapi bluthsapi:latest
   ```

### Rollback Procedure

```bash
# On server
docker ps -a  # Find previous container ID

# Restart old container
docker start <old-container-id>

# Or rebuild from previous git commit
git checkout <previous-commit>
docker build -t bluthsapi:latest .
docker run ...
```

---

## Performance Tuning

### Optimize Docker Image Size

```dockerfile
# Use alpine base (smaller)
FROM python:3.11-alpine

# Multi-stage build (already in Dockerfile)

# Remove unnecessary files
RUN rm -rf /root/.cache
```

### Enable Uvicorn Workers (for production)

```bash
# In Dockerfile CMD, add workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### Add Caching Headers

```python
# In app/main.py
from fastapi import Response

@app.get("/api/quotes/random")
async def random_quote(response: Response):
    response.headers["Cache-Control"] = "public, max-age=60"
    # ... rest of endpoint
```

---

## Monitoring & Logging

### View Logs

```bash
# Docker
docker logs -f bluthsapi

# Systemd service (if using)
journalctl -u bluthsapi -f
```

### Add Structured Logging

```python
# In app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@app.get("/api/quotes/random")
async def random_quote():
    logger.info("Random quote requested")
    # ...
```

---

## Next Steps

1. **Implement endpoints**: Follow `contracts/openapi.yaml` spec
2. **Write tests**: Use examples in this guide
3. **Create index.html**: Document API for users
4. **Add quotes**: Populate `quotes.json` (future feature)
5. **Deploy**: Choose hosting option and deploy

---

## Helpful Resources

- [uv Documentation](https://docs.astral.sh/uv/) - Fast Python package manager
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [OpenAPI Spec](./contracts/openapi.yaml)
- [Data Model](./data-model.md)

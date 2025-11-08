# Arrested Development Quotes API

A read-only REST API serving memorable quotes from the TV show Arrested Development. Built with FastAPI and deployed as a Docker container.

## Features

- **Random Quote Retrieval**: Get a random quote from the entire collection
- **Character-Filtered Quotes**: Filter quotes by speaker (case-insensitive)
- **Meme Quote Retrieval**: Get quotes with associated images for social media sharing
- **API Documentation**: Human-readable documentation page at root URL
- **Auto-Generated Docs**: FastAPI provides interactive API docs at `/docs` and `/redoc`

## API Endpoints

- `GET /api/quotes/random` - Get a random quote from all available quotes
- `GET /api/quotes/{speaker}` - Get a random quote from a specific character (case-insensitive)
- `GET /api/quotes/meme` - Get a random quote that has an associated image
- `GET /health` - Health check endpoint
- `GET /` - Static HTML documentation page

## Quick Start

### Prerequisites

- Python 3.11+ ([download](https://www.python.org/downloads/))
- uv package manager ([install](https://docs.astral.sh/uv/))
- Docker (for containerized deployment)

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Local Development Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/bluthsapi.git
cd bluthsapi
```

2. **Create virtual environment and install dependencies**:
```bash
# Create virtual environment with uv (fast!)
uv venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

3. **Create environment configuration**:
```bash
# Copy example env file
cp .env.example .env

# Edit .env and set your S3_BASE_URL
nano .env
```

4. **Start the development server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Test the API**:
```bash
# Get random quote
curl http://localhost:8000/api/quotes/random

# Get quote by speaker
curl http://localhost:8000/api/quotes/tobias

# View auto-generated API docs
open http://localhost:8000/docs
```

## Docker Deployment

### Build and Run

```bash
# Build the Docker image
docker build -t bluthsapi:latest .

# Run the container
docker run -d \
  -p 8000:8000 \
  -e S3_BASE_URL=https://your-bucket.s3.amazonaws.com \
  --name bluthsapi \
  --restart unless-stopped \
  bluthsapi:latest

# Check logs
docker logs -f bluthsapi

# Stop container
docker stop bluthsapi
```

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

Configuration is managed through environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `S3_BASE_URL` | Yes | - | Base URL for S3 bucket hosting images |
| `HOST` | No | `0.0.0.0` | Host to bind the server to |
| `PORT` | No | `8000` | Port to run the server on |

Create a `.env` file for local development:

```bash
S3_BASE_URL=https://your-bucket.s3.amazonaws.com
HOST=0.0.0.0
PORT=8000
```

## Testing

### Run Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dev dependencies
uv pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Manual Testing

```bash
# Test all endpoints
curl http://localhost:8000/api/quotes/random
curl http://localhost:8000/api/quotes/gob
curl http://localhost:8000/api/quotes/meme
curl http://localhost:8000/health

# Test case-insensitive speaker matching
curl http://localhost:8000/api/quotes/TOBIAS
curl http://localhost:8000/api/quotes/tobias
```

## Project Structure

```
bluthsapi/
├── app/
│   ├── main.py              # FastAPI app and routes
│   ├── models.py            # Pydantic models
│   ├── services.py          # Business logic
│   ├── config.py            # Configuration
│   └── data/
│       └── quotes.json      # Quote data
├── public/
│   └── index.html           # Static documentation
├── tests/
│   ├── test_api.py          # API endpoint tests
│   ├── test_services.py     # Service logic tests
│   └── conftest.py          # pytest fixtures
├── Dockerfile               # Docker build configuration
├── docker-compose.yml       # Docker Compose setup
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .env.example             # Environment template
└── README.md               # This file
```

## Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: uv (10-100x faster than pip)
- **Framework**: FastAPI
- **Server**: Uvicorn (ASGI server)
- **Validation**: Pydantic
- **Testing**: pytest with httpx
- **Deployment**: Docker
- **Storage**: Static JSON file, images in AWS S3

## AWS Lambda Deployment

This project is configured for serverless deployment to AWS Lambda using AWS SAM (Serverless Application Model).

### Prerequisites

- AWS CLI configured with credentials
- AWS SAM CLI installed
- Docker (for building Lambda packages)

### Deploy to AWS Lambda

```bash
# Build and deploy using SAM
sam build --use-container
sam deploy --guided

# Or use the configured samconfig.toml
sam build --use-container
sam deploy
```

### Budget Controls

The application includes automatic cost controls:
- **Monthly budget**: $20/month
- **Alert at $10**: Email notification
- **Alert at $20**: Email + automatic API shutdown (429 errors)

To set up budget monitoring:

```bash
# 1. Deploy the application stack first (includes shutdown Lambda)
sam deploy

# 2. Run the budget setup script
./aws/setup-budget.sh

# 3. Confirm email subscription (check <operator-email>)
```

If the API is shut down due to budget limits, see [docs/budget-reset.md](docs/budget-reset.md) for recovery instructions.

### Other Deployment Options

#### Option 1: VPS Deployment (DigitalOcean, Linode, etc.)

```bash
# SSH into your server
ssh user@your-server.com

# Clone repository
git clone https://github.com/yourusername/bluthsapi.git
cd bluthsapi

# Build and run with Docker
docker build -t bluthsapi:latest .
docker run -d -p 80:8000 --env-file .env --name bluthsapi bluthsapi:latest
```

#### Option 2: Cloud Container Services

- **AWS ECS/Fargate**: Deploy to Amazon ECS
- **Google Cloud Run**: Serverless container deployment
- **Azure Container Instances**: Run containers on Azure

#### Option 3: Container Platforms (Free Tier Available)

- **Railway.app**: Auto-deploy from GitHub
- **Fly.io**: Global container deployment
- **Render**: Docker-based hosting

See [quickstart.md](specs/001-quotes-api/quickstart.md) for detailed deployment guides.

## API Response Format

### Success Response

```json
{
  "data": {
    "id": "quote-001",
    "quote": "I've made a huge mistake.",
    "primarySpeaker": "Gob",
    "speakers": ["Gob"],
    "context": "Season 1, Episode 1 - Pilot",
    "imageUrl": "https://bucket.s3.amazonaws.com/gob-mistake.jpg"
  }
}
```

### Error Response

```json
{
  "error": "No quotes found for character: Hermano"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `404 Not Found` - No quotes found for requested resource
- `500 Internal Server Error` - Server error (missing quotes file, etc.)

## Performance

- **Response Time**: < 1 second (in-memory data lookup)
- **Resource Usage**: < 100MB RAM
- **Scale**: Designed for low-to-medium traffic
- **Caching**: HTTP cache headers included (max-age=3600)

## Error Handling

The API handles the following error scenarios gracefully:

- **Missing quotes.json**: Server fails to start with clear error message
- **Malformed JSON**: Server fails to start with JSONDecodeError
- **Empty quotes array**: Returns 500 status with appropriate error message
- **No quotes for speaker**: Returns 404 with descriptive message
- **No meme quotes available**: Returns 404 when no images exist

## Development Workflow

### Making Changes

1. Create feature branch: `git checkout -b feature-name`
2. Make changes to `app/` files
3. Run tests: `pytest`
4. Test locally: `uvicorn app.main:app --reload`
5. Test in Docker: `docker build -t bluthsapi:test . && docker run -p 8000:8000 bluthsapi:test`
6. Commit and push: `git add . && git commit -m "Description" && git push`

### Updating Quotes

Edit `app/data/quotes.json`:

```json
{
  "quotes": [
    {
      "id": "quote-001",
      "quote": "There are dozens of us! DOZENS!!!",
      "primarySpeaker": "Tobias"
    },
    {
      "id": "quote-002",
      "quote": "I've made a huge mistake.",
      "primarySpeaker": "Gob",
      "speakers": ["Gob"],
      "context": "Season 1, Episode 1 - Pilot",
      "imageUrl": "gob-mistake.jpg"
    }
  ]
}
```

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

MIT License - See LICENSE file for details

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Docker Documentation](https://docs.docker.com/)
- [API Specification](specs/001-quotes-api/contracts/openapi.yaml)
- [Implementation Plan](specs/001-quotes-api/plan.md)
- [Quickstart Guide](specs/001-quotes-api/quickstart.md)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: This project includes a placeholder quote dataset with a single Tobias quote. A full quotes dataset will be added in a future feature update.

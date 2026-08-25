# Arrested Development Quotes API

A read-only REST API serving memorable quotes from the TV show Arrested Development. Built with FastAPI, deployed to AWS Lambda with AWS SAM, and runnable locally with uvicorn. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

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
git clone https://github.com/bbhart/bluthsapi.git
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

# One-time: the e2e tier drives a real browser via Playwright
playwright install chromium

# Run all tests (starts a local uvicorn server automatically)
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run the API tests only (e2e tests require Playwright: `playwright install chromium`)
pytest tests/api -v
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
│   ├── index.html           # Landing page / API documentation
│   └── prettyquote.html     # Shareable quote-card page
├── tests/
│   ├── api/                 # API endpoint tests
│   ├── e2e/                 # Playwright browser tests
│   ├── pages/               # Page objects for e2e tests
│   └── conftest.py          # pytest fixtures
├── scripts/                 # Twitter-archive → quotes.json pipeline (see scripts/README.md)
├── docs/                    # Architecture and operational docs
├── specs/                   # Feature specs (spec-kit workflow)
├── template.yaml            # AWS SAM / CloudFormation stack
├── samconfig.toml           # SAM deploy configuration
├── .github/workflows/       # CI: tests on PRs, deploy on push to main
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
- **Testing**: pytest with httpx (API tier) and Playwright (e2e tier)
- **Deployment**: AWS Lambda via AWS SAM (GitHub Actions on push to main)
- **Storage**: Static JSON file, images in AWS S3

## AWS Lambda Deployment

This project is configured for serverless deployment to AWS Lambda using AWS SAM (Serverless Application Model).

### Prerequisites

- AWS CLI configured with credentials
- AWS SAM CLI installed
- Docker running (`sam build --use-container` builds inside SAM's image)

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

The application includes automatic cost controls, fully managed by CloudFormation in `template.yaml`:

- **Monthly budget**: $30/month hard cap
- **Alert at $20** (actual spend): Email notification to the address in the `AlertEmail` stack parameter
- **Alert at $30** (actual spend): Email + automatic API shutdown (sets API Gateway throttle to 0; requests return 429)
- **CloudWatch Alarm**: If the shutdown Lambda errors, the alarm publishes to the same SNS topic so you're notified of silent failures.
- **Month-rollover safety net**: On the 1st of each month, a read-only Lambda checks the API Gateway throttle; if still 0, emails a reminder pointing at the recovery doc.

No manual setup script needed — everything is provisioned by `sam deploy`. See [`specs/010-budget-cloudformation/quickstart.md`](specs/010-budget-cloudformation/quickstart.md) for the deploy + verify runbook.

If the API is shut down due to budget limits, see [`docs/budget-reset.md`](docs/budget-reset.md) for recovery instructions.

### Running it somewhere else

There is no container image in this repository. The application is an ordinary
ASGI app, so anywhere that can run `uvicorn app.main:app` will serve it: a VPS
under systemd, a PaaS that builds from `requirements.txt`, or your own image if
you write one. Only `app/` and `public/` are needed at runtime.

## API Response Format

### Success Response

```json
{
  "data": {
    "id": "quote-001",
    "quote": "I've made a huge mistake.",
    "speakers": "GOB",
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
5. Commit and push: `git add . && git commit -m "Description" && git push`

### Updating Quotes

Edit `app/data/quotes.json`:

```json
[
  {
    "id": "quote-001",
    "quote": "There are dozens of us! DOZENS!!!",
    "speakers": "Tobias"
  },
  {
    "id": "quote-002",
    "quote": "I've made a huge mistake.",
    "speakers": "GOB",
    "context": "Season 1, Episode 1 - Pilot",
    "imageUrl": "gob-mistake.jpg"
  },
  {
    "id": "quote-288",
    "quote": "Lucille: You tricked me. Michael: I deceived you, Mom.",
    "speakers": "Lucille,Michael"
  }
]
```

`speakers` is a comma-separated list of everyone who speaks in the quote, in the
order they speak, and `""` when unknown. Every name must appear in
`app/data/list-of-characters.txt` — run `python scripts/normalize_speakers.py --check`
to verify. See [CONTRIBUTING.md](CONTRIBUTING.md#character-names) for why.

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## Contact

Questions, corrections and bug reports are best filed as
[issues](https://github.com/bbhart/bluthsapi/issues). For anything else, DM
[@bluthquotes.lucille2.com](https://bsky.app/profile/bluthquotes.lucille2.com) on Bluesky.

## License

MIT License - See LICENSE file for details

The MIT license covers the code in this repository only. Arrested Development
quotes and imagery are the property of their respective rights-holders (20th
Television / Netflix); this is a non-commercial fan project and claims no
rights over that content.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [API Specification](specs/001-quotes-api/contracts/openapi.yaml)
- [Implementation Plan](specs/001-quotes-api/plan.md)
- [Quickstart Guide](specs/001-quotes-api/quickstart.md)

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---


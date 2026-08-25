# Architecture

bluthsapi is a small, read-only REST API that serves Arrested Development quotes. It runs as a FastAPI application on AWS Lambda behind an API Gateway HTTP API, with a static front-end. The quote database is a hand-maintained JSON file bundled into the Lambda package.

```
app/data/quotes.json ─┐ (bundled at deploy)
                      ▼
api.lucille2.com ──► API Gateway (HTTP API, throttled) ──► Lambda (Mangum + FastAPI) ──► JSON responses
                                                            │
public/ static pages (index, prettyquote) ◄─────────────────┘        media images served from S3
```

## Components

### API application (`app/`)

| File | Role |
|---|---|
| `main.py` | FastAPI app, routes, CORS, static-file mounting, Mangum Lambda handler |
| `services.py` | Quote loading, random selection, speaker/meme filtering |
| `models.py` | Pydantic models (`Quote`, `QuoteResponse`, `ErrorResponse`) |
| `config.py` | Settings via pydantic-settings (`.env` supported locally) |
| `data/quotes.json` | The quote database, bundled into the Lambda package |
| `budget_shutdown.py` | Lambda: throttles API Gateway to 0 when the AWS budget trips |
| `month_rollover_check.py` | Lambda: monthly read-only check that the API was re-enabled |

Endpoints:

- `GET /health` — health check with quote count
- `GET /api/quotes/random` — random quote
- `GET /api/quotes/meme` — random quote that has an image
- `GET /api/quotes/{speaker}` — random quote by character (case-insensitive)
- `GET /` and other paths — static files from `public/`

Quotes load once at startup (Lambda cold start) into an in-memory list; there is no database.

### Static front-end (`public/`)

Pure HTML/CSS/JS, no build step. `index.html` is the landing page; `prettyquote.html` renders a shareable quote card using the API. Served by FastAPI `StaticFiles` (and therefore through Lambda).

### Data tooling (`scripts/`)

`quotes.json` was originally seeded from an export of the @bluthquotes Twitter
archive. That was a one-time import and its tooling has been removed; the file is
now maintained by hand and by pull request.

What remains keeps the speaker data honest:

- `speaker_names.py` — canonical character registry, alias resolution, and the
  parser that reads speakers out of quote text
- `normalize_speakers.py` — normalizes the `speakers` field and regenerates
  `app/data/list-of-characters.txt`; `--check` runs in CI
- `quote_id_generator.py` — next sequential `quote-N` id

Standard library only; see `scripts/README.md`.

### Infrastructure (`template.yaml`, SAM)

Single CloudFormation/SAM stack (`bluths-api`, us-east-1) containing:

- **BluthsApiFunction** — the API Lambda (python3.13, 512 MB, reserved concurrency 3, `live` alias with auto-published versions for rollback)
- **BluthsHttpApi** — API Gateway HTTP API, `prod` stage, global throttling via `GlobalRateLimit`, access logs to CloudWatch (7-day retention)
- **Custom domain** — `api.lucille2.com` (ACM cert parameter; optional via the `HasCertificate` condition)
- **Cost controls** (feature 010):
  - `AWS::Budgets::Budget` with $20 warning and $30 shutdown thresholds
  - Two SNS topics: alerts (email) and shutdown-trigger (invokes `budget_shutdown` Lambda)
  - CloudWatch alarm on shutdown-Lambda errors
  - EventBridge monthly schedule for `month_rollover_check`
- Narrowly-scoped IAM roles per Lambda; `iam-policy.json` is the deploy user's policy (resources scoped to `bluths-api-*`)

Media images live in a separate, pre-existing S3 bucket; the API only prefixes image keys with `S3_BASE_URL`.

### Deployment (`.github/workflows/deploy.yml`)

Push to `main` triggers: validate `quotes.json` → check Lambda package size → run tests → `sam build --use-container` → package to the artifact S3 bucket → `sam deploy` → smoke-test `/health` and `/api/quotes/random` → roll back the Lambda alias on failure. Credentials come from GitHub Actions secrets.

Local development uses `uvicorn` directly (see README).

### Tests (`tests/`)

- `tests/api/` — endpoint tests (pytest + FastAPI TestClient)
- `tests/e2e/` + `tests/pages/` — Playwright page-object tests for the static pages

### Specs (`specs/`, `.specify/`)

The project is developed with a spec-driven workflow ([spec-kit](https://github.com/github/spec-kit)); each numbered directory under `specs/` documents one feature's requirements, plan, and tasks. These are historical design records, not runtime code.

# bluthsapi Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-24

## Active Technologies
- Python 3.11+ (matches existing project) + Standard library (json, pathlib, urllib.request), no external packages needed for core functionality (002-tweet-to-quote-conversion)
- File-based (JSON) - reads etc/tweets.js, writes to staging and app/data/quotes.json (002-tweet-to-quote-conversion)
- Python 3.11+ (matches existing project) + Standard library only (difflib.SequenceMatcher, string, json, pathlib) (003-tweet-filtering)
- File-based (JSON) - reads/writes etc/staging/tweets_staging.json (003-tweet-filtering)
- Python 3.11+ (matches existing project - see requirements.txt) + FastAPI 0.104.0, Mangum (ASGI-to-Lambda adapter), AWS SAM CLI, python-dotenv (for .env support) (005-aws-lambda-deployment)
- File-based (quotes.json bundled in Lambda package, media files on S3 as currently configured) (005-aws-lambda-deployment)
- HTML5, CSS3 (static files served by FastAPI) + None (pure HTML/CSS, no build tools or frameworks) (006-index-styling)
- Static files in `public/` directory (served by FastAPI StaticFiles) (006-index-styling)

- (001-quotes-api)

## Project Structure

```text
src/
tests/
```

## Commands

# Add commands for 

## Code Style

: Follow standard conventions

## Recent Changes
- 006-index-styling: Added HTML5, CSS3 (static files served by FastAPI) + None (pure HTML/CSS, no build tools or frameworks)
- 005-aws-lambda-deployment: Added Python 3.11+ (matches existing project - see requirements.txt) + FastAPI 0.104.0, Mangum (ASGI-to-Lambda adapter), AWS SAM CLI, python-dotenv (for .env support)
- 003-tweet-filtering: Added Python 3.11+ (matches existing project) + Standard library only (difflib.SequenceMatcher, string, json, pathlib)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

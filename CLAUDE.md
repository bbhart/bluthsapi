# bluthsapi Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-24

## Active Technologies
- Python 3.11+ (matches existing project) + Standard library (json, pathlib, urllib.request), no external packages needed for core functionality (002-tweet-to-quote-conversion)
- File-based (JSON) - reads etc/tweets.js, writes to staging and app/data/quotes.json (002-tweet-to-quote-conversion)
- Python 3.11+ (matches existing project) + Standard library only (difflib.SequenceMatcher, string, json, pathlib) (003-tweet-filtering)
- File-based (JSON) - reads/writes etc/staging/tweets_staging.json (003-tweet-filtering)

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
- 003-tweet-filtering: Added Python 3.11+ (matches existing project) + Standard library only (difflib.SequenceMatcher, string, json, pathlib)
- 002-tweet-to-quote-conversion: Added Python 3.11+ (matches existing project) + Standard library (json, pathlib, urllib.request), no external packages needed for core functionality

- 001-quotes-api: Added

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

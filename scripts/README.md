# Tweet to Quote Conversion Scripts

Utility scripts for converting Twitter archive data to application-ready quotes.

## Overview

This directory contains Python scripts that process tweet data through a three-stage pipeline:

1. **Extract** - Parse tweets.js and create human-reviewable staging file
2. **Review** - Manual curation of staging file (add/remove/edit entries)
3. **Convert** - Transform reviewed staging into quotes.json format
4. **Download** (Optional) - Download tweet media files for S3 upload

## Quick Start

For detailed setup and usage instructions, see the [complete quickstart guide](../specs/002-tweet-to-quote-conversion/quickstart.md).

### Basic Workflow

```bash
# 1. Extract tweets to staging file
python3 scripts/extract_tweets.py --verbose

# 2. Review and edit staging file (manual step)
# Edit etc/staging/tweets_staging.json in your text editor
# - Remove unwanted entries
# - Edit text content
# - Add "exclude": true to skip entries

# 3. Validate staging file (optional but recommended)
python3 scripts/validate_staging.py

# 4. Convert staging to quotes.json
python3 scripts/convert_to_quotes.py --verbose

# 5. Download media files (optional)
python3 scripts/download_media.py --verbose --skip-existing
```

## Scripts

### extract_tweets.py

Extracts tweets from Twitter archive to staging file.

**Usage:**
```bash
python3 scripts/extract_tweets.py [options]
```

**Options:**
- `--source PATH` - Path to tweets.js (default: etc/tweets.js)
- `--output PATH` - Path for staging output (default: etc/staging/tweets_staging.json)
- `-v, --verbose` - Enable verbose progress output

**Example:**
```bash
python3 scripts/extract_tweets.py --verbose
```

### validate_staging.py

Validates staging file JSON syntax and schema.

**Usage:**
```bash
python3 scripts/validate_staging.py [file]
```

**Example:**
```bash
python3 scripts/validate_staging.py etc/staging/tweets_staging.json
```

### convert_to_quotes.py

Converts reviewed staging file to quotes.json format.

**Usage:**
```bash
python3 scripts/convert_to_quotes.py [options]
```

**Options:**
- `--staging PATH` - Path to staging file (default: etc/staging/tweets_staging.json)
- `--quotes PATH` - Path to quotes output (default: app/data/quotes.json)
- `--dry-run` - Preview conversion without writing
- `-v, --verbose` - Enable verbose progress output

**Example:**
```bash
# Preview conversion
python3 scripts/convert_to_quotes.py --dry-run --verbose

# Perform conversion
python3 scripts/convert_to_quotes.py --verbose
```

### download_media.py

Downloads tweet media files to local folder.

**Usage:**
```bash
python3 scripts/download_media.py [options]
```

**Options:**
- `--staging PATH` - Path to staging file (default: etc/staging/tweets_staging.json)
- `--output-dir PATH` - Directory for downloads (default: media/tweet_images)
- `--skip-existing` - Skip files that already exist
- `--timeout SECONDS` - HTTP timeout (default: 30)
- `-v, --verbose` - Enable verbose progress output

**Example:**
```bash
python3 scripts/download_media.py --verbose --skip-existing
```

## Utility Modules

### tweet_parser.py

Parses tweets.js JavaScript wrapper and extracts JSON data.

**Key Function:**
```python
parse_tweets_file(file_path: str | Path) -> list[dict]
```

### speaker_detector.py

Detects speaker names from "Name:" prefix pattern in text.

**Key Function:**
```python
detect_speaker(text: str) -> tuple[str | None, str]
# Returns (speaker_name, remaining_text) or (None, original_text)
```

**Examples:**
- `"Michael: I've made a huge mistake"` → `("Michael", "I've made a huge mistake")`
- `"George Michael: Her?"` → `("George Michael", "Her?")`
- `"No speaker here"` → `(None, "No speaker here")`

### quote_id_generator.py

Generates unique quote IDs with collision detection.

**Key Function:**
```python
get_next_quote_id(existing_quotes: list[dict]) -> str
# Returns formatted ID like "quote-1", "quote-42"
```

### staging_validator.py

Validates staging file structure and schema.

**Key Function:**
```python
validate_staging_file(file_path: str | Path) -> tuple[bool, list[str]]
# Returns (is_valid, error_messages)
```

## Data Flow

```
etc/tweets.js (Twitter archive)
    ↓ extract_tweets.py
etc/staging/tweets_staging.json
    ↓ (manual review & editing)
etc/staging/tweets_staging.json (reviewed)
    ↓ convert_to_quotes.py
app/data/quotes.json
```

Media download runs independently:
```
etc/staging/tweets_staging.json
    ↓ download_media.py
media/tweet_images/*.jpg
media/download_log.json
```

## Requirements

- Python 3.11+
- No external dependencies (uses standard library only)

## File Locations

- **Source**: `etc/tweets.js` - Twitter archive export
- **Staging**: `etc/staging/tweets_staging.json` - Intermediate format (gitignored)
- **Quotes**: `app/data/quotes.json` - Application data
- **Media**: `media/tweet_images/` - Downloaded images (gitignored)
- **Logs**: `media/download_log.json` - Download status (gitignored)

## Error Handling

All scripts use standard exit codes:
- `0` - Success
- `1` - General error (file not found, permission error)
- `2` - Invalid data (corrupted JSON, invalid format)

Errors are printed to stderr with descriptive messages.

## Speaker Extraction

The conversion script automatically detects speaker names from tweet text:

- Pattern: `Name: text content`
- Matches: Alphabetical characters and spaces only
- Preserves exact capitalization
- Strips speaker prefix from quote text

**Examples:**
- `"Lucille: I don't understand the question"` → Speaker: "Lucille", Quote: "I don't understand the question"
- `"GOB: I've made a huge tiny mistake"` → Speaker: "GOB", Quote: "I've made a huge tiny mistake"
- `"R2D2: Beep"` → No match (contains numbers)

## Common Issues

### Extraction fails with "Invalid tweets.js format"

The tweets.js file must have this structure:
```javascript
window.YTD.tweets.part0 = [...json array...];
```

### Validation fails with JSON syntax errors

Edit the staging file carefully. Common issues:
- Missing commas between entries
- Trailing commas in arrays/objects
- Unclosed quotes or brackets

Use `python3 -m json.tool < file.json` to check JSON syntax.

### Download fails with 403/404 errors

Some media URLs may no longer be available. The script logs errors but continues downloading remaining files. Check `media/download_log.json` for details.

## See Also

- [Full Quickstart Guide](../specs/002-tweet-to-quote-conversion/quickstart.md)
- [Data Model Documentation](../specs/002-tweet-to-quote-conversion/data-model.md)
- [JSON Schemas](../specs/002-tweet-to-quote-conversion/contracts/schemas.md)

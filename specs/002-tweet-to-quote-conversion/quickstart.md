# Quickstart: Tweet to Quote Conversion

**Feature**: 002-tweet-to-quote-conversion
**Date**: 2025-10-24

## Overview

This guide walks you through converting Twitter archive data to application-ready quotes in three simple steps: extract, review, convert. Optional fourth step downloads associated media.

**Estimated Time**: 15-30 minutes for typical tweet archive

---

## Prerequisites

### Required Files
- `etc/tweets.js` - Your Twitter archive export file
- `app/data/quotes.json` - Target quotes file (will be created if missing)

### System Requirements
- Python 3.11+ (already installed in project)
- Text editor for manual review (any editor: VS Code, nano, vim, etc.)
- Internet connection (for media download only)

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.11 or higher

# Verify source file exists
ls -lh etc/tweets.js

# Check target directory is writable
touch app/data/test && rm app/data/test && echo "✓ Writable"
```

---

## Quick Start (3 Steps)

### Step 1: Extract Tweets to Staging File

Extract tweets from your Twitter archive into a human-reviewable format.

```bash
# Run extraction script
python3 scripts/extract_tweets.py

# Expected output:
# Extracting tweets from etc/tweets.js...
#   Processed 100 tweets...
#   Processed 200 tweets...
# ✓ Extraction complete: 245 tweets → etc/staging/tweets_staging.json
#
# Summary:
#   Total extracted: 245
#   Retweets (flagged): 45
#   With media: 78
```

**What it does**:
- Reads `etc/tweets.js`
- Filters out empty tweets
- Flags retweets automatically
- Extracts media URLs
- Creates `etc/staging/tweets_staging.json`

**Common Issues**:
- `File not found: etc/tweets.js` → Place your Twitter archive file in `etc/` directory
- `Invalid JSON` → Archive file may be corrupted, verify it's a valid Twitter export

---

### Step 2: Review and Edit Staging File

Open the staging file and manually review/edit quotes before final conversion.

```bash
# Open in your preferred editor
code etc/staging/tweets_staging.json          # VS Code
nano etc/staging/tweets_staging.json          # nano
vim etc/staging/tweets_staging.json           # vim
```

**What to look for**:

✅ **Keep**: Good quotes you want in the app
❌ **Remove**: Delete entire entry or set `"exclude": true`
✏️ **Edit**: Modify `"text"` field if needed (fix typos, shorten, etc.)

**Example Edits**:

```json
{
  "tweets": [
    {
      "tweet_id": "123",
      "text": "Great quote to keep!",
      "is_retweet": false,
      // Keep this one - no changes needed
    },
    {
      "tweet_id": "456",
      "text": "Boring tweet with just a URL",
      "is_retweet": false,
      "exclude": true  // ← Add this to skip during conversion
    },
    {
      "tweet_id": "789",
      "text": "Quote with a small typo here",
      "is_retweet": false,
      // Edit "typo" → "type" in the text field
    }
  ]
}
```

**Tips**:
- Retweets (`"is_retweet": true`) are automatically excluded, but you can review them
- Add `"notes": "your comment"` for context (not included in final output)
- Tweets with media show URLs in `"media_urls"` array
- Save file when done (must be valid JSON)

**Validate JSON** (optional):
```bash
python3 -m json.tool etc/staging/tweets_staging.json > /dev/null && echo "✓ Valid JSON"
```

---

### Step 3: Convert to Final Quotes Format

Convert the reviewed staging file to application-ready quotes.

```bash
# Run conversion script
python3 scripts/convert_to_quotes.py

# Expected output:
# Loading existing quotes from app/data/quotes.json...
#   Found 1 existing quote, highest ID: quote-001
#   Starting new IDs from: quote-002
#
# Converting staging file...
#   Skipped 45 retweets
#   Skipped 12 manually excluded entries
#   Converting 188 quotes...
#
# ✓ Conversion complete: 188 new quotes added
#
# Output: app/data/quotes.json
#   Total quotes now: 189 (was 1, added 188)
```

**What it does**:
- Reads `etc/staging/tweets_staging.json`
- Loads existing `app/data/quotes.json` to find highest ID
- Skips retweets and excluded entries
- Generates unique quote IDs (quote-002, quote-003, ...)
- Appends new quotes to `app/data/quotes.json`
- Preserves text exactly from staging file

**Common Issues**:
- `Invalid staging file` → Check JSON syntax from Step 2
- `ID collision detected` → Script auto-increments, this is informational
- `Quotes file not writable` → Check permissions on `app/data/`

**Verify Output**:
```bash
# Check quotes file is valid JSON
python3 -m json.tool app/data/quotes.json > /dev/null && echo "✓ Valid"

# Count total quotes
python3 -c "import json; data = json.load(open('app/data/quotes.json')); print(f'Total quotes: {len(data[\"quotes\"])}')"

# View last few quotes added
tail -20 app/data/quotes.json
```

---

## Optional: Download Media (Step 4)

Download tweet images/videos to local storage for S3 upload.

```bash
# Run media download script
python3 scripts/download_media.py

# Expected output:
# Downloading media from staging file...
#   Found 78 tweets with media (125 total files)
#
#   [1/125] Downloading 1234567890_0.jpg... ✓
#   [2/125] Downloading 1234567891_0.jpg... ✓
#   [3/125] Skipped 1234567892_0.jpg (already exists)
#   [4/125] Downloading 1234567893_0.jpg... ✗ HTTP 404
#   ...
#
# ✓ Download complete
#
# Summary:
#   Total: 125
#   Success: 98
#   Skipped: 15 (already downloaded)
#   Errors: 12 (logged below)
#
# Failed downloads:
#   - https://pbs.twimg.com/media/invalid.jpg → HTTP 404: Not Found
#   - https://pbs.twimg.com/media/deleted.jpg → HTTP 403: Forbidden
#
# Output directory: media/tweet_images/
# Download log: media/download_log.json
```

**What it does**:
- Reads media URLs from staging file
- Downloads each file to `media/tweet_images/`
- Names files: `<tweet-id>_<index>.<ext>`
- Skips files that already exist (matches size)
- Logs errors but continues processing
- Creates `media/download_log.json` with details

**Post-Download**:
```bash
# List downloaded files
ls -lh media/tweet_images/

# Check download log for details
cat media/download_log.json | python3 -m json.tool

# Upload to S3 (example - customize for your setup)
aws s3 sync media/tweet_images/ s3://your-bucket/images/
```

**Common Issues**:
- `HTTP 404` errors → Original tweet media deleted/unavailable (expected for some old tweets)
- `Connection timeout` → Retry script, it will skip successfully downloaded files
- `Permission denied` → Check write access to `media/` directory

---

## Complete Workflow Example

```bash
# Full workflow from start to finish
cd /path/to/bluthsapi

# 1. Extract
python3 scripts/extract_tweets.py

# 2. Review (open in editor, make changes, save)
code etc/staging/tweets_staging.json

# 3. Convert
python3 scripts/convert_to_quotes.py

# 4. Download media (optional)
python3 scripts/download_media.py

# 5. Verify
python3 -m json.tool app/data/quotes.json > /dev/null && echo "✓ All done!"
```

---

## Script Options & Flags

### extract_tweets.py

```bash
python3 scripts/extract_tweets.py [OPTIONS]

Options:
  --source FILE       Source tweets file (default: etc/tweets.js)
  --output FILE       Output staging file (default: etc/staging/tweets_staging.json)
  --include-retweets  Include retweets in staging (default: flag them but include)
  --verbose, -v       Show detailed progress
  --help, -h          Show help message
```

### convert_to_quotes.py

```bash
python3 scripts/convert_to_quotes.py [OPTIONS]

Options:
  --staging FILE      Staging file to convert (default: etc/staging/tweets_staging.json)
  --quotes FILE       Target quotes file (default: app/data/quotes.json)
  --dry-run           Show what would be converted without writing
  --verbose, -v       Show detailed progress
  --help, -h          Show help message
```

### download_media.py

```bash
python3 scripts/download_media.py [OPTIONS]

Options:
  --staging FILE      Staging file with media URLs (default: etc/staging/tweets_staging.json)
  --output-dir DIR    Media output directory (default: media/tweet_images/)
  --skip-existing     Skip files that already exist (default: true)
  --timeout SECONDS   Download timeout (default: 30)
  --verbose, -v       Show detailed progress
  --help, -h          Show help message
```

---

## Troubleshooting

### "No tweets extracted"

**Cause**: Source file empty or all tweets filtered out

**Fix**:
```bash
# Check source file
head -20 etc/tweets.js

# Verify it contains "window.YTD.tweets.part0 = [...]"
grep "YTD.tweets" etc/tweets.js
```

### "Quote ID collision"

**Cause**: Existing quotes.json has gaps in numbering

**Fix**: Script auto-increments to next available ID. This is expected behavior and safe.

### "Staging file not found"

**Cause**: Step 1 (extraction) not completed or failed

**Fix**:
```bash
# Re-run extraction
python3 scripts/extract_tweets.py

# Check output directory exists
mkdir -p etc/staging
```

### "Invalid JSON" after manual edit

**Cause**: Syntax error introduced during manual review

**Fix**:
```bash
# Validate and show error location
python3 -m json.tool etc/staging/tweets_staging.json

# Common fixes:
# - Remove trailing comma in last array element
# - Escape quotes in text: "He said \"hello\""
# - Ensure proper JSON structure
```

---

## Next Steps

After successful conversion:

1. **Test the API** with new quotes:
   ```bash
   # Start the API
   python3 app/main.py

   # Get a random quote
   curl http://localhost:8000/quotes/random
   ```

2. **Upload media to S3** (if downloaded):
   ```bash
   aws s3 sync media/tweet_images/ s3://your-bucket/images/
   ```

3. **Update quote speakers** (separate curation process):
   - Edit `app/data/quotes.json` manually
   - Or build a separate speaker assignment tool

4. **Run additional conversions**:
   - Archive the staging file: `mv etc/staging/tweets_staging.json etc/staging/tweets_staging_2024.json`
   - Process another Twitter archive by repeating Steps 1-3

---

## Files & Directories Reference

```text
etc/
├── tweets.js                       # INPUT: Twitter archive (you provide)
└── staging/
    └── tweets_staging.json         # INTERMEDIATE: Review and edit this

app/data/
└── quotes.json                     # OUTPUT: Final application data

media/
├── tweet_images/                   # OUTPUT: Downloaded media files
│   ├── <tweet-id>_0.jpg
│   ├── <tweet-id>_1.jpg
│   └── ...
└── download_log.json               # OUTPUT: Media download status log

scripts/
├── extract_tweets.py               # Step 1 script
├── convert_to_quotes.py            # Step 3 script
└── download_media.py               # Step 4 script
```

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section above
2. Review [data-model.md](./data-model.md) for data structure details
3. Consult [contracts/schemas.md](./contracts/schemas.md) for JSON validation
4. See [plan.md](./plan.md) for implementation details

---

**Last Updated**: 2025-10-24
**Feature Branch**: `002-tweet-to-quote-conversion`

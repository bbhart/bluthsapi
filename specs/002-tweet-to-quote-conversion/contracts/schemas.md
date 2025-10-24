# Data Schemas: Tweet to Quote Conversion

**Feature**: 002-tweet-to-quote-conversion
**Date**: 2025-10-24
**Version**: 1.0

## Overview

This document defines JSON schemas for all data formats in the conversion pipeline. These schemas serve as contracts for validation and documentation.

---

## 1. Staging File Schema

**File**: `etc/staging/tweets_staging.json`
**Purpose**: Human-reviewable intermediate format

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Tweet Staging File",
  "type": "object",
  "required": ["metadata", "tweets"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["extracted_at", "source_file", "total_extracted", "version"],
      "properties": {
        "extracted_at": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp when extraction occurred"
        },
        "source_file": {
          "type": "string",
          "description": "Path to source tweets.js file"
        },
        "total_extracted": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of tweet entries extracted"
        },
        "version": {
          "type": "string",
          "pattern": "^\\d+\\.\\d+$",
          "description": "Schema version (e.g., '1.0')"
        }
      }
    },
    "tweets": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/StagingEntry"
      }
    }
  },
  "definitions": {
    "StagingEntry": {
      "type": "object",
      "required": ["tweet_id", "text", "created_at", "is_retweet", "favorite_count", "retweet_count", "media_urls"],
      "properties": {
        "tweet_id": {
          "type": "string",
          "description": "Original Twitter tweet ID"
        },
        "text": {
          "type": "string",
          "minLength": 1,
          "description": "Tweet text content (exact copy from source)"
        },
        "created_at": {
          "type": "string",
          "description": "Tweet creation timestamp (preserved as-is from Twitter archive, typically RFC 2822 format)"
        },
        "is_retweet": {
          "type": "boolean",
          "description": "True if text starts with 'RT @'"
        },
        "favorite_count": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of likes"
        },
        "retweet_count": {
          "type": "integer",
          "minimum": 0,
          "description": "Number of retweets"
        },
        "media_urls": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uri",
            "pattern": "^https://"
          },
          "description": "Array of media URLs from tweet"
        },
        "notes": {
          "type": "string",
          "description": "Optional curator notes (not used in conversion)"
        },
        "exclude": {
          "type": "boolean",
          "description": "If true, skip this entry during conversion"
        }
      }
    }
  }
}
```

### Example

```json
{
  "metadata": {
    "extracted_at": "2025-10-24T10:30:00Z",
    "source_file": "etc/tweets.js",
    "total_extracted": 3,
    "version": "1.0"
  },
  "tweets": [
    {
      "tweet_id": "1753998433135002100",
      "text": "IT'S A WONDERFUL RESTAURANT!!",
      "created_at": "Sun Feb 04 04:26:28 +0000 2024",
      "is_retweet": false,
      "favorite_count": 780,
      "retweet_count": 24,
      "media_urls": [
        "https://pbs.twimg.com/media/GFd0PIwakAAv6S-.jpg"
      ]
    },
    {
      "tweet_id": "1753562991294099892",
      "text": "RT @bluthquotes: Whoa, whoa, whoa. There's still plenty of meat on that bone...",
      "created_at": "Fri Feb 02 23:36:11 +0000 2024",
      "is_retweet": true,
      "favorite_count": 0,
      "retweet_count": 0,
      "media_urls": []
    },
    {
      "tweet_id": "1697639616361242973",
      "text": "If I may take off my acting pants for a moment and pull my analrapist stocking over my head...",
      "created_at": "Fri Sep 01 15:56:39 +0000 2023",
      "is_retweet": false,
      "favorite_count": 912,
      "retweet_count": 50,
      "media_urls": [],
      "notes": "Great quote about Tobias",
      "exclude": false
    }
  ]
}
```

---

## 2. Quote File Schema

**File**: `app/data/quotes.json`
**Purpose**: Application-ready quote data (API source)

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Quote Collection",
  "type": "object",
  "required": ["quotes"],
  "properties": {
    "quotes": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/QuoteRecord"
      }
    }
  },
  "definitions": {
    "QuoteRecord": {
      "type": "object",
      "required": ["id", "quote", "primarySpeaker"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^quote-\\d+$",
          "description": "Unique quote identifier (format: quote-XXX)"
        },
        "quote": {
          "type": "string",
          "minLength": 1,
          "description": "The quote text"
        },
        "primarySpeaker": {
          "type": ["string", "null"],
          "description": "Speaker name extracted from 'Name:' prefix pattern, or empty/null if no match"
        },
        "imageUrl": {
          "type": ["string", "null"],
          "format": "uri",
          "description": "Optional media URL associated with quote"
        }
      }
    }
  }
}
```

### Example

```json
{
  "quotes": [
    {
      "id": "quote-1",
      "quote": "There are dozens of us! DOZENS!!!",
      "primarySpeaker": "Tobias"
    },
    {
      "id": "quote-2",
      "quote": "IT'S A WONDERFUL RESTAURANT!!",
      "primarySpeaker": "",
      "imageUrl": "https://pbs.twimg.com/media/GFd0PIwakAAv6S-.jpg"
    },
    {
      "id": "quote-3",
      "quote": "If I may take off my acting pants for a moment and pull my analrapist stocking over my head...",
      "primarySpeaker": null,
      "imageUrl": null
    }
  ]
}
```

---

## 3. Media Download Log Schema

**File**: `media/download_log.json` (generated by download script)
**Purpose**: Track media download status and errors

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Media Download Log",
  "type": "object",
  "required": ["downloaded_at", "summary", "downloads"],
  "properties": {
    "downloaded_at": {
      "type": "string",
      "format": "date-time",
      "description": "When download process ran"
    },
    "summary": {
      "type": "object",
      "required": ["total", "success", "skipped", "error"],
      "properties": {
        "total": {
          "type": "integer",
          "minimum": 0
        },
        "success": {
          "type": "integer",
          "minimum": 0
        },
        "skipped": {
          "type": "integer",
          "minimum": 0
        },
        "error": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "downloads": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/DownloadRecord"
      }
    }
  },
  "definitions": {
    "DownloadRecord": {
      "type": "object",
      "required": ["source_url", "filename", "tweet_id", "status"],
      "properties": {
        "source_url": {
          "type": "string",
          "format": "uri"
        },
        "filename": {
          "type": "string",
          "description": "Local filename (relative to media directory)"
        },
        "tweet_id": {
          "type": "string",
          "description": "Associated tweet ID"
        },
        "status": {
          "type": "string",
          "enum": ["success", "skipped", "error"]
        },
        "file_size_bytes": {
          "type": "integer",
          "minimum": 0,
          "description": "Downloaded file size (if success/skipped)"
        },
        "error_message": {
          "type": "string",
          "description": "Error details (if status = error)"
        }
      }
    }
  }
}
```

### Example

```json
{
  "downloaded_at": "2025-10-24T11:00:00Z",
  "summary": {
    "total": 5,
    "success": 3,
    "skipped": 1,
    "error": 1
  },
  "downloads": [
    {
      "source_url": "https://pbs.twimg.com/media/GFd0PIwakAAv6S-.jpg",
      "filename": "1753998433135002100_0.jpg",
      "tweet_id": "1753998433135002100",
      "status": "success",
      "file_size_bytes": 245678
    },
    {
      "source_url": "https://pbs.twimg.com/media/F5XGMu_XMAAdbEI.jpg",
      "filename": "1699482427121377321_0.jpg",
      "tweet_id": "1699482427121377321",
      "status": "skipped",
      "file_size_bytes": 189234
    },
    {
      "source_url": "https://pbs.twimg.com/media/invalid.jpg",
      "filename": "1234567890_0.jpg",
      "tweet_id": "1234567890",
      "status": "error",
      "error_message": "HTTP Error 404: Not Found"
    }
  ]
}
```

---

## Validation Tools

### Python Validation (using jsonschema)

```python
from jsonschema import validate, ValidationError
import json

def validate_staging_file(data):
    """Validate staging file against schema."""
    schema = {
        # Schema from section 1 above
    }
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)

# Usage
with open('etc/staging/tweets_staging.json') as f:
    data = json.load(f)
    valid, error = validate_staging_file(data)
    if not valid:
        print(f"Validation error: {error}")
```

### Command-Line Validation

```bash
# Install jsonschema CLI (if not using Python validation)
pip install check-jsonschema

# Validate staging file
check-jsonschema --schemafile staging_schema.json etc/staging/tweets_staging.json

# Validate quotes file
check-jsonschema --schemafile quotes_schema.json app/data/quotes.json
```

---

## Schema Evolution Guidelines

### Adding Fields (Backward Compatible)

1. Add new field as optional in schema
2. Provide default value in code if field missing
3. Update `version` in metadata (minor bump: 1.0 → 1.1)

### Changing Required Fields (Breaking Change)

1. Create new schema version (major bump: 1.0 → 2.0)
2. Implement migration script for existing data
3. Update all scripts to handle both versions during transition

### Deprecating Fields

1. Mark as deprecated in schema description
2. Continue accepting for 1-2 versions
3. Remove in major version bump with migration path

---

## Field Format Standards

### Timestamps
- **Format**: ISO 8601 with UTC timezone
- **Example**: `"2025-10-24T10:30:00Z"`
- **Python**: `datetime.utcnow().isoformat() + 'Z'`

### URLs
- **Format**: HTTPS only
- **Pattern**: `^https://`
- **Validation**: Must be well-formed URI

### Quote IDs
- **Format**: `quote-` prefix + numeric suffix
- **Pattern**: `^quote-\\d+$`
- **Example**: `"quote-001"`, `"quote-123"`

### Tweet IDs
- **Format**: Numeric string (Twitter's format)
- **Example**: `"1753998433135002100"`
- **Note**: Preserve as string to avoid integer overflow

---

## Testing Schemas

### Valid Test Cases

**Minimal Staging Entry**:
```json
{
  "tweet_id": "123",
  "text": "Test",
  "created_at": "2025-10-24T10:00:00Z",
  "is_retweet": false,
  "favorite_count": 0,
  "retweet_count": 0,
  "media_urls": []
}
```

**Minimal Quote Record**:
```json
{
  "id": "quote-1",
  "quote": "Test",
  "primarySpeaker": ""
}
```

(Note: ID format uses no zero-padding: "quote-1", "quote-42", not "quote-001")

### Invalid Test Cases

**Missing Required Field**:
```json
{
  "tweet_id": "123",
  "text": "Test"
  // Missing: created_at, is_retweet, counts, media_urls
}
```

**Invalid Quote ID Format**:
```json
{
  "id": "invalid-id",  // Should be "quote-123"
  "quote": "Test",
  "primarySpeaker": ""
}
```

**Non-HTTPS Media URL**:
```json
{
  "media_urls": ["http://example.com/image.jpg"]  // Should be https://
}
```

---

## References

- [JSON Schema Specification](https://json-schema.org/)
- [Twitter API Documentation](https://developer.twitter.com/en/docs/twitter-api) (for source data format understanding)
- Data Model: [data-model.md](../data-model.md)
- Implementation Plan: [plan.md](../plan.md)

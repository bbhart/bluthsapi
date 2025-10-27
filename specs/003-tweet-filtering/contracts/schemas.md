# API Contracts: Smart Tweet Staging Filter

**Feature**: 003-tweet-filtering
**Date**: 2025-10-27
**Phase**: Phase 1 - Design

## Overview

This feature is a command-line utility script, not an HTTP API. The "contracts" here define the input/output schemas and configuration interface that the script must adhere to.

## Command-Line Interface

### Script Invocation

```bash
python etc/scripts/filter_tweets.py [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--input` | path | `etc/staging/tweets_staging.json` | Input staging file path |
| `--output` | path | (overwrites input) | Output file path |
| `--report` | path | (stdout) | Report output file path |
| `--similarity-threshold` | float | `0.85` | Similarity ratio 0.0-1.0 for duplicate detection |
| `--min-favorites` | int | `100` | Minimum favorite count |
| `--min-retweets` | int | `5` | Minimum retweet count |
| `--help` | flag | - | Show help message |
| `--version` | flag | - | Show script version |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - filtering completed |
| 1 | File not found or not readable |
| 2 | Invalid JSON in input file |
| 3 | Invalid file structure (missing required keys) |
| 4 | Invalid configuration parameters |
| 5 | Write error (cannot write output file) |

### Examples

```bash
# Basic usage with defaults
python etc/scripts/filter_tweets.py

# Custom thresholds
python etc/scripts/filter_tweets.py \
  --min-favorites 150 \
  --min-retweets 10 \
  --similarity-threshold 0.90

# Specify output and report files
python etc/scripts/filter_tweets.py \
  --input etc/staging/tweets_staging.json \
  --output etc/staging/tweets_filtered.json \
  --report etc/staging/filter_report.txt

# Show help
python etc/scripts/filter_tweets.py --help
```

## Input Schema

### File Format: JSON

**Path**: `etc/staging/tweets_staging.json` (configurable via `--input`)

**Structure**:

```json
{
  "metadata": {
    "extracted_at": "ISO8601 timestamp",
    "source_file": "string",
    "total_extracted": "integer",
    "version": "string"
  },
  "tweets": [
    {
      "tweet_id": "string (unique)",
      "text": "string (non-empty)",
      "created_at": "string (timestamp)",
      "is_retweet": "boolean",
      "favorite_count": "integer (>= 0)",
      "retweet_count": "integer (>= 0)",
      "media_urls": ["string (URL)", ...],
      "primarySpeaker": "string (may be empty)"
    }
  ]
}
```

### Field Validation Rules

**metadata** (required object):
- `extracted_at` (required string): ISO 8601 timestamp
- `source_file` (required string): Path to original source
- `total_extracted` (required integer): Count of original tweets
- `version` (required string): Schema version

**tweets** (required array):
- `tweet_id` (required string): Must be unique across all tweets
- `text` (required string): Must not be null or empty
- `created_at` (required string): Timestamp in Twitter date format
- `is_retweet` (required boolean): Defaults to false if missing
- `favorite_count` (optional integer): Defaults to 0 if missing
- `retweet_count` (optional integer): Defaults to 0 if missing
- `media_urls` (optional array): Defaults to empty array if missing
- `primarySpeaker` (optional string): Defaults to empty string if missing

### Example Input

```json
{
  "metadata": {
    "extracted_at": "2025-10-25T00:13:54.886889Z",
    "source_file": "etc/tweets.js",
    "total_extracted": 5240,
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
      ],
      "primarySpeaker": ""
    },
    {
      "tweet_id": "1753562838193623289",
      "text": "Rest in peace, Carl.",
      "created_at": "Fri Feb 02 23:35:34 +0000 2024",
      "is_retweet": false,
      "favorite_count": 2593,
      "retweet_count": 112,
      "media_urls": [],
      "primarySpeaker": ""
    },
    {
      "tweet_id": "1699482427121377321",
      "text": "Always. Leave. A. Note. #Starfield",
      "created_at": "Wed Sep 06 17:59:20 +0000 2023",
      "is_retweet": false,
      "favorite_count": 221,
      "retweet_count": 12,
      "media_urls": [
        "https://pbs.twimg.com/media/F5XGMu_XMAAdbEI.jpg"
      ],
      "primarySpeaker": ""
    }
  ]
}
```

## Output Schema

### File Format: JSON

**Path**: Overwrites input OR custom path via `--output`

**Structure**: Same as input with modified metadata and filtered tweets array

```json
{
  "metadata": {
    "extracted_at": "ISO8601 timestamp (preserved from input)",
    "source_file": "string (preserved from input)",
    "total_extracted": "integer (preserved from input)",
    "version": "string (preserved from input)",
    "filtered_at": "ISO8601 timestamp (added)",
    "filter_version": "string (added)",
    "tweets_retained": "integer (added)"
  },
  "tweets": [
    {
      "tweet_id": "string",
      "text": "string",
      "created_at": "string",
      "is_retweet": "boolean",
      "favorite_count": "integer",
      "retweet_count": "integer",
      "media_urls": ["string", ...],
      "primarySpeaker": "string"
    }
  ]
}
```

### Added Metadata Fields

- `filtered_at` (string): ISO 8601 timestamp when filter was applied
- `filter_version` (string): Version of filter script (e.g., "1.0.0")
- `tweets_retained` (integer): Count of tweets in filtered output

### Output Guarantees

**Filtered tweets array will NOT contain**:
- Tweets with `is_retweet: true`
- Tweets with "#" symbol in `text` field
- Tweets with `favorite_count < 100 AND retweet_count < 5`
- Tweets consisting only of hashtags, @mentions, or URLs
- Near-duplicate tweets (similarity >= threshold to previously retained tweet)

**Preserved**:
- Tweet order (chronological or as in input)
- All tweet fields (no modification to tweet objects)
- Original metadata fields

### Example Output

```json
{
  "metadata": {
    "extracted_at": "2025-10-25T00:13:54.886889Z",
    "source_file": "etc/tweets.js",
    "total_extracted": 5240,
    "version": "1.0",
    "filtered_at": "2025-10-27T14:30:00.123456Z",
    "filter_version": "1.0.0",
    "tweets_retained": 1247
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
      ],
      "primarySpeaker": ""
    },
    {
      "tweet_id": "1753562838193623289",
      "text": "Rest in peace, Carl.",
      "created_at": "Fri Feb 02 23:35:34 +0000 2024",
      "is_retweet": false,
      "favorite_count": 2593,
      "retweet_count": 112,
      "media_urls": [],
      "primarySpeaker": ""
    }
  ]
}
```

*Note: Tweet with ID 1699482427121377321 was removed (contains hashtag "#Starfield")*

## Report Schema

### File Format: Plain Text

**Destination**: Standard output OR file via `--report`

**Structure**:

```
Tweet Filtering Report
======================
Generated: YYYY-MM-DD HH:MM:SS

Summary
-------
Total tweets processed: {tweets_processed}
Tweets retained: {tweets_retained} ({percentage}%)
Tweets removed: {tweets_removed} ({percentage}%)
Processing time: {time} seconds

Removal Breakdown
-----------------
Retweets: {count} ({percentage}%)
Low engagement: {count} ({percentage}%)
Contains hashtags: {count} ({percentage}%)
No substantive content: {count} ({percentage}%)
Near-duplicate: {count} ({percentage}%)

Similarity Examples (for validation)
------------------------------------

Example {N}: Similarity {score}
KEPT (ID: {tweet_id}, ❤️ {favorites}, 🔁 {retweets}):
  "{text}"

REMOVED (ID: {tweet_id}, ❤️ {favorites}, 🔁 {retweets}):
  "{text}"

[Repeated for 5 examples]

Configuration Used
------------------
Min favorites: {min_favorites}
Min retweets: {min_retweets}
Similarity threshold: {similarity_threshold}
Exclude hashtags: {true/false}
Exclude retweets: {true/false}
```

### Similarity Examples Section

**Requirements**:
- Exactly 5 examples (or fewer if < 5 duplicates found)
- Each example shows 1 kept tweet and 1+ removed similar tweets
- Examples should span range of similarity scores if possible
- Display similarity score (0.00-1.00 format) for transparency

### Example Report

```
Tweet Filtering Report
======================
Generated: 2025-10-27 14:30:00

Summary
-------
Total tweets processed: 5,240
Tweets retained: 1,247 (23.8%)
Tweets removed: 3,993 (76.2%)
Processing time: 3.2 seconds

Removal Breakdown
-----------------
Retweets: 1,850 (35.3%)
Low engagement: 1,420 (27.1%)
Contains hashtags: 380 (7.3%)
No substantive content: 145 (2.8%)
Near-duplicate: 198 (3.8%)

Similarity Examples (for validation)
------------------------------------

Example 1: Similarity 0.87
KEPT (ID: 1706121712784347238, ❤️ 335, 🔁 13):
  "It's, like, 'Hey, you want to go down to the whirlpool?' 'Yeah, I don't have a husband.' I call it Swing City."

REMOVED (ID: 1706XXXXXXXXXXX, ❤️ 89, 🔁 4):
  "Its like Hey you want to go down to the whirlpool Yeah I dont have a husband I call it Swing City"

Example 2: Similarity 0.91
KEPT (ID: 1697639616361242973, ❤️ 912, 🔁 50):
  "If I may take off my acting pants for a moment and pull my analrapist stocking over my head..."

REMOVED (ID: 1697XXXXXXXXXXX, ❤️ 102, 🔁 6):
  "If I may take off my acting pants for a moment and pull my analrapist stocking over my head"

Example 3: Similarity 0.85
KEPT (ID: 1694816732530028951, ❤️ 801, 🔁 42):
  "He had not, in fact, overcome the desire to be liked"

REMOVED (ID: 1694XXXXXXXXXXX, ❤️ 95, 🔁 5):
  "He had not in fact overcome the desire to be liked"

Example 4: Similarity 0.94
KEPT (ID: 1686505466921078789, ❤️ 1070, 🔁 64):
  "I've made a huge mistake."

REMOVED (ID: 1686XXXXXXXXXXX, ❤️ 120, 🔁 8):
  "I have made a huge mistake"

Example 5: Similarity 0.98
KEPT (ID: 1653998433135002100, ❤️ 780, 🔁 24):
  "There's always money in the banana stand!"

REMOVED (ID: 1653XXXXXXXXXXX, ❤️ 105, 🔁 7):
  "Theres always money in the banana stand"

Configuration Used
------------------
Min favorites: 100
Min retweets: 5
Similarity threshold: 0.85
Exclude hashtags: true
Exclude retweets: true
```

## Standard Output Schema

### Similarity Examples Display

**Requirement**: Five similarity comparison examples must be output to stdout for human validation

**Format**: Same as in report (shown above in Similarity Examples section)

**Purpose**: Allow user to immediately see if similarity threshold is appropriate without reading full report

**Display Timing**: After filtering completes, before report summary

## Configuration File Schema (Optional)

*Note: CLI arguments take precedence over config file*

### File Format: JSON

**Path**: `etc/filter_config.json` (optional)

**Structure**:

```json
{
  "similarity_threshold": 0.85,
  "min_favorites": 100,
  "min_retweets": 5,
  "exclude_hashtags": true,
  "exclude_retweets": true,
  "exclude_empty_content": true
}
```

### Fields

All fields are optional (defaults used if not specified):

- `similarity_threshold` (float): 0.0-1.0, default 0.85
- `min_favorites` (integer): >= 0, default 100
- `min_retweets` (integer): >= 0, default 5
- `exclude_hashtags` (boolean): default true
- `exclude_retweets` (boolean): default true
- `exclude_empty_content` (boolean): default true

## Error Response Schema

### Format: stderr + exit code

**Structure**:

```
ERROR: {error_category}
{detailed_message}

{optional_help_text}
```

### Examples

```bash
# Exit code 1 - File not found
ERROR: Input file not found
File path: etc/staging/tweets_staging.json

Check that the file exists or specify a different path with --input

# Exit code 2 - Invalid JSON
ERROR: Invalid JSON in input file
File path: etc/staging/tweets_staging.json
Line: 42
Error: Unexpected token ','

# Exit code 3 - Invalid structure
ERROR: Invalid file structure
File path: etc/staging/tweets_staging.json
Missing required key: "metadata"

Expected structure: { "metadata": {...}, "tweets": [...] }

# Exit code 4 - Invalid configuration
ERROR: Invalid configuration parameter
Parameter: similarity_threshold
Value: 1.5
Expected: Float between 0.0 and 1.0
```

## Contract Validation

### Input Contract

**Script MUST**:
- Accept valid JSON with metadata + tweets structure
- Handle missing optional fields with documented defaults
- Reject invalid JSON with clear error message
- Reject invalid structure with clear error message

**Script MUST NOT**:
- Modify or corrupt input file
- Proceed with invalid configuration
- Silently ignore errors

### Output Contract

**Script MUST**:
- Produce valid JSON matching input schema
- Add filtered_at, filter_version, tweets_retained to metadata
- Ensure no filtered tweets violate removal criteria
- Preserve tweet object structure (no field modifications)

**Script MUST NOT**:
- Modify tweet objects (except removing entire tweets)
- Reorder tweets unless explicitly documented
- Produce invalid JSON

### CLI Contract

**Script MUST**:
- Accept all documented command-line options
- Use documented default values
- Return documented exit codes
- Output help text with `--help`
- Output version with `--version`

**Script MUST NOT**:
- Require undocumented parameters
- Use non-standard exit codes
- Produce unstructured error messages

## Summary

**Input**: JSON file (tweets_staging.json) + CLI options
**Output**: Filtered JSON file + text report + similarity examples
**Exit Codes**: 0-5 (success, file errors, validation errors)
**Configuration**: CLI args (required) + optional JSON config file
**Validation**: Strict schema enforcement with clear error messages

**Ready for**: Quickstart documentation and implementation

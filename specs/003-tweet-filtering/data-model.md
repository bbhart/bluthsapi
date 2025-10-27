# Data Model: Smart Tweet Staging Filter

**Feature**: 003-tweet-filtering
**Date**: 2025-10-27
**Phase**: Phase 1 - Design

## Entities

### Tweet (Input/Output)

Represents a tweet in the staging file. Structure is unchanged from feature 002 output.

**Fields**:
- `tweet_id` (string): Unique identifier from Twitter/X
- `text` (string): Tweet content
- `created_at` (string): ISO timestamp of tweet creation
- `is_retweet` (boolean): Whether tweet is a retweet
- `favorite_count` (integer): Number of favorites/likes
- `retweet_count` (integer): Number of retweets
- `media_urls` (array of strings): URLs to associated media
- `primarySpeaker` (string): Speaker attribution (may be empty)

**Validation Rules**:
- `tweet_id` must be unique
- `text` must not be null or empty
- `favorite_count` and `retweet_count` must be non-negative integers
- Missing metadata fields treated as: numeric → 0, text → ""

**State**: Immutable - tweets are filtered but not modified

### FilterCriteria (Configuration)

Represents the filtering rules to apply.

**Fields**:
- `min_favorites` (integer): Minimum favorite count (default: 100)
- `min_retweets` (integer): Minimum retweet count (default: 5)
- `similarity_threshold` (float): Similarity ratio for duplicate detection (0.0-1.0, default: 0.85)
- `exclude_hashtags` (boolean): Remove tweets containing "#" (default: true)
- `exclude_retweets` (boolean): Remove retweets (default: true)
- `exclude_empty_content` (boolean): Remove tweets with only hashtags/@mentions/URLs (default: true)

**Validation Rules**:
- `min_favorites` >= 0
- `min_retweets` >= 0
- `similarity_threshold` must be 0.0 <= x <= 1.0
- Boolean fields default to true if not specified

**Source**: Command-line arguments or configuration file

### FilterResult

Represents the outcome of the filtering process.

**Fields**:
- `tweets_processed` (integer): Total tweets in input file
- `tweets_retained` (integer): Tweets that passed all filters
- `tweets_removed` (integer): Tweets that failed at least one filter
- `removal_reasons` (dictionary): Counts by category
  - `retweets` (integer): Removed as retweets
  - `low_engagement` (integer): Below engagement thresholds
  - `contains_hashtags` (integer): Contains "#" symbol
  - `no_substantive_content` (integer): Only hashtags/@mentions/URLs
  - `near_duplicate` (integer): Similar to previous retained tweet
- `similarity_examples` (array): Five SimilarityComparison objects
- `processing_time_seconds` (float): Total execution time

**Relationships**:
- Contains array of `SimilarityComparison` objects

### SimilarityComparison (Example Output)

Represents one example of duplicate detection for human validation.

**Fields**:
- `kept_tweet` (object): The retained tweet
  - `tweet_id` (string)
  - `text` (string)
  - `favorite_count` (integer)
  - `retweet_count` (integer)
- `removed_tweets` (array of objects): One or more tweets removed as duplicates
  - `tweet_id` (string)
  - `text` (string)
  - `similarity_score` (float): Ratio 0.0-1.0
  - `favorite_count` (integer)
  - `retweet_count` (integer)

**Purpose**: Human validation of similarity threshold effectiveness

**Selection**: Choose examples with varied similarity scores (e.g., 0.85, 0.88, 0.91, 0.94, 0.97)

## Data Flow

### Input

**File**: `etc/staging/tweets_staging.json`

**Format**:
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
      "media_urls": ["https://pbs.twimg.com/media/GFd0PIwakAAv6S-.jpg"],
      "primarySpeaker": ""
    }
  ]
}
```

### Output

**File**: `etc/staging/tweets_filtered.json` (or overwrites input)

**Format**: Same structure as input, with reduced tweet array

```json
{
  "metadata": {
    "extracted_at": "2025-10-25T00:13:54.886889Z",
    "source_file": "etc/tweets.js",
    "total_extracted": 5240,
    "filtered_at": "2025-10-27T14:30:00.000000Z",
    "filter_version": "1.0",
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
      "media_urls": ["https://pbs.twimg.com/media/GFd0PIwakAAv6S-.jpg"],
      "primarySpeaker": ""
    }
  ]
}
```

**Metadata Changes**:
- Added `filtered_at`: Timestamp when filter was applied
- Added `filter_version`: Filter script version
- Added `tweets_retained`: Count of tweets in filtered output

### Report Output

**Destination**: Standard output or file if `--report` specified

**Format**: Human-readable text

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

REMOVED (ID: 1706XXX, ❤️ 89, 🔁 4):
  "Its like Hey you want to go down to the whirlpool Yeah I dont have a husband I call it Swing City"

[... 4 more examples ...]

Configuration Used
------------------
Min favorites: 100
Min retweets: 5
Similarity threshold: 0.85
Exclude hashtags: true
Exclude retweets: true
```

## Processing Pipeline

### Stage 1: Load and Validate

1. Load `tweets_staging.json`
2. Validate JSON structure
3. Count total tweets
4. Initialize FilterResult

### Stage 2: Apply Filters (in order)

```
Input: tweets[]

1. Retweet Filter
   IF is_retweet == true → REMOVE
   ↓
2. Hashtag Filter
   IF "#" in text → REMOVE
   ↓
3. Engagement Filter
   IF (favorite_count < 100) AND (retweet_count < 5) → REMOVE
   ↓
4. Substantive Content Filter
   IF text contains only hashtags/@mentions/URLs → REMOVE
   ↓
5. Deduplication Filter
   FOR EACH remaining tweet:
     normalized_text = normalize(tweet.text)
     FOR EACH previously_retained_tweet:
       IF similarity(normalized_text, retained_text) >= threshold:
         REMOVE current tweet
         ADD to similarity_examples (if < 5)
         BREAK
     IF not removed:
       ADD to retained_tweets

Output: filtered_tweets[]
```

### Stage 3: Generate Output

1. Create output metadata (add filtered_at, filter_version, tweets_retained)
2. Write filtered tweets to output file
3. Generate and display/save filter report
4. Display five similarity examples to stdout

## Validation

### Input Validation

**Required**:
- Input file must exist and be readable
- Input file must be valid JSON
- Must contain "metadata" and "tweets" keys
- "tweets" must be an array

**Error Handling**:
- Missing file → Exit code 1, error to stderr
- Invalid JSON → Exit code 2, error to stderr with line number
- Invalid structure → Exit code 3, error to stderr with details

### Configuration Validation

**Rules**:
- similarity_threshold must be 0.0-1.0 → Exit code 4 if invalid
- min_favorites must be >= 0 → Exit code 4 if invalid
- min_retweets must be >= 0 → Exit code 4 if invalid

### Output Validation

**Guarantees**:
- Output JSON is valid and matches input structure
- No tweets with is_retweet=true in output
- No tweets with "#" in text in output
- No tweets with engagement below thresholds in output
- Metadata accurately reflects filtered state

## Performance Considerations

### Memory Usage

**Approach**: Load entire file into memory

**Justification**:
- Expected file size: 1-5 MB (5,000 tweets × ~200 bytes average)
- Well within memory constraints
- Simplifies processing logic
- Allows multiple passes if needed

**Alternative** (if needed): Stream processing for very large files

### Time Complexity

**Per Filter**:
- Retweets: O(n) - single pass, boolean check
- Hashtags: O(n) - single pass, string contains
- Engagement: O(n) - single pass, numeric comparison
- Substantive content: O(n) - single pass, regex/parsing
- Deduplication: O(n × m) where m = retained tweets (~O(n²) worst case)

**Total**: O(n²) dominated by deduplication

**Optimization**: Early filtering reduces n for deduplication stage

**Expected** (5,000 tweets):
- After engagement filter: ~1,500 tweets
- Deduplication: ~1.5M comparisons
- With SequenceMatcher: ~2-3 seconds

## Testing Strategy

### Unit Tests

1. **Filter functions**:
   - Test is_retweet filter with retweets and non-retweets
   - Test hashtag filter with various hashtag placements
   - Test engagement filter with boundary values (99, 100, 101)
   - Test similarity with known similar/dissimilar pairs

2. **Text normalization**:
   - Test punctuation removal
   - Test case normalization
   - Test whitespace collapsing

3. **Configuration parsing**:
   - Test default values
   - Test CLI argument parsing
   - Test config file loading

### Integration Tests

1. **End-to-end filtering**:
   - Input file with known tweets → verify correct output
   - Count tweets by category → verify report accuracy

2. **Example generation**:
   - Verify five examples are output
   - Verify examples show varied similarity scores

### Contract Tests

1. **Input/output schema validation**:
   - Verify output matches input schema
   - Verify metadata fields are added correctly

## Summary

**Entities**: Tweet (I/O), FilterCriteria (config), FilterResult (outcome), SimilarityComparison (examples)

**Flow**: Load → Validate → Filter (5 stages) → Generate Output → Report

**Performance**: O(n²) worst case, expected 2-5 seconds for 5,000 tweets

**Testing**: Unit (filter functions, normalization) + Integration (end-to-end) + Contract (schema validation)

**Ready for**: Contract definition (schemas) and quickstart documentation

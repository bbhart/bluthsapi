# Research: Tweet to Quote Conversion System

**Feature**: 002-tweet-to-quote-conversion
**Date**: 2025-10-24
**Status**: Complete

## Overview

This document captures research findings and technical decisions for the tweet-to-quote conversion pipeline. The feature requires parsing Twitter archive format, transforming data through a human-reviewable staging format, and generating application-ready quote records.

## Research Areas

### 1. Twitter Archive Data Format

**Question**: What is the structure of Twitter archive tweets.js files?

**Decision**: Parse standard Twitter archive JSON format wrapped in JavaScript assignment

**Rationale**:
- Twitter archives export data as `window.YTD.tweets.part0 = [...]` JavaScript files
- Need to strip the JavaScript wrapper and parse the JSON array
- Each tweet object contains: `tweet.full_text`, `tweet.id_str`, `tweet.created_at`, `tweet.entities.media[]`, `tweet.extended_entities.media[]`
- Retweets identified by `full_text` starting with "RT @"

**Implementation Approach**:
```python
# Read file, strip JS wrapper, parse JSON
content = Path('etc/tweets.js').read_text()
json_start = content.index('[')
json_end = content.rindex(']') + 1
tweets_data = json.loads(content[json_start:json_end])
```

**Alternatives Considered**:
- Using JavaScript parser (rejected: unnecessary complexity, Python-only solution preferred)
- Regex extraction (rejected: fragile for edge cases, direct string manipulation more reliable)

---

### 2. Staging File Format

**Question**: What format should the staging file use for human editability?

**Decision**: Use pretty-printed JSON with 2-space indentation

**Rationale**:
- JSON is universally editable in any text editor
- Pretty-printing makes structure clear for human review
- Can validate JSON syntax before final conversion
- Preserves all data types (strings, numbers, booleans, null)

**Schema**:
```json
{
  "tweets": [
    {
      "tweet_id": "1234567890",
      "text": "Quote text here",
      "created_at": "2024-01-01T12:00:00Z",
      "is_retweet": false,
      "favorite_count": 100,
      "retweet_count": 10,
      "media_urls": ["https://..."]
    }
  ],
  "metadata": {
    "extracted_at": "2025-10-24T...",
    "source_file": "etc/tweets.js",
    "total_extracted": 150
  }
}
```

**Alternatives Considered**:
- CSV format (rejected: loses structure, harder to edit multi-line text, no nested media arrays)
- YAML format (rejected: whitespace-sensitive, harder to validate programmatically)
- Custom text format (rejected: requires custom parser, not standard)

---

### 3. Quote ID Generation Strategy

**Question**: How to efficiently find the highest existing quote ID and handle collisions?

**Decision**: Scan existing quotes.json once at conversion start, maintain counter in memory

**Rationale**:
- Single file read at startup is acceptable overhead (quotes.json expected to be <10MB)
- Extract numeric portion from "quote-XXX" pattern using regex `quote-(\d+)`
- Maintain set of used IDs to detect collisions
- Auto-increment on collision per clarification requirement

**Implementation Approach**:
```python
def get_next_quote_id(existing_quotes):
    used_ids = set()
    max_id = 0
    for quote in existing_quotes:
        match = re.match(r'quote-(\d+)', quote['id'])
        if match:
            num = int(match.group(1))
            used_ids.add(num)
            max_id = max(max_id, num)

    # Start from max + 1, skip any collisions
    next_id = max_id + 1
    while next_id in used_ids:
        next_id += 1
    return next_id
```

**Alternatives Considered**:
- UUID-based IDs (rejected: doesn't match specified "quote-XXX" format)
- Hash-based IDs (rejected: not sequential, harder for humans to reference)
- Database sequence (rejected: no database in scope)

---

### 4. Media Download Strategy

**Question**: How to efficiently download media files with proper error handling and resume capability?

**Decision**: Use `urllib.request` with timeout, skip existing files by checking file size match

**Rationale**:
- `urllib.request` is standard library, no external dependencies
- Set 30-second timeout to handle slow/hung connections
- Compare local file size with Content-Length header to detect partial downloads
- Use tweet ID + media index for filename uniqueness
- Log all errors but continue processing (per FR-013)

**Implementation Approach**:
```python
from urllib.request import urlopen, Request
from pathlib import Path

def download_media(url, output_path, timeout=30):
    if output_path.exists():
        # Check if complete by comparing size
        try:
            req = Request(url, method='HEAD')
            with urlopen(req, timeout=timeout) as response:
                remote_size = int(response.headers.get('Content-Length', 0))
                local_size = output_path.stat().st_size
                if local_size == remote_size:
                    return 'skipped'  # Already downloaded
        except Exception:
            pass  # Re-download if HEAD fails

    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=timeout) as response:
            output_path.write_bytes(response.read())
        return 'success'
    except Exception as e:
        return f'error: {e}'
```

**Alternatives Considered**:
- `requests` library (rejected: external dependency, overkill for simple downloads)
- Parallel downloads with ThreadPoolExecutor (deferred: can add if performance insufficient)
- Resume with Range headers (rejected: complexity not justified for small images)

---

### 5. Text Preservation Strategy

**Question**: How to ensure 100% text accuracy including special characters, emojis, and URLs?

**Decision**: Use JSON encoding/decoding throughout, avoid string manipulation

**Rationale**:
- Python's `json` module handles Unicode (emojis, special chars) correctly by default
- Never manipulate tweet text except during extraction (take as-is from `full_text`)
- Preserve exact whitespace, line breaks, and formatting
- Use UTF-8 encoding for all file I/O

**Implementation Approach**:
```python
# Read with explicit UTF-8
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Write with explicit UTF-8, ensure_ascii=False preserves Unicode
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

**Alternatives Considered**:
- Text cleaning/normalization (rejected: violates FR-003 requirement for exact preservation)
- ASCII encoding with escape sequences (rejected: harder for humans to read in staging file)

---

### 6. Progress Feedback Strategy

**Question**: How to provide clear progress feedback during long-running operations?

**Decision**: Use simple print statements with progress counts, no external libraries

**Rationale**:
- Simple `print()` to stdout for progress, stderr for errors
- Show progress every N items (e.g., every 100 tweets)
- Display final summary with counts
- No fancy progress bars (avoids dependencies, works in any terminal)

**Implementation Approach**:
```python
print(f"Extracting tweets from {source_file}...")
for i, tweet in enumerate(tweets, 1):
    # Process tweet
    if i % 100 == 0:
        print(f"  Processed {i} tweets...")
print(f"✓ Extraction complete: {total} tweets → {output_file}")
```

**Alternatives Considered**:
- `tqdm` progress bars (rejected: external dependency)
- Logging library (deferred: simple print sufficient for CLI scripts)
- Silent operation (rejected: violates FR-015 progress feedback requirement)

---

## Technology Stack Summary

| Component | Choice | Justification |
|-----------|--------|---------------|
| Language | Python 3.11+ | Matches existing project; excellent JSON support |
| JSON parsing | `json` stdlib | Standard, reliable, handles Unicode correctly |
| File I/O | `pathlib` + `open()` | Modern, cross-platform path handling |
| HTTP downloads | `urllib.request` | Standard library, no dependencies needed |
| CLI arguments | `argparse` | Standard library, sufficient for simple scripts |
| Testing | `pytest` | Matches existing test infrastructure |
| Type hints | Yes (Python 3.11+) | Improves code clarity and catches errors |

---

## Best Practices Applied

### Code Organization
- Each script is standalone (extract, convert, download)
- Shared utilities in common module if needed
- Clear separation of concerns

### Error Handling
- Explicit try/except for I/O operations
- Meaningful error messages to stderr
- Non-zero exit codes on failure
- Continue on media download errors (log and skip)

### Testing Strategy
- Unit tests for core functions (ID generation, parsing, validation)
- Integration tests with sample data files
- Edge case tests (empty files, malformed JSON, missing fields)
- No external API mocking needed (file-based operations)

### Performance Considerations
- Single-pass processing where possible
- Stream large files if memory becomes concern
- Batch media downloads (current design supports parallel execution if needed)

---

## Open Questions (Resolved During Research)

1. **Q: Should staging file include all tweet metadata?**
   - A: Yes - include tweet_id, created_at, counts for curator context during review

2. **Q: What if tweets.js contains multiple parts (part0, part1, etc.)?**
   - A: Out of scope for initial implementation; manual merge or script enhancement in future

3. **Q: Should media downloads preserve original filenames?**
   - A: No - use tweet_id + index for predictability and collision avoidance

4. **Q: How to handle tweets with multiple media items?**
   - A: Use first image URL for imageUrl field; future enhancement could support multiple

---

## Dependencies & Prerequisites

**Runtime Requirements**:
- Python 3.11+ (already installed in project)
- No external packages needed (pure stdlib)

**File Dependencies**:
- Input: `etc/tweets.js` must exist and be readable
- Output directory: `etc/staging/` will be created if missing
- Target: `app/data/quotes.json` must be writable

**Network Requirements** (media download only):
- Access to `pbs.twimg.com` and `video.twimg.com`
- Outbound HTTPS (port 443)

---

## Next Steps

Research complete. Proceed to:
1. **Phase 1**: Generate data-model.md and contracts/schemas.md
2. **Phase 1**: Create quickstart.md for running the conversion pipeline
3. **Phase 2**: Generate tasks.md with implementation breakdown

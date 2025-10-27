# Quickstart: Smart Tweet Staging Filter

**Feature**: 003-tweet-filtering
**Date**: 2025-10-27
**For**: Developers implementing the filter script

## Overview

The Smart Tweet Staging Filter is a command-line utility that processes `tweets_staging.json` (created by feature 002) to remove low-quality content. It filters out retweets, hashtag-containing tweets, low-engagement content, and near-duplicates, producing a cleaned staging file ready for quote conversion.

**Input**: `etc/staging/tweets_staging.json` (raw staging data)
**Output**: Filtered JSON + text report + similarity examples
**Language**: Python 3.11+ (stdlib only)
**Time**: ~2-5 seconds for 5,000 tweets

## Prerequisites

- Python 3.11 or higher
- Feature 002 (tweet-to-quote-conversion) completed
- Input file `etc/staging/tweets_staging.json` exists

## Quick Start

### 1. Basic Usage

```bash
# Filter with default settings
python etc/scripts/filter_tweets.py

# This will:
# - Read from etc/staging/tweets_staging.json
# - Apply default filters (min 100 favorites OR 5 retweets)
# - Remove retweets, hashtags, and duplicates (85% similarity)
# - Overwrite the input file with filtered results
# - Display similarity examples and report
```

### 2. Custom Configuration

```bash
# More aggressive filtering
python etc/scripts/filter_tweets.py \
  --min-favorites 150 \
  --min-retweets 10 \
  --similarity-threshold 0.90
```

### 3. Separate Output File

```bash
# Keep original file, write filtered to new file
python etc/scripts/filter_tweets.py \
  --input etc/staging/tweets_staging.json \
  --output etc/staging/tweets_filtered.json \
  --report etc/staging/filter_report.txt
```

### 4. Review Results

The script outputs five similarity comparison examples to help you validate the threshold:

```
Example 1: Similarity 0.87
KEPT (ID: 1706121712784347238, ❤️ 335, 🔁 13):
  "It's, like, 'Hey, you want to go down to the whirlpool?'..."

REMOVED (ID: 1706XXX, ❤️ 89, 🔁 4):
  "Its like Hey you want to go down to the whirlpool"
```

If false positives occur (good tweets removed), increase threshold to 0.90-0.95 and re-run.

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input PATH` | Input staging file | `etc/staging/tweets_staging.json` |
| `--output PATH` | Output file | (overwrites input) |
| `--report PATH` | Report output file | (prints to stdout) |
| `--similarity-threshold N` | Duplicate detection threshold (0.0-1.0) | `0.85` |
| `--min-favorites N` | Minimum favorite count | `100` |
| `--min-retweets N` | Minimum retweet count | `5` |
| `--help` | Show help message | - |
| `--version` | Show script version | - |

## Filtering Rules

### Applied in This Order:

1. **Retweet Filter**: Removes tweets with `is_retweet: true`
2. **Hashtag Filter**: Removes tweets containing "#" symbol
3. **Engagement Filter**: Removes tweets with `favorite_count < 100 AND retweet_count < 5`
4. **Substantive Content Filter**: Removes tweets with only hashtags/@mentions/URLs
5. **Deduplication Filter**: Removes near-duplicate tweets (similarity >= threshold)

### Similarity Detection:

Tweets are compared after normalization:
- Convert to lowercase
- Remove all punctuation
- Collapse whitespace

Example:
- Original: `"I've made a huge mistake!"`
- Normalized: `"i ve made a huge mistake"`
- If another tweet has normalized text `"i have made a huge mistake"` → similarity ~0.94 → removed as duplicate

## Output Files

### Filtered JSON

**Location**: Overwrites input OR custom path via `--output`

**Changes**:
- `metadata.filtered_at`: Added timestamp
- `metadata.filter_version`: Added version
- `metadata.tweets_retained`: Added count
- `tweets` array: Reduced to passing tweets only

**Guarantees**:
- No retweets
- No tweets with hashtags
- No low-engagement tweets (below thresholds)
- No near-duplicates (above similarity threshold)

### Filter Report

**Location**: stdout OR file via `--report`

**Sections**:
1. **Summary**: Total processed, retained, removed, time
2. **Removal Breakdown**: Counts by category
3. **Similarity Examples**: Five duplicate detection examples
4. **Configuration Used**: Active filter settings

## Error Handling

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Proceed to quote conversion |
| 1 | File not found | Check input path |
| 2 | Invalid JSON | Fix JSON syntax in input file |
| 3 | Invalid structure | Verify file has metadata + tweets |
| 4 | Invalid config | Check parameter values |
| 5 | Write error | Check output path permissions |

### Example Errors

```bash
# File not found
$ python etc/scripts/filter_tweets.py --input nonexistent.json
ERROR: Input file not found
File path: nonexistent.json
Exit code: 1

# Invalid similarity threshold
$ python etc/scripts/filter_tweets.py --similarity-threshold 1.5
ERROR: Invalid configuration parameter
Parameter: similarity_threshold
Value: 1.5
Expected: Float between 0.0 and 1.0
Exit code: 4
```

## Workflow Integration

### Complete Pipeline (Features 002 + 003)

```bash
# Step 1: Extract tweets (feature 002)
python etc/scripts/extract_tweets.py \
  --input etc/tweets.js \
  --output etc/staging/tweets_staging.json

# Step 2: Filter tweets (feature 003) ← THIS FEATURE
python etc/scripts/filter_tweets.py \
  --input etc/staging/tweets_staging.json \
  --output etc/staging/tweets_filtered.json

# Step 3: Review filtered tweets manually
# Open etc/staging/tweets_filtered.json in text editor
# Remove/edit any remaining unwanted entries

# Step 4: Convert to quotes (feature 002)
python etc/scripts/convert_to_quotes.py \
  --input etc/staging/tweets_filtered.json \
  --output app/data/quotes.json
```

### Recommended Workflow

1. **Initial filtering** with default settings
2. **Review similarity examples** in output
3. **Adjust threshold** if needed (0.80-0.95 range)
4. **Re-filter** if adjustments made
5. **Manual review** of filtered staging file (optional)
6. **Proceed to quote conversion**

## Configuration Tuning

### Similarity Threshold Guidelines

| Threshold | Effect | Use When |
|-----------|--------|----------|
| 0.80 | Aggressive deduplication | Many near-duplicates expected |
| 0.85 | **Recommended default** | Balanced approach |
| 0.90 | Conservative deduplication | Minimize false positives |
| 0.95 | Very conservative | Only remove near-exact duplicates |

### Engagement Threshold Guidelines

| Setting | Effect | Use When |
|---------|--------|----------|
| 100 favorites / 5 retweets | **Recommended default** | Standard quality bar |
| 150 favorites / 10 retweets | Stricter filtering | Want only highly engaged content |
| 50 favorites / 3 retweets | Lenient filtering | Preserve more content for manual review |

## Testing

### Validation Checklist

After filtering, verify:

- [ ] Output file is valid JSON
- [ ] `metadata.tweets_retained` matches array length
- [ ] No tweets with `is_retweet: true` remain
- [ ] No tweets with "#" in text remain
- [ ] All remaining tweets meet engagement thresholds
- [ ] Similarity examples show reasonable duplicate detection
- [ ] Processing completed in under 10 seconds

### Sample Test Command

```bash
# Test with stricter settings
python etc/scripts/filter_tweets.py \
  --input etc/staging/tweets_staging.json \
  --output etc/staging/tweets_test.json \
  --similarity-threshold 0.90 \
  --min-favorites 150

# Validate output
python -m json.tool etc/staging/tweets_test.json > /dev/null
echo "Exit code: $?"  # Should be 0 if valid JSON
```

## Performance

### Expected Performance (5,000 tweets)

| Stage | Time |
|-------|------|
| Load and parse JSON | ~0.1s |
| Retweet filter | ~0.1s |
| Hashtag filter | ~0.1s |
| Engagement filter | ~0.1s |
| Substantive content filter | ~0.5s |
| Deduplication (~1,500 remaining) | ~2-3s |
| Report generation | ~0.5s |
| **Total** | **~3-5s** |

### Performance Tips

- Run on input file directly (in-place filtering) for faster I/O
- Use default similarity threshold (0.85) - higher thresholds don't improve performance
- Filter progression reduces comparison count (70-80% removed before deduplication)

## Troubleshooting

### Issue: Too many tweets removed

**Solution**: Decrease engagement thresholds or increase similarity threshold

```bash
python etc/scripts/filter_tweets.py \
  --min-favorites 75 \
  --min-retweets 3 \
  --similarity-threshold 0.90
```

### Issue: Not enough duplicates caught

**Solution**: Decrease similarity threshold

```bash
python etc/scripts/filter_tweets.py --similarity-threshold 0.80
```

### Issue: False positives (good tweets marked as duplicates)

**Solution**: Increase similarity threshold

```bash
python etc/scripts/filter_tweets.py --similarity-threshold 0.90
```

Review the five similarity examples to verify the new threshold is appropriate.

### Issue: Slow processing

**Check**:
- Input file size (should be < 10 MB)
- Number of tweets (should be < 10,000)
- System resources

**Optimize**: Run engagement filter first to reduce tweets for deduplication

## Next Steps

After successful filtering:

1. **Review similarity examples** to validate threshold
2. **Check filter report** to understand what was removed
3. **Optionally** perform manual review of filtered staging file
4. **Proceed to feature 002** quote conversion step
5. **Optional**: Download media (if feature 002 media script used)

## Implementation Notes

### Key Files

```
etc/
├── staging/
│   ├── tweets_staging.json       # Input (from feature 002)
│   ├── tweets_filtered.json      # Output (optional separate file)
│   └── filter_report.txt         # Report (optional file)
└── scripts/
    └── filter_tweets.py          # This script (to be implemented)
```

### Core Dependencies

```python
import json                  # JSON parsing
import pathlib              # File path handling
from difflib import SequenceMatcher  # Similarity detection
import string               # Punctuation removal
import argparse             # CLI argument parsing
import sys                  # Exit codes and stderr
from datetime import datetime # Timestamps
```

**All stdlib** - no external packages required.

### Entry Point

```python
def main():
    """Main entry point for filter script."""
    # Parse CLI arguments
    # Load configuration
    # Validate input
    # Apply filters
    # Generate output
    # Display examples
    # Print report
    # Exit with appropriate code
```

## Summary

**Purpose**: Filter low-quality tweets from staging data
**Input**: `tweets_staging.json` (feature 002 output)
**Output**: Filtered JSON + report + examples
**Time**: 2-5 seconds for 5,000 tweets
**Configuration**: CLI args (defaults: 100 favorites, 5 retweets, 0.85 similarity)
**Next**: Quote conversion (feature 002) or manual review

**Ready for**: Implementation (`/speckit.tasks`)

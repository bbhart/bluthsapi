# Research: Smart Tweet Staging Filter

**Feature**: 003-tweet-filtering
**Date**: 2025-10-27
**Phase**: Phase 0 - Technical Research

## Research Questions

From Technical Context NEEDS CLARIFICATION markers:
1. Text similarity algorithm selection (difflib stdlib vs external library)
2. Package management compatibility with uv

## Research Findings

### 1. Text Similarity Algorithm

**Decision**: Use Python's built-in `difflib.SequenceMatcher` from standard library

**Rationale**:
- **No external dependencies**: Keeps the project lightweight and aligns with feature 002's approach (stdlib only)
- **Sufficient for use case**: SequenceMatcher provides a similarity ratio (0.0 to 1.0) based on the Ratcliff/Obershelp algorithm, which is effective for detecting near-duplicate text
- **Performance**: Fast enough for our scale (5,000 tweets in under 10 seconds)
- **Configurable threshold**: Easy to adjust similarity cutoff (e.g., 0.85 = 85% similar)
- **Built-in text normalization**: Can normalize text (lowercase, remove punctuation) before comparison

**Alternatives Considered**:
- **fuzzywuzzy/rapidfuzz**: More sophisticated fuzzy string matching with partial ratio, token sort ratio
  - **Rejected**: Adds external dependency; overkill for our use case; stdlib solution is sufficient
- **Levenshtein distance (python-Levenshtein)**: Edit distance metric
  - **Rejected**: External dependency; more complex than needed; SequenceMatcher provides similar functionality
- **TF-IDF + cosine similarity (sklearn)**: Vector-based similarity
  - **Rejected**: Heavy dependency (scikit-learn); excessive for tweet text comparison

**Implementation Approach**:
```python
from difflib import SequenceMatcher

def normalize_text(text):
    """Remove punctuation, lowercase, collapse whitespace."""
    import string
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Lowercase and collapse whitespace
    return ' '.join(text.lower().split())

def texts_are_similar(text1, text2, threshold=0.85):
    """Return True if texts are similar above threshold."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold
```

**Performance Characteristics**:
- SequenceMatcher has O(n*m) time complexity where n and m are string lengths
- For 5,000 tweets with average length 100 chars, worst-case ~25M comparisons
- With early filtering (engagement/hashtags first), expect ~1,000-2,000 tweets remaining for deduplication
- Estimated deduplication time: 1-3 seconds for 2,000 tweets

**Configurable Parameters**:
- Similarity threshold (default: 0.85)
- Can be adjusted via command-line arg: `--similarity-threshold 0.90`

### 2. Package Management Compatibility

**Decision**: No package management changes needed

**Rationale**:
- Using Python standard library only (difflib, string, json, pathlib)
- Fully compatible with existing uv package management setup
- No new entries needed in requirements.txt or requirements-dev.txt
- Follows the pattern established in feature 002-tweet-to-quote-conversion

**Verification**:
- difflib: Python stdlib since 2.1
- string: Python stdlib (core module)
- json: Python stdlib since 2.6
- pathlib: Python stdlib since 3.4

**Result**: No dependency conflicts; constitution compliance confirmed

## Best Practices

### Text Normalization for Similarity

**Best Practice**: Normalize text before comparison to ignore irrelevant differences

**Approach**:
1. **Convert to lowercase**: "I've made a huge mistake" == "I've made a huge mistake"
2. **Remove punctuation**: "mistake." == "mistake"
3. **Collapse whitespace**: "huge  mistake" == "huge mistake"
4. **Preserve word order**: "huge mistake" != "mistake huge" (order matters for meaning)

**Implementation**:
- Use `string.punctuation` to remove all punctuation
- Use `str.lower()` for case normalization
- Use `split()` + `join()` to collapse whitespace

### Deduplication Order

**Best Practice**: Keep first occurrence, remove subsequent duplicates

**Rationale**:
- Preserves chronological order (tweets are time-ordered)
- First tweet likely has better engagement (if both passed filters)
- Simpler logic than trying to pick "best" of duplicates

**Implementation**:
- Process tweets in order from staging file
- Maintain list of retained tweet texts (normalized)
- For each new tweet, compare against all retained tweets
- If similar to any retained tweet, mark for removal
- Otherwise, add to retained list

### Similarity Threshold Tuning

**Best Practice**: Start conservative (higher threshold) and adjust based on examples

**Recommended**:
- **Default: 0.85 (85% similar)**: Catches most true duplicates while minimizing false positives
- **Conservative: 0.90**: Fewer false positives, may miss some duplicates
- **Aggressive: 0.80**: Catches more duplicates, higher false positive risk

**Validation**:
- Output five examples of removed duplicates for human review
- User can adjust threshold and re-run if needed
- Include similarity score in example output for transparency

### Filter Pipeline Order

**Best Practice**: Apply cheap filters first, expensive filters last

**Recommended Order**:
1. **Retweet filter** (simple boolean check)
2. **Hashtag filter** (string contains "#")
3. **Engagement filter** (numeric comparison)
4. **Substantive content filter** (regex/string analysis)
5. **Deduplication** (expensive O(n²) similarity comparison)

**Rationale**:
- Early filters remove 70-80% of tweets quickly
- Deduplication only runs on ~20-30% of original data
- Reduces total processing time significantly

## Configuration Design

### Command-Line Interface

**Recommended**:
```bash
python etc/scripts/filter_tweets.py \
  --input etc/staging/tweets_staging.json \
  --output etc/staging/tweets_filtered.json \
  --report etc/staging/filter_report.txt \
  --similarity-threshold 0.85 \
  --min-favorites 100 \
  --min-retweets 5
```

**Default Values**:
- `--similarity-threshold`: 0.85
- `--min-favorites`: 100
- `--min-retweets`: 5
- `--input`: etc/staging/tweets_staging.json
- `--output`: etc/staging/tweets_filtered.json (overwrites input if not specified)
- `--report`: Print to stdout (write to file if specified)

### Configuration File (Optional Enhancement)

**Alternative**: JSON config file for repeated runs

```json
{
  "similarity_threshold": 0.85,
  "min_favorites": 100,
  "min_retweets": 5,
  "exclude_hashtags": true,
  "exclude_retweets": true
}
```

**Implementation**: Load config from `etc/filter_config.json` if present, override with CLI args

## Performance Validation

### Expected Processing Times

**Dataset**: 5,000 tweets in staging file

1. **Retweet filter**: < 0.1s (boolean check)
2. **Hashtag filter**: < 0.1s (string contains)
3. **Engagement filter**: < 0.1s (numeric comparison)
4. **Substantive content filter**: < 0.5s (regex analysis)
5. **Deduplication** (on ~1,500 remaining tweets): 1-3s (O(n²) comparisons)
6. **Report generation**: < 0.5s (count aggregation)

**Total**: ~2-5 seconds (well under 10-second constraint)

### Optimization Strategies (if needed)

If performance issues arise:
1. **Early termination**: Stop comparing once similarity exceeds threshold
2. **Length pre-filter**: Don't compare tweets with significantly different lengths
3. **Hash-based dedup**: Use hash for exact duplicates before similarity check
4. **Sampling**: Only compare with recent N retained tweets (e.g., last 100)

## Summary

**Technical Decisions**:
- Text similarity: Python stdlib `difflib.SequenceMatcher`
- No external dependencies
- Configurable threshold (default 0.85)
- Process order: cheap filters → expensive deduplication

**Constitution Compliance**: ✅ No package management changes; stdlib only

**Ready for Phase 1**: All NEEDS CLARIFICATION items resolved; can proceed to data model and contracts design.

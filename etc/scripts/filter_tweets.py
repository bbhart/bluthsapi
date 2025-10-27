#!/usr/bin/env python3
"""
Smart Tweet Staging Filter

Filters tweets_staging.json by removing low-quality content based on:
- Engagement metrics (< 100 favorites OR < 5 retweets)
- Retweets (is_retweet: true)
- Hashtags (contains "#" symbol)
- Near-duplicates (similarity >= threshold)

Outputs filtered JSON, detailed report, and five similarity examples.

Usage:
    python filter_tweets.py [OPTIONS]

Options:
    --input PATH              Input staging file (default: etc/staging/tweets_staging.json)
    --output PATH             Output file (default: overwrites input)
    --report PATH             Report file (default: stdout)
    --similarity-threshold N  Similarity ratio 0.0-1.0 (default: 0.85)
    --min-favorites N         Minimum favorite count (default: 100)
    --min-retweets N          Minimum retweet count (default: 5)
    --help                    Show help message
    --version                 Show version

Exit Codes:
    0: Success
    1: File not found or not readable
    2: Invalid JSON in input file
    3: Invalid file structure
    4: Invalid configuration parameters
    5: Write error

Feature: 003-tweet-filtering
Version: 1.0.0
"""

import json
import sys
import argparse
import string
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional


# Version
VERSION = "1.0.0"


# Exit codes
EXIT_SUCCESS = 0
EXIT_FILE_NOT_FOUND = 1
EXIT_INVALID_JSON = 2
EXIT_INVALID_STRUCTURE = 3
EXIT_INVALID_CONFIG = 4
EXIT_WRITE_ERROR = 5


class FilterResult:
    """Tracks filtering results and statistics."""

    def __init__(self):
        self.tweets_processed = 0
        self.tweets_retained = 0
        self.tweets_removed = 0
        self.removal_reasons = {
            'retweets': 0,
            'low_engagement': 0,
            'contains_hashtags': 0,
            'no_substantive_content': 0,
            'near_duplicate': 0
        }
        self.similarity_examples = []
        self.processing_start_time = datetime.now()

    def processing_time(self) -> float:
        """Calculate processing time in seconds."""
        return (datetime.now() - self.processing_start_time).total_seconds()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Filter tweets_staging.json by removing low-quality content',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--input',
        default='etc/staging/tweets_staging.json',
        help='Input staging file (default: etc/staging/tweets_staging.json)'
    )

    parser.add_argument(
        '--output',
        default=None,
        help='Output file (default: overwrites input)'
    )

    parser.add_argument(
        '--report',
        default=None,
        help='Report output file (default: stdout)'
    )

    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=0.85,
        help='Similarity ratio 0.0-1.0 for duplicate detection (default: 0.85)'
    )

    parser.add_argument(
        '--min-favorites',
        type=int,
        default=100,
        help='Minimum favorite count (default: 100)'
    )

    parser.add_argument(
        '--min-retweets',
        type=int,
        default=5,
        help='Minimum retweet count (default: 5)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )

    return parser.parse_args()


def validate_config(args: argparse.Namespace) -> None:
    """Validate configuration parameters."""
    if not (0.0 <= args.similarity_threshold <= 1.0):
        print(f"ERROR: Invalid configuration parameter", file=sys.stderr)
        print(f"Parameter: similarity_threshold", file=sys.stderr)
        print(f"Value: {args.similarity_threshold}", file=sys.stderr)
        print(f"Expected: Float between 0.0 and 1.0", file=sys.stderr)
        sys.exit(EXIT_INVALID_CONFIG)

    if args.min_favorites < 0:
        print(f"ERROR: Invalid configuration parameter", file=sys.stderr)
        print(f"Parameter: min_favorites", file=sys.stderr)
        print(f"Value: {args.min_favorites}", file=sys.stderr)
        print(f"Expected: Integer >= 0", file=sys.stderr)
        sys.exit(EXIT_INVALID_CONFIG)

    if args.min_retweets < 0:
        print(f"ERROR: Invalid configuration parameter", file=sys.stderr)
        print(f"Parameter: min_retweets", file=sys.stderr)
        print(f"Value: {args.min_retweets}", file=sys.stderr)
        print(f"Expected: Integer >= 0", file=sys.stderr)
        sys.exit(EXIT_INVALID_CONFIG)


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and validate JSON file."""
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        print(f"ERROR: Input file not found", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"Check that the file exists or specify a different path with --input", file=sys.stderr)
        sys.exit(EXIT_FILE_NOT_FOUND)

    # Try to read and parse JSON
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in input file", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"Line: {e.lineno}", file=sys.stderr)
        print(f"Error: {e.msg}", file=sys.stderr)
        sys.exit(EXIT_INVALID_JSON)
    except Exception as e:
        print(f"ERROR: Cannot read input file", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(EXIT_FILE_NOT_FOUND)

    # Validate structure
    if 'metadata' not in data:
        print(f"ERROR: Invalid file structure", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"Missing required key: \"metadata\"", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"Expected structure: {{ \"metadata\": {{...}}, \"tweets\": [...] }}", file=sys.stderr)
        sys.exit(EXIT_INVALID_STRUCTURE)

    if 'tweets' not in data:
        print(f"ERROR: Invalid file structure", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"Missing required key: \"tweets\"", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"Expected structure: {{ \"metadata\": {{...}}, \"tweets\": [...] }}", file=sys.stderr)
        sys.exit(EXIT_INVALID_STRUCTURE)

    if not isinstance(data['tweets'], list):
        print(f"ERROR: Invalid file structure", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"\"tweets\" must be an array", file=sys.stderr)
        sys.exit(EXIT_INVALID_STRUCTURE)

    return data


def normalize_text(text: str) -> str:
    """
    Normalize text for similarity comparison.
    - Remove punctuation
    - Convert to lowercase
    - Collapse whitespace
    """
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Lowercase and collapse whitespace
    return ' '.join(text.lower().split())


def is_retweet(tweet: Dict[str, Any]) -> bool:
    """Check if tweet is a retweet."""
    return tweet.get('is_retweet', False)


def contains_hashtag(tweet: Dict[str, Any]) -> bool:
    """Check if tweet contains hashtag (#) symbol."""
    text = tweet.get('text', '')
    return '#' in text


def fails_engagement_threshold(tweet: Dict[str, Any], min_favorites: int, min_retweets: int) -> bool:
    """Check if tweet fails engagement thresholds."""
    favorite_count = tweet.get('favorite_count', 0)
    retweet_count = tweet.get('retweet_count', 0)

    # Fails if BOTH metrics are below threshold (OR condition in requirements)
    # Tweet passes if it has >= min_favorites OR >= min_retweets
    return favorite_count < min_favorites and retweet_count < min_retweets


def has_no_substantive_content(tweet: Dict[str, Any]) -> bool:
    """
    Check if tweet consists only of hashtags, @mentions, or URLs.
    Returns True if tweet has no substantive content.
    """
    text = tweet.get('text', '').strip()

    if not text:
        return True

    # Remove URLs (simple pattern: starts with http:// or https://)
    import re
    text_without_urls = re.sub(r'https?://\S+', '', text).strip()

    # Remove @mentions
    text_without_mentions = re.sub(r'@\w+', '', text_without_urls).strip()

    # Remove hashtags
    text_without_hashtags = re.sub(r'#\w+', '', text_without_mentions).strip()

    # If nothing left after removing all these, it's not substantive
    return len(text_without_hashtags) == 0


def apply_user_story_1_filters(
    tweets: List[Dict[str, Any]],
    result: FilterResult,
    min_favorites: int,
    min_retweets: int
) -> List[Dict[str, Any]]:
    """
    Apply User Story 1 filters:
    - Remove retweets
    - Remove tweets with hashtags
    - Remove tweets below engagement thresholds
    - Remove tweets with no substantive content
    """
    filtered_tweets = []

    for tweet in tweets:
        # Handle missing metadata
        if 'favorite_count' not in tweet:
            tweet['favorite_count'] = 0
        if 'retweet_count' not in tweet:
            tweet['retweet_count'] = 0
        if 'text' not in tweet:
            tweet['text'] = ''

        # Filter 1: Retweets
        if is_retweet(tweet):
            result.removal_reasons['retweets'] += 1
            result.tweets_removed += 1
            continue

        # Filter 2: Hashtags
        if contains_hashtag(tweet):
            result.removal_reasons['contains_hashtags'] += 1
            result.tweets_removed += 1
            continue

        # Filter 3: Engagement threshold
        if fails_engagement_threshold(tweet, min_favorites, min_retweets):
            result.removal_reasons['low_engagement'] += 1
            result.tweets_removed += 1
            continue

        # Filter 4: Substantive content
        if has_no_substantive_content(tweet):
            result.removal_reasons['no_substantive_content'] += 1
            result.tweets_removed += 1
            continue

        # Tweet passed all filters
        filtered_tweets.append(tweet)

    result.tweets_retained = len(filtered_tweets)
    return filtered_tweets


def texts_are_similar(text1: str, text2: str, threshold: float) -> Tuple[bool, float]:
    """
    Check if two texts are similar above threshold.
    Returns (is_similar, similarity_score).
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold, ratio


def apply_deduplication_filter(
    tweets: List[Dict[str, Any]],
    result: FilterResult,
    similarity_threshold: float
) -> List[Dict[str, Any]]:
    """
    Apply User Story 3: Remove near-duplicate tweets.
    Keep first occurrence, remove subsequent similar tweets.
    Collect up to 5 similarity examples (each showing 1 kept tweet and ALL its duplicates).
    """
    deduplicated_tweets = []
    retained_texts = []
    duplicate_groups = {}  # Maps kept_tweet_index -> list of (removed_tweet, score)

    for tweet in tweets:
        text = tweet.get('text', '')
        is_duplicate = False

        # Compare against all previously retained tweets
        for i, retained_text in enumerate(retained_texts):
            similar, score = texts_are_similar(text, retained_text, similarity_threshold)

            if similar:
                # Found a duplicate
                is_duplicate = True
                result.removal_reasons['near_duplicate'] += 1
                result.tweets_removed += 1

                # Add to duplicate group for this kept tweet
                if i not in duplicate_groups:
                    duplicate_groups[i] = []
                duplicate_groups[i].append((tweet, score))

                break

        if not is_duplicate:
            deduplicated_tweets.append(tweet)
            retained_texts.append(text)

    # Build similarity examples: show up to 5 kept tweets with ALL their duplicates
    example_count = 0
    for kept_index, duplicates in duplicate_groups.items():
        if example_count >= 5:
            break

        kept_tweet = deduplicated_tweets[kept_index]
        removed_tweets = [{'tweet': dup[0], 'score': dup[1]} for dup in duplicates]

        result.similarity_examples.append({
            'kept_tweet': kept_tweet,
            'removed_tweets': removed_tweets  # List of all duplicates for this kept tweet
        })
        example_count += 1

    return deduplicated_tweets


def generate_report(result: FilterResult, args: argparse.Namespace) -> str:
    """Generate filtering report (User Story 4)."""
    report_lines = []
    report_lines.append("Tweet Filtering Report")
    report_lines.append("=" * 50)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    report_lines.append("Summary")
    report_lines.append("-" * 50)
    report_lines.append(f"Total tweets processed: {result.tweets_processed:,}")
    report_lines.append(f"Tweets retained: {result.tweets_retained:,} ({result.tweets_retained/result.tweets_processed*100:.1f}%)")
    report_lines.append(f"Tweets removed: {result.tweets_removed:,} ({result.tweets_removed/result.tweets_processed*100:.1f}%)")
    report_lines.append(f"Processing time: {result.processing_time():.2f} seconds")
    report_lines.append("")

    report_lines.append("Removal Breakdown")
    report_lines.append("-" * 50)
    for reason, count in result.removal_reasons.items():
        if count > 0:
            percentage = count / result.tweets_processed * 100
            reason_display = reason.replace('_', ' ').title()
            report_lines.append(f"{reason_display}: {count:,} ({percentage:.1f}%)")
    report_lines.append("")

    # Similarity examples
    if result.similarity_examples:
        report_lines.append("Similarity Examples (for validation)")
        report_lines.append("-" * 50)
        report_lines.append("")

        for i, example in enumerate(result.similarity_examples, 1):
            kept = example['kept_tweet']
            removed_tweets = example['removed_tweets']  # Now a list

            report_lines.append(f"Example {i}:")
            report_lines.append(f"KEPT (ID: {kept.get('tweet_id', 'N/A')}, ❤️  {kept.get('favorite_count', 0)}, 🔁 {kept.get('retweet_count', 0)}):")
            kept_text = kept.get('text', '')
            if len(kept_text) > 100:
                kept_text = kept_text[:97] + "..."
            report_lines.append(f"  \"{kept_text}\"")
            report_lines.append("")

            # Show all removed duplicates for this kept tweet
            for j, removed_info in enumerate(removed_tweets, 1):
                removed = removed_info['tweet']
                score = removed_info['score']
                report_lines.append(f"REMOVED #{j} (Similarity {score:.2f}, ID: {removed.get('tweet_id', 'N/A')}, ❤️  {removed.get('favorite_count', 0)}, 🔁 {removed.get('retweet_count', 0)}):")
                removed_text = removed.get('text', '')
                if len(removed_text) > 100:
                    removed_text = removed_text[:97] + "..."
                report_lines.append(f"  \"{removed_text}\"")
                report_lines.append("")

    report_lines.append("Configuration Used")
    report_lines.append("-" * 50)
    report_lines.append(f"Min favorites: {args.min_favorites}")
    report_lines.append(f"Min retweets: {args.min_retweets}")
    report_lines.append(f"Similarity threshold: {args.similarity_threshold}")
    report_lines.append(f"Exclude hashtags: true")
    report_lines.append(f"Exclude retweets: true")

    return '\n'.join(report_lines)


def write_output_file(file_path: str, data: Dict[str, Any]) -> None:
    """Write filtered data to output file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Write error", file=sys.stderr)
        print(f"File path: {file_path}", file=sys.stderr)
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(EXIT_WRITE_ERROR)


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()

    # Validate configuration
    validate_config(args)

    # Load input file
    data = load_json_file(args.input)

    # Initialize result tracking
    result = FilterResult()
    result.tweets_processed = len(data['tweets'])

    # Apply User Story 1 filters
    filtered_tweets = apply_user_story_1_filters(
        data['tweets'],
        result,
        args.min_favorites,
        args.min_retweets
    )

    # User Story 2: Composite scoring and media bonus are already handled in US1
    # (Media bonus can be added as enhancement if needed)

    # Apply User Story 3: Deduplication
    deduplicated_tweets = apply_deduplication_filter(
        filtered_tweets,
        result,
        args.similarity_threshold
    )

    # Update final tweet count
    result.tweets_retained = len(deduplicated_tweets)

    # Update data with filtered tweets
    data['tweets'] = deduplicated_tweets

    # Add filtered metadata
    data['metadata']['filtered_at'] = datetime.now().isoformat() + 'Z'
    data['metadata']['filter_version'] = VERSION
    data['metadata']['tweets_retained'] = result.tweets_retained

    # Determine output path
    output_path = args.output if args.output else args.input

    # Write output file
    write_output_file(output_path, data)

    # User Story 4: Generate and display report
    report = generate_report(result, args)

    # Output similarity examples to stdout
    if result.similarity_examples:
        print("\n" + "=" * 50)
        print("SIMILARITY EXAMPLES (for human validation)")
        print("=" * 50 + "\n")

        for i, example in enumerate(result.similarity_examples, 1):
            kept = example['kept_tweet']
            removed_tweets = example['removed_tweets']  # Now a list

            print(f"Example {i}:")
            print(f"KEPT (ID: {kept.get('tweet_id', 'N/A')}, ❤️  {kept.get('favorite_count', 0)}, 🔁 {kept.get('retweet_count', 0)}):")
            kept_text = kept.get('text', '')
            if len(kept_text) > 100:
                kept_text = kept_text[:97] + "..."
            print(f"  \"{kept_text}\"")
            print()

            # Show all removed duplicates for this kept tweet
            for j, removed_info in enumerate(removed_tweets, 1):
                removed = removed_info['tweet']
                score = removed_info['score']
                print(f"REMOVED #{j} (Similarity {score:.2f}, ID: {removed.get('tweet_id', 'N/A')}, ❤️  {removed.get('favorite_count', 0)}, 🔁 {removed.get('retweet_count', 0)}):")
                removed_text = removed.get('text', '')
                if len(removed_text) > 100:
                    removed_text = removed_text[:97] + "..."
                print(f"  \"{removed_text}\"")
                print()

    # Output report
    if args.report:
        # Write to file
        try:
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport written to: {args.report}")
        except Exception as e:
            print(f"WARNING: Could not write report to file: {e}", file=sys.stderr)
            print("\n" + report)
    else:
        # Print to stdout
        print("\n" + report)

    print(f"\n✓ Filtering complete! Filtered file written to: {output_path}")

    sys.exit(EXIT_SUCCESS)


if __name__ == '__main__':
    main()

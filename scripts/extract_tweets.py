#!/usr/bin/env python3
"""Extract Tweets to Staging File

Extracts tweets from Twitter archive (tweets.js) to human-reviewable staging format.

Usage:
    python3 scripts/extract_tweets.py [options]

Examples:
    # Extract with defaults
    python3 scripts/extract_tweets.py

    # Specify custom paths
    python3 scripts/extract_tweets.py --source etc/tweets.js --output etc/staging/tweets_staging.json

    # Verbose output
    python3 scripts/extract_tweets.py --verbose
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import utility modules
from tweet_parser import parse_tweets_file, extract_tweet_data
from speaker_detector import detect_speaker
import re


def is_meaningful_text(text: str) -> bool:
    """
    Check if tweet text contains meaningful content.

    Excludes:
    - Empty or whitespace-only text
    - Tweets with only URLs (no other content)

    Args:
        text: Tweet text to check

    Returns:
        True if text is meaningful, False otherwise
    """
    if not text or not text.strip():
        return False

    # Remove URLs to check if there's any other content
    # Simple URL pattern: http(s)://...
    import re
    text_without_urls = re.sub(r'https?://\S+', '', text).strip()

    # If nothing left after removing URLs, not meaningful
    if not text_without_urls:
        return False

    return True


def has_mentions(text: str) -> bool:
    """
    Check if tweet text contains user mentions.

    Args:
        text: Tweet text to check

    Returns:
        True if text contains @ symbol (mentions), False otherwise
    """
    return '@' in text


def strip_urls(text: str) -> str:
    """
    Remove URLs from text.

    Args:
        text: Text potentially containing URLs

    Returns:
        Text with URLs removed, stripped of extra whitespace
    """
    # Remove http(s):// URLs
    text_without_urls = re.sub(r'https?://\S+', '', text)
    # Clean up extra whitespace
    text_without_urls = ' '.join(text_without_urls.split())
    return text_without_urls.strip()


def is_retweet(text: str) -> bool:
    """
    Check if tweet is a retweet.

    Retweets start with "RT @"

    Args:
        text: Tweet text

    Returns:
        True if retweet, False otherwise
    """
    return text.strip().startswith('RT @')


def extract_media_urls(tweet: dict) -> list[str]:
    """
    Extract image URLs from tweet media fields.

    Searches entities.media and extended_entities.media for photos only.

    Args:
        tweet: Tweet object

    Returns:
        List of media_url_https strings (photos only)
    """
    media_urls = []

    # Check entities.media
    entities = tweet.get('entities', {})
    media = entities.get('media', [])

    for item in media:
        if item.get('type') == 'photo':
            url = item.get('media_url_https')
            if url and url not in media_urls:
                media_urls.append(url)

    # Check extended_entities.media (for multi-image tweets)
    extended = tweet.get('extended_entities', {})
    ext_media = extended.get('media', [])

    for item in ext_media:
        if item.get('type') == 'photo':
            url = item.get('media_url_https')
            if url and url not in media_urls:
                media_urls.append(url)

    return media_urls


def extract_to_staging(source_path: str, output_path: str, verbose: bool = False) -> dict:
    """
    Extract tweets from source to staging file.

    Args:
        source_path: Path to tweets.js file
        output_path: Path for staging JSON output
        verbose: Enable verbose progress output

    Returns:
        Dictionary with extraction statistics

    Raises:
        FileNotFoundError: If source file doesn't exist
        ValueError: If file format is invalid
        PermissionError: If cannot write to output path
    """
    source_path = Path(source_path)
    output_path = Path(output_path)

    if verbose:
        print(f"Reading tweets from: {source_path}")

    # Parse tweets.js file
    try:
        tweet_wrappers = parse_tweets_file(source_path)
    except Exception as e:
        print(f"Error parsing tweets file: {e}", file=sys.stderr)
        raise

    if verbose:
        print(f"Found {len(tweet_wrappers)} total tweets in archive")

    # Process each tweet
    staging_entries = []
    stats = {
        'total_in_archive': len(tweet_wrappers),
        'extracted': 0,
        'excluded_empty': 0,
        'excluded_url_only': 0,
        'excluded_mentions': 0,
        'flagged_retweets': 0,
        'with_media': 0,
        'speaker_detected': 0,
    }

    for i, wrapper in enumerate(tweet_wrappers):
        try:
            tweet = extract_tweet_data(wrapper)
        except ValueError as e:
            if verbose:
                print(f"Warning: Skipping invalid tweet wrapper: {e}", file=sys.stderr)
            continue

        # Extract fields
        tweet_id = tweet.get('id_str', '')
        full_text = tweet.get('full_text', '')
        created_at = tweet.get('created_at', '')

        # Convert counts from string to int (Twitter archive format quirk)
        try:
            favorite_count = int(tweet.get('favorite_count', '0'))
        except (ValueError, TypeError):
            favorite_count = 0

        try:
            retweet_count = int(tweet.get('retweet_count', '0'))
        except (ValueError, TypeError):
            retweet_count = 0

        # Check if meaningful
        if not is_meaningful_text(full_text):
            stats['excluded_empty'] += 1
            continue

        # Check for mentions - exclude tweets with @
        if has_mentions(full_text):
            stats['excluded_mentions'] += 1
            continue

        # Check retweet status
        is_rt = is_retweet(full_text)
        if is_rt:
            stats['flagged_retweets'] += 1

        # Strip URLs from text
        text_without_urls = strip_urls(full_text)

        # Detect speaker from cleaned text
        speaker, remaining_text = detect_speaker(text_without_urls)
        if speaker:
            stats['speaker_detected'] += 1

        # Extract media URLs
        media_urls = extract_media_urls(tweet)
        if media_urls:
            stats['with_media'] += 1

        # Create staging entry
        entry = {
            'tweet_id': tweet_id,
            'text': text_without_urls,  # URLs stripped, cleaned
            'created_at': created_at,  # Preserved as-is (RFC 2822 format from Twitter)
            'is_retweet': is_rt,
            'favorite_count': favorite_count,
            'retweet_count': retweet_count,
            'media_urls': media_urls,
            'primarySpeaker': speaker if speaker else '',  # Empty string if no speaker detected
        }

        staging_entries.append(entry)
        stats['extracted'] += 1

        # Progress feedback every 100 tweets
        if verbose and (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(tweet_wrappers)} tweets...")

    if verbose:
        print(f"\nExtraction complete!")
        print(f"  Total in archive: {stats['total_in_archive']}")
        print(f"  Extracted: {stats['extracted']}")
        print(f"  Excluded (empty/URL-only): {stats['excluded_empty'] + stats['excluded_url_only']}")
        print(f"  Excluded (mentions with @): {stats['excluded_mentions']}")
        print(f"  Flagged as retweets: {stats['flagged_retweets']}")
        print(f"  Speaker detected: {stats['speaker_detected']}")
        print(f"  With media: {stats['with_media']}")

    # Create staging file structure
    staging_file = {
        'metadata': {
            'extracted_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_file': str(source_path),
            'total_extracted': len(staging_entries),
            'version': '1.0',
        },
        'tweets': staging_entries,
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write staging file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(staging_file, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing staging file: {e}", file=sys.stderr)
        raise

    if verbose:
        print(f"\nStaging file written to: {output_path}")
        print(f"File size: {output_path.stat().st_size:,} bytes")

    return stats


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Extract tweets from Twitter archive to human-reviewable staging file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract with defaults
  %(prog)s

  # Specify custom paths
  %(prog)s --source etc/tweets.js --output etc/staging/tweets_staging.json

  # Verbose output
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--source',
        default='etc/tweets.js',
        help='Path to tweets.js source file (default: etc/tweets.js)'
    )

    parser.add_argument(
        '--output',
        default='etc/staging/tweets_staging.json',
        help='Path for staging JSON output (default: etc/staging/tweets_staging.json)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose progress output'
    )

    args = parser.parse_args()

    # Run extraction
    try:
        stats = extract_to_staging(args.source, args.output, args.verbose)

        # Success - print summary even without verbose
        if not args.verbose:
            print(f"✓ Extracted {stats['extracted']} tweets to {args.output}")

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

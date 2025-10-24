#!/usr/bin/env python3
"""Convert Staging File to Quotes

Converts reviewed staging file to application-ready quotes.json format.

Usage:
    python3 scripts/convert_to_quotes.py [options]

Examples:
    # Convert with defaults
    python3 scripts/convert_to_quotes.py

    # Dry run (preview without writing)
    python3 scripts/convert_to_quotes.py --dry-run

    # Specify custom paths
    python3 scripts/convert_to_quotes.py --staging etc/staging/tweets_staging.json --quotes app/data/quotes.json

    # Verbose output
    python3 scripts/convert_to_quotes.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path

from speaker_detector import detect_speaker
from quote_id_generator import get_next_quote_id


def load_staging_file(file_path: str | Path) -> dict:
    """
    Load and parse staging file.

    Args:
        file_path: Path to staging JSON file

    Returns:
        Parsed staging file data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is corrupted or invalid JSON
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Staging file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in staging file: {e}")

    if not isinstance(data, dict) or 'tweets' not in data:
        raise ValueError("Invalid staging file structure: missing 'tweets' field")

    return data


def load_quotes_file(file_path: str | Path) -> list[dict]:
    """
    Load existing quotes from quotes.json.

    Creates empty structure if file doesn't exist.

    Args:
        file_path: Path to quotes.json file

    Returns:
        List of existing quote dictionaries
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in quotes file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading quotes file: {e}")

    # Handle both array format and object format
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'quotes' in data:
        return data['quotes']
    else:
        raise ValueError("Invalid quotes file structure")


def convert_staging_to_quotes(
    staging_file: str | Path,
    quotes_file: str | Path,
    dry_run: bool = False,
    verbose: bool = False
) -> dict:
    """
    Convert staging file to quotes.json format.

    Args:
        staging_file: Path to staging JSON
        quotes_file: Path to quotes.json output
        dry_run: If True, preview conversion without writing
        verbose: Enable verbose progress output

    Returns:
        Dictionary with conversion statistics
    """
    if verbose:
        print(f"Loading staging file: {staging_file}")

    # Load staging data
    staging_data = load_staging_file(staging_file)
    staging_entries = staging_data['tweets']

    if verbose:
        print(f"Found {len(staging_entries)} entries in staging file")

    # Load existing quotes
    if verbose:
        print(f"Loading existing quotes from: {quotes_file}")

    existing_quotes = load_quotes_file(quotes_file)

    if verbose:
        print(f"Found {len(existing_quotes)} existing quotes")

    # Get starting quote ID
    next_id_num = get_next_quote_id(existing_quotes)

    if verbose:
        print(f"Next quote ID will be: {next_id_num}")

    # Process staging entries
    new_quotes = []
    stats = {
        'total_staging': len(staging_entries),
        'converted': 0,
        'skipped_retweets': 0,
        'skipped_excluded': 0,
        'speaker_extracted': 0,
    }

    # Parse the ID number for incrementing
    import re
    match = re.match(r'^quote-(\d+)$', next_id_num)
    current_id_num = int(match.group(1))

    for entry in staging_entries:
        # Skip retweets
        if entry.get('is_retweet', False):
            stats['skipped_retweets'] += 1
            continue

        # Skip manually excluded entries
        if entry.get('exclude', False):
            stats['skipped_excluded'] += 1
            continue

        # Extract speaker from text
        text = entry['text']
        speaker, quote_text = detect_speaker(text)

        if speaker:
            stats['speaker_extracted'] += 1

        # Get first media URL if available
        media_urls = entry.get('media_urls', [])
        image_url = media_urls[0] if media_urls else None

        # Create quote record
        quote = {
            'id': f'quote-{current_id_num}',
            'quote': quote_text,
            'primarySpeaker': speaker or '',
        }

        # Only include imageUrl if it exists
        if image_url:
            quote['imageUrl'] = image_url

        new_quotes.append(quote)
        current_id_num += 1
        stats['converted'] += 1

        # Progress feedback every 100 quotes
        if verbose and stats['converted'] % 100 == 0:
            print(f"Converted {stats['converted']}/{stats['total_staging']} entries...")

    if verbose:
        print(f"\nConversion complete!")
        print(f"  Total in staging: {stats['total_staging']}")
        print(f"  Converted: {stats['converted']}")
        print(f"  Skipped (retweets): {stats['skipped_retweets']}")
        print(f"  Skipped (excluded): {stats['skipped_excluded']}")
        print(f"  Speaker extracted: {stats['speaker_extracted']}")

    # Merge with existing quotes
    all_quotes = existing_quotes + new_quotes

    if dry_run:
        print("\n=== DRY RUN MODE - No files modified ===")
        print(f"Would write {len(all_quotes)} total quotes to {quotes_file}")
        print(f"  Existing: {len(existing_quotes)}")
        print(f"  New: {len(new_quotes)}")

        if new_quotes:
            print("\nSample of new quotes (first 3):")
            for quote in new_quotes[:3]:
                print(f"  - {quote['id']}: \"{quote['quote'][:60]}...\"")
                if quote.get('primarySpeaker'):
                    print(f"    Speaker: {quote['primarySpeaker']}")

        return stats

    # Write quotes file
    quotes_file = Path(quotes_file)
    quotes_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(quotes_file, 'w', encoding='utf-8') as f:
            json.dump(all_quotes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing quotes file: {e}", file=sys.stderr)
        raise

    if verbose:
        print(f"\nQuotes file written to: {quotes_file}")
        print(f"Total quotes in file: {len(all_quotes)}")
        print(f"File size: {quotes_file.stat().st_size:,} bytes")

    return stats


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Convert reviewed staging file to quotes.json format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert with defaults
  %(prog)s

  # Dry run (preview without writing)
  %(prog)s --dry-run

  # Specify custom paths
  %(prog)s --staging etc/staging/tweets_staging.json --quotes app/data/quotes.json

  # Verbose output
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--staging',
        default='etc/staging/tweets_staging.json',
        help='Path to staging JSON file (default: etc/staging/tweets_staging.json)'
    )

    parser.add_argument(
        '--quotes',
        default='app/data/quotes.json',
        help='Path to quotes.json output (default: app/data/quotes.json)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview conversion without writing to quotes.json'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose progress output'
    )

    args = parser.parse_args()

    # Run conversion
    try:
        stats = convert_staging_to_quotes(
            args.staging,
            args.quotes,
            args.dry_run,
            args.verbose
        )

        # Success - print summary even without verbose
        if not args.verbose and not args.dry_run:
            print(f"✓ Converted {stats['converted']} quotes to {args.quotes}")
            if stats['skipped_retweets'] > 0 or stats['skipped_excluded'] > 0:
                skipped_total = stats['skipped_retweets'] + stats['skipped_excluded']
                print(f"  (Skipped {skipped_total}: {stats['skipped_retweets']} retweets, {stats['skipped_excluded']} excluded)")

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

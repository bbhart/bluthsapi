#!/usr/bin/env python3
"""Verify Media Files in S3

Checks that all imageUrl references in quotes.json exist in the S3 bucket.

Usage:
    python3 scripts/verify_media_files.py [options]

Examples:
    # Verify with defaults
    python3 scripts/verify_media_files.py

    # Specify custom paths
    python3 scripts/verify_media_files.py --quotes-file app/data/quotes.json

    # Verbose output
    python3 scripts/verify_media_files.py --verbose
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse


def load_quotes_file(file_path: str | Path) -> list:
    """
    Load quotes file.

    Args:
        file_path: Path to quotes JSON file

    Returns:
        List of quote records

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is corrupted
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Quotes file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in quotes file: {e}")

    if not isinstance(data, list):
        raise ValueError("Invalid quotes file structure - expected a list")

    return data


def extract_filename(image_url: str) -> str:
    """
    Extract filename from an image URL.

    Args:
        image_url: Full or partial URL to image

    Returns:
        Filename only
    """
    # Parse the URL and get the path component
    parsed = urlparse(image_url)
    path = parsed.path if parsed.path else image_url

    # Get the last component (filename)
    filename = Path(path).name

    return filename


def check_s3_file(bucket_url: str, filename: str, timeout: int = 10) -> tuple[bool, str]:
    """
    Check if file exists in S3 bucket using HEAD request.

    Args:
        bucket_url: Base S3 bucket URL
        filename: Filename to check
        timeout: HTTP timeout in seconds

    Returns:
        Tuple of (exists, error_message)
    """
    url = f"{bucket_url}/{filename}"

    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; BluthsAPIBot/1.0)')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return (True, '')

    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        return (False, f"URL Error: {e.reason}")
    except TimeoutError:
        return (False, "Timeout")
    except Exception as e:
        return (False, str(e))


def verify_media_files(
    quotes_file: str | Path,
    bucket_url: str = "https://bqaasmedia.s3.us-east-1.amazonaws.com",
    timeout: int = 10,
    verbose: bool = False
) -> dict:
    """
    Verify that all media files referenced in quotes exist in S3.

    Args:
        quotes_file: Path to quotes JSON
        bucket_url: S3 bucket base URL
        timeout: HTTP timeout in seconds
        verbose: Enable verbose progress output

    Returns:
        Dictionary with verification statistics
    """
    if verbose:
        print(f"Loading quotes file: {quotes_file}")

    # Load quotes
    quotes = load_quotes_file(quotes_file)

    if verbose:
        print(f"Found {len(quotes)} quotes in file")

    # Collect all quotes with imageUrl
    quotes_with_images = [q for q in quotes if 'imageUrl' in q and q['imageUrl']]

    if verbose:
        print(f"Found {len(quotes_with_images)} quotes with imageUrl")

    # Verify each file
    stats = {
        'total': len(quotes_with_images),
        'success': 0,
        'fail': 0,
    }

    failed_files = []

    for i, quote in enumerate(quotes_with_images):
        quote_id = quote.get('id', 'unknown')
        image_url = quote['imageUrl']
        filename = extract_filename(image_url)

        # Check if file exists
        exists, error_msg = check_s3_file(bucket_url, filename, timeout)

        if exists:
            stats['success'] += 1
            if verbose:
                print(f"[{i+1}/{stats['total']}] ✓ {filename}")
        else:
            stats['fail'] += 1
            failed_files.append({
                'quote_id': quote_id,
                'filename': filename,
                'error': error_msg
            })
            print(f"[{i+1}/{stats['total']}] ✗ {filename} - {error_msg}")

    # Print summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total quotes with images: {stats['total']}")
    print(f"Successful verifications:  {stats['success']}")
    print(f"Failed verifications:      {stats['fail']}")
    print(f"{'='*60}")

    if failed_files:
        print(f"\nFailed files ({len(failed_files)}):")
        for item in failed_files:
            print(f"  • {item['filename']} (quote: {item['quote_id']}) - {item['error']}")

    return stats


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Verify media files in S3 bucket',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify with defaults
  %(prog)s

  # Specify custom paths
  %(prog)s --quotes-file app/data/quotes.json

  # Verbose output
  %(prog)s --verbose
        """
    )

    parser.add_argument(
        '--quotes-file',
        default='app/data/quotes.json',
        help='Path to quotes JSON file (default: app/data/quotes.json)'
    )

    parser.add_argument(
        '--bucket-url',
        default='https://bqaasmedia.s3.us-east-1.amazonaws.com',
        help='S3 bucket base URL (default: https://bqaasmedia.s3.us-east-1.amazonaws.com)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='HTTP timeout in seconds (default: 10)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose progress output'
    )

    args = parser.parse_args()

    # Run verification
    try:
        stats = verify_media_files(
            args.quotes_file,
            args.bucket_url,
            args.timeout,
            args.verbose
        )

        # Exit with error code if any failures
        sys.exit(0 if stats['fail'] == 0 else 1)

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

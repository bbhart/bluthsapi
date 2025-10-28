#!/usr/bin/env python3
"""Download Tweet Media Assets

Downloads images from tweets to local folder for S3 upload preparation.

Usage:
    python3 scripts/download_media.py [options]

Examples:
    # Download with defaults
    python3 scripts/download_media.py

    # Specify custom paths
    python3 scripts/download_media.py --staging etc/staging/tweets_staging.json --output-dir media/tweet_images

    # Skip existing files
    python3 scripts/download_media.py --skip-existing

    # Verbose output
    python3 scripts/download_media.py --verbose
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def load_staging_file(file_path: str | Path) -> dict:
    """
    Load staging file and extract media URLs.

    Args:
        file_path: Path to staging JSON file

    Returns:
        Parsed staging file data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is corrupted
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
        raise ValueError("Invalid staging file structure")

    return data


def get_original_filename(url: str) -> str:
    """
    Extract the original filename from a URL.

    Args:
        url: Media URL

    Returns:
        Original filename from URL, or generated name if extraction fails
    """
    from urllib.parse import urlparse, unquote

    # Parse the URL and extract the path
    parsed = urlparse(url)
    path = unquote(parsed.path)

    # Get the last component of the path
    filename = Path(path).name

    # If we got a valid filename with an extension, return it
    if filename and '.' in filename:
        return filename

    # Fallback: use a hash of the URL as filename
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{url_hash}.jpg"


def get_file_extension(url: str, content_type: str = None) -> str:
    """
    Determine file extension from URL or Content-Type.

    Args:
        url: Media URL
        content_type: HTTP Content-Type header (optional)

    Returns:
        File extension including dot (e.g., '.jpg')
    """
    # Try URL first
    if url.endswith('.jpg') or url.endswith('.jpeg'):
        return '.jpg'
    elif url.endswith('.png'):
        return '.png'
    elif url.endswith('.gif'):
        return '.gif'

    # Try Content-Type
    if content_type:
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'

    # Default to .jpg for Twitter images
    return '.jpg'


def check_file_exists(output_path: Path, url: str, timeout: int = 30) -> tuple[bool, int]:
    """
    Check if file exists and matches remote size.

    Args:
        output_path: Local file path
        url: Remote URL
        timeout: HTTP timeout in seconds

    Returns:
        Tuple of (should_skip, remote_size)
    """
    if not output_path.exists():
        return (False, 0)

    # File exists - check if size matches
    local_size = output_path.stat().st_size

    try:
        # Send HEAD request to get Content-Length
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; BluthsAPIBot/1.0)')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            remote_size = int(response.headers.get('Content-Length', 0))

            if remote_size > 0 and local_size == remote_size:
                return (True, remote_size)

    except Exception:
        # If HEAD request fails, re-download to be safe
        pass

    return (False, 0)


def download_file(url: str, output_path: Path, timeout: int = 30) -> tuple[bool, int, str]:
    """
    Download file from URL.

    Args:
        url: Remote URL
        output_path: Local file path
        timeout: HTTP timeout in seconds

    Returns:
        Tuple of (success, file_size, error_message)
    """
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; BluthsAPIBot/1.0)')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)

        return (True, len(data), '')

    except urllib.error.HTTPError as e:
        return (False, 0, f"HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        return (False, 0, f"URL Error: {e.reason}")
    except TimeoutError:
        return (False, 0, "Timeout")
    except Exception as e:
        return (False, 0, str(e))


def download_media(
    staging_file: str | Path,
    output_dir: str | Path,
    skip_existing: bool = False,
    timeout: int = 30,
    verbose: bool = False
) -> dict:
    """
    Download tweet media files.

    Args:
        staging_file: Path to staging JSON
        output_dir: Directory for downloaded files
        skip_existing: Skip files that already exist
        timeout: HTTP timeout in seconds
        verbose: Enable verbose progress output

    Returns:
        Dictionary with download statistics
    """
    if verbose:
        print(f"Loading staging file: {staging_file}")

    # Load staging data
    staging_data = load_staging_file(staging_file)
    tweets = staging_data['tweets']

    if verbose:
        print(f"Found {len(tweets)} tweets in staging file")

    # Collect all media URLs
    media_items = []
    for tweet in tweets:
        tweet_id = tweet.get('tweet_id', 'unknown')
        media_urls = tweet.get('media_urls', [])

        for index, url in enumerate(media_urls):
            media_items.append({
                'tweet_id': tweet_id,
                'url': url,
                'index': index,
            })

    if verbose:
        print(f"Found {len(media_items)} total media files to download")

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download each file
    stats = {
        'total': len(media_items),
        'success': 0,
        'skipped': 0,
        'error': 0,
    }

    download_records = []

    for i, item in enumerate(media_items):
        tweet_id = item['tweet_id']
        url = item['url']
        index = item['index']

        # Use original filename from URL
        filename = get_original_filename(url)
        output_path = output_dir / filename

        # Check if should skip
        if skip_existing:
            should_skip, remote_size = check_file_exists(output_path, url, timeout)
            if should_skip:
                stats['skipped'] += 1

                if verbose:
                    print(f"[{i+1}/{len(media_items)}] {filename}... ⊘ skipped (exists)")

                download_records.append({
                    'source_url': url,
                    'filename': filename,
                    'tweet_id': tweet_id,
                    'status': 'skipped',
                    'file_size_bytes': remote_size,
                })
                continue

        # Download file
        success, file_size, error_msg = download_file(url, output_path, timeout)

        if success:
            stats['success'] += 1
            status_icon = '✓'

            download_records.append({
                'source_url': url,
                'filename': filename,
                'tweet_id': tweet_id,
                'status': 'success',
                'file_size_bytes': file_size,
            })
        else:
            stats['error'] += 1
            status_icon = '✗'

            download_records.append({
                'source_url': url,
                'filename': filename,
                'tweet_id': tweet_id,
                'status': 'error',
                'error_message': error_msg,
            })

        if verbose:
            print(f"[{i+1}/{len(media_items)}] {filename}... {status_icon}")
            if not success:
                print(f"  Error: {error_msg}")

    # Write download log
    log_file = output_dir.parent / 'download_log.json'
    log_data = {
        'downloaded_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'summary': {
            'total': stats['total'],
            'success': stats['success'],
            'skipped': stats['skipped'],
            'error': stats['error'],
        },
        'downloads': download_records,
    }

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"\nDownload complete!")
        print(f"  Total: {stats['total']}")
        print(f"  Success: {stats['success']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Errors: {stats['error']}")
        print(f"\nDownload log written to: {log_file}")

    return stats


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Download tweet media assets to local folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download with defaults
  %(prog)s

  # Specify custom paths
  %(prog)s --staging etc/staging/tweets_staging.json --output-dir media/tweet_images

  # Skip existing files
  %(prog)s --skip-existing

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
        '--output-dir',
        default='media/tweet_images',
        help='Directory for downloaded images (default: media/tweet_images)'
    )

    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip files that already exist (check by size)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='HTTP timeout in seconds (default: 30)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose progress output'
    )

    args = parser.parse_args()

    # Run download
    try:
        stats = download_media(
            args.staging,
            args.output_dir,
            args.skip_existing,
            args.timeout,
            args.verbose
        )

        # Success - print summary even without verbose
        if not args.verbose:
            print(f"✓ Downloaded {stats['success']} media files to {args.output_dir}")
            if stats['skipped'] > 0:
                print(f"  (Skipped {stats['skipped']} existing files)")
            if stats['error'] > 0:
                print(f"  (Failed: {stats['error']} files)")

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

"""Staging File Validator

Validates staging file structure and schema.
"""

import json
from pathlib import Path


def validate_staging_structure(data: dict) -> tuple[bool, list[str]]:
    """
    Validate staging file matches expected schema.

    Checks:
    - Required top-level fields (metadata, tweets)
    - Metadata structure
    - Tweet entry structure

    Args:
        data: Parsed staging file data

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check top-level structure
    if not isinstance(data, dict):
        errors.append("Root must be a JSON object")
        return (False, errors)

    if 'metadata' not in data:
        errors.append("Missing required field: 'metadata'")

    if 'tweets' not in data:
        errors.append("Missing required field: 'tweets'")
        return (False, errors)

    # Validate metadata
    metadata = data.get('metadata', {})
    required_meta_fields = ['extracted_at', 'source_file', 'total_extracted', 'version']

    for field in required_meta_fields:
        if field not in metadata:
            errors.append(f"Metadata missing required field: '{field}'")

    # Validate tweets array
    tweets = data.get('tweets', [])

    if not isinstance(tweets, list):
        errors.append("'tweets' must be an array")
        return (False, errors)

    # Check count matches metadata
    if 'total_extracted' in metadata:
        expected_count = metadata['total_extracted']
        actual_count = len(tweets)
        if expected_count != actual_count:
            errors.append(
                f"Metadata total_extracted ({expected_count}) doesn't match "
                f"actual tweet count ({actual_count})"
            )

    # Validate tweet entries
    required_tweet_fields = [
        'tweet_id', 'text', 'created_at', 'is_retweet',
        'favorite_count', 'retweet_count', 'media_urls'
    ]

    for i, tweet in enumerate(tweets):
        if not isinstance(tweet, dict):
            errors.append(f"Tweet at index {i} must be an object")
            continue

        for field in required_tweet_fields:
            if field not in tweet:
                errors.append(f"Tweet at index {i} missing required field: '{field}'")

        # Type checks
        if 'text' in tweet and not isinstance(tweet['text'], str):
            errors.append(f"Tweet at index {i}: 'text' must be a string")

        if 'text' in tweet and not tweet['text'].strip():
            errors.append(f"Tweet at index {i}: 'text' cannot be empty")

        if 'is_retweet' in tweet and not isinstance(tweet['is_retweet'], bool):
            errors.append(f"Tweet at index {i}: 'is_retweet' must be a boolean")

        if 'media_urls' in tweet and not isinstance(tweet['media_urls'], list):
            errors.append(f"Tweet at index {i}: 'media_urls' must be an array")

        # Check media URLs are HTTPS
        if 'media_urls' in tweet:
            for j, url in enumerate(tweet['media_urls']):
                if not isinstance(url, str):
                    errors.append(f"Tweet at index {i}: media_urls[{j}] must be a string")
                elif not url.startswith('https://'):
                    errors.append(
                        f"Tweet at index {i}: media_urls[{j}] must use HTTPS protocol"
                    )

    is_valid = len(errors) == 0
    return (is_valid, errors)


def validate_staging_file(file_path: str | Path) -> tuple[bool, list[str]]:
    """
    Validate staging file at path.

    Args:
        file_path: Path to staging JSON file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    file_path = Path(file_path)
    errors = []

    # Check file exists
    if not file_path.exists():
        return (False, [f"File not found: {file_path}"])

    # Parse JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return (False, [f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"])
    except Exception as e:
        return (False, [f"Error reading file: {e}"])

    # Validate structure
    return validate_staging_structure(data)

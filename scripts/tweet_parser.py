"""Tweet Parser Utility

Parses tweets.js JavaScript wrapper and extracts JSON data.
"""

import json
import re
from pathlib import Path


def parse_tweets_file(file_path: str | Path) -> list[dict]:
    """
    Parse tweets.js file and extract tweet data.

    The Twitter archive format wraps JSON in a JavaScript assignment:
    window.YTD.tweets.part0 = [...]

    Args:
        file_path: Path to tweets.js file

    Returns:
        List of tweet objects extracted from the file

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid or JSON cannot be parsed
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Tweet file not found: {file_path}")

    # Read file content
    content = file_path.read_text(encoding='utf-8')

    # Strip JavaScript wrapper
    # Pattern: window.YTD.tweets.part0 = [...];
    # We want to extract just the JSON array part
    match = re.search(r'window\.YTD\.tweets\.part\d+\s*=\s*(\[.*\]);?$', content, re.DOTALL)

    if not match:
        raise ValueError(
            f"Invalid tweets.js format. Expected 'window.YTD.tweets.partN = [...]' "
            f"but got different format"
        )

    json_str = match.group(1)

    # Parse JSON
    try:
        tweets = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in tweets file: {e}")

    if not isinstance(tweets, list):
        raise ValueError(f"Expected JSON array, got {type(tweets).__name__}")

    return tweets


def extract_tweet_data(tweet_wrapper: dict) -> dict:
    """
    Extract tweet data from Twitter archive wrapper object.

    Archive format has structure: {"tweet": {...actual tweet data...}}

    Args:
        tweet_wrapper: Wrapper object containing tweet data

    Returns:
        The inner tweet object with all fields

    Raises:
        ValueError: If wrapper doesn't contain expected structure
    """
    if not isinstance(tweet_wrapper, dict):
        raise ValueError(f"Expected dict wrapper, got {type(tweet_wrapper).__name__}")

    if 'tweet' not in tweet_wrapper:
        raise ValueError("Tweet wrapper missing 'tweet' field")

    return tweet_wrapper['tweet']

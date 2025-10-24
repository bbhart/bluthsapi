"""Business logic for quote filtering and selection."""

import json
import random
from pathlib import Path
from typing import Optional

from app.models import Quote, QuoteResponse, ErrorResponse
from app.config import settings


def load_quotes() -> list[Quote]:
    """Load quotes from quotes.json file.

    Returns:
        List of Quote objects parsed from JSON file.

    Raises:
        FileNotFoundError: If quotes.json doesn't exist.
        json.JSONDecodeError: If quotes.json is malformed.
    """
    quotes_file = Path(__file__).parent / "data" / "quotes.json"

    with open(quotes_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [Quote(**quote) for quote in data["quotes"]]


def get_random_quote(quotes: list[Quote]) -> Optional[Quote]:
    """Select a random quote from the provided list.

    Args:
        quotes: List of Quote objects to select from.

    Returns:
        A randomly selected Quote, or None if list is empty.
    """
    if not quotes:
        return None

    return random.choice(quotes)


def filter_by_speaker(quotes: list[Quote], speaker: str) -> list[Quote]:
    """Filter quotes by primary speaker (case-insensitive).

    Args:
        quotes: List of Quote objects to filter.
        speaker: Speaker name to filter by (case-insensitive).

    Returns:
        List of quotes where primarySpeaker matches (case-insensitive).
    """
    speaker_lower = speaker.lower()
    return [
        q for q in quotes
        if q.primarySpeaker and q.primarySpeaker.lower() == speaker_lower
    ]


def filter_meme_quotes(quotes: list[Quote]) -> list[Quote]:
    """Filter quotes that have an associated image URL.

    Args:
        quotes: List of Quote objects to filter.

    Returns:
        List of quotes that have a non-null imageUrl.
    """
    return [q for q in quotes if q.imageUrl]


def build_quote_response(quote: Quote, s3_base_url: str) -> QuoteResponse:
    """Transform Quote to QuoteResponse with full S3 URL.

    Args:
        quote: Quote object to transform.
        s3_base_url: Base URL for S3 bucket.

    Returns:
        QuoteResponse with imageUrl prefixed with S3 base URL if present.
    """
    # Create a copy of the quote data
    quote_data = quote.model_dump(exclude_none=True)

    # If imageUrl exists, prefix it with S3 base URL
    if quote.imageUrl:
        quote_data["imageUrl"] = f"{s3_base_url.rstrip('/')}/{quote.imageUrl}"

    # Reconstruct Quote with full URL
    transformed_quote = Quote(**quote_data)

    return QuoteResponse(data=transformed_quote)


def build_error_response(message: str) -> ErrorResponse:
    """Create an error response.

    Args:
        message: Human-readable error message.

    Returns:
        ErrorResponse with the provided message.
    """
    return ErrorResponse(error=message)

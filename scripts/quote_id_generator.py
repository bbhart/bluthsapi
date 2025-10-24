"""Quote ID Generation Utility

Generates unique quote IDs with collision detection.
"""

import re


def get_next_quote_id(existing_quotes: list[dict]) -> str:
    """
    Find highest existing quote ID and return next available.

    Handles collisions by auto-incrementing.

    Format: "quote-N" (no zero-padding, e.g., "quote-1", "quote-42")

    Args:
        existing_quotes: List of quote dictionaries with 'id' field

    Returns:
        Formatted ID string (e.g., "quote-1", "quote-123")

    Examples:
        >>> get_next_quote_id([])
        'quote-1'

        >>> get_next_quote_id([{'id': 'quote-1'}, {'id': 'quote-2'}])
        'quote-3'

        >>> get_next_quote_id([{'id': 'quote-1'}, {'id': 'quote-5'}])
        'quote-6'

        >>> get_next_quote_id([{'id': 'quote-10'}, {'id': 'invalid'}])
        'quote-11'
    """
    used_ids = set()
    max_id = 0

    for quote in existing_quotes:
        quote_id = quote.get('id', '')
        match = re.match(r'^quote-(\d+)$', quote_id)

        if match:
            num = int(match.group(1))
            used_ids.add(num)
            max_id = max(max_id, num)

    # Start from max_id + 1
    next_id = max_id + 1

    # Handle collisions (shouldn't happen with monotonic IDs, but be safe)
    while next_id in used_ids:
        next_id += 1

    return f'quote-{next_id}'


def generate_quote_ids(existing_quotes: list[dict], count: int) -> list[str]:
    """
    Generate multiple sequential quote IDs.

    Args:
        existing_quotes: List of existing quote dictionaries
        count: Number of IDs to generate

    Returns:
        List of quote ID strings

    Examples:
        >>> generate_quote_ids([{'id': 'quote-1'}], 3)
        ['quote-2', 'quote-3', 'quote-4']
    """
    if count <= 0:
        return []

    # Get starting ID
    first_id = get_next_quote_id(existing_quotes)
    match = re.match(r'^quote-(\d+)$', first_id)
    start_num = int(match.group(1))

    # Generate sequential IDs
    return [f'quote-{start_num + i}' for i in range(count)]

"""Speaker Detection Utility

Detects speaker names from "Name:" prefix pattern in text.
"""

import re


def detect_speaker(text: str) -> tuple[str | None, str]:
    """
    Detect speaker from "Name:" prefix pattern.

    Matches alphabetical characters and spaces followed by a colon.
    Preserves exact capitalization from source text.

    Pattern: ^([A-Za-z\\s]+):\\s*(.+)$

    Args:
        text: Text to analyze for speaker pattern

    Returns:
        Tuple of (speaker_name, remaining_text)
        If no match: (None, original_text)

    Examples:
        >>> detect_speaker("Michael: I've made a huge mistake")
        ('Michael', "I've made a huge mistake")

        >>> detect_speaker("George Michael: Her?")
        ('George Michael', 'Her?')

        >>> detect_speaker("GOB: I've made a huge tiny mistake")
        ('GOB', "I've made a huge tiny mistake")

        >>> detect_speaker("R2D2: Beep boop")
        (None, 'R2D2: Beep boop')  # No match (contains numbers)

        >>> detect_speaker("No speaker here")
        (None, 'No speaker here')
    """
    if not text:
        return (None, text)

    # Pattern matches:
    # - One or more alphabetical characters or spaces
    # - Followed by a colon
    # - Optionally followed by whitespace
    # - Followed by remaining text
    match = re.match(r'^([A-Za-z\s]+):\s*(.+)$', text, re.DOTALL)

    if match:
        speaker = match.group(1).strip()
        remaining = match.group(2).strip()
        return (speaker, remaining)

    return (None, text)

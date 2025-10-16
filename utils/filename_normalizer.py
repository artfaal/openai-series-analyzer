"""
Filename Normalizer
Normalizes series titles for use in filenames and paths
"""

import re


def normalize_filename(text: str) -> str:
    """
    Normalizes text for use in filenames

    Removes or replaces characters that are problematic in filenames:
    - Colons (:) → nothing (removed)
    - Forward slashes (/) → nothing (removed)
    - Backslashes (\\) → nothing (removed)
    - Pipes (|) → nothing (removed)
    - Question marks (?) → nothing (removed)
    - Asterisks (*) → nothing (removed)
    - Quotes (" ') → nothing (removed)
    - Less than/greater than (< >) → nothing (removed)
    - Multiple spaces → single space
    - Leading/trailing spaces → removed

    Args:
        text: Text to normalize

    Returns:
        Normalized text safe for filenames

    Examples:
        "Dr. Stone: Science Future" → "Dr Stone Science Future"
        "Attack on Titan: Final Season" → "Attack on Titan Final Season"
        "Series / Movie" → "Series  Movie"
    """
    if not text:
        return ""

    # Remove problematic characters
    # Colons - just remove
    text = text.replace(':', '')
    # Slashes - remove
    text = text.replace('/', '')
    text = text.replace('\\', '')
    # Other forbidden characters
    text = text.replace('|', '')
    text = text.replace('?', '')
    text = text.replace('*', '')
    text = text.replace('"', '')
    text = text.replace("'", '')
    text = text.replace('<', '')
    text = text.replace('>', '')

    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing spaces
    text = text.strip()

    return text


def normalize_series_title(title: str) -> str:
    """
    Normalizes series title for directory/file names

    Same as normalize_filename but specifically for series titles
    Also removes trailing punctuation (., , - etc.) to prevent
    different folder names for the same series

    Args:
        title: Series title

    Returns:
        Normalized title

    Examples:
        "Bakuman." → "Bakuman"
        "Bakuman ." → "Bakuman"
        "Series Title," → "Series Title"
        "Title -" → "Title"
    """
    # First apply standard filename normalization
    normalized = normalize_filename(title)

    # Remove trailing punctuation (., , - etc.) and spaces
    # This prevents "Bakuman" and "Bakuman." from creating different folders
    normalized = normalized.rstrip('.,;:!?- ')

    return normalized

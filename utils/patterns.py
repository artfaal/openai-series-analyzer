"""
Regex patterns for file and directory recognition
"""

import re
from typing import Tuple, Optional


# Pattern for directory name: Title.S01.quality-GROUP
DIRECTORY_PATTERN = r'^(.+?)\.S(\d+).*?-(\w+)$'

# Pattern for episode number: S01E01 or s01e01
EPISODE_PATTERN = r'[Ss](\d+)[Ee](\d+)'


def parse_directory_name(dirname: str) -> dict:
    """
    Parses directory name

    Returns:
        dict: {'title': str, 'season': int, 'release_group': str} or empty values
    """
    info = {
        'title': None,
        'season': None,
        'year': None,
        'release_group': None
    }

    match = re.match(DIRECTORY_PATTERN, dirname)
    if match:
        info['title'] = match.group(1).replace('.', ' ')
        info['season'] = int(match.group(2))
        info['release_group'] = match.group(3)

    return info


def extract_episode_info(filename: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extracts season and episode number from filename

    Returns:
        Tuple[season, episode] or (None, None)
    """
    match = re.search(EPISODE_PATTERN, filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return season, episode

    return None, None


def detect_subtitle_track(filename: str, parent_dir: str = '') -> Optional[str]:
    """
    Determines subtitle type from filename or directory

    Returns:
        str: Track name ('Анимевод', 'Crunchyroll') or None
    """
    # From filename
    if 'Анимевод' in filename or 'анимевод' in filename.lower():
        return 'Анимевод'
    if 'CR' in filename or filename.endswith('.ru_CR.ass'):
        return 'Crunchyroll'

    # From parent directory
    if 'Анимевод' in parent_dir:
        return 'Анимевод'
    if 'CR' in parent_dir:
        return 'Crunchyroll'

    return None

"""
Regex паттерны для распознавания файлов и директорий
"""

import re
from typing import Tuple, Optional


# Паттерн для названия директории: Название.S01.качество-ГРУППА
DIRECTORY_PATTERN = r'^(.+?)\.S(\d+).*?-(\w+)$'

# Паттерн для номера эпизода: S01E01 или s01e01
EPISODE_PATTERN = r'[Ss](\d+)[Ee](\d+)'


def parse_directory_name(dirname: str) -> dict:
    """
    Парсит название директории

    Returns:
        dict: {'title': str, 'season': int, 'release_group': str} или пустые значения
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
    Извлекает номер сезона и эпизода из имени файла

    Returns:
        Tuple[season, episode] или (None, None)
    """
    match = re.search(EPISODE_PATTERN, filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return season, episode

    return None, None


def detect_subtitle_track(filename: str, parent_dir: str = '') -> Optional[str]:
    """
    Определяет тип субтитров по имени файла или директории

    Returns:
        str: Название трека ('Анимевод', 'Crunchyroll') или None
    """
    # Из имени файла
    if 'Анимевод' in filename or 'анимевод' in filename.lower():
        return 'Анимевод'
    if 'CR' in filename or filename.endswith('.ru_CR.ass'):
        return 'Crunchyroll'

    # Из родительской директории
    if 'Анимевод' in parent_dir:
        return 'Анимевод'
    if 'CR' in parent_dir:
        return 'Crunchyroll'

    return None

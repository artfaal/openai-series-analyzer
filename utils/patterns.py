"""
File and directory recognition using AI
"""

import re
import os
import json
from typing import Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from config.prompts import (
    AI_DIRECTORY_PARSING_PROMPT,
    AI_SUBTITLE_DETECTION_PROMPT,
    AI_SUBTITLE_LANGUAGE_PROMPT,
    AI_EPISODE_EXTRACTION_PROMPT,
    AI_AUDIO_STUDIO_DETECTION_PROMPT
)

# Load environment variables
load_dotenv()

# Episode number extraction is now done via AI (see extract_episode_numbers_batch)

# Initialize OpenAI client
_openai_client = None


def _get_openai_client() -> OpenAI:
    """Gets or creates OpenAI client"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file. Please add your API key.")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def parse_directory_name(dirname: str) -> dict:
    """
    Parses directory name using AI

    Args:
        dirname: Directory name

    Returns:
        dict: {'title': str, 'season': int, 'year': int, 'release_group': str}

    Raises:
        Exception: If OpenAI API request fails
    """
    try:
        client = _get_openai_client()
        model = os.getenv('OPENAI_SIMPLE_MODEL', 'gpt-4o-mini')

        prompt = AI_DIRECTORY_PARSING_PROMPT.format(dirname=dirname)

        response = client.responses.create(
            model=model,
            input=prompt
        )

        output_text = response.output_text.strip()

        # Remove markdown blocks if present
        if output_text.startswith('```'):
            output_text = output_text.split('```')[1]
            if output_text.startswith('json'):
                output_text = output_text[4:]
            output_text = output_text.strip()

        result = json.loads(output_text)
        return result

    except Exception as e:
        error_msg = f"Failed to parse directory name via OpenAI API: {e}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


def extract_episode_numbers_batch(filenames: list) -> dict:
    """
    Batch extraction of episode numbers using AI

    Args:
        filenames: List of filenames

    Returns:
        dict: {index: {'season': int or None, 'episode': int or None}}

    Raises:
        Exception: If OpenAI API request fails
    """
    if not filenames:
        return {}

    try:
        client = _get_openai_client()
        model = os.getenv('OPENAI_SIMPLE_MODEL', 'gpt-4o-mini')

        # Build batch prompt
        files_text = "\n".join([
            f"{i}. {filename}"
            for i, filename in enumerate(filenames)
        ])

        prompt = AI_EPISODE_EXTRACTION_PROMPT.format(filenames=files_text)

        response = client.responses.create(
            model=model,
            input=prompt
        )

        output_text = response.output_text.strip()

        # Remove markdown blocks if present
        if output_text.startswith('```'):
            output_text = output_text.split('```')[1]
            if output_text.startswith('json'):
                output_text = output_text[4:]
            output_text = output_text.strip()

        # Extract only JSON part (sometimes AI adds explanations after JSON)
        first_bracket = output_text.find('[')
        last_bracket = output_text.rfind(']')
        if first_bracket != -1 and last_bracket != -1:
            json_text = output_text[first_bracket:last_bracket + 1]
        else:
            json_text = output_text

        # Try to parse JSON
        try:
            results = json.loads(json_text)
        except json.JSONDecodeError as json_err:
            # Try to fix common JSON issues
            print(f"⚠️  Невалидный JSON, пытаюсь исправить...")

            # Fix trailing commas
            import re
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)

            # Try again
            try:
                results = json.loads(json_text)
                print(f"✅ JSON исправлен успешно")
            except json.JSONDecodeError:
                # Last resort: print the problematic JSON for debugging
                print(f"❌ Не удалось распарсить JSON:")
                print(json_text[:500])  # Print first 500 chars
                raise

        # Convert to dict indexed by file index
        return {
            item['index']: {
                'season': item.get('season'),
                'episode': item.get('episode')
            }
            for item in results
        }

    except Exception as e:
        error_msg = f"Failed to extract episode numbers via OpenAI API: {e}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


def extract_episode_info(filename: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Legacy function for single file episode extraction
    Uses batch function internally (inefficient, use extract_episode_numbers_batch for multiple files)

    Returns:
        Tuple[season, episode] or (None, None)
    """
    result = extract_episode_numbers_batch([filename])
    if 0 in result:
        return result[0].get('season'), result[0].get('episode')
    return None, None


def detect_subtitle_tracks_batch(file_info_list: list) -> dict:
    """
    Batch detection of subtitle tracks using AI

    Args:
        file_info_list: List of dicts with {'filename': str, 'parent_dir': str}

    Returns:
        dict: {index: track_name or None}

    Raises:
        Exception: If OpenAI API request fails
    """
    if not file_info_list:
        return {}

    try:
        client = _get_openai_client()
        model = os.getenv('OPENAI_SIMPLE_MODEL', 'gpt-4o-mini')

        # Build batch prompt
        files_text = "\n".join([
            f"{i}. Файл: {info['filename']}, Директория: {info['parent_dir']}"
            for i, info in enumerate(file_info_list)
        ])

        prompt = f"""Определи типы субтитров для следующих файлов (батч-обработка):

{files_text}

Возможные типы субтитров:
- "Анимевод" (Animevod)
- "Crunchyroll" (CR)
- "BudLightSubs" (BudLight)
- Другие студии озвучки (укажи название)
- null (если не удаётся определить)

Ответь ТОЛЬКО валидным JSON (массив объектов):
[
  {{"index": 0, "subtitle_track": "название" или null}},
  {{"index": 1, "subtitle_track": "название" или null}},
  ...
]

Примечания:
- Индекс должен соответствовать номеру файла
- Название трека должно быть на русском для русских студий"""

        response = client.responses.create(
            model=model,
            input=prompt
        )

        output_text = response.output_text.strip()

        # Remove markdown blocks if present
        if output_text.startswith('```'):
            output_text = output_text.split('```')[1]
            if output_text.startswith('json'):
                output_text = output_text[4:]
            output_text = output_text.strip()

        results = json.loads(output_text)

        # Convert to dict by index
        return {item['index']: item.get('subtitle_track') for item in results}

    except Exception as e:
        error_msg = f"Failed to detect subtitle tracks via OpenAI API (batch): {e}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


def detect_subtitle_track(filename: str, parent_dir: str = '') -> Optional[str]:
    """
    Determines subtitle type from filename or directory

    NOTE: For better performance, use detect_subtitle_tracks_batch() for multiple files

    Args:
        filename: Filename
        parent_dir: Parent directory name

    Returns:
        str: Track name ('Анимевод', 'Crunchyroll', etc.) or None
    """
    # Use batch method for single file
    result = detect_subtitle_tracks_batch([{'filename': filename, 'parent_dir': parent_dir}])
    return result.get(0)


def _read_subtitle_sample(file_path, max_lines=10, max_chars=500):
    """
    Reads a sample from subtitle file for language detection

    Args:
        file_path: Path to subtitle file
        max_lines: Maximum lines to read
        max_chars: Maximum characters to read

    Returns:
        str: Sample text from subtitle
    """
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return ""

    try:
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'shift-jis']:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    lines = []
                    total_chars = 0

                    for line in f:
                        line = line.strip()
                        # Skip empty lines and subtitle metadata
                        if not line or line.startswith('[') or '-->' in line or line.isdigit():
                            continue

                        lines.append(line)
                        total_chars += len(line)

                        if len(lines) >= max_lines or total_chars >= max_chars:
                            break

                    return '\n'.join(lines)
            except (UnicodeDecodeError, LookupError):
                continue

    except Exception as e:
        print(f"⚠️  Не удалось прочитать файл субтитров {path.name}: {e}")

    return ""


def detect_subtitle_languages_batch(subtitle_files: list) -> dict:
    """
    Batch detection of subtitle languages by analyzing content

    Args:
        subtitle_files: List of dicts with {'index': int, 'path': Path, 'filename': str}

    Returns:
        dict: {index: {'language': str, 'language_name': str}}

    Raises:
        Exception: If OpenAI API request fails
    """
    if not subtitle_files:
        return {}

    try:
        client = _get_openai_client()
        model = os.getenv('OPENAI_SIMPLE_MODEL', 'gpt-4o-mini')

        # Read samples from subtitle files
        samples_text = []
        for item in subtitle_files:
            sample = _read_subtitle_sample(item['path'])
            samples_text.append(f"{item['index']}. Файл: {item['filename']}\nСодержимое:\n{sample[:300]}")

        subtitles_samples = "\n\n".join(samples_text)

        prompt = AI_SUBTITLE_LANGUAGE_PROMPT.format(subtitles_samples=subtitles_samples)

        response = client.responses.create(
            model=model,
            input=prompt
        )

        output_text = response.output_text.strip()

        # Remove markdown blocks if present
        if output_text.startswith('```'):
            output_text = output_text.split('```')[1]
            if output_text.startswith('json'):
                output_text = output_text[4:]
            output_text = output_text.strip()

        results = json.loads(output_text)

        # Convert to dict by index
        return {
            item['index']: {
                'language': item.get('language'),
                'language_name': item.get('language_name')
            }
            for item in results
        }

    except Exception as e:
        error_msg = f"Failed to detect subtitle languages via OpenAI API (batch): {e}"
        print(f"❌ {error_msg}")
        # Don't raise - return empty dict as fallback
        return {}


def detect_audio_studios_batch(audio_info_list: list) -> dict:
    """
    Batch detection of audio studios using AI

    Args:
        audio_info_list: List of dicts with {'filename': str, 'parent_dir': str}

    Returns:
        dict: {index: studio_name or None}

    Raises:
        Exception: If OpenAI API request fails
    """
    if not audio_info_list:
        return {}

    try:
        client = _get_openai_client()
        model = os.getenv('OPENAI_SIMPLE_MODEL', 'gpt-4o-mini')

        # Build batch prompt
        files_text = "\n".join([
            f"{i}. Файл: {info['filename']}, Директория: {info['parent_dir']}"
            for i, info in enumerate(audio_info_list)
        ])

        prompt = AI_AUDIO_STUDIO_DETECTION_PROMPT.format(audio_files_info=files_text)

        response = client.responses.create(
            model=model,
            input=prompt
        )

        output_text = response.output_text.strip()

        # Remove markdown blocks if present
        if output_text.startswith('```'):
            output_text = output_text.split('```')[1]
            if output_text.startswith('json'):
                output_text = output_text[4:]
            output_text = output_text.strip()

        # Extract only JSON part
        first_bracket = output_text.find('[')
        last_bracket = output_text.rfind(']')
        if first_bracket != -1 and last_bracket != -1:
            json_text = output_text[first_bracket:last_bracket + 1]
        else:
            json_text = output_text

        results = json.loads(json_text)

        # Convert to dict by index
        return {item['index']: item.get('audio_track') for item in results}

    except Exception as e:
        error_msg = f"Failed to detect audio studios via OpenAI API (batch): {e}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

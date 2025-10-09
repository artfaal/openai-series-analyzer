"""
File Scanner
Scans directory and classifies media files
"""

from pathlib import Path
from typing import List
from models.data_models import MediaFile
from utils.patterns import extract_episode_info, detect_subtitle_track


class FileScanner:
    """Directory file scanner"""

    def __init__(self):
        self.media_extensions = {
            'video': ['.mkv', '.mp4', '.avi', '.m4v', '.ts'],
            'audio': ['.mka', '.aac', '.mp3', '.flac', '.ac3', '.dts'],
            'subtitle': ['.srt', '.ass', '.ssa', '.sub', '.sup']
        }

    def scan_directory(self, directory: Path) -> List[MediaFile]:
        """
        Scans directory and classifies files

        Args:
            directory: Path to directory to scan

        Returns:
            List of MediaFile objects
        """
        print(f"\n🔍 Сканирование директории: {directory}")

        files = []
        subtitle_hashes = {}  # For detecting duplicates

        for item in directory.rglob('*'):
            if not item.is_file() or item.name == 'Комментарий.txt':
                continue

            ext = item.suffix.lower()

            # Determine file type
            file_type = None
            for ftype, extensions in self.media_extensions.items():
                if ext in extensions:
                    file_type = ftype
                    break

            if file_type:
                season, episode = extract_episode_info(item.name)

                media_file = MediaFile(
                    path=item,
                    filename=item.name,
                    file_type=file_type,
                    season_number=season,
                    episode_number=episode
                )

                # For subtitles
                if file_type == 'subtitle':
                    media_file.subtitle_track = detect_subtitle_track(
                        item.name,
                        item.parent.name
                    )

                    # Check for subtitle duplicates
                    file_size = item.stat().st_size
                    hash_key = (episode, media_file.subtitle_track, file_size)

                    if hash_key in subtitle_hashes:
                        media_file.is_duplicate = True
                        print(f"🔄 Дубликат субтитров: {item.name}")
                    else:
                        subtitle_hashes[hash_key] = item

                files.append(media_file)

        print(f"✅ Найдено файлов: {len(files)}")
        print(f"   - Видео: {sum(1 for f in files if f.file_type == 'video')}")
        print(f"   - Аудио: {sum(1 for f in files if f.file_type == 'audio')}")
        print(f"   - Субтитры: {sum(1 for f in files if f.file_type == 'subtitle')}")

        return files

"""
File Scanner
Scans directory and classifies media files
"""

from pathlib import Path
from typing import List
from models.data_models import MediaFile
from utils.patterns import extract_episode_numbers_batch, detect_subtitle_tracks_batch, detect_subtitle_languages_batch


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
        subtitle_files = []  # Collect subtitle files for batch processing
        subtitle_hashes = {}  # For detecting duplicates

        # First pass: collect all files (without episode extraction)
        for item in directory.rglob('*'):
            # Skip preprocessing temp directory
            if '.preprocessing_temp' in item.parts:
                continue

            # Skip macOS metadata files (._*)
            if item.name.startswith('._'):
                continue

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
                media_file = MediaFile(
                    path=item,
                    filename=item.name,
                    file_type=file_type,
                    season_number=None,  # Will be filled by batch processing
                    episode_number=None  # Will be filled by batch processing
                )

                if file_type == 'subtitle':
                    subtitle_files.append(media_file)

                files.append(media_file)

        # Batch extract episode numbers for all files
        if files:
            print(f"🤖 AI-распознавание номеров эпизодов ({len(files)} файлов)...")
            filenames = [f.filename for f in files]
            episode_results = extract_episode_numbers_batch(filenames)

            # Apply results
            for idx, media_file in enumerate(files):
                if idx in episode_results:
                    media_file.season_number = episode_results[idx].get('season')
                    media_file.episode_number = episode_results[idx].get('episode')

        # Batch process subtitle track detection and language detection
        if subtitle_files:
            print(f"🤖 AI-распознавание субтитров ({len(subtitle_files)} файлов)...")

            # Detect tracks (by filename)
            subtitle_info = [
                {'filename': f.filename, 'parent_dir': f.path.parent.name}
                for f in subtitle_files
            ]
            subtitle_tracks = detect_subtitle_tracks_batch(subtitle_info)

            # Detect languages (by content) - sample first subtitle per episode
            unique_subs = {}
            for idx, media_file in enumerate(subtitle_files):
                ep_num = media_file.episode_number
                if ep_num and ep_num not in unique_subs:
                    unique_subs[ep_num] = (idx, media_file)

            if unique_subs:
                print(f"🌐 Определение языков ({len(unique_subs)} образцов)...")
                lang_detection_files = [
                    {'index': idx, 'path': mf.path, 'filename': mf.filename}
                    for idx, mf in unique_subs.values()
                ]
                language_results = detect_subtitle_languages_batch(lang_detection_files)

            # Apply results
            for idx, media_file in enumerate(subtitle_files):
                media_file.subtitle_track = subtitle_tracks.get(idx)

                # Apply language from sample if available
                if unique_subs and media_file.episode_number in unique_subs:
                    sample_idx = unique_subs[media_file.episode_number][0]
                    lang_info = language_results.get(sample_idx, {})
                    if lang_info:
                        media_file.language = lang_info.get('language_name')

                # Check for duplicates
                file_size = media_file.path.stat().st_size
                hash_key = (media_file.episode_number, media_file.subtitle_track, file_size)

                if hash_key in subtitle_hashes:
                    media_file.is_duplicate = True
                    print(f"🔄 Дубликат субтитров: {media_file.filename}")
                else:
                    subtitle_hashes[hash_key] = media_file.path

        print(f"✅ Найдено файлов: {len(files)}")
        print(f"   - Видео: {sum(1 for f in files if f.file_type == 'video')}")
        print(f"   - Аудио: {sum(1 for f in files if f.file_type == 'audio')}")
        print(f"   - Субтитры: {sum(1 for f in files if f.file_type == 'subtitle')}")

        return files
